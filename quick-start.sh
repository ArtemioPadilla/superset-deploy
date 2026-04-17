#!/bin/bash
# Unified Quick Start Script - Choose your Apache Superset deployment

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Source common functions
if [ -f "$SCRIPT_DIR/scripts/common.sh" ]; then
    source "$SCRIPT_DIR/scripts/common.sh"
else
    # Fallback if common.sh doesn't exist yet
    set -e
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    RED='\033[0;31m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    NC='\033[0m'
fi

# Banner
echo -e "${CYAN}🚀 Apache Superset Quick Start${NC}"
echo "=============================="
echo ""

# Detect platform
if [[ $(uname -m) == "arm64" ]]; then
    echo -e "${YELLOW}📱 Detected Apple Silicon (ARM64)${NC}"
    echo -e "${YELLOW}   Note: First run may take longer due to emulation${NC}"
    echo ""
fi

# Check Docker
check_docker

# Function to check multiple ports
check_ports() {
    local ports=("$@")
    local port_names=("Superset" "PostgreSQL" "Redis" "Prometheus" "Grafana" "MinIO" "Firestore" "Pub/Sub" "Traefik")
    
    for i in "${!ports[@]}"; do
        if ! check_port "${ports[$i]}" "${port_names[$i]:-Port ${ports[$i]}}"; then
            return 1
        fi
    done
    return 0
}

# Function to create minimal .env
create_minimal_env() {
    if [ ! -f .env ]; then
        echo -e "${YELLOW}Creating .env file for minimal setup...${NC}"
        
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
        
        cat > .env << EOF
# Minimal Superset Configuration
SUPERSET_VERSION=5.0.0
SUPERSET_SECRET_KEY=$SUPERSET_SECRET_KEY
SUPERSET_ADMIN_USERNAME=admin
SUPERSET_ADMIN_PASSWORD=admin
SUPERSET_ADMIN_EMAIL=admin@localhost
SUPERSET_PORT=8088
EOF
        # Set secure permissions
        chmod 600 .env
        echo -e "${GREEN}✓ Created .env file with secure permissions${NC}"
    fi
}

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
        else
            DB_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(16))' 2>/dev/null || python -c 'import secrets; print(secrets.token_urlsafe(16))')
            REDIS_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(16))' 2>/dev/null || python -c 'import secrets; print(secrets.token_urlsafe(16))')
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
DATABASE_NAME=superset
DATABASE_USER=superset
DATABASE_PASSWORD=$DB_PASSWORD
DATABASE_PORT=5432

# Redis Configuration
REDIS_PORT=6379
REDIS_PASSWORD=$REDIS_PASSWORD

# Monitoring Configuration
GRAFANA_ADMIN_PASSWORD=admin
PROMETHEUS_RETENTION_DAYS=7
EOF
        # Set secure permissions
        chmod 600 .env.full
        echo -e "${GREEN}✓ Created .env.full file with secure permissions${NC}"
        echo -e "${YELLOW}NOTE: Secure passwords have been generated for database and Redis${NC}"
    fi
}

