"""
Example Checker Template

This is a template for creating game-specific checkers.
Each game should have its own checker module following this pattern.

The checker module MUST have a function named `check` with this signature:
    def check(team_ip: str, game_id: str, team_id: str, tick_number: int) -> dict | bool

Return value:
    - bool: True = UP (100% SLA), False = DOWN (0% SLA)
    - dict: {"status": "up|down|error", "sla": 0-100, "message": "optional"}
"""

import requests
from typing import Any


def check(team_ip: str, game_id: str, team_id: str, tick_number: int) -> dict[str, Any]:
    """
    Main checker function called by CheckerWorker.
    
    Args:
        team_ip: IP address of team's vulnbox container
        game_id: UUID of the game
        team_id: Team identifier
        tick_number: Current tick number
    
    Returns:
        dict with status, sla percentage, and optional message
    """
    try:
        response = requests.get(f"http://{team_ip}:80/", timeout=5)
        
        if response.status_code == 200:
            return {
                "status": "up",
                "sla": 100.0,
                "message": None,
            }
        else:
            return {
                "status": "down",
                "sla": 0.0,
                "message": f"HTTP {response.status_code}",
            }
    
    except requests.Timeout:
        return {
            "status": "down",
            "sla": 0.0,
            "message": "Connection timeout",
        }
    
    except requests.ConnectionError:
        return {
            "status": "down",
            "sla": 0.0,
            "message": "Connection refused",
        }
    
    except Exception as e:
        return {
            "status": "error",
            "sla": 0.0,
            "message": str(e),
        }
