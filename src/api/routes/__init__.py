from src.api.routes.games import router as games_router
from src.api.routes.checker import router as checker_router
from src.api.routes.submission import router as submission_router
from src.api.routes.scoreboard import router as scoreboard_router

__all__ = [
    "games_router",
    "checker_router",
    "submission_router",
    "scoreboard_router",
]
