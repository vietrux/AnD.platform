#!/bin/bash
# Complete CTF System Startup Script

set -e  # Exit on error

echo "🚀 Starting CTF System..."
echo ""

# Check if venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated!"
    echo "Run: source .venv/bin/activate"
    exit 1
fi

# 1. Start infrastructure
echo "📦 Starting infrastructure (PostgreSQL + Redis)..."
cd infrastructure
docker compose up -d
cd ..
sleep 3

# 2. Run migrations
echo ""
echo "🗄️  Running database migrations..."
export DJANGO_SETTINGS_MODULE=gameserver.config.settings
python manage.py migrate

# 3. Setup teams and services
echo ""
echo "👥 Setting up teams and services..."
python infrastructure/setup_database.py

echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo "✅ CTF System Ready!"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "🎯 Start the gameserver components:"
echo ""
echo "Terminal 1 - Tick Manager (generates flags every 60s):"
echo "  python -m gameserver.controller.tick_manager"
echo ""
echo "Terminal 2 - Submission Server (port 31337):"
echo "  python -m gameserver.submission.submission_server"
echo ""
echo "Terminal 3 - Django Admin (optional):"
echo "  python manage.py createsuperuser  # First time only"
echo "  python manage.py runserver"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
