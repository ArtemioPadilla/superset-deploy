#!/bin/bash
# Quick Start Script - Get Superset running in under 2 minutes!

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🚀 Apache Superset Quick Start"
echo "=============================="
echo ""

# Detect platform
if [[ $(uname -m) == "arm64" ]]; then
    echo -e "${YELLOW}📱 Detected Apple Silicon (ARM64)${NC}"
    echo -e "${YELLOW}   Using AMD64 emulation for Superset${NC}"
    echo ""
fi

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    echo "Please start Docker and try again"
    exit 1
fi

# Check if port 8088 is available
if lsof -Pi :8088 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port 8088 is already in use${NC}"
    echo "You can either:"
    echo "1. Stop the process using port 8088"
    echo "2. Use a different port: SUPERSET_PORT=8089 ./quick-start.sh"
    exit 1
fi

# Create minimal .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cat > .env << EOF
# Minimal Superset Configuration
SUPERSET_VERSION=5.0.0
SUPERSET_SECRET_KEY=$(openssl rand -base64 32 2>/dev/null || echo "CHANGE-ME-IN-PRODUCTION-$(date +%s)")
SUPERSET_ADMIN_USERNAME=admin
SUPERSET_ADMIN_PASSWORD=admin
SUPERSET_ADMIN_EMAIL=admin@localhost
SUPERSET_PORT=${SUPERSET_PORT:-8088}
EOF
    echo -e "${GREEN}✓ Created .env file${NC}"
fi

# Create data directory
mkdir -p data

# Clean up any existing containers
echo -e "${YELLOW}Cleaning up any existing containers...${NC}"
docker-compose -f docker/docker-compose.minimal.yaml down 2>/dev/null || true

# Start Superset with SQLite (no external dependencies)
echo -e "${YELLOW}Starting Superset...${NC}"
echo -e "${YELLOW}(This may take a minute on first run)${NC}"
docker-compose -f docker/docker-compose.minimal.yaml up -d

# Wait for initialization
echo -e "${YELLOW}Waiting for Superset to initialize...${NC}"
echo -e "${YELLOW}(This may take up to 2 minutes on Apple Silicon)${NC}"

# Wait for container to be ready
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker-compose -f docker/docker-compose.minimal.yaml ps | grep -q "superset.*Up.*8088"; then
        break
    fi
    echo -n "."
    sleep 2
    attempt=$((attempt + 1))
done
echo ""

# Check if superset is running
if docker-compose -f docker/docker-compose.minimal.yaml ps | grep -q "superset.*Up"; then
    echo -e "${GREEN}✅ Superset is running!${NC}"
    echo ""
    echo "📊 Access Superset at: http://localhost:${SUPERSET_PORT:-8088}"
    echo "👤 Login with: admin / admin"
    echo ""
    echo "Next steps:"
    echo "- View logs: docker-compose -f docker/docker-compose.minimal.yaml logs -f superset"
    echo "- Stop Superset: docker-compose -f docker/docker-compose.minimal.yaml down"
    echo "- Add PostgreSQL: docker-compose -f docker/docker-compose.yaml --profile postgres up -d"
    echo "- Full documentation: docs/QUICK_START.md"
else
    echo -e "${RED}❌ Failed to start Superset${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check logs: docker-compose -f docker/docker-compose.minimal.yaml logs superset"
    echo "2. Run diagnostics: ./troubleshoot.sh"
    echo "3. Clean and retry: docker-compose -f docker/docker-compose.minimal.yaml down -v && ./quick-start.sh"
    echo ""
    if [[ $(uname -m) == "arm64" ]]; then
        echo "Note: You're on Apple Silicon. First run may take 2-3 minutes due to emulation."
    fi
    exit 1
fi