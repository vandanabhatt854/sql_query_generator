import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.app import main, auth
from backend.app.database import Base, get_db
from backend.app.agents.schema_understanding import SchemaUnderstandingAgent
from backend.app.agents.query_impact import QueryImpactAnalyzer
from backend.app.agents.query_execution import QueryExecutionAgent
from backend.app.agents.offline_query import QueryRequestError

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        self.addCleanup(self.engine.dispose)
        Base.metadata.create_all(self.engine)
        with self.engine.begin() as connection:
            connection.execute(text("INSERT INTO Department(id,name,location) VALUES (1,'IT','Delhi')"))
            connection.execute(text("INSERT INTO Employee(id,name,department,salary,join_date,email) VALUES(1,'Test','IT',50000,'2025-01-01','test@example.com')"))
        factory = sessionmaker(bind=self.engine)
        schema_agent = SchemaUnderstandingAgent(self.engine)
        def ensure(): schema_agent.refresh()
        patches = [patch.object(auth, 'AUTH_DB', Path(self.temp.name)/'accounts.db'), patch.object(main, 'ensure_demo_ready', ensure), patch.object(main, 'schema_agent', schema_agent), patch.object(main, 'impact_agent', QueryImpactAnalyzer(factory)), patch.object(main, 'execution_agent', QueryExecutionAgent(self.engine)), patch.object(main.limiter, 'enabled', False), patch.dict('os.environ', {'SIMULATE_WRITES_ONLY': 'True'})]
        for p in patches:
            p.start(); self.addCleanup(p.stop)
        def database():
            with factory() as session: yield session
        main.app.dependency_overrides[get_db] = database
        self.addCleanup(main.app.dependency_overrides.clear)
        self.client = TestClient(main.app)
        self.addCleanup(self.client.close)
        ensure()

    def test_register_session_logout(self):
        response = self.client.post('/auth/register', json={'name':'Tester','email':'tester@example.com','password':'Test-password-123'})
        self.assertEqual(response.status_code,200)
        self.assertIn('HttpOnly', response.headers['set-cookie'])
        self.assertNotIn('password', response.text)
        self.assertEqual(self.client.get('/auth/me').json()['user']['name'],'Tester')
        self.assertEqual(self.client.post('/auth/logout').status_code,200)
        self.assertEqual(self.client.get('/auth/me').status_code,401)

    def test_login_and_duplicate(self):
        values={'name':'Tester','email':'test@example.com','password':'Test-password-123'}
        self.client.post('/auth/register',json=values)
        self.assertEqual(self.client.post('/auth/register',json=values).status_code,409)
        self.client.post('/auth/logout')
        self.assertEqual(self.client.post('/auth/login',json={'email':values['email'],'password':'wrong-password'}).status_code,401)
        self.assertEqual(self.client.post('/auth/login',json=values).status_code,200)

    def test_auth_origin_and_weak_password(self):
        self.assertEqual(self.client.post('/auth/register',json={'name':'X','email':'x@example.com','password':'short'}).status_code,422)
        self.assertEqual(self.client.post('/auth/logout',headers={'Origin':'https://untrusted.example'}).status_code,403)

    def test_schema_excludes_internal_tables(self):
        response=self.client.get('/schema')
        self.assertEqual(response.status_code,200)
        self.assertIn('Employee',response.json())
        self.assertNotIn('QueryHistory',response.json())
        self.assertNotIn('users',response.json())

    def test_select_and_history_preserve_operators(self):
        sql='SELECT name FROM Employee WHERE salary > 100;'
        response=self.client.post('/execute',json={'sql':sql})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['rows'],[{'name':'Test'}])
        self.assertEqual(self.client.get('/history').json()[0]['sql_generated'],sql)

    def test_cte_read(self):
        response=self.client.post('/execute',json={'sql':'WITH people AS (SELECT name FROM Employee) SELECT name FROM people;'})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['rows'],[{'name':'Test'}])

    def test_unsafe_sql_and_unknown_columns(self):
        for sql in ['DROP TABLE Employee;', 'DELETE FROM Employee;', "DELETE FROM Employee WHERE 'x'='x'; DROP TABLE Students;", 'SELECT grade FROM Students;', 'PRAGMA table_info(Employee);', 'SELECT * FROM users;', 'SELECT name FROM Employee -- comment']:
            with self.subTest(sql=sql):
                self.assertEqual(self.client.post('/execute',json={'sql':sql}).status_code,400)

    def test_write_simulation_leaves_data_unchanged(self):
        response=self.client.post('/execute',json={'sql':'UPDATE "Employee" SET salary=1 WHERE id=1;'})
        self.assertTrue(response.json()['simulated'])
        self.assertEqual(response.json()['rows_affected'],1)
        self.assertEqual(self.client.post('/execute',json={'sql':'SELECT salary FROM Employee;'}).json()['rows'][0]['salary'],50000)

    def test_generate_success(self):
        with patch.object(main.QueryGenerationAgent,'generate',return_value=[{'sql':'SELECT name FROM Employee;'}]):
            response=self.client.post('/generate',json={'nl_query':'Show employee names'})
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.json()['candidates'][0]['explanation']['query_explanation'])
        self.assertEqual(self.client.get('/history').json()[0]['nl_input'],'Show employee names')

    def test_clarification_and_provider_failure(self):
        for error in [QueryRequestError('Which department?'),QueryRequestError('Provider unavailable','provider_unavailable',503)]:
            with patch.object(main.QueryGenerationAgent,'generate',side_effect=error):
                response=self.client.post('/generate',json={'nl_query':'show best'})
            self.assertEqual(response.status_code,error.status_code)
            self.assertEqual(response.json()['detail']['code'],error.code)

    def test_input_limits(self):
        self.assertEqual(self.client.post('/generate',json={'nl_query':'x'*501}).status_code,422)
        self.assertEqual(self.client.post('/execute',json={'sql':''}).status_code,422)

if __name__=='__main__': unittest.main()
