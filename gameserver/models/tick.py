"""
Tick Model
Represents a round/tick in the CTF competition
"""

from django.db import models
from django.utils import timezone


class Tick(models.Model):
    """
    A round/tick in the competition (typically 60 seconds)
    """
    
    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'
    STATUS_ERROR = 'error'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_ERROR, 'Error'),
    ]
    
    # Tick Information
    tick_number = models.IntegerField(unique=True, db_index=True)
    
    # Timing
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(
        default=60,
        help_text="Expected duration in seconds"
    )
    
    # Status
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    
    # Statistics
    flags_placed = models.IntegerField(default=0)
    flags_checked = models.IntegerField(default=0)
    checker_errors = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ticks'
        ordering = ['-tick_number']
    
    def __str__(self):
        return f"Tick {self.tick_number} ({self.status})"
    
    def start(self):
        """Mark tick as active"""
        self.status = self.STATUS_ACTIVE
        self.start_time = timezone.now()
        self.save(update_fields=['status', 'start_time', 'updated_at'])
    
    def complete(self):
        """Mark tick as completed"""
        self.status = self.STATUS_COMPLETED
        self.end_time = timezone.now()
        self.save(update_fields=['status', 'end_time', 'updated_at'])
    
    def mark_error(self):
        """Mark tick as having encountered an error"""
        self.status = self.STATUS_ERROR
        self.save(update_fields=['status', 'updated_at'])
    
    @property
    def actual_duration(self):
        """Get actual duration if tick has ended"""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @classmethod
    def get_current_tick(cls):
        """Get the currently active tick"""
        return cls.objects.filter(status=cls.STATUS_ACTIVE).first()
    
    @classmethod
    def get_latest_tick(cls):
        """Get the most recent tick"""
        return cls.objects.first()  # Ordered by -tick_number
