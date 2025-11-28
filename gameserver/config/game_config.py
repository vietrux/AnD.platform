"""
Game Configuration
Core game parameters and settings
"""

# Competition Timing
TICK_DURATION_SECONDS = 60  # 1 minute per round
FLAG_VALIDITY_TICKS = 5  # Flags valid for 5 rounds

# Flag Configuration
FLAG_FORMAT = "FLAG{{{team_hash}_{service_id}_{tick}_{flag_type}_{random}}}"
FLAG_HMAC_KEY = "change-this-in-production-secret-key"  # MUST change in production
FLAG_RANDOM_LENGTH = 16  # Length of random component

# Flag Paths in Containers
USER_FLAG_PATH = "/home/ctf/flag1.txt"
ROOT_FLAG_PATH = "/root/flag2.txt"

# Flag Permissions
USER_FLAG_UID = 1000  # ctf user
USER_FLAG_GID = 1000  # ctf group
USER_FLAG_PERMISSIONS = 0o644  # -rw-r--r--

ROOT_FLAG_UID = 0  # root user
ROOT_FLAG_GID = 0  # root group
ROOT_FLAG_PERMISSIONS = 0o600  # -rw-------

# Scoring
USER_FLAG_POINTS = 50
ROOT_FLAG_POINTS = 150
FIRST_BLOOD_BONUS_USER = 25
FIRST_BLOOD_BONUS_ROOT = 75
SLA_POINTS_PER_SERVICE_PER_TICK = 100

# Network Configuration
TEAM_NETWORK_PREFIX = "10.1"  # Teams get 10.1.X.0/24
GAMESERVER_IP = "10.0.0.1"

# Checker Configuration
CHECKER_TIMEOUT_SECONDS = 30
CHECKER_MAX_RETRIES = 2

# Submission Server
SUBMISSION_SERVER_HOST = "0.0.0.0"
SUBMISSION_SERVER_PORT = 31337
SUBMISSION_RATE_LIMIT_PER_TEAM = 100  # Max submissions per tick per team

# Docker Configuration
DOCKER_HOST = "unix://var/run/docker.sock"  # Default Docker socket

# Celery Configuration
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
