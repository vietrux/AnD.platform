#!/bin/bash
# ==============================================================
# AnD Platform - Database Setup Script
# ==============================================================
# This script sets up the complete database for first run
# 
# Prerequisites:
#   - Docker and docker-compose installed
#   - AnD.platform docker-compose services running
#
# Usage:
#   chmod +x setup-db.sh
#   ./setup-db.sh
# ==============================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================="
echo "  AnD Platform - Database Setup"
echo -e "==========================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Check if postgres container is running
POSTGRES_CONTAINER="andplatform-postgres-1"
if ! docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
    echo -e "${YELLOW}Starting Docker services...${NC}"
    docker-compose up -d
    echo "Waiting for PostgreSQL to be ready..."
    sleep 5
fi

# Wait for PostgreSQL to be ready
echo -e "${YELLOW}Checking PostgreSQL connection...${NC}"
for i in {1..30}; do
    if docker exec $POSTGRES_CONTAINER pg_isready -U postgres > /dev/null 2>&1; then
        echo -e "${GREEN}PostgreSQL is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Error: PostgreSQL is not ready after 30 seconds${NC}"
        exit 1
    fi
    sleep 1
done

# Run the init script
echo ""
echo -e "${YELLOW}Initializing database...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker exec -i $POSTGRES_CONTAINER psql -U postgres -d adg_core < "$SCRIPT_DIR/init-db.sql"

echo ""
echo -e "${GREEN}=========================================="
echo "  Database setup complete!"
echo -e "==========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Start the GameCoreServer (Python): uv run python main.py"
echo "  2. Start the Wrapper (Java): ./mvnw spring-boot:run"
echo "  3. Start the Frontend: npm run dev"
echo ""
echo "Default admin credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo -e "${YELLOW}IMPORTANT: Change the admin password after first login!${NC}"
