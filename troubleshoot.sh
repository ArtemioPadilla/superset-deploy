#!/bin/bash
# Troubleshooting script for common Superset issues

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🔍 Superset Troubleshooting"
echo "=========================="
echo ""

# Check Docker
echo "1. Checking Docker..."
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker is running${NC}"
    docker version | grep "Version:" | head -1
else
    echo -e "${RED}✗ Docker is not running${NC}"
    echo "  Please start Docker Desktop and try again"
    exit 1
fi

# Check platform
echo ""
echo "2. Checking platform..."
ARCH=$(uname -m)
echo "   Architecture: $ARCH"
if [[ $ARCH == "arm64" ]]; then
    echo -e "${YELLOW}⚠️  Apple Silicon detected - will use AMD64 emulation${NC}"
    echo "   This may take longer to start"
fi

# Check containers
echo ""
echo "3. Checking containers..."
if docker ps -a | grep -q superset; then
    echo "   Found Superset containers:"
    docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep superset || true
else
    echo "   No Superset containers found"
fi

# Check logs
echo ""
echo "4. Recent logs:"
if docker ps -a | grep -q superset_app; then
    echo -e "${YELLOW}Last 10 lines from Superset:${NC}"
    docker logs --tail 10 superset_app 2>&1 || echo "   No logs available"
fi

# Check port availability
echo ""
echo "5. Checking port 8088..."
if lsof -Pi :8088 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}✗ Port 8088 is in use${NC}"
    echo "   Process using port:"
    lsof -Pi :8088 -sTCP:LISTEN
else
    echo -e "${GREEN}✓ Port 8088 is available${NC}"
fi

# Cleanup option
echo ""
echo "6. Cleanup options:"
echo "   To remove all Superset containers and start fresh:"
echo -e "${YELLOW}   docker-compose -f docker/docker-compose.minimal.yaml down -v${NC}"
echo "   To remove all Docker images and start completely fresh:"
echo -e "${YELLOW}   docker system prune -a${NC}"

# Test connectivity
echo ""
echo "7. Testing connectivity..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8088/health 2>/dev/null | grep -q "200"; then
    echo -e "${GREEN}✓ Superset is responding at http://localhost:8088${NC}"
else
    echo -e "${YELLOW}⚠️  Superset is not responding yet${NC}"
    echo "   This is normal during startup"
fi

echo ""
echo "Common solutions:"
echo "1. If containers won't start: docker-compose -f docker/docker-compose.minimal.yaml down -v"
echo "2. If port is in use: kill -9 \$(lsof -ti:8088)"
echo "3. If images won't download: check your internet connection"
echo "4. For Apple Silicon: be patient, emulation takes longer"