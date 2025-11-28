"""
Flag Formatter
Format and parse flag strings
"""

import re

from gameserver.config import game_config


def format_flag(team_hash, service_id, tick_number, flag_type, random):
    """
    Format a flag using the configured template
    
    Args:
        team_hash: HMAC-based team hash (12 chars)
        service_id: Service ID
        tick_number: Tick number
        flag_type: 'user' or 'root'
        random: Random hex string
    
    Returns:
        str: Formatted flag
    """
    return game_config.FLAG_FORMAT.format(
        team_hash=team_hash,
        service_id=service_id,
        tick=tick_number,
        flag_type=flag_type,
        random=random
    )


def parse_flag(flag_string):
    """
    Parse a flag string to extract components
    
    Args:
        flag_string: Flag string to parse
    
    Returns:
        dict or None: Dictionary with components if valid, None otherwise
        {
            'team_hash': str,
            'service_id': int,
            'tick': int,
            'flag_type': str,
            'random': str
        }
    """
    # Create regex pattern from flag format
    # FLAG{team_hash_service_id_tick_flag_type_random}
    pattern = r'FLAG\{([a-f0-9]{12})_(\d+)_(\d+)_(user|root)_([a-f0-9]+)\}'
    
    match = re.match(pattern, flag_string)
    if not match:
        return None
    
    return {
        'team_hash': match.group(1),
        'service_id': int(match.group(2)),
        'tick': int(match.group(3)),
        'flag_type': match.group(4),
        'random': match.group(5)
    }


def is_valid_flag_format(flag_string):
    """
    Check if a string matches the flag format
    
    Args:
        flag_string: String to check
    
    Returns:
        bool: True if valid format
    """
    return parse_flag(flag_string) is not None
