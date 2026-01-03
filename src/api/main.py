from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.core.database import engine, Base
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
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods including OPTIONS
        allow_headers=["*"],  # Allow all headers
    )
    
    app.include_router(games_router)
    app.include_router(checker_router)
    app.include_router(submissions_router)
    app.include_router(scoreboard_router)
    app.include_router(flags_router)
    app.include_router(ticks_router)
    app.include_router(vulnboxes_router)
    app.include_router(checkers_router)
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    return app


app = create_app()