# Function to ask about Cloudflare tunnel
ask_cloudflare() {
    echo ""
    echo -e "${CYAN}🔐 Secure Access with Cloudflare Tunnel (FREE)${NC}"
    echo "Would you like to enable Cloudflare Tunnel for secure access?"
    echo "Benefits:"
    echo "  • ✅ Completely FREE (no bandwidth charges)"
    echo "  • ✅ No public IP exposure"
    echo "  • ✅ Enterprise-grade security"
    echo "  • ✅ Replaces expensive load balancers"
    echo ""
    read -p "Enable Cloudflare Tunnel? [y/N]: " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# Function to setup Cloudflare if not configured
setup_cloudflare_if_needed() {
    local token_to_use=""
    
    # Check if token exists in environment
    if [ -n "${CLOUDFLARE_TUNNEL_TOKEN}" ]; then
        echo -e "${GREEN}✓ Found existing Cloudflare Tunnel token in environment${NC}"
        echo "Token preview: ${CLOUDFLARE_TUNNEL_TOKEN:0:20}..."
        echo ""
        read -p "Use this token? [Y/n]: " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            token_to_use="${CLOUDFLARE_TUNNEL_TOKEN}"
        fi
    fi
    
    # If no token selected yet, ask for input
    if [ -z "$token_to_use" ]; then
        echo ""
        echo -e "${CYAN}Choose how to configure Cloudflare Tunnel:${NC}"
        echo "1) Create new tunnel (recommended for first-time setup)"
        echo "2) Enter existing tunnel token"
        echo "3) Skip for now"
        echo ""
        read -p "Enter choice [1-3]: " choice
        echo ""
        
        case $choice in
            1)
                # Run setup script to create new tunnel
                if [ -f ./scripts/setup-tunnel.sh ]; then
                    ./scripts/setup-tunnel.sh
                    # Reload environment to get new token
                    if [ -f .env ]; then
                        set -a
                        source .env
                        set +a
                    fi
                    return 0
                else
                    echo -e "${RED}❌ setup-tunnel.sh not found${NC}"
                    return 1
                fi
                ;;
            2)
                # Ask for token input
                echo -e "${YELLOW}Enter your Cloudflare Tunnel token:${NC}"
                echo "You can get this from:"
                echo "  • Cloudflare Zero Trust Dashboard > Access > Tunnels"
                echo "  • Run: cloudflared tunnel token YOUR-TUNNEL-NAME"
                echo ""
                read -p "Token: " input_token
                
                if [ -n "$input_token" ]; then
                    token_to_use="$input_token"
                    
                    # Save to .env file
                    if [ -f .env ]; then
                        # Update existing .env
                        if grep -q "CLOUDFLARE_TUNNEL_TOKEN=" .env; then
                            # Use sed with backup for compatibility
                            sed -i.bak "s|CLOUDFLARE_TUNNEL_TOKEN=.*|CLOUDFLARE_TUNNEL_TOKEN=$token_to_use|" .env
                            rm -f .env.bak
                        else
                            echo "CLOUDFLARE_TUNNEL_TOKEN=$token_to_use" >> .env
                        fi
                    else
                        # Create new .env with token
                        echo "CLOUDFLARE_TUNNEL_TOKEN=$token_to_use" > .env
                    fi
                    
                    # Export for current session
                    export CLOUDFLARE_TUNNEL_TOKEN="$token_to_use"
                    echo -e "${GREEN}✓ Tunnel token saved${NC}"
                else
                    echo -e "${RED}❌ No token provided${NC}"
                    return 1
                fi
                ;;
            3)
                echo -e "${YELLOW}Skipping Cloudflare Tunnel setup${NC}"
                return 1
                ;;
            *)
                echo -e "${RED}Invalid choice${NC}"
                return 1
                ;;
        esac
    else
        # Use the confirmed existing token
        export CLOUDFLARE_TUNNEL_TOKEN="$token_to_use"
    fi
    
    # Ask for hostname if not set
    if [ -z "${CLOUDFLARE_HOSTNAME}" ] && [ -n "$token_to_use" ]; then
        echo ""
        echo -e "${CYAN}Enter your domain for Cloudflare Tunnel:${NC}"
        echo "Examples:"
        echo "  • superset.yourdomain.com"
        echo "  • analytics.company.com"
        echo "  • localhost (for testing)"
        echo ""
        read -p "Domain: " hostname
        
        if [ -n "$hostname" ]; then
            # Save to .env
            if grep -q "CLOUDFLARE_HOSTNAME=" .env 2>/dev/null; then
                sed -i.bak "s|CLOUDFLARE_HOSTNAME=.*|CLOUDFLARE_HOSTNAME=$hostname|" .env
                rm -f .env.bak
            else
                echo "CLOUDFLARE_HOSTNAME=$hostname" >> .env
            fi
            export CLOUDFLARE_HOSTNAME="$hostname"
            echo -e "${GREEN}✓ Domain saved${NC}"
        fi
    fi
    
    return 0
}

