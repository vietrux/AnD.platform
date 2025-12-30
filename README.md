# CTF Attack-Defense Gameserver - Testing Guide

A complete Attack-Defense CTF platform with standalone vulnbox/checker management and full CRUD API.

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone and navigate
git clone <repository-url>
cd attack-defense-gameserver

# Start PostgreSQL
docker compose up -d

# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e ".[dev]"
```

### 2. Configure Database

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/adg_core
UPLOAD_DIR=./uploads
SSH_HOST=localhost
SSH_PORT_BASE=2200
```

### 3. Run Migrations

```bash
# Create database tables
uv run alembic upgrade head
```

### 4. Start Server

```bash
# Start API + Workers (single process)
python main.py

# OR run separately for development:
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
python -m src.workers.tick_worker
python -m src.workers.checker_worker
```

**API Documentation:** http://localhost:8000/docs

---

## 📋 Complete API Reference

### Vulnbox Management (`/vulnboxes`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/vulnboxes` | Upload vulnbox.zip (multipart/form-data) |
| GET | `/vulnboxes` | List all vulnboxes (paginated) |
| GET | `/vulnboxes/{id}` | Get vulnbox details |
| PATCH | `/vulnboxes/{id}` | Update vulnbox metadata |
| DELETE | `/vulnboxes/{id}` | Delete vulnbox |
| POST | `/vulnboxes/{id}/build` | Build Docker image from vulnbox |

### Checker Management (`/checkers`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/checkers` | Upload checker.py (multipart/form-data) |
| GET | `/checkers` | List all checkers (paginated) |
| GET | `/checkers/{id}` | Get checker details |
| PATCH | `/checkers/{id}` | Update checker metadata |
| DELETE | `/checkers/{id}` | Delete checker |
| POST | `/checkers/{id}/validate` | Validate checker Python syntax |

### Game Management (`/games`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/games` | Create new game |
| GET | `/games` | List all games (paginated) |
| GET | `/games/{id}` | Get game details |
| PATCH | `/games/{id}` | Update game metadata |
| DELETE | `/games/{id}` | Delete game (only DRAFT/FINISHED) |
| POST | `/games/{id}/assign-vulnbox` | Assign vulnbox to game |
| POST | `/games/{id}/assign-checker` | Assign checker to game |
| POST | `/games/{id}/teams` | Add team to game |
| GET | `/games/{id}/teams` | List game teams |
| GET | `/games/{id}/teams/{team_id}` | Get team details |
| PATCH | `/games/{id}/teams/{team_id}` | Update team |
| DELETE | `/games/{id}/teams/{team_id}` | Remove team |
| POST | `/games/{id}/start` | Deploy and start game |
| POST | `/games/{id}/pause` | Pause running game |
| POST | `/games/{id}/stop` | Stop game and cleanup |

### Flag & Tick Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/flags` | List all flags (paginated) |
| GET | `/flags/{id}` | Get flag by ID |
| GET | `/flags/value/{value}` | Get flag by value |
| PATCH | `/flags/{id}` | Update flag |
| DELETE | `/flags/{id}` | Delete flag |
| GET | `/ticks` | List all ticks (paginated) |
| GET | `/ticks/{id}` | Get tick by ID |
| POST | `/ticks` | Create tick |
| PATCH | `/ticks/{id}` | Update tick |
| DELETE | `/ticks/{id}` | Delete tick |

### Submissions (`/submissions`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/submissions` | Submit flag |
| GET | `/submissions` | List all submissions (filter by game/team/status) |
| GET | `/submissions/{id}` | Get submission details |
| GET | `/submissions/game/{game_id}` | List game submissions |
| GET | `/submissions/team/{team_id}` | List team submissions |
| DELETE | `/submissions/{id}` | Delete submission |

