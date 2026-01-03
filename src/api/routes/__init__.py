from src.api.routes.games import router as games_router
from src.api.routes.checker import router as checker_router
from src.api.routes.submissions import router as submissions_router
from src.api.routes.scoreboard import router as scoreboard_router
from src.api.routes.flags import router as flags_router
from src.api.routes.ticks import router as ticks_router
from src.api.routes.vulnboxes import router as vulnboxes_router
from src.api.routes.checkers import router as checkers_router

__all__ = [
    "games_router",
    "checker_router",
    "submissions_router",
    "scoreboard_router",
    "flags_router",
    "ticks_router",
    "vulnboxes_router",
    "checkers_router",
]

