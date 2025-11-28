"""
Flag Generator
Generate unique flags for teams/services/ticks
"""

import logging

from .crypto_utils import hash_team_for_flag, generate_random_hex
from .formatter import format_flag
from gameserver.config import game_config

logger = logging.getLogger(__name__)


def generate_flag(team_id, service_id, tick_number, flag_type='user'):
    """
    Generate a unique flag for a team/service/tick combination
    
    Args:
        team_id: Team ID
        service_id: Service ID
        tick_number: Current tick number
        flag_type: 'user' or 'root'
    
    Returns:
        str: Generated flag
    """
    # Generate team-specific hash component
    team_hash = hash_team_for_flag(team_id, service_id, tick_number)
    
    # Generate random component
    random = generate_random_hex(game_config.FLAG_RANDOM_LENGTH)
    
    # Format flag
    flag = format_flag(
        team_hash=team_hash,
        service_id=service_id,
        tick_number=tick_number,
        flag_type=flag_type,
        random=random
    )
    
    logger.debug(f"Generated {flag_type} flag for team={team_id}, service={service_id}, tick={tick_number}")
    
    return flag


def generate_flag_pair(team_id, service_id, tick_number):
    """
    Generate both user and root flags for a team/service/tick
    
    Args:
        team_id: Team ID
        service_id: Service ID
        tick_number: Current tick number
    
    Returns:
        dict: {'user': str, 'root': str}
    """
    return {
        'user': generate_flag(team_id, service_id, tick_number, 'user'),
        'root': generate_flag(team_id, service_id, tick_number, 'root')
    }


def generate_flag_id(flag_type, tick_number):
    """
    Generate a flag ID for checker to use
    
    Args:
        flag_type: 'user' or 'root'
        tick_number: Tick number
    
    Returns:
        str: Flag ID (e.g., 'user_42', 'root_42')
    """
    return f"{flag_type}_{tick_number}"
