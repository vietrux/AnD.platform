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
uv run alembic upgrade head
```

### 4. Start Server

```bash
# Start API + Workers (single process)
python main.py

# OR run separately for development:
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**API Documentation:** http://localhost:8000/docs

---

## 📋 Complete API Reference (60 Endpoints)

### Vulnbox Management (`/vulnboxes`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/vulnboxes` | Upload vulnbox.zip |
| GET | `/vulnboxes` | List all vulnboxes |
| GET | `/vulnboxes/{id}` | Get vulnbox details |
| PATCH | `/vulnboxes/{id}` | Update metadata |
| DELETE | `/vulnboxes/{id}` | Delete vulnbox |
| POST | `/vulnboxes/{id}/build` | Build Docker image |

### Checker Management (`/checkers`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/checkers` | Upload checker.py |
| GET | `/checkers` | List all checkers |
| GET | `/checkers/{id}` | Get checker details |
| PATCH | `/checkers/{id}` | Update metadata |
| DELETE | `/checkers/{id}` | Delete checker |
| POST | `/checkers/{id}/validate` | Validate syntax |

### Game Management (`/games`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/games` | Create new game |
| GET | `/games` | List all games |
| GET | `/games/{id}` | Get game details |
| PATCH | `/games/{id}` | Update game |
| DELETE | `/games/{id}` | Delete game |
| POST | `/games/{id}/assign-vulnbox` | Assign vulnbox |
| POST | `/games/{id}/assign-checker` | Assign checker |
| POST | `/games/{id}/teams` | Add team |
| GET | `/games/{id}/teams` | List teams |
| GET | `/games/{id}/teams/{team_id}` | Get team |
| DELETE | `/games/{id}/teams/{team_id}` | Remove team |
| POST | `/games/{id}/start` | Start game |
| POST | `/games/{id}/pause` | Pause game |
| POST | `/games/{id}/stop` | Stop game |

### Flags (Read-Only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/flags` | List flags (filter by game/team/tick) |
| GET | `/flags/{id}` | Get flag by ID |
| GET | `/flags/stats` | Get flag statistics |
| GET | `/flags/by-value/{value}` | Get flag by value |
| GET | `/flags/tick/{tick_id}` | List flags for tick |
| GET | `/flags/team/{team_id}/tick/{tick_id}` | List team's tick flags |

### Ticks (Read-Only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ticks` | List ticks (filter by game/status) |
| GET | `/ticks/{id}` | Get tick by ID |
| GET | `/ticks/current` | Get current active tick |
| GET | `/ticks/latest` | Get most recent tick |
| GET | `/ticks/number/{n}` | Get tick by number |

### Submissions (`/submissions`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/submissions` | Submit flag |
| GET | `/submissions` | List all submissions |
| GET | `/submissions/{id}` | Get submission |
| GET | `/submissions/game/{game_id}` | List by game |
| GET | `/submissions/team/{team_id}` | List by team |
| DELETE | `/submissions/{id}` | Delete submission |

### Checker Status (`/checker`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/checker/status` | Submit SLA report |
| GET | `/checker/statuses` | List all statuses |
| GET | `/checker/statuses/{id}` | Get status |
| GET | `/checker/statuses/game/{game_id}` | List by game |
| GET | `/checker/statuses/team/{team_id}` | List by team |
| DELETE | `/checker/statuses/{id}` | Delete status |

### Scoreboard (`/scoreboard`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/scoreboard` | List all scoreboards |
| GET | `/scoreboard/{game_id}` | Get game scoreboard |
| GET | `/scoreboard/{game_id}/team/{team_id}` | Get team score |
| POST | `/scoreboard/{game_id}/recalculate` | Recalculate scores |
| DELETE | `/scoreboard/{game_id}` | Reset scoreboard |

---

## 🧪 Testing Workflow

### Test 1: Vulnbox & Checker Setup

```bash
# Upload vulnbox
curl -X POST "http://localhost:8000/vulnboxes" \
  -F "name=test-vulnbox" \
  -F "file=@vulnbox.zip"

# Upload checker
curl -X POST "http://localhost:8000/checkers" \
  -F "name=test-checker" \
  -F "file=@checker.py"

# Validate checker
curl -X POST "http://localhost:8000/checkers/{id}/validate"
```

### Test 2: Game Flow

```bash
# 1. Create game
curl -X POST "http://localhost:8000/games" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test CTF", "tick_duration_seconds": 60}'

# 2. Assign vulnbox & checker
curl -X POST "http://localhost:8000/games/{id}/assign-vulnbox?vulnbox_id={id}"
curl -X POST "http://localhost:8000/games/{id}/assign-checker?checker_id={id}"

# 3. Add teams
curl -X POST "http://localhost:8000/games/{id}/teams" \
  -H "Content-Type: application/json" -d '{"team_id": "team1"}'

# 4. Start game
curl -X POST "http://localhost:8000/games/{id}/start"
```

### Test 3: Flag Submission

```bash
curl -X POST "http://localhost:8000/submissions" \
  -H "Content-Type: application/json" \
  -d '{"team_token": "token", "flag": "FLAG{...}"}'

# View scoreboard
curl "http://localhost:8000/scoreboard/{game_id}"
```

---

## 📝 Checker Template

```python
def check(team_ip: str, game_id: str, team_id: str, tick_number: int) -> dict:
    return {
        "status": "up",  # up|down|error
        "sla": 100.0,    # 0-100
        "message": None  # optional error
    }
```

---

## 🏗️ Project Structure

```
src/
├── api/routes/     # 61 API endpoints
├── models/         # SQLAlchemy ORM
├── schemas/        # Pydantic validation
├── services/       # Business logic
├── workers/        # Tick & Checker workers
└── core/           # Config, DB, exceptions
```

---

## 🔍 Testing Checklist

- [ ] Vulnbox: Upload, list, build, delete
- [ ] Checker: Upload, validate, delete
- [ ] Game: Create → Assign → Teams → Start → Stop
- [ ] Submissions: Submit valid/invalid flags
- [ ] Scoreboard: View, recalculate, reset
- [ ] Flags/Ticks: View only (auto-generated)

---

## 🐛 Troubleshooting

```bash
# Check database
docker compose ps

# Reset migrations
uv run alembic downgrade base && uv run alembic upgrade head

# Verify imports
uv run python -c "from src.api.main import app; print(f'{len(app.routes)} routes')"
```

---

## 📊 Expected Behavior

- **Game States**: DRAFT → DEPLOYING → RUNNING → PAUSED/FINISHED
- **Flags**: Auto-generated each tick by tick_worker
- **Ticks**: Auto-generated every tick_duration_seconds
- **Scoring**: Attack (50/150 pts), SLA (100 pts/tick)