### Checker Status (`/checker/statuses`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/checker/status` | Submit checker SLA report |
| GET | `/checker/statuses` | List all statuses (filter by game/team/tick) |
| GET | `/checker/statuses/{id}` | Get status by ID |
| GET | `/checker/statuses/game/{game_id}` | List game statuses |
| GET | `/checker/statuses/team/{team_id}` | List team statuses |
| DELETE | `/checker/statuses/{id}` | Delete status |

### Scoreboard (`/scoreboard`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/scoreboard` | List all game scoreboards |
| GET | `/scoreboard/{game_id}` | Get game scoreboard |
| GET | `/scoreboard/{game_id}/team/{team_id}` | Get team score |
| POST | `/scoreboard/{game_id}/recalculate` | Recalculate scores |
| DELETE | `/scoreboard/{game_id}` | Reset scoreboard |

**Total: 71 API Endpoints**

---

## 🧪 Testing Workflow

### Test 1: Vulnbox Management

```bash
# 1. Upload vulnbox
curl -X POST "http://localhost:8000/vulnboxes" \
  -F "name=test-vulnbox" \
  -F "description=Test vulnerable box" \
  -F "file=@vulnbox.zip"

# Response: {"id": "uuid", "name": "test-vulnbox", ...}

# 2. List vulnboxes
curl "http://localhost:8000/vulnboxes"

# 3. Build Docker image
curl -X POST "http://localhost:8000/vulnboxes/{id}/build"

# 4. Get vulnbox details
curl "http://localhost:8000/vulnboxes/{id}"
```

### Test 2: Checker Management

```bash
# 1. Upload checker
curl -X POST "http://localhost:8000/checkers" \
  -F "name=test-checker" \
  -F "description=Test checker script" \
  -F "file=@checker.py"

# 2. Validate checker syntax
curl -X POST "http://localhost:8000/checkers/{id}/validate"

# 3. List checkers
curl "http://localhost:8000/checkers"
```

### Test 3: Complete Game Flow

```bash
# 1. Create game
curl -X POST "http://localhost:8000/games" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test CTF",
    "description": "Testing game",
    "tick_duration_seconds": 60
  }'

# 2. Assign vulnbox and checker
curl -X POST "http://localhost:8000/games/{game_id}/assign-vulnbox?vulnbox_id={vulnbox_id}"
curl -X POST "http://localhost:8000/games/{game_id}/assign-checker?checker_id={checker_id}"

# 3. Add teams
curl -X POST "http://localhost:8000/games/{game_id}/teams" \
  -H "Content-Type: application/json" \
  -d '{"team_id": "team1"}'

curl -X POST "http://localhost:8000/games/{game_id}/teams" \
  -H "Content-Type: application/json" \
  -d '{"team_id": "team2"}'

# 4. Start game
curl -X POST "http://localhost:8000/games/{game_id}/start"

# Response includes SSH credentials for each team
```

### Test 4: Flag Submission

```bash
# Submit flag
curl -X POST "http://localhost:8000/submissions" \
  -H "Content-Type: application/json" \
  -d '{
    "team_token": "team_token_from_start_response",
    "flag": "FLAG{...}"
  }'

# Check scoreboard
curl "http://localhost:8000/scoreboard/{game_id}"
```

### Test 5: Checker Status

```bash
# Submit checker status (from checker worker)
curl -X POST "http://localhost:8000/checker/status" \
  -H "Content-Type: application/json" \
  -d '{
    "game_id": "uuid",
    "team_id": "team1",
    "tick_id": "uuid",
    "status": "up",
    "sla_percentage": 100.0,
    "check_duration_ms": 150
  }'

# List statuses
curl "http://localhost:8000/checker/statuses?game_id={game_id}"
```

---

## 📝 Checker Template

Create a `checker.py` file with this structure:

