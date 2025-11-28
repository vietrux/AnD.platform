"""
Flag Injector
Docker API-based flag injection into running containers
"""

import docker
import tarfile
import io
import os
import time
import logging

from gameserver.config import game_config

logger = logging.getLogger(__name__)


class FlagInjector:
    """
    Inject flags into running Docker containers using Docker API
    Primary method uses tar archives for robust flag placement
    """
    
    def __init__(self, docker_client=None):
        """
        Initialize flag injector
        
        Args:
            docker_client: Optional Docker client instance
        """
        self.docker = docker_client or docker.from_env()
        logger.info("FlagInjector initialized with Docker API")
    
    def inject_flag_docker_api(self, container_name, flag_value, flag_path, 
                               owner_uid=0, owner_gid=0, permissions=0o600):
        """
        ⭐ PRIMARY METHOD: Inject flag using Docker Python API
        
        This is the most robust and recommended approach for production.
        Uses tar archive to inject files with proper permissions.
        
        Args:
            container_name: Name of the target container
            flag_value: The flag content to inject
            flag_path: Path where flag should be placed (e.g., /root/flag2.txt)
            owner_uid: User ID of file owner (0=root, 1000=ctf)
            owner_gid: Group ID of file owner (0=root, 1000=ctf)
            permissions: Octal file permissions (e.g., 0o600, 0o644)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            container = self.docker.containers.get(container_name)
            
            # Create file info for tar archive
            tarinfo = tarfile.TarInfo(name=os.path.basename(flag_path))
            tarinfo.size = len(flag_value)
            tarinfo.mode = permissions
            tarinfo.uid = owner_uid
            tarinfo.gid = owner_gid
            tarinfo.mtime = int(time.time())
            
            # Create tar archive in memory
            tar_stream = io.BytesIO()
            tar = tarfile.open(fileobj=tar_stream, mode='w')
            tar.addfile(tarinfo, io.BytesIO(flag_value.encode()))
            tar.close()
            
            # Inject archive into container
            tar_stream.seek(0)
            container.put_archive(
                path=os.path.dirname(flag_path),
                data=tar_stream.read()
            )
            
            logger.info(f"Successfully injected flag via Docker API: {container_name}:{flag_path}")
            return True
            
        except docker.errors.NotFound:
            logger.error(f"Container not found: {container_name}")
            return False
        except docker.errors.APIError as e:
            logger.error(f"Docker API error during flag injection: {e}")
            return False
        except Exception as e:
            logger.error(f"Flag injection failed for {container_name}: {str(e)}")
            return False
    
    def inject_user_flag(self, container_name, flag_value):
        """
        Convenience method: Inject user flag with standard permissions
        
        User flags: /home/ctf/flag1.txt, 644 permissions, ctf:ctf owner
        Easily readable via LFI, SQL injection, etc.
        
        Args:
            container_name: Name of the target container
            flag_value: The flag content
        
        Returns:
            bool: True if successful
        """
        return self.inject_flag_docker_api(
            container_name=container_name,
            flag_value=flag_value,
            flag_path=game_config.USER_FLAG_PATH,
            owner_uid=game_config.USER_FLAG_UID,
            owner_gid=game_config.USER_FLAG_GID,
            permissions=game_config.USER_FLAG_PERMISSIONS
        )
    
    def inject_root_flag(self, container_name, flag_value):
        """
        Convenience method: Inject root flag with restricted permissions
        
        Root flags: /root/flag2.txt, 600 permissions, root:root owner
        Requires RCE + privilege escalation to read
        
        Args:
            container_name: Name of the target container
            flag_value: The flag content
        
        Returns:
            bool: True if successful
        """
        return self.inject_flag_docker_api(
            container_name=container_name,
            flag_value=flag_value,
            flag_path=game_config.ROOT_FLAG_PATH,
            owner_uid=game_config.ROOT_FLAG_UID,
            owner_gid=game_config.ROOT_FLAG_GID,
            permissions=game_config.ROOT_FLAG_PERMISSIONS
        )
    
    def inject_both_flags(self, container_name, user_flag, root_flag):
        """
        Inject both user and root flags into a container
        
        Args:
            container_name: Name of the target container
            user_flag: User flag value
            root_flag: Root flag value
        
        Returns:
            dict: {'user': bool, 'root': bool, 'success': bool}
        """
        result = {
            'user': False,
            'root': False,
            'success': False
        }
        
        # Inject user flag
        result['user'] = self.inject_user_flag(container_name, user_flag)
        
        # Inject root flag
        result['root'] = self.inject_root_flag(container_name, root_flag)
        
        # Overall success if both succeeded
        result['success'] = result['user'] and result['root']
        
        if result['success']:
            logger.info(f"Successfully injected both flags into {container_name}")
        else:
            logger.warning(f"Partial flag injection for {container_name}: {result}")
        
        return result
    
    def verify_flag_exists(self, container_name, flag_path, expected_flag):
        """
        Verify that a flag exists and matches expected value
        Uses Docker exec with root privileges
        
        Args:
            container_name: Name of the target container
            flag_path: Path to flag file
            expected_flag: Expected flag content
        
        Returns:
            bool: True if flag exists and matches
        """
        try:
            container = self.docker.containers.get(container_name)
            
            # Read flag file as root
            exec_result = container.exec_run(f'cat {flag_path}', user='root')
            
            if exec_result.exit_code == 0:
                actual_flag = exec_result.output.decode().strip()
                return actual_flag == expected_flag
            
            return False
            
        except Exception as e:
            logger.error(f"Flag verification failed for {container_name}:{flag_path}: {e}")
            return False
