"""
Base Checker
Abstract base class for all service checkers
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseChecker(ABC):
    """
    Abstract base class for service-specific checkers
    Checkers interact with services to place and retrieve flags
    """
    
    def __init__(self):
        self.logger = logger
    
    @abstractmethod
    def place_flag(self, team_ip, service_port, flag_value, flag_id):
        """
        Place a flag into the service using legitimate functionality
        
        Args:
            team_ip: IP address of team's service
            service_port: Port number
            flag_value: The flag to place
            flag_id: Identifier for this flag
        
        Returns:
            bool: True if successful
        """
        pass
    
    @abstractmethod
    def check_service(self, team_ip, service_port):
        """
        Check if service is up and responding
        
        Args:
            team_ip: IP address of team's service
            service_port: Port number
        
        Returns:
            bool: True if service is up
        """
        pass
    
    @abstractmethod
    def get_flag(self, team_ip, service_port, flag_id, expected_flag):
        """
        Retrieve and verify a flag from the service
        
        Args:
            team_ip: IP address of team's service
            service_port: Port number
            flag_id: Identifier for the flag to retrieve
            expected_flag: Expected flag value
        
        Returns:
            bool: True if flag was retrieved and matches
        """
        pass