# Function to start minimal stack
start_minimal() {
    echo -e "${BLUE}Starting Minimal Stack (SQLite only)...${NC}"
    
    # Check port
    if ! check_ports 8088; then
        return 1
    fi
    
    # Create env
    create_minimal_env
    
    # Create directories
    mkdir -p data
    
    # Ask about Cloudflare
    local use_cloudflare=false
    if ask_cloudflare; then
        use_cloudflare=true
        setup_cloudflare_if_needed
    fi
    
    # Clean up any existing containers
    echo -e "${YELLOW}Cleaning up any existing containers...${NC}"
    docker-compose -f docker/docker-compose.minimal.yaml down 2>/dev/null || true
    
    # Start
    echo -e "${YELLOW}Starting Superset...${NC}"
    if [ "$use_cloudflare" = true ] && [ -n "${CLOUDFLARE_TUNNEL_TOKEN}" ]; then
        # Start with Cloudflare profile
        docker-compose -f docker/docker-compose.yaml --profile cloudflare up -d superset cloudflared
    else
        # Start without Cloudflare
        docker-compose -f docker/docker-compose.minimal.yaml up -d
    fi
    
    # Wait for initialization
    echo -e "${YELLOW}Waiting for Superset to initialize...${NC}"
    sleep 10
    
    # Check if running
    if docker-compose -f docker/docker-compose.minimal.yaml ps 2>/dev/null | grep -q "superset.*Up" || \
       docker-compose -f docker/docker-compose.yaml ps 2>/dev/null | grep -q "superset.*Up"; then
        echo -e "${GREEN}✅ Superset is running!${NC}"
        echo ""
        echo "📊 Access Superset at: http://localhost:8088"
        echo "👤 Login with: admin / admin"
        
        if [ "$use_cloudflare" = true ] && [ -n "${CLOUDFLARE_HOSTNAME}" ]; then
            echo "🔐 Secure access via: https://${CLOUDFLARE_HOSTNAME}"
        fi
        
        echo ""
        echo "Commands:"
        echo "  • View logs: docker-compose -f docker/docker-compose.minimal.yaml logs -f"
        echo "  • Stop: docker-compose -f docker/docker-compose.minimal.yaml down"
        echo "  • Clean all: docker-compose -f docker/docker-compose.minimal.yaml down -v"
        
        if [ "$use_cloudflare" = true ]; then
            echo ""
            echo "Cloudflare Tunnel:"
            echo "  • View tunnel logs: docker logs superset_cloudflared"
            echo "  • Setup access policies: https://one.dash.cloudflare.com/"
        fi
    else
        echo -e "${RED}❌ Failed to start Superset${NC}"
        echo "Check logs: docker-compose -f docker/docker-compose.minimal.yaml logs"
        return 1
    fi
}

# Function to start full stack
start_fullstack() {
    echo -e "${BLUE}Starting Full Stack (PostgreSQL + Redis + Monitoring)...${NC}"
    
    # Check ports
    if ! check_ports 8088 5432 6379 9090 3000; then
        return 1
    fi
    
    # Run the full stack script
    ./quick-start-full.sh
}

