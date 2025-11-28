"""
Flag Model
Represents flags in the CTF (supports two-flag system)
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta


class Flag(models.Model):
    """
    Flag placed in a service for teams to attack/defend
    Supports two-flag system: user flags and root flags
    """
    
    FLAG_TYPE_USER = 'user'
    FLAG_TYPE_ROOT = 'root'
    
    FLAG_TYPE_CHOICES = [
        (FLAG_TYPE_USER, 'User Flag'),
        (FLAG_TYPE_ROOT, 'Root Flag'),
    ]
    
    # Relations
    team = models.ForeignKey(
        'Team',
        on_delete=models.CASCADE,
        related_name='flags'
    )
    service = models.ForeignKey(
        'Service',
        on_delete=models.CASCADE,
        related_name='flags'
    )
    tick = models.ForeignKey(
        'Tick',
        on_delete=models.CASCADE,
        related_name='flags'
    )
    
    # Flag Data
    flag_type = models.CharField(
        max_length=4,
        choices=FLAG_TYPE_CHOICES,
        default=FLAG_TYPE_USER
    )
    flag_value = models.CharField(
        max_length=128,
        unique=True,
        db_index=True
    )
    flag_id = models.CharField(
        max_length=100,
        help_text="ID used by checker to retrieve flag"
    )
    
    # Validity
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    # Status
    is_stolen = models.BooleanField(default=False)
    stolen_count = models.IntegerField(
        default=0,
        help_text="Number of teams that stole this flag"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'flags'
        unique_together = [['team', 'service', 'tick', 'flag_type']]
        indexes = [
            models.Index(fields=['flag_value']),
            models.Index(fields=['team', 'service', 'tick']),
            models.Index(fields=['valid_until']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.flag_type} flag for {self.team.name}/{self.service.name} (tick {self.tick.tick_number})"
    
    def is_valid(self):
        """Check if flag is currently valid"""
        now = timezone.now()
        return self.valid_from <= now <= self.valid_until
    
    def get_points(self):
        """Get point value based on flag type"""
        if self.flag_type == self.FLAG_TYPE_USER:
            return self.service.user_flag_points
        return self.service.root_flag_points
    
    @classmethod
    def cleanup_expired(cls, before_datetime=None):
        """Delete expired flags"""
        if before_datetime is None:
            before_datetime = timezone.now() - timedelta(hours=1)
        
        expired = cls.objects.filter(valid_until__lt=before_datetime)
        count = expired.count()
        expired.delete()
        return count
