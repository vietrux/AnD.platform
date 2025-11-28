"""
Service Model
Represents a vulnerable service in the CTF
"""

from django.db import models


class Service(models.Model):
    """
    Vulnerable service that teams must attack and defend
    """
    
    # Basic Information
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Service Configuration
    port = models.IntegerField(
        help_text="Port number where service listens"
    )
    
    # Checker Configuration
    checker_script = models.CharField(
        max_length=200,
        help_text="Path to checker script (e.g., 'checkers.web_service_checker')"
    )
    checker_timeout = models.IntegerField(
        default=30,
        help_text="Checker timeout in seconds"
    )
    
    # Docker Configuration
    docker_image = models.CharField(
        max_length=200,
        help_text="Docker image name for this service"
    )
    container_name_template = models.CharField(
        max_length=100,
        default="{team_prefix}_{service_name}",
        help_text="Template for container naming"
    )
    
    # Flag Configuration
    supports_two_flags = models.BooleanField(
        default=True,
        help_text="Whether this service uses user + root flag system"
    )
    
    # Scoring
    user_flag_points = models.IntegerField(default=50)
    root_flag_points = models.IntegerField(default=150)
    sla_points_per_tick = models.IntegerField(default=100)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'services'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_container_name(self, team):
        """Generate Docker container name for a team"""
        return self.container_name_template.format(
            team_prefix=team.container_name_prefix,
            service_name=self.name.lower().replace(' ', '_')
        )
