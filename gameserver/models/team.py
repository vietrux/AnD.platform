"""
Team Model
Represents a participating team in the CTF
"""

from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class Team(models.Model):
    """
    Team participating in the CTF competition
    """

    # Basic Information
    name = models.CharField(max_length=100, unique=True)
    token = models.CharField(max_length=64, unique=True, db_index=True)

    # Authentication
    password_hash = models.CharField(max_length=128)

    # Network Configuration
    ip_address = models.GenericIPAddressField(unique=True)
    vpn_public_key = models.TextField(blank=True, null=True)

    # Contact Information
    email = models.EmailField(blank=True)
    contact_person = models.CharField(max_length=100, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_nop_team = models.BooleanField(
        default=False, help_text="NOP team used for testing exploits"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "teams"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def set_password(self, raw_password):
        """Hash and set the team password"""
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        """Verify the team password"""
        return check_password(raw_password, self.password_hash)

    @property
    def container_name_prefix(self):
        """Generate container name prefix for this team"""
        return str(self.id)
