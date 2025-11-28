"""
ServiceStatus Model
Tracks SLA and checker results for each team's service
"""

from django.db import models


class ServiceStatus(models.Model):
    """
    Service Level Agreement (SLA) tracking per team per service per tick
    """
    
    STATUS_UP = 'up'
    STATUS_DOWN = 'down'
    STATUS_CORRUPTED = 'corrupted'
    STATUS_UNKNOWN = 'unknown'
    
    STATUS_CHOICES = [
        (STATUS_UP, 'Up'),
        (STATUS_DOWN, 'Down'),
        (STATUS_CORRUPTED, 'Corrupted'),
        (STATUS_UNKNOWN, 'Unknown'),
    ]
    
    # Relations
    team = models.ForeignKey(
        'Team',
        on_delete=models.CASCADE,
        related_name='service_statuses'
    )
    service = models.ForeignKey(
        'Service',
        on_delete=models.CASCADE,
        related_name='service_statuses'
    )
    tick = models.ForeignKey(
        'Tick',
        on_delete=models.CASCADE,
        related_name='service_statuses'
    )
    
    # Status
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_UNKNOWN
    )
    
    # Checker Results
    user_flag_placed = models.BooleanField(default=False)
    root_flag_placed = models.BooleanField(default=False)
    user_flag_retrieved = models.BooleanField(default=False)
    root_flag_retrieved = models.BooleanField(default=False)
    
    # Performance Metrics
    check_duration_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Checker execution time in milliseconds"
    )
    
    # Error Tracking
    error_message = models.TextField(blank=True)
    
    # SLA Calculation
    sla_percentage = models.FloatField(
        default=0.0,
        help_text="0-100 percentage for this check"
    )
    
    # Metadata
    checked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'service_statuses'
        unique_together = [['team', 'service', 'tick']]
        indexes = [
            models.Index(fields=['team', 'service']),
            models.Index(fields=['tick']),
            models.Index(fields=['status']),
        ]
        ordering = ['-checked_at']
    
    def __str__(self):
        return f"{self.team.name}/{self.service.name} @ tick {self.tick.tick_number}: {self.status}"
    
    def calculate_sla(self):
        """
        Calculate SLA percentage based on check results
        100% if all checks passed, proportional otherwise
        """
        total_checks = 0
        passed_checks = 0
        
        # Service must be up
        if self.status != self.STATUS_UP:
            self.sla_percentage = 0.0
            return
        
        # Count flag checks
        if self.user_flag_placed:
            total_checks += 1
            if self.user_flag_retrieved:
                passed_checks += 1
        
        if self.root_flag_placed:
            total_checks += 1
            if self.root_flag_retrieved:
                passed_checks += 1
        
        if total_checks > 0:
            self.sla_percentage = (passed_checks / total_checks) * 100.0
        else:
            self.sla_percentage = 100.0 if self.status == self.STATUS_UP else 0.0
        
        self.save(update_fields=['sla_percentage'])
