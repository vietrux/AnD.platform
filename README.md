# ADG Core - CTF Attack-Defense Game Engine

Core engine for Attack-Defense CTF competitions.

## Quick Start

```bash
# Install dependencies
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Setup database
cp .env.example .env
# Edit .env with your PostgreSQL settings

# Run migrations
alembic upgrade head

# Start everything (API + Workers) with one command
python main.py
```

 **Note:** This starts the API server on port 8000, tick worker, and checker worker all in a single process. For development with hot-reload, you can still run components separately:
 ```bash
 uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
 python -m src.workers.tick_worker
 python -m src.workers.checker_worker
 ```

## Project Structure

```
src/
├── api/          # FastAPI endpoints
├── schemas/      # Pydantic validation
├── models/       # SQLAlchemy ORM
├── services/     # Business logic
├── workers/      # Background tasks
└── core/         # Config, DB, exceptions
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/games` | Create game |
| GET | `/games/{id}` | Get game |
| POST | `/games/{id}/vulnbox` | Upload vulnbox.zip |
| POST | `/games/{id}/checker` | Upload checker.py |
| POST | `/games/{id}/teams` | Add team |
| GET  | `/games/{id}/teams` | List teams |
| POST | `/games/{id}/start` | Start game |
| POST | `/submit` | Submit flag |
| POST | `/checker/status` | Checker SLA report |
| GET | `/scoreboard/{game_id}` | Get scoreboard |

## Checker Template

```python
def check(team_ip: str, game_id: str, team_id: str, tick_number: int) -> dict:
    return {
        "status": "up",  # up|down|error
        "sla": 100.0,    # 0-100
        "message": None  # optional
    }
```

## Docker Compose

```bash
docker-compose up -d  # Start PostgreSQL
```
