"""
Score Calculator
Calculate and update team scores
"""

import logging
from django.db.models import Sum, Count, Q

from gameserver.models import Team, Score, FlagSubmission, ServiceStatus

logger = logging.getLogger(__name__)


class ScoreCalculator:
    """
    Calculate attack, defense, and SLA scores for all teams
    """
    
    @staticmethod
    def calculate_all_scores():
        """
        Calculate scores for all teams
        Returns number of teams updated
        """
        teams = Team.objects.filter(is_active=True, is_nop_team=False)
        count = 0
        
        for team in teams:
            ScoreCalculator.calculate_team_score(team)
            count += 1
        
        # Update rankings
        Score.update_rankings()
        
        logger.info(f"Updated scores for {count} teams")
        return count
    
    @staticmethod
    def calculate_team_score(team):
        """
        Calculate score for a single team
        
        Args:
            team: Team object
        """
        # Get or create score object
        score, created = Score.objects.get_or_create(team=team)
        
        # Calculate attack points
        attack_pts = ScoreCalculator._calculate_attack_points(team)
        
        # Calculate defense points
        defense_pts = ScoreCalculator._calculate_defense_points(team)
        
        # Calculate SLA points
        sla_pts, services_up, services_total = ScoreCalculator._calculate_sla_points(team)
        
        # Count flags
        flags_captured = FlagSubmission.objects.filter(
            submitter_team=team,
            status=FlagSubmission.STATUS_ACCEPTED
        ).count()
        
        from gameserver.models import Flag
        flags_lost = Flag.objects.filter(
            team=team,
            is_stolen=True
        ).count()
        
        # Update score
        score.attack_points = attack_pts
        score.defense_points = defense_pts
        score.sla_points = sla_pts
        score.flags_captured = flags_captured
        score.flags_lost = flags_lost
        score.services_up = services_up
        score.services_total = services_total
        score.calculate_total()
        
        logger.debug(
            f"{team.name}: A={attack_pts} D={defense_pts} S={sla_pts} "
            f"Total={score.total_points}"
        )
        
        return score
    
    @staticmethod
    def _calculate_attack_points(team):
        """Calculate attack points from successful submissions"""
        total = FlagSubmission.objects.filter(
            submitter_team=team,
            status=FlagSubmission.STATUS_ACCEPTED
        ).aggregate(total=Sum('points_awarded'))['total']
        
        return total or 0
    
    @staticmethod
    def _calculate_defense_points(team):
        """
        Calculate defense points
        Points for flags that were NOT stolen
        """
        from gameserver.models import Flag
        
        # Count flags that are still valid and not stolen
        defended_flags = Flag.objects.filter(
            team=team,
            is_stolen=False
        ).count()
        
        # Approximate points (would need per-flag calculation for accuracy)
        return defended_flags * 25  # Simplified defense scoring
    
    @staticmethod
    def _calculate_sla_points(team):
        """
        Calculate SLA points based on service availability
        
        Returns:
            tuple: (points, services_up, services_total)
        """
        # Get latest service statuses
        from gameserver.models import Service
        
        services = Service.objects.filter(is_active=True)
        services_total = services.count()
        
        if services_total == 0:
            return 0, 0, 0
        
        # Calculate average SLA percentage
        avg_sla = ServiceStatus.objects.filter(
            team=team,
            service__in=services
        ).aggregate(avg=Sum('sla_percentage'))['avg']
        
        if not avg_sla:
            return 0, 0, services_total
        
        # Count services that are up (SLA > 50%)
        services_up = ServiceStatus.objects.filter(
            team=team,
            service__in=services,
            sla_percentage__gte=50.0
        ).values('service').distinct().count()
        
        # SLA points based on average
        sla_points = int((avg_sla / 100.0) * services_total * 100)
        
        return sla_points, services_up, services_total
