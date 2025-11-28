"""
Database models package
Each model in its own file for better organization
"""

from .team import Team
from .service import Service
from .flag import Flag
from .tick import Tick
from .service_status import ServiceStatus
from .submission import FlagSubmission
from .score import Score

__all__ = [
    'Team',
    'Service',
    'Flag',
    'Tick',
    'ServiceStatus',
    'FlagSubmission',
    'Score',
]
