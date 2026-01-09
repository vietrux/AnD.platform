#!/bin/bash
# ==============================================================
# AnD Platform - Complete Database Setup Script
# ==============================================================
# This script sets up the complete database for first run.
# It will:
#   1. Start Docker services if not running
#   2. Wait for PostgreSQL to be ready
#   3. Create database if needed
#   4. Initialize all tables and indexes
#   5. Create default admin account
#
# Prerequisites:
#   - Docker and docker-compose installed
#   - AnD.platform directory with docker-compose.yml
#
# Usage:
#   chmod +x setup-db.sh
#   ./setup-db.sh
#
# Options:
#   --reset    Drop and recreate the database (WARNING: loses all data)
#   --check    Only check database status, don't initialize
#
# Last Updated: 2026-01-09
# ==============================================================

set -e

# Configuration
POSTGRES_CONTAINER="andplatform-postgres-1"
POSTGRES_USER="postgres"
DATABASE_NAME="adg_core"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
RESET_DB=false
CHECK_ONLY=false
for arg in "$@"; do
    case $arg in
        --reset)
            RESET_DB=true
            ;;
        --check)
            CHECK_ONLY=true
            ;;
    esac
done

echo -e "${GREEN}================================================"
echo "   AnD Platform - Database Setup"
echo -e "================================================${NC}"
echo ""

# ==============================================================
# Step 1: Check Docker
# ==============================================================
echo -e "${BLUE}[1/5]${NC} Checking Docker..."

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker daemon is not running${NC}"
    echo "Please start Docker and try again"
    exit 1
fi

echo -e "  ${GREEN}✓${NC} Docker is running"

# ==============================================================
# Step 2: Start PostgreSQL container
# ==============================================================
echo -e "${BLUE}[2/5]${NC} Checking PostgreSQL container..."

if ! docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
    echo -e "  ${YELLOW}Starting Docker services...${NC}"
    
    if [ -f "$SCRIPT_DIR/docker-compose.yml" ]; then
        cd "$SCRIPT_DIR"
        docker-compose up -d postgres
        echo "  Waiting for container to start..."
        sleep 3
    else
        echo -e "${RED}Error: docker-compose.yml not found in $SCRIPT_DIR${NC}"
        exit 1
    fi
fi

echo -e "  ${GREEN}✓${NC} Container ${POSTGRES_CONTAINER} is running"

# ==============================================================
# Step 3: Wait for PostgreSQL to be ready
# ==============================================================
echo -e "${BLUE}[3/5]${NC} Waiting for PostgreSQL to be ready..."

MAX_ATTEMPTS=30
for i in $(seq 1 $MAX_ATTEMPTS); do
    if docker exec $POSTGRES_CONTAINER pg_isready -U $POSTGRES_USER > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} PostgreSQL is ready"
        break
    fi
    
    if [ $i -eq $MAX_ATTEMPTS ]; then
        echo -e "${RED}Error: PostgreSQL is not ready after ${MAX_ATTEMPTS} seconds${NC}"
        echo "Check container logs: docker logs $POSTGRES_CONTAINER"
        exit 1
    fi
    
    echo -e "  Waiting... ($i/$MAX_ATTEMPTS)"
    sleep 1
done

# Check only mode - show status and exit
if [ "$CHECK_ONLY" = true ]; then
    echo ""
    echo -e "${BLUE}[STATUS]${NC} Database status:"
    
    # Check if database exists
    if docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -lqt | cut -d \| -f 1 | grep -qw "$DATABASE_NAME"; then
        echo -e "  ${GREEN}✓${NC} Database '$DATABASE_NAME' exists"
        
        # Count tables
        TABLE_COUNT=$(docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $DATABASE_NAME -tAc \
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
        echo -e "  ${GREEN}✓${NC} Tables: $TABLE_COUNT"
        
        # Check users
        USER_COUNT=$(docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $DATABASE_NAME -tAc \
            "SELECT COUNT(*) FROM users" 2>/dev/null || echo "0")
        echo -e "  ${GREEN}✓${NC} Users: $USER_COUNT"
    else
        echo -e "  ${YELLOW}!${NC} Database '$DATABASE_NAME' does not exist"
    fi
    
    exit 0
fi

# ==============================================================
# Step 4: Create/Reset Database
# ==============================================================
echo -e "${BLUE}[4/5]${NC} Setting up database..."

# Check if database exists
DB_EXISTS=$(docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -lqt | cut -d \| -f 1 | grep -cw "$DATABASE_NAME" || true)

if [ "$RESET_DB" = true ] && [ "$DB_EXISTS" -gt 0 ]; then
    echo -e "  ${YELLOW}WARNING: Dropping existing database...${NC}"
    docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -c "DROP DATABASE IF EXISTS $DATABASE_NAME;"
    DB_EXISTS=0
fi

if [ "$DB_EXISTS" -eq 0 ]; then
    echo -e "  Creating database '$DATABASE_NAME'..."
    docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -c "CREATE DATABASE $DATABASE_NAME;"
    echo -e "  ${GREEN}✓${NC} Database created"
else
    echo -e "  ${GREEN}✓${NC} Database already exists"
fi

# ==============================================================
# Step 5: Initialize Schema
# ==============================================================
echo -e "${BLUE}[5/5]${NC} Initializing database schema..."

if [ ! -f "$SCRIPT_DIR/init-db.sql" ]; then
    echo -e "${RED}Error: init-db.sql not found in $SCRIPT_DIR${NC}"
    exit 1
fi

# Run initialization script
docker exec -i $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $DATABASE_NAME < "$SCRIPT_DIR/init-db.sql"

echo -e "  ${GREEN}✓${NC} Schema initialized"

# ==============================================================
# Complete!
# ==============================================================
echo ""
echo -e "${GREEN}================================================"
echo "   Database Setup Complete!"
echo -e "================================================${NC}"
echo ""
echo "Tables created:"
docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $DATABASE_NAME -c \
    "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;" \
    2>/dev/null | grep -E "^\s+\w+" | head -15

echo ""
echo -e "${YELLOW}Default Admin Account:${NC}"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo -e "${RED}IMPORTANT: Change the admin password after first login!${NC}"
echo ""
echo "Next steps:"
echo "  1. Start GameCoreServer: cd AnD.platform && uv run python main.py"
echo "  2. Start Wrapper:        cd AnD.wrapper && ./mvnw spring-boot:run"
echo "  3. Start Frontend:       cd AnD.frontend && bun run dev"
echo ""
