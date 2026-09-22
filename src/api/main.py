"""Run from the repository root: uvicorn Web.src.api.main:app --host 127.0.0.1 --port 8000."""
from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy.exc import SQLAlchemyError

from .db import DatabaseConfigurationError, engine
from .core import router as core_router
from .sequence import router as sequence_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    if engine.cache_info().currsize:
        engine().dispose()


app = FastAPI(title='memVar API', version='0.1.0', lifespan=lifespan,
              description='Read-only access to confirmed membrane-protein entities and source evidence.')
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.include_router(core_router)
app.include_router(sequence_router)

from .evidence import router as evidence_router
from .structures import router as structures_router

app.include_router(evidence_router)
app.include_router(structures_router)

from .interface_predictions import router as interface_router
app.include_router(interface_router)

from .alphagenome import router as alphagenome_router
app.include_router(alphagenome_router)

from .catalog_statistics import router as catalog_statistics_router
app.include_router(catalog_statistics_router)

from .sequence_prediction_coverage import router as sequence_prediction_router
app.include_router(sequence_prediction_router)


@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, exc: SQLAlchemyError):
    logging.getLogger('memvar.api').error('Database request failed: %s', type(exc).__name__)
    return JSONResponse(status_code=503, content={'detail': 'Database query is temporarily unavailable. Please retry or narrow the filter.'})


@app.exception_handler(DatabaseConfigurationError)
async def database_configuration_error(request: Request, exc: DatabaseConfigurationError):
    return JSONResponse(status_code=503, content={'detail': 'The read-only database connection is not configured.'})


DIST = Path(__file__).resolve().parents[2] / 'frontend/dist'
if (DIST / 'assets').is_dir():
    app.mount('/assets', StaticFiles(directory=DIST / 'assets'), name='assets')


@app.get('/{path:path}', include_in_schema=False)
def frontend(path: str):
    if path == 'api' or path.startswith('api/'):
        raise HTTPException(404, 'Unknown API endpoint.')
    if '\x00' in path or any(part.startswith('.') for part in Path(path).parts):
        raise HTTPException(404, 'File not found.')
    candidate = (DIST / path).resolve()
    if candidate != DIST.resolve() and DIST.resolve() not in candidate.parents:
        raise HTTPException(404, 'File not found.')
    if DIST.resolve() in candidate.parents and candidate.is_file():
        return FileResponse(candidate)
    if path.startswith('assets/') or Path(path).suffix:
        raise HTTPException(404, 'Static asset not found.')
    if (DIST / 'index.html').is_file():
        return FileResponse(DIST / 'index.html', headers={'Cache-Control': 'no-cache'})
    raise HTTPException(404, 'Frontend build is not present. Run npm run build in Web/frontend.')
