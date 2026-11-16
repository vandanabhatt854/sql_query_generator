import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.app.hosting import create_app
from backend.app.auth import allowed_origins

class HostingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        directory=Path(self.temp.name)
        (directory/'index.html').write_text('<html>QueryGenie</html>')
        (directory/'assets').mkdir()
        (directory/'assets'/'app.js').write_text('console.log("ready")')
        self.client=TestClient(create_app(directory))
        self.addCleanup(self.client.close)

    def test_health(self):
        self.assertEqual(self.client.get('/healthz').json(),{'status':'ok'})

    def test_frontend_root_and_spa_refresh(self):
        for path in ['/','/login','/history','/schema']:
            with self.subTest(path=path):
                response=self.client.get(path)
                self.assertEqual(response.status_code,200)
                self.assertIn('QueryGenie',response.text)

    def test_missing_assets_stay_404(self):
        self.assertEqual(self.client.get('/assets/missing.js').status_code,404)
        self.assertEqual(self.client.get('/assets/app.js').status_code,200)

    def test_api_mount_does_not_return_spa(self):
        self.assertIn('mode',self.client.get('/api/generation-status').json())
        self.assertEqual(self.client.get('/api/nonexistent').status_code,404)

    def test_render_origin(self):
        with patch.dict('os.environ',{'RENDER_EXTERNAL_HOSTNAME':'querygenie-example.onrender.com'}):
            self.assertIn('https://querygenie-example.onrender.com',allowed_origins())

if __name__=='__main__':unittest.main()
