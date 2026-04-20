import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import assistant, config, files, reports, runtime, stats, timeline
from .api import intelligence, system_api
from .services.data_service import initialize_database


def _resolve_dist_dir() -> Path | None:
    if getattr(sys, 'frozen', False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parents[2]
    dist = base / 'dist'
    if dist.is_dir() and (dist / 'index.html').exists():
        return dist
    return None


def create_app() -> FastAPI:
    initialize_database()

    app = FastAPI(title="Activity Review API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
    app.include_router(timeline.router, prefix="/api/timeline", tags=["timeline"])
    app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
    app.include_router(config.router, prefix="/api/config", tags=["config"])
    app.include_router(files.router, prefix="/api/files", tags=["files"])
    app.include_router(assistant.router, prefix="/api/assistant", tags=["assistant"])
    app.include_router(runtime.router, prefix="/api/runtime", tags=["runtime"])
    app.include_router(intelligence.router, prefix="/api/intelligence", tags=["intelligence"])
    app.include_router(system_api.router, prefix="/api/system", tags=["system"])

    dist_dir = _resolve_dist_dir()
    if dist_dir:
        app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")

    return app


app = create_app()
