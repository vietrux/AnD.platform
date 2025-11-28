"""
FlagSubmission Model
Tracks flag submissions by teams
"""

from django.db import models
from django.utils import timezone


class FlagSubmission(models.Model):
    """
    Record of a flag submission by a team
    """
    
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_DUPLICATE = 'duplicate'
    STATUS_INVALID = 'invalid'
    STATUS_EXPIRED = 'expired'
    STATUS_OWN_FLAG = 'own_flag'
    
    STATUS_CHOICES = [
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_DUPLICATE, 'Duplicate'),
        (STATUS_INVALID, 'Invalid'),
        (STATUS_EXPIRED, 'Expired'),
        (STATUS_OWN_FLAG, 'Own Flag'),
    ]
    
    # Relations
    submitter_team = models.ForeignKey(
        'Team',
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    flag = models.ForeignKey(
        'Flag',
        on_delete=models.CASCADE,
        related_name='submissions',
        null=True,
        blank=True
    )
    
    # Submission Data
    submitted_flag = models.CharField(max_length=128, db_index=True)
    submitter_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Result
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        db_index=True
    )
    points_awarded = models.IntegerField(default=0)
    
    # Metadata
    submitted_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        db_table = 'flag_submissions'
        indexes = [
            models.Index(fields=['submitter_team', '-submitted_at']),
            models.Index(fields=['flag']),
            models.Index(fields=['status']),
        ]
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.submitter_team.name} submitted flag ({self.status})"
    
    @property
    def is_successful(self):
        """Check if submission was accepted"""
        return self.status == self.STATUS_ACCEPTED
    
    @classmethod
    def check_duplicate(cls, submitter_team, flag):
        """Check if this team already submitted this flag"""
        return cls.objects.filter(
            submitter_team=submitter_team,
            flag=flag,
            status=cls.STATUS_ACCEPTED
        ).exists()
    
    @classmethod
    def get_first_blood(cls, flag):
        """Get first blood submission for a flag"""
        return cls.objects.filter(
            flag=flag,
            status=cls.STATUS_ACCEPTED
        ).order_by('submitted_at').first()
