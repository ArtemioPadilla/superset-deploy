#!/bin/bash
# Common functions and error handling for all scripts

# Enable strict error handling
set -euo pipefail

# Colors for output
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export RED='\033[0;31m'
export BLUE='\033[0;34m'
export CYAN='\033[0;36m'
export NC='\033[0m' # No Color

# Error handler
error_handler() {
    local line_no=$1
    local bash_lineno=$2
    local last_command=$3
    local code=$4
    echo -e "${RED}❌ ERROR: Command failed at line $line_no: $last_command (exit code: $code)${NC}" >&2
}

# Set up error handling
trap 'error_handler ${LINENO} ${BASH_LINENO} "$BASH_COMMAND" $?' ERR

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check required commands
check_requirements() {
    local requirements=("$@")
    local missing=()
    
    for cmd in "${requirements[@]}"; do
        if ! command_exists "$cmd"; then
            missing+=("$cmd")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        echo -e "${RED}❌ Missing required commands: ${missing[*]}${NC}"
        echo "Please install the missing commands and try again."
        exit 1
    fi
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running${NC}"
        echo "Please start Docker Desktop and try again"
        exit 1
    fi
}

# Function to check if port is in use
check_port() {
    local port=$1
    local service=${2:-"service"}
    
    if command_exists lsof; then
        if lsof -Pi :${port} -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e "${RED}❌ Port ${port} (${service}) is already in use${NC}"
            echo "You can either:"
            echo "1. Stop the process using port ${port}: kill -9 \$(lsof -ti:${port})"
            echo "2. Choose a different port"
            return 1
        fi
    elif command_exists netstat; then
        if netstat -tuln 2>/dev/null | grep -q ":${port} "; then
            echo -e "${RED}❌ Port ${port} (${service}) is already in use${NC}"
            return 1
        fi
    else
        # If we can't check, warn but continue
        echo -e "${YELLOW}⚠ Cannot check if port ${port} is in use (install lsof or netstat)${NC}"
    fi
    return 0
}

# Function to generate secure password
generate_password() {
    local length=${1:-32}
    
    if command_exists openssl; then
        openssl rand -base64 $length | tr -d "=+/" | cut -c1-$length
    elif command_exists python3; then
        python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range($length)))"
    elif command_exists python; then
        python -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range($length)))"
    else
        echo -e "${RED}❌ ERROR: No secure random generator available${NC}"
        echo "Please install openssl or python3 for secure password generation"
        exit 1
    fi
}

# Function to create directory with proper permissions
create_secure_directory() {
    local dir=$1
    local perms=${2:-755}
    
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        chmod "$perms" "$dir"
        echo -e "${GREEN}✓ Created directory: $dir${NC}"
    fi
}

# Function to wait for service
wait_for_service() {
    local host=$1
    local port=$2
    local service=${3:-"service"}
    local timeout=${4:-60}
    
    echo -n "Waiting for $service"
    
    local count=0
    while [ $count -lt $timeout ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        count=$((count + 1))
    done
    
    echo -e " ${RED}✗ (timeout)${NC}"
    return 1
}

# Function to confirm action
confirm() {
    local message=${1:-"Continue?"}
    read -p "$message [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# Function to get docker compose command
get_docker_compose_cmd() {
    if command_exists docker-compose; then
        echo "docker-compose"
    elif docker compose version >/dev/null 2>&1; then
        echo "docker compose"
    else
        echo -e "${RED}❌ Neither 'docker-compose' nor 'docker compose' found${NC}"
        exit 1
    fi
}

# Export the docker compose command
export DOCKER_COMPOSE=$(get_docker_compose_cmd)

# Function to cleanup on exit
cleanup() {
    # Add any cleanup tasks here
    :
}

# Set up cleanup trap
trap cleanup EXIT