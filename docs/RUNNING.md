# Running the Full CTF System

## Quick Start (All-in-One)

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Run the startup script
./start_system.sh
```

This will:
1. ✅ Start PostgreSQL + Redis
2. ✅ Run database migrations
3. ✅ Create 5 teams in database
4. ✅ Create the test service

Then follow the instructions to start the gameserver components.

---

## Manual Step-by-Step

### 1. Start Infrastructure

```bash
cd infrastructure
docker-compose up -d
cd ..
```

### 2. Setup Database

```bash
# Run migrations
export DJANGO_SETTINGS_MODULE=gameserver.config.settings
python manage.py migrate

# Setup teams and services
python infrastructure/setup_database.py
```

### 3. Start Gameserver Components

**Terminal 1 - Tick Manager** (generates and places flags every 60 seconds):
```bash
source .venv/bin/activate
python -m gameserver.controller.tick_manager
```

You'll see:
```
TickManager initialized
Starting tick loop
=== Starting Tick 1 ===
Tick 1: Generating flags...
Successfully injected both flags into team1_vuln
Successfully injected both flags into team2_vuln
...
Placed 10 flags for tick 1
=== Completed Tick 1 in 2.5s ===
```

**Terminal 2 - Submission Server** (accepts flag submissions on port 31337):
```bash
source .venv/bin/activate
python -m gameserver.submission.submission_server
```

You'll see:
```
Submission server listening on 0.0.0.0:31337
```

**Terminal 3 - Django Admin** (optional - view database):
```bash
source .venv/bin/activate
python manage.py createsuperuser  # First time only
python manage.py runserver
```

Visit http://localhost:8000/admin

---

## Testing the Complete Flow

### 1. Wait for Flags to be Generated

The tick manager runs every 60 seconds. Wait for tick 1 to complete, then:

```bash
# Verify flags were injected
docker exec team1_vuln cat /home/ctf/flag1.txt
docker exec team1_vuln cat /root/flag2.txt
```

### 2. Steal Flags (Simulate Attack)

```bash
# Team 2 steals Team 1's user flag
curl 'http://localhost:8002/read?file=/home/ctf/flag1.txt'

# Extract just the flag value
FLAG=$(curl -s 'http://localhost:8002/read?file=/home/ctf/flag1.txt' | grep -oP 'FLAG\{[^}]+\}')
echo $FLAG
```

### 3. Submit Flag

```bash
# Get Team 2's token from database
TEAM2_TOKEN="<get from setup_database.py output>"

# Submit flag
echo "SUBMIT $TEAM2_TOKEN $FLAG" | nc localhost 31337

# Should return: OK 50
```

### 4. Check Scores

```python
python manage.py shell

from gameserver.models import Score, Team
from gameserver.scoring import ScoreCalculator

# Calculate scores
ScoreCalculator.calculate_all_scores()

# View scores
for score in Score.objects.all().order_by('-total_points'):
    print(f"{score.team.name}: {score.total_points} pts (A:{score.attack_points} D:{score.defense_points} S:{score.sla_points})")
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Tick Manager (60s loop)                   │
│  • Generates flags for all teams                            │
│  • Injects via Docker API                                   │
│  • Triggers checkers (optional)                             │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│               Team Containers (5 deployed)                   │
│  team1_vuln, team2_vuln, ..., team5_vuln                    │
│  • Flask web service on ports 8002-8006                     │
│  • SSH on ports 2223-2227                                   │
│  • Flags at /home/ctf/flag1.txt and /root/flag2.txt         │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ Teams exploit vulnerabilities
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│             Submission Server (port 31337)                   │
│  • Validates flags                                           │
│  • Awards points                                            │
│  • Updates database                                         │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                PostgreSQL Database                           │
│  • Teams, Services, Flags, Submissions, Scores              │
└─────────────────────────────────────────────────────────────┘
```

---

## Monitoring

### View Docker Containers
```bash
docker ps | grep team
```

### View Logs
```bash
# Tick manager logs (in Terminal 1)
# Submission server logs (in Terminal 2)

# Container logs
docker logs team1_vuln
```

### View Database
```bash
python manage.py shell

from gameserver.models import *

# View teams
Team.objects.all()

# View flags
Flag.objects.all()

# View submissions
FlagSubmission.objects.all()

# View scores
Score.objects.all().order_by('-total_points')
```

---

## Cleanup

```bash
# Stop gameserver (Ctrl+C in both terminals)

# Stop containers
docker stop $(docker ps -q --filter "name=team*_vuln")
docker rm $(docker ps -aq --filter "name=team*_vuln")

# Stop infrastructure
cd infrastructure
docker-compose down
```

---

## Troubleshooting

### Flags Not Generating
- Check tick manager is running
- Verify containers are running: `docker ps | grep team`
- Check logs for errors

### Submission Server Not Accepting Flags
- Verify port 31337 is not in use
- Check team token is correct
- Ensure flag is still valid (< 5 ticks old)

### Database Connection Failed
- Ensure infrastructure is running: `docker-compose ps`
- Check PostgreSQL logs: `docker logs infrastructure-db-1`
