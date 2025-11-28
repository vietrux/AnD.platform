# Attack & Defense CTF System - Setup Guide

## Quick Start

### 1. Prerequisites

```bash
# System requirements
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 16
- Redis 7
```

### 2. Installation

```bash
# Clone and setup
cd /home/dev/Workspaces/CanisWare/sliverpayload

# Install dependencies
pip install -r requirements.txt

# Start infrastructure
cd infrastructure
docker-compose up -d

# Wait for database to be ready
sleep 5

# Run migrations
cd ..
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 3. Build Test Vulnbox

```bash
# Build vulnerable service
cd services/test_vuln_web
docker build -t test_vuln_web .

# Run test container
docker run -d -p 8001:8001 --name team1_test test_vuln_web
```

### 4. Start Gameserver Components

```bash
# Terminal 1: Tick Manager (Controller)
python -m gameserver.controller.tick_manager

# Terminal 2: Submission Server
python -m gameserver.submission.submission_server

# Terminal 3: Django Admin (optional)
python manage.py runserver 8000
```

## Testing the System

### Test Flag Injection

```python
# Python shell
python manage.py shell

from gameserver.checker import FlagInjector
from gameserver.flags import generate_flag_pair

# Generate flags
flags = generate_flag_pair(team_id=1, service_id=1, tick_number=1)
print(f"User: {flags['user']}")
print(f"Root: {flags['root']}")

# Inject into container
injector = FlagInjector()
result = injector.inject_both_flags('team1_test', flags['user'], flags['root'])
print(result)
```

### Test Vulnerabilities

```bash
# Path Traversal (User Flag)
curl "http://localhost:8001/read?file=/home/ctf/flag1.txt"

# Command Injection (Root Flag - requires RCE)
curl "http://localhost:8001/ping?host=127.0.0.1;cat%20/root/flag2.txt"
```

### Test Flag Submission

```bash
# Submit flag (you'll need a team token from database)
echo "SUBMIT <team_token> FLAG{...}" | nc localhost 31337
```

## Configuration

Edit `gameserver/config/game_config.py`:

```python
# Timing
TICK_DURATION_SECONDS = 60
FLAG_VALIDITY_TICKS = 5

# Scoring
USER_FLAG_POINTS = 50
ROOT_FLAG_POINTS = 150
```

## Database Setup

```bash
# Create test data
python manage.py shell

from gameserver.models import Team, Service

# Create test team
team = Team.objects.create(
    name="TestTeam",
    token="test_token_123",
    ip_address="10.1.1.10"
)
team.set_password("password")
team.save()

# Create test service
service = Service.objects.create(
    name="test",
    port=8001,
    checker_script="checkers.test_checker",
    docker_image="test_vuln_web",
    container_name_template="team{team_id}_test"
)
```

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check connection
python manage.py dbshell
```

### Docker Permission Issues
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again
```

### Flag Injection Fails
```bash
# Check container is running
docker ps | grep team

# Check logs
docker logs team1_test

# Verify Docker socket access
ls -la /var/run/docker.sock
```

## Architecture

```
gameserver/
├── models/         # Database models
├── config/         # Configuration
├── controller/     # Tick management
├── flags/          # Flag generation
├── checker/        # Service checking & injection
├── submission/     # Flag submission server
└── scoring/        # Score calculation
```

## Next Steps

1. **Create more services**: Add to `services/`
2. **Develop checkers**: Implement service-specific checkers
3. **Add teams**: Register teams via admin or API
4. **Deploy infrastructure**: Scale with Docker Swarm/Kubernetes
5. **Add web UI**: Build scoreboard and dashboard

## Security Notes

⚠️ **Change these in production**:
- `SECRET_KEY` in Django settings
- `FLAG_HMAC_KEY` in game_config
- Database passwords
- Enable HTTPS/TLS
