"""
Submission Server
TCP server for flag submissions
"""

import socket
import threading
import logging
from django.utils import timezone

from gameserver.config import game_config
from gameserver.models import Team, Flag, FlagSubmission
from gameserver.flags import validate_flag_submission

logger = logging.getLogger(__name__)


class SubmissionServer:
    """
    TCP server handling flag submissions
    Protocol: SUBMIT <team_token> <flag>
    Response: OK <points> | ERROR <reason>
    """
    
    def __init__(self, host=None, port=None):
        self.host = host or game_config.SUBMISSION_SERVER_HOST
        self.port = port or game_config.SUBMISSION_SERVER_PORT
        self.running = False
        self.sock = None
        logger.info(f"SubmissionServer initialized on {self.host}:{self.port}")
    
    def start(self):
        """Start the submission server"""
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        
        logger.info(f"Submission server listening on {self.host}:{self.port}")
        
        while self.running:
            try:
                client_sock, client_addr = self.sock.accept()
                logger.debug(f"Connection from {client_addr}")
                
                # Handle in separate thread
                thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, client_addr)
                )
                thread.daemon = True
                thread.start()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error accepting connection: {e}")
        
        self.stop()
    
    def stop(self):
        """Stop the submission server"""
        self.running = False
        if self.sock:
            self.sock.close()
        logger.info("Submission server stopped")
    
    def _handle_client(self, client_sock, client_addr):
        """Handle a client connection"""
        try:
            # Receive data
            data = client_sock.recv(4096).decode().strip()
            
            if not data:
                return
            
            # Parse submission
            response = self._process_submission(data, client_addr[0])
            
            # Send response
            client_sock.sendall(response.encode() + b'\n')
            
        except Exception as e:
            logger.error(f"Error handling client {client_addr}: {e}")
            try:
                client_sock.sendall(b'ERROR Internal server error\n')
            except:
                pass
        finally:
            client_sock.close()
    
    def _process_submission(self, data, client_ip):
        """
        Process a flag submission
        
        Args:
            data: Submission data
            client_ip: Client IP address
        
        Returns:
            str: Response message
        """
        # Parse: SUBMIT <team_token> <flag>
        parts = data.split()
        
        if len(parts) != 3 or parts[0].upper() != 'SUBMIT':
            return "ERROR Invalid format. Use: SUBMIT <team_token> <flag>"
        
        team_token = parts[1]
        flag_string = parts[2]
        
        # Look up team
        try:
            team = Team.objects.get(token=team_token, is_active=True)
        except Team.DoesNotExist:
            logger.warning(f"Invalid team token from {client_ip}")
            return "ERROR Invalid team token"
        
        # Validate flag submission
        status, message, flag, points = validate_flag_submission(
            flag_string=flag_string,
            submitter_team=team,
            flag_model_class=Flag
        )
        
        # Create submission record
        submission = FlagSubmission.objects.create(
            submitter_team=team,
            flag=flag,
            submitted_flag=flag_string,
            submitter_ip=client_ip,
            status=status,
            points_awarded=points
        )
        
        # Update flag if stolen
        if status == 'accepted' and flag:
            if not flag.is_stolen:
                flag.is_stolen = True
            flag.stolen_count += 1
            flag.save(update_fields=['is_stolen', 'stolen_count'])
            
            # Update team score (simplified - would trigger score recalculation)
            logger.info(
                f"{team.name} captured {flag.flag_type} flag from "
                f"{flag.team.name}/{flag.service.name} for {points} points"
            )
        
        # Return response
        if status == 'accepted':
            return f"OK {points}"
        else:
            return f"ERROR {message}"


def main():
    """Entry point when run as module"""
    import django
    django.setup()
    
    server = SubmissionServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()


if __name__ == "__main__":
    main()
