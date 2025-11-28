# Attack & Defense CTF System

A scalable attack-defense CTF infrastructure with dynamic flag rotation, two-flag system, and real-time scoring.

## Features

- **Two-Flag System**: User flags (50 pts) and root flags (150 pts) requiring different exploitation techniques
- **Dynamic Flags**: Flags rotate every 60 seconds with HMAC-based generation
- **Docker API Integration**: Robust flag injection using Docker Python API
- **Real-time Scoring**: Attack points, defense points, and SLA tracking
- **Modular Architecture**: Clean separation of concerns with focused modules

## Project Structure

```
├── gameserver/          # Main gameserver application
│   ├── models/          # Database models (Team, Service, Flag, etc.)
│   ├── config/          # Configuration files
│   ├── flags/           # Flag generation and validation
│   ├── checker/         # Service checking and flag injection
│   ├── controller/      # Round/tick management
│   ├── submission/      # Flag submission server
│   ├── scoring/         # Scoring system
│   └── web/             # Web interface and scoreboard
├── infrastructure/      # Docker Compose and deployment scripts
├── services/            # Vulnerable services
├── docs/                # Documentation
└── tests/               # Test suite
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 16
- Redis 7

### Installation

```bash
# Clone repository
git clone <repository-url>
cd sliverpayload

# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Running the Gameserver

```bash
# Start services
docker-compose up -d

# Run gameserver components
python manage.py runserver          # Web interface
python -m gameserver.controller     # Tick controller
celery -A gameserver worker         # Checker workers
python -m gameserver.submission     # Flag submission server
```

## Configuration

Edit `gameserver/config/game_config.py`:

- `TICK_DURATION_SECONDS`: Round duration (default: 60s)
- `FLAG_VALIDITY_TICKS`: How long flags are valid (default: 5 ticks)
- Scoring parameters
- Docker and network settings

## Development Status

🚧 **Active Development** - Phase 1 (Foundation) completed:

- ✅ Database models (Team, Service, Flag, Tick, ServiceStatus, Submission, Score)
- ✅ Flag generation system with HMAC-based uniqueness
- ✅ Docker API flag injector
- ✅ Configuration system
- 🔄 Controller and checker system (in progress)
- ⏳ Submission server
- ⏳ Scoring system
- ⏳ Web interface

## License

MIT License - see [LICENSE](LICENSE) file for details.

This project is open source and free to use for educational purposes, CTF competitions, and security training.

## Contributors

Created as an Attack & Defense CTF infrastructure for cybersecurity competitions and training.
