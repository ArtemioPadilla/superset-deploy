#!/bin/bash
# Quick Start Script for Full Stack Apache Superset (PostgreSQL + Redis + Monitoring)

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${CYAN}🚀 Apache Superset Full Stack Quick Start${NC}"
echo "=========================================="
echo ""

# Detect platform
if [[ $(uname -m) == "arm64" ]]; then
    echo -e "${YELLOW}📱 Detected Apple Silicon (ARM64)${NC}"
    echo -e "${YELLOW}   Note: First run may take longer due to emulation${NC}"
    echo ""
fi

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Function to check ports
check_ports() {
    local ports=("$@")
    local port_names=("Superset" "PostgreSQL" "Redis" "Prometheus" "Grafana")
    
    for i in "${!ports[@]}"; do
        if lsof -Pi :${ports[$i]} -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e "${RED}❌ Port ${ports[$i]} (${port_names[$i]}) is already in use${NC}"
            echo "You can either:"
            echo "1. Stop the process using port ${ports[$i]}: kill -9 \$(lsof -ti:${ports[$i]})"
            echo "2. Exit and free up the port"
            return 1
        fi
    done
    return 0
}

# Check required ports
echo -e "${YELLOW}Checking ports...${NC}"
if ! check_ports 8088 5432 6379 9090 3000; then
    echo -e "${RED}Please free up the required ports and try again${NC}"
    exit 1
fi
echo -e "${GREEN}✓ All ports are available${NC}"

# Function to create full stack .env
create_fullstack_env() {
    if [ ! -f .env.full ]; then
        echo -e "${YELLOW}Creating .env.full file for full stack...${NC}"
        
        # Generate secure secret key
        if command -v openssl >/dev/null 2>&1; then
            SUPERSET_SECRET_KEY=$(openssl rand -base64 32)
        elif command -v python3 >/dev/null 2>&1; then
            SUPERSET_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
        elif command -v python >/dev/null 2>&1; then
            SUPERSET_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
        else
            echo -e "${RED}❌ ERROR: No secure random generator available${NC}"
            echo "Please install openssl or python3 for secure secret generation"
            exit 1
        fi
        
        # Generate secure passwords
        if command -v openssl >/dev/null 2>&1; then
            DB_PASSWORD=$(openssl rand -base64 16)
            REDIS_PASSWORD=$(openssl rand -base64 16)
            GRAFANA_PASSWORD=$(openssl rand -base64 12)
        else
            DB_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(16))' 2>/dev/null || python -c 'import secrets; print(secrets.token_urlsafe(16))')
            REDIS_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(16))' 2>/dev/null || python -c 'import secrets; print(secrets.token_urlsafe(16))')
            GRAFANA_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(12))' 2>/dev/null || python -c 'import secrets; print(secrets.token_urlsafe(12))')
        fi
        
        cat > .env.full << EOF
# Full Stack Superset Configuration
SUPERSET_VERSION=5.0.0
SUPERSET_SECRET_KEY=$SUPERSET_SECRET_KEY
SUPERSET_ADMIN_USERNAME=admin
SUPERSET_ADMIN_PASSWORD=admin
SUPERSET_ADMIN_EMAIL=admin@localhost
SUPERSET_PORT=8088

# PostgreSQL Configuration
POSTGRES_DB=superset
POSTGRES_USER=superset
POSTGRES_PASSWORD=$DB_PASSWORD
DATABASE_HOST=db
DATABASE_PORT=5432
DATABASE_NAME=superset
DATABASE_USER=superset
DATABASE_PASSWORD=$DB_PASSWORD
DATABASE_URL=postgresql://superset:$DB_PASSWORD@db:5432/superset

# Redis Configuration
REDIS_PORT=6379
REDIS_PASSWORD=$REDIS_PASSWORD
REDIS_URL=redis://:$REDIS_PASSWORD@redis:6379/0

# Monitoring Configuration
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=$GRAFANA_PASSWORD
PROMETHEUS_RETENTION_DAYS=7

# Prometheus Exporters
DATA_SOURCE_NAME=postgresql://superset:$DB_PASSWORD@db:5432/superset?sslmode=disable
EOF
        # Set secure permissions
        chmod 600 .env.full
        echo -e "${GREEN}✓ Created .env.full file with secure permissions${NC}"
        echo ""
        echo -e "${CYAN}Generated secure passwords:${NC}"
        echo -e "  Database password: ${YELLOW}[hidden - see .env.full]${NC}"
        echo -e "  Redis password: ${YELLOW}[hidden - see .env.full]${NC}"
        echo -e "  Grafana password: ${YELLOW}$GRAFANA_PASSWORD${NC}"
        echo ""
    else
        echo -e "${GREEN}✓ Using existing .env.full file${NC}"
        # Source the existing file to get the passwords
        set -a
        source .env.full
        set +a
    fi
}

# Function to create necessary directories
create_directories() {
    echo -e "${YELLOW}Creating necessary directories...${NC}"
    mkdir -p data/postgres
    mkdir -p data/redis
    mkdir -p data/prometheus
    mkdir -p data/grafana
    mkdir -p docker/monitoring
    echo -e "${GREEN}✓ Directories created${NC}"
}

# Function to create Prometheus configuration
create_prometheus_config() {
    if [ ! -f docker/monitoring/prometheus.yml ]; then
        echo -e "${YELLOW}Creating Prometheus configuration...${NC}"
        cat > docker/monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
EOF
        echo -e "${GREEN}✓ Prometheus configuration created${NC}"
    fi
}

