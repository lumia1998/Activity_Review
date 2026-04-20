from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import assistant, config, files, reports, runtime, stats, timeline
from .api import intelligence, system_api
from .services.data_service import initialize_database


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

    return app


app = create_app()
