from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.core.database import engine, Base
from src.api.routes import (
    games_router,
    checker_router,
    submission_router,
    scoreboard_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ADG Core",
        description="CTF Attack-Defense Game Core Engine",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    app.include_router(games_router)
    app.include_router(checker_router)
    app.include_router(submission_router)
    app.include_router(scoreboard_router)
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    return app


app = create_app()
