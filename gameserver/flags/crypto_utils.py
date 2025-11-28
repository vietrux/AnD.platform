"""
Cryptographic Utilities
HMAC generation and secure random generation for flags
"""

import hmac
import hashlib
import secrets

from gameserver.config import game_config


def generate_hmac(data, key=None):
    """
    Generate HMAC-SHA256 hash
    
    Args:
        data: String data to hash
        key: HMAC key (defaults to FLAG_HMAC_KEY from config)
    
    Returns:
        str: Hex digest of HMAC
    """
    if key is None:
        key = game_config.FLAG_HMAC_KEY
    
    h = hmac.new(
        key.encode(),
        data.encode(),
        hashlib.sha256
    )
    return h.hexdigest()


def generate_random_hex(length=16):
    """
    Generate cryptographically secure random hex string
    
    Args:
        length: Length of random hex string
    
    Returns:
        str: Random hex string
    """
    return secrets.token_hex(length // 2)


def hash_team_for_flag(team_id, service_id, tick_number):
    """
    Generate team hash component for flag
    Uses first 12 characters of HMAC for brevity
    
    Args:
        team_id: Team ID
        service_id: Service ID
        tick_number: Tick number
    
    Returns:
        str: 12-character team hash
    """
    data = f"{team_id}:{service_id}:{tick_number}"
    full_hash = generate_hmac(data)
    return full_hash[:12]
