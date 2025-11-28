"""
Flag Coordinator
Generates and places flags for all teams/services
"""

import logging
from datetime import timedelta
from django.utils import timezone

from gameserver.models import Team, Service, Flag
from gameserver.flags import generate_flag_pair, generate_flag_id
from gameserver.checker import FlagInjector
from gameserver.config import game_config

logger = logging.getLogger(__name__)


class FlagCoordinator:
    """
    Coordinates flag generation and placement across all teams/services
    """
    
    def __init__(self):
        self.injector = FlagInjector()
    
    def generate_and_place_flags(self, tick):
        """
        Generate and place flags for all active teams and services
        
        Args:
            tick: Current Tick object
        
        Returns:
            int: Number of flags successfully placed
        """
        teams = Team.objects.filter(is_active=True, is_nop_team=False)
        services = Service.objects.filter(is_active=True, supports_two_flags=True)
        
        total_flags = 0
        
        for team in teams:
            for service in services:
                flags_placed = self._generate_and_place_for_team_service(
                    team, service, tick
                )
                total_flags += flags_placed
        
        logger.info(f"Placed {total_flags} flags for tick {tick.tick_number}")
        return total_flags
    
    def _generate_and_place_for_team_service(self, team, service, tick):
        """
        Generate and place both flags for a specific team/service
        
        Returns:
            int: Number of flags placed (0-2)
        """
        try:
            # Generate flag pair
            flags = generate_flag_pair(
                team_id=team.id,
                service_id=service.id,
                tick_number=tick.tick_number
            )
            
            # Calculate validity period
            valid_from = timezone.now()
            valid_until = valid_from + timedelta(
                seconds=game_config.TICK_DURATION_SECONDS * game_config.FLAG_VALIDITY_TICKS
            )
            
            # Create database records
            user_flag = Flag.objects.create(
                team=team,
                service=service,
                tick=tick,
                flag_type=Flag.FLAG_TYPE_USER,
                flag_value=flags['user'],
                flag_id=generate_flag_id('user', tick.tick_number),
                valid_from=valid_from,
                valid_until=valid_until
            )
            
            root_flag = Flag.objects.create(
                team=team,
                service=service,
                tick=tick,
                flag_type=Flag.FLAG_TYPE_ROOT,
                flag_value=flags['root'],
                flag_id=generate_flag_id('root', tick.tick_number),
                valid_from=valid_from,
                valid_until=valid_until
            )
            
            # Inject flags into container
            container_name = service.get_container_name(team)
            result = self.injector.inject_both_flags(
                container_name=container_name,
                user_flag=flags['user'],
                root_flag=flags['root']
            )
            
            if result['success']:
                logger.info(
                    f"Placed flags for {team.name}/{service.name} "
                    f"in container {container_name}"
                )
                return 2
            else:
                logger.warning(
                    f"Partial flag placement for {team.name}/{service.name}: {result}"
                )
                return sum(1 for v in result.values() if v and isinstance(v, bool))
                
        except Exception as e:
            logger.error(
                f"Failed to place flags for {team.name}/{service.name}: {e}",
                exc_info=True
            )
            return 0
