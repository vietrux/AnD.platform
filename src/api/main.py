from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.core.database import init_db
from src.api.routes import (
    games_router,
    checker_router,
    submissions_router,
    scoreboard_router,
    flags_router,
    ticks_router,
    vulnboxes_router,
    checkers_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ADG Core",
        description="CTF Attack-Defense Game Core Engine",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(games_router)
    app.include_router(vulnboxes_router)
    app.include_router(checkers_router)
    app.include_router(checker_router)
    app.include_router(submissions_router)
    app.include_router(scoreboard_router)
    app.include_router(flags_router)
    app.include_router(ticks_router)
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    return app


app = create_app()
