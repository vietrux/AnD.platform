"""
Score Model
Cached scores for each team
"""

from django.db import models


class Score(models.Model):
    """
    Aggregated score for a team
    Updated after each tick
    """
    
    # Relation
    team = models.OneToOneField(
        'Team',
        on_delete=models.CASCADE,
        related_name='score',
        primary_key=True
    )
    
    # Score Components
    attack_points = models.IntegerField(default=0)
    defense_points = models.IntegerField(default=0)
    sla_points = models.IntegerField(default=0)
    
    # Total
    total_points = models.IntegerField(default=0, db_index=True)
    
    # Ranking
    rank = models.IntegerField(default=0, db_index=True)
    
    # Statistics
    flags_captured = models.IntegerField(default=0)
    flags_lost = models.IntegerField(default=0)
    services_up = models.IntegerField(default=0)
    services_total = models.IntegerField(default=0)
    
    # Metadata
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'scores'
        ordering = ['-total_points', 'team__name']
    
    def __str__(self):
        return f"{self.team.name}: {self.total_points} pts (rank #{self.rank})"
    
    def calculate_total(self):
        """Calculate total score from components"""
        self.total_points = (
            self.attack_points +
            self.defense_points +
            self.sla_points
        )
        self.save(update_fields=['total_points', 'last_updated'])
    
    @property
    def sla_percentage(self):
        """Calculate SLA percentage"""
        if self.services_total == 0:
            return 0.0
        return (self.services_up / self.services_total) * 100.0
    
    @classmethod
    def update_rankings(cls):
        """Update rankings for all teams based on total points"""
        scores = cls.objects.all().order_by('-total_points', 'team__name')
        
        current_rank = 1
        prev_points = None
        teams_with_same_points = 0
        
        for score in scores:
            if prev_points is not None and score.total_points < prev_points:
                current_rank += teams_with_same_points
                teams_with_same_points = 1
            else:
                teams_with_same_points += 1
            
            score.rank = current_rank
            score.save(update_fields=['rank'])
            prev_points = score.total_points