```python
def check(team_ip: str, game_id: str, team_id: str, tick_number: int) -> dict:
    """
    Check service availability and functionality.
    
    Args:
        team_ip: IP address of team's vulnbox
        game_id: UUID of the game
        team_id: Team identifier
        tick_number: Current tick number
    
    Returns:
        dict with keys:
            - status: "up" | "down" | "error"
            - sla: float (0-100)
            - message: str | None (optional error message)
    """
    try:
        # Example: Check HTTP service
        import requests
        response = requests.get(f"http://{team_ip}:8080/health", timeout=5)
        
        if response.status_code == 200:
            return {
                "status": "up",
                "sla": 100.0,
                "message": None
            }
        else:
            return {
                "status": "down",
                "sla": 0.0,
                "message": f"HTTP {response.status_code}"
            }
    except Exception as e:
        return {
            "status": "error",
            "sla": 0.0,
            "message": str(e)
        }
```

---

## 🏗️ Project Structure

```
src/
├── api/
│   ├── main.py              # FastAPI app
│   └── routes/              # API endpoints (71 routes)
│       ├── games.py         # Game CRUD + assignment
│       ├── vulnboxes.py     # Vulnbox CRUD
│       ├── checkers.py      # Checker CRUD
│       ├── submissions.py   # Flag submissions
│       ├── scoreboard.py    # Scoreboard operations
│       ├── flags.py         # Flag management
│       ├── ticks.py         # Tick management
│       └── checker.py       # Checker status
├── models/                  # SQLAlchemy ORM
│   ├── game.py             # Game, GameTeam
│   ├── vulnbox.py          # Vulnbox model
│   ├── checker.py          # Checker model
│   ├── tick.py             # Tick model
│   ├── flag.py             # Flag model
│   ├── submission.py       # FlagSubmission
│   ├── service_status.py   # ServiceStatus
│   └── scoreboard.py       # Scoreboard
├── schemas/                # Pydantic validation
├── services/               # Business logic
│   ├── game_service.py
│   ├── vulnbox_service.py
│   ├── checker_crud_service.py
│   ├── submission_service.py
│   ├── scoring_service.py
│   └── docker_service.py
├── workers/                # Background tasks
│   ├── tick_worker.py      # Tick generation
│   └── checker_worker.py   # Service checks
└── core/                   # Config, DB, exceptions
```

---

## 🔍 Testing Checklist

- [ ] **Vulnbox CRUD**: Upload, list, get, update, delete, build
- [ ] **Checker CRUD**: Upload, list, get, update, delete, validate
- [ ] **Game Lifecycle**: Create → Assign vulnbox → Assign checker → Add teams → Start → Pause → Stop → Delete
- [ ] **Team Management**: Add, list, get, update, remove teams
- [ ] **Flag Submission**: Submit valid/invalid/expired/own flags
- [ ] **Scoreboard**: View, recalculate, reset
- [ ] **Checker Status**: Submit status, list by game/team
- [ ] **Pagination**: Test skip/limit on all list endpoints
- [ ] **Error Handling**: Test 404s, 400s, validation errors
- [ ] **Docker Integration**: Verify containers deploy correctly

---

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker compose ps

# Verify .env DATABASE_URL
cat .env | grep DATABASE_URL

# Test connection
uv run python -c "from src.core.database import engine; print('OK')"
```

### Migration Issues
```bash
# Reset database (WARNING: deletes all data)
uv run alembic downgrade base
uv run alembic upgrade head

# Create new migration
uv run alembic revision --autogenerate -m "description"
```

### Import Errors
```bash
# Verify all imports work
uv run python -c "from src.api.main import app; print(f'{len(app.routes)} routes')"
```

---

## 📊 Expected Behavior

- **Game States**: DRAFT → DEPLOYING → RUNNING → PAUSED/FINISHED
- **Flag Lifetime**: 5 ticks (configurable)
- **SLA Points**: 100 per tick (based on checker status)
- **Attack Points**: 50 (user flag), 150 (root flag)
- **Scoreboard**: Auto-updates on flag submission and checker reports

---

## 📞 Support

For issues or questions, please check:
1. API documentation at `/docs`
2. Database migrations are up to date
3. All environment variables are set correctly
4. Docker containers are running
