import json
import os
import sqlite3
import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, patch

from backend.app.agents.query_generation import QueryGenerationAgent
from backend.app.agents.offline_query import OfflineQuery, QueryRequestError
from backend.app.agents.query_explanation import QueryExplanationAgent

SCHEMA = {
    'Employee': {'columns': [{'name': name, 'type': kind} for name, kind in [('id', 'INTEGER'), ('name', 'TEXT'), ('salary', 'REAL'), ('department', 'TEXT'), ('join_date', 'TEXT')]]},
    'Students': {'columns': [{'name': name, 'type': kind} for name, kind in [('id', 'INTEGER'), ('name', 'TEXT'), ('course', 'TEXT'), ('cgpa', 'REAL')]]},
    'Department': {'columns': [{'name': 'name', 'type': 'TEXT'}]},
}

class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'ANTHROPIC_API_KEY': '', 'GOOGLE_API_KEY': '', 'LLM_PROVIDER': 'ANTHROPIC'})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.agent = QueryGenerationAgent(SCHEMA)
        self.db = sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)
        self.db.executescript('''CREATE TABLE Employee (id INTEGER, name TEXT, salary REAL, department TEXT, join_date TEXT);
        INSERT INTO Employee VALUES (1, 'A', 50000, 'Sales', '2025-01-01'), (2, 'B', 90000, 'IT', '2025-12-31'), (3, 'C', 90000, 'IT', '2026-01-01');
        CREATE TABLE Students (id INTEGER, name TEXT, course TEXT, cgpa REAL);
        INSERT INTO Students VALUES (1, 'S', 'Computer Science', 9.4);
        CREATE TABLE Department (name TEXT);''')

    def run_request(self, text):
        candidate = self.agent.generate(text, 'UNKNOWN')[0]
        return self.db.execute(candidate['sql']).fetchall()

    def test_total_salary(self):
        self.assertEqual(self.run_request('Calculate total salary'), [(230000.0,)])

    def test_aggregate_by_department(self):
        self.assertEqual(self.run_request('What is the average salary in each department?'), [('IT', 90000.0), ('Sales', 50000.0)])

    def test_highest_earner_includes_ties(self):
        self.assertEqual([r[1] for r in self.run_request('Who earns the most?')], ['B', 'C'])

    def test_last_year_calendar_boundaries(self):
        sql = OfflineQuery(SCHEMA, date(2026, 11, 16)).generate('Show employees who joined last year')
        self.assertEqual([r[1] for r in self.db.execute(sql)], ['A', 'B'])

    def test_numeric_filter(self):
        self.assertEqual(len(self.run_request('Show all employees whose salary is greater than 50,000')), 2)

    def test_case_insensitive_department(self):
        self.assertEqual(self.run_request('Show me all employees from the sales department')[0][1], 'A')

    def test_count_groups(self):
        self.assertEqual(self.run_request('Count how many employees are in each department'), [('IT', 2), ('Sales', 1)])

    def test_course_filter(self):
        self.assertEqual(len(self.run_request('Get all students enrolled in Computer Science')), 1)

    def test_no_invented_grade(self):
        with self.assertRaises(QueryRequestError) as error:
            self.run_request('Get all students enrolled in Computer Science with grade A or B')
        self.assertEqual(error.exception.code, 'unsupported')

    def test_no_unknown_table_fallback(self):
        with self.assertRaises(QueryRequestError):
            self.run_request('Show all customers')

    def test_ambiguous_and_unrelated_requests(self):
        for text in ['show best people', 'hello', 'employees with good salaries', 'increase employee salary', 'average salary of employees in sales', 'show employees with salary above 50000 and department is sales']:
            with self.subTest(text=text), self.assertRaises(QueryRequestError):
                self.run_request(text)

    def test_sql_validation(self):
        for sql in ['SELECT grade FROM Students;', 'SELECT "grade" FROM Students;', 'SELECT * FROM Customers;', 'DELETE FROM Employee;', 'SELECT * FROM Employee; DROP TABLE Employee;', 'SELECT name FROM Employee -- ignore rules']:
            with self.subTest(sql=sql):
                self.assertFalse(self.agent._validate_sql(sql))
        self.assertTrue(self.agent._validate_sql('SELECT e.name FROM Employee e JOIN Department d ON e.department = d.name;'))

    def ai(self, payload):
        client = Mock()
        client.messages.create.return_value = SimpleNamespace(content=[SimpleNamespace(text=json.dumps(payload))])
        return QueryGenerationAgent(SCHEMA, llm_client=client)

    def test_ai_handles_non_template_wording(self):
        agent = self.ai({'status': 'ok', 'candidates': [{'sql': 'SELECT name FROM Employee WHERE salary > (SELECT AVG(salary) FROM Employee);'}]})
        sql = agent.generate('Which staff members earn above the company average?', 'UNKNOWN')[0]['sql']
        self.assertEqual(self.db.execute(sql).fetchall(), [('B',), ('C',)])
        sent = agent.client.messages.create.call_args.kwargs['messages'][0]['content']
        self.assertIn('join_date', sent)
        self.assertIn('Which staff', sent)

    def test_ai_clarification(self):
        agent = self.ai({'status': 'clarification', 'message': 'Which field defines best?'})
        with self.assertRaisesRegex(QueryRequestError, 'Which field'):
            agent.generate('best employees', 'UNKNOWN')

    def test_ai_invalid_sql_never_falls_back(self):
        agent = self.ai({'status': 'ok', 'candidates': [{'sql': 'SELECT nonexistent FROM Employee;'}]})
        with self.assertRaises(QueryRequestError) as error:
            agent.generate('show employees', 'SELECT')
        self.assertEqual(error.exception.code, 'invalid_sql')

    def test_provider_failure_never_falls_back(self):
        client = Mock()
        client.messages.create.side_effect = RuntimeError('secret provider detail')
        with self.assertRaises(QueryRequestError) as error:
            QueryGenerationAgent(SCHEMA, client).generate('show employees', 'SELECT')
        self.assertEqual(error.exception.status_code, 503)
        self.assertNotIn('secret provider detail', str(error.exception))

    def test_gemini_adapter(self):
        with patch.dict(os.environ, {'LLM_PROVIDER': 'GOOGLE'}):
            client = Mock()
            client.models.generate_content.return_value = SimpleNamespace(text=json.dumps({'status': 'ok', 'candidates': [{'sql': 'SELECT SUM(salary) FROM Employee;'}]}))
            agent = QueryGenerationAgent(SCHEMA, client)
            self.assertIn('SUM', agent.generate('total salary', 'AGGREGATE')[0]['sql'])
            self.assertEqual(client.models.generate_content.call_args.kwargs['config']['response_mime_type'], 'application/json')

    def test_explanation_quoted_identifiers(self):
        details = QueryExplanationAgent().explain('SELECT "join_date" FROM "Employee";')
        self.assertEqual(details['tables_involved'], ['employee'])
        self.assertNotIn('JOIN', details['clauses_used'])

if __name__ == '__main__':
    unittest.main()