# Function to ask about Cloudflare tunnel
ask_cloudflare() {
    echo ""
    echo -e "${CYAN}🔐 Secure Access with Cloudflare Tunnel (FREE)${NC}"
    echo "Would you like to enable Cloudflare Tunnel for secure access?"
    echo ""
    read -p "Enable Cloudflare Tunnel? [y/N]: " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# Create environment file
create_fullstack_env

# Create directories
create_directories

# Create Prometheus config
create_prometheus_config

# Load environment variables
set -a
source .env.full
set +a

# Ask about Cloudflare
USE_CLOUDFLARE=false
CLOUDFLARE_PROFILE=""
if ask_cloudflare; then
    USE_CLOUDFLARE=true
    CLOUDFLARE_PROFILE="--profile cloudflare"
    
    # Check if we have the setup script
    if [ -f ./scripts/setup-tunnel.sh ]; then
        echo -e "${YELLOW}Setting up Cloudflare tunnel...${NC}"
        ./scripts/setup-tunnel.sh
    fi
fi

# Clean up any existing containers
echo -e "${YELLOW}Cleaning up any existing containers...${NC}"
docker-compose -f docker/docker-compose.yaml -f docker/docker-compose.local.yaml down 2>/dev/null || true

# Start services
echo -e "${BLUE}Starting Full Stack services...${NC}"
echo "This includes:"
echo "  • PostgreSQL (database)"
echo "  • Redis (cache)"
echo "  • Superset (BI tool)"
echo "  • Prometheus (metrics)"
echo "  • Grafana (dashboards)"
echo "  • Database & cache exporters"
if [ "$USE_CLOUDFLARE" = true ]; then
    echo "  • Cloudflare Tunnel (secure access)"
fi
echo ""

# Use the correct env file
docker-compose --env-file .env.full \
    -f docker/docker-compose.yaml \
    -f docker/docker-compose.local.yaml \
    $CLOUDFLARE_PROFILE \
    up -d

# Wait for services to be ready
echo ""
echo -e "${YELLOW}Waiting for services to initialize...${NC}"
echo -n "Starting"

# Wait for PostgreSQL
for i in {1..30}; do
    if docker exec superset_db pg_isready -U superset >/dev/null 2>&1; then
        echo -n " [PostgreSQL ✓]"
        break
    fi
    echo -n "."
    sleep 2
done

# Wait for Redis
for i in {1..20}; do
    if docker exec superset_cache redis-cli ping >/dev/null 2>&1; then
        echo -n " [Redis ✓]"
        break
    fi
    echo -n "."
    sleep 1
done

# Wait for Superset
for i in {1..60}; do
    if curl -s http://localhost:8088/health >/dev/null 2>&1; then
        echo -n " [Superset ✓]"
        break
    fi
    echo -n "."
    sleep 2
done

echo ""
echo ""

# Check if all services are running
if docker-compose -f docker/docker-compose.yaml ps | grep -E "(superset|db|redis|prometheus|grafana).*Up" >/dev/null; then
    echo -e "${GREEN}✅ Full Stack is running successfully!${NC}"
    echo ""
    echo -e "${CYAN}🌐 Access Points:${NC}"
    echo "  • Superset: http://localhost:8088 (admin/admin)"
    echo "  • Grafana: http://localhost:3000 (admin/${GRAFANA_ADMIN_PASSWORD:-admin})"
    echo "  • Prometheus: http://localhost:9090"
    echo "  • PostgreSQL: localhost:5432 (superset/${DATABASE_PASSWORD})"
    echo "  • Redis: localhost:6379 (password: ${REDIS_PASSWORD})"
    
    if [ "$USE_CLOUDFLARE" = true ] && [ -n "${CLOUDFLARE_HOSTNAME}" ]; then
        echo ""
        echo -e "${CYAN}🔐 Secure Access:${NC}"
        echo "  • Superset: https://${CLOUDFLARE_HOSTNAME}"
        echo "  • Grafana: https://grafana.${CLOUDFLARE_HOSTNAME#*.}"
    fi
    
    echo ""
    echo -e "${CYAN}📊 Monitoring:${NC}"
    echo "  • Grafana has pre-configured dashboards for:"
    echo "    - PostgreSQL performance"
    echo "    - Redis metrics"
    echo "    - System resources"
    echo ""
    echo -e "${CYAN}🛠 Useful Commands:${NC}"
    echo "  • View logs: docker-compose -f docker/docker-compose.yaml logs -f [service]"
    echo "  • Stop all: docker-compose -f docker/docker-compose.yaml -f docker/docker-compose.local.yaml down"
    echo "  • Restart service: docker-compose -f docker/docker-compose.yaml restart [service]"
    echo "  • View stats: docker stats"
    echo ""
    echo -e "${YELLOW}💡 Tips:${NC}"
    echo "  • Database connection string: postgresql://superset:${DATABASE_PASSWORD}@localhost:5432/superset"
    echo "  • Redis URL: redis://:${REDIS_PASSWORD}@localhost:6379/0"
    echo "  • All passwords are stored in .env.full"
else
    echo -e "${RED}❌ Some services failed to start${NC}"
    echo "Check logs with: docker-compose -f docker/docker-compose.yaml logs"
    exit 1
fi