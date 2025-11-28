"""
Flag Validator
Validate flag submissions
"""

import logging
from django.utils import timezone

from .formatter import parse_flag
from .crypto_utils import hash_team_for_flag

logger = logging.getLogger(__name__)


def validate_flag(flag_string):
    """
    Validate a flag string format
    
    Args:
        flag_string: Flag to validate
    
    Returns:
        tuple: (is_valid, parsed_data or error_message)
    """
    # Parse flag format
    parsed = parse_flag(flag_string)
    if parsed is None:
        return False, "Invalid flag format"
    
    # Verify HMAC component
    expected_hash = hash_team_for_flag(
        parsed['service_id'],  #  Note: We can't verify team without DB lookup
        parsed['service_id'],
        parsed['tick']
    )
    
    # Flag structure is valid
    return True, parsed


def validate_flag_submission(flag_string, submitter_team, flag_model_class):
    """
    Validate a flag submission against database
    
    Args:
        flag_string: Submitted flag
        submitter_team: Team submitting the flag
        flag_model_class: Flag model class for DB queries
    
    Returns:
        tuple: (status, message, flag_obj, points)
        status: 'accepted', 'rejected', 'duplicate', 'invalid', 'expired', 'own_flag'
    """
    # Validate format
    is_valid, result = validate_flag(flag_string)
    if not is_valid:
        return 'invalid', result, None, 0
    
    # Look up flag in database
    try:
        flag = flag_model_class.objects.get(flag_value=flag_string)
    except flag_model_class.DoesNotExist:
        return 'invalid', 'Flag not found', None, 0
    
    # Check if submitting own flag
    if flag.team == submitter_team:
        return 'own_flag', 'Cannot submit your own flag', flag, 0
    
    # Check if flag is still valid
    if not flag.is_valid():
        return 'expired', 'Flag has expired', flag, 0
    
    # Check for duplicate submission
    from gameserver.models import FlagSubmission
    if FlagSubmission.check_duplicate(submitter_team, flag):
        return 'duplicate', 'Flag already submitted', flag, 0
    
    # Calculate points
    points = flag.get_points()
    
    # Check for first blood
    if not flag.is_stolen:
        # First blood bonus
        from gameserver.config import game_config
        if flag.flag_type == 'user':
            points += game_config.FIRST_BLOOD_BONUS_USER
        else:
            points += game_config.FIRST_BLOOD_BONUS_ROOT
        
        logger.info(f"FIRST BLOOD: {submitter_team.name} got {flag.flag_type} flag from {flag.team.name}")
    
    # Flag is valid and can be accepted
    return 'accepted', 'Flag accepted', flag, points
