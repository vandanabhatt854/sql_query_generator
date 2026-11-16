"""Single-origin hosted application: API under /api and built React frontend."""
from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from .main import app as api, ensure_demo_ready


@asynccontextmanager
async def lifespan(app):
    ensure_demo_ready()
    yield


class SPAFiles(StaticFiles):
    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as error:
            # Only application routes fall back; missing JS/CSS must remain 404.
            if error.status_code == 404 and not Path(path).suffix:
                return FileResponse(Path(self.directory) / 'index.html')
            raise


def create_app(frontend_dir=None):
    hosted = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @hosted.get('/healthz')
    def health():
        return {'status': 'ok'}

    hosted.mount('/api', api)
    directory = Path(frontend_dir or os.getenv('FRONTEND_DIST', str(Path(__file__).resolve().parents[2] / 'frontend' / 'dist')))
    hosted.mount('/', SPAFiles(directory=directory, html=True, check_dir=False), name='frontend')
    return hosted


app = create_app()