# Function to start free tier emulation
start_freetier() {
    echo -e "${BLUE}Starting Free Tier Emulation...${NC}"
    echo -e "${YELLOW}Note: This emulates GCP's actual free tier, which does NOT include:${NC}"
    echo "  • Cloud SQL (PostgreSQL) - Using SQLite instead"
    echo "  • Memorystore (Redis) - No caching layer"
    echo ""
    
    # Check ports
    if ! check_ports 8088 9001 3000 8080 8085 8090; then
        return 1
    fi
    
    # Ask about Cloudflare (especially important for free tier)
    local use_cloudflare=false
    echo ""
    echo -e "${CYAN}💡 Recommended for Free Tier:${NC}"
    if ask_cloudflare; then
        use_cloudflare=true
        setup_cloudflare_if_needed
    fi
    
    # Initialize free tier
    if [ -f ./scripts/init-free-tier.sh ]; then
        echo -e "${YELLOW}Initializing free tier environment...${NC}"
        ./scripts/init-free-tier.sh
    fi
    
    # Start services
    echo -e "${YELLOW}Starting free tier services...${NC}"
    if [ "$use_cloudflare" = true ] && [ -n "${CLOUDFLARE_TUNNEL_TOKEN}" ]; then
        # Start with Cloudflare profile
        docker-compose -f docker/docker-compose.yaml -f docker/docker-compose.full-free-tier.yaml --profile cloudflare up -d
    else
        # Start without Cloudflare
        docker-compose -f docker/docker-compose.yaml -f docker/docker-compose.full-free-tier.yaml up -d
    fi
    
    echo ""
    echo -e "${GREEN}✅ Free Tier Emulation is running!${NC}"
    echo ""
    echo "🌐 Access Points:"
    echo "  • Superset: http://localhost:8088 (admin/admin)"
    echo "  • MinIO: http://localhost:9001 (minioadmin/minioadmin)"
    echo "  • Grafana: http://localhost:3000 (admin/admin)"
    echo "  • Firestore UI: http://localhost:8080"
    
    if [ "$use_cloudflare" = true ] && [ -n "${CLOUDFLARE_HOSTNAME}" ]; then
        echo ""
        echo "🔐 Secure access:"
        echo "  • Superset: https://${CLOUDFLARE_HOSTNAME}"
        echo "  • Grafana: https://grafana.${CLOUDFLARE_HOSTNAME#*.}"
    fi
    
    echo ""
    echo "📊 Emulated Limits:"
    echo "  • CPU: 0.25 vCPU (e2-micro)"
    echo "  • Memory: 1GB RAM"
    echo "  • Storage: 5GB (Cloud Storage)"
    echo "  • Requests: 2M/month (rate limited)"
    
    if [ "$use_cloudflare" = false ]; then
        echo ""
        echo -e "${YELLOW}💡 Tip:${NC} For GCP deployment, use Cloudflare Tunnel"
        echo "   to avoid $18/month Load Balancer costs!"
        echo "   Run: ./scripts/setup-tunnel.sh"
    fi
}

# Function to show menu
show_menu() {
    echo "Choose your deployment type:"
    echo ""
    echo -e "${CYAN}1)${NC} Minimal - SQLite only, fastest start (1 minute)"
    echo -e "   ${YELLOW}Includes:${NC} Superset + SQLite"
    echo ""
    echo -e "${CYAN}2)${NC} Full Stack - Production-like with all databases (3 minutes)"
    echo -e "   ${YELLOW}Includes:${NC} Superset + PostgreSQL + Redis + Prometheus + Grafana"
    echo ""
    echo -e "${CYAN}3)${NC} Free Tier Emulation - Test GCP Free Tier limits (5 minutes)"
    echo -e "   ${YELLOW}Includes:${NC} Superset + SQLite + MinIO + Firestore/Pub/Sub emulators"
    echo -e "   ${YELLOW}Note:${NC} Uses SQLite (not PostgreSQL) to match GCP free tier"
    echo ""
    echo -e "${CYAN}4)${NC} Exit"
    echo ""
    echo -e "${GREEN}🔐 All options include FREE Cloudflare Tunnel for secure access!${NC}"
    echo ""
}

# Main menu loop
while true; do
    show_menu
    read -p "Enter your choice [1-4]: " choice
    echo ""
    
    case $choice in
        1)
            start_minimal
            break
            ;;
        2)
            start_fullstack
            break
            ;;
        3)
            start_freetier
            break
            ;;
        4)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Please try again.${NC}"
            echo ""
            ;;
    esac
done

echo ""
echo -e "${CYAN}Need help?${NC}"
echo "  • Documentation: docs/QUICK_START.md"
echo "  • Troubleshooting: ./troubleshoot.sh"
echo "  • FAQ: docs/FAQ.md"