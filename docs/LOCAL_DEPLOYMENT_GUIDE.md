# Local Deployment Guide

This guide explains how to run Apache Superset locally using the system.yaml configuration approach.

## 🚀 Quick Start Options

### Option 1: Minimal Setup (3 minutes)
```bash
make setup
make dev
# Access at http://localhost:8088 (admin/admin)
```

### Option 2: Free Tier Emulation (5 minutes)
```bash
# Initialize free tier environment
./scripts/init-free-tier.sh
cp .env.free-tier .env

# Start with resource limits
docker-compose -f docker/docker-compose.yaml \
               -f docker/docker-compose.free-tier.yaml up
# Access at http://localhost:8088
```

### Option 3: Full Stack with PostgreSQL (5 minutes)
```bash
make setup
docker-compose -f docker/docker-compose.yaml --profile postgres up
# Access at http://localhost:8088
```

## 🏗️ Architecture Overview

### Free Tier Emulation Architecture

When emulating GCP Free Tier locally:

```
Local Machine
├── Superset (0.25 CPU, 1GB RAM)  # e2-micro limits
├── SQLite (1GB max)               # Firestore limits
├── MinIO (5GB max)                # Cloud Storage limits
├── Firestore Emulator             # Database emulation
├── Pub/Sub Emulator               # Messaging emulation
└── Traefik Rate Limiter           # 2M requests/month limit
```

### Configuration Files Relationship

```
system.yaml                    # Your deployment configuration
    ↓
pulumi/__main__.py            # Reads system.yaml
    ↓
Determines stack type         # minimal/standard/production
    ↓
For local environment:        # Uses Docker Compose
- docker-compose.yaml         # Base Superset service
- docker-compose.local.yaml   # Additional local services
```

### Pulumi.yaml Role in Local Development

For **local deployments**, `pulumi/Pulumi.yaml` serves a minimal role:
- It identifies this as a Pulumi project
- It's not actively used since we're using Docker Compose
- The actual configuration comes from `system.yaml`

For **cloud deployments**, Pulumi.yaml becomes important:
- Defines GCP project and region parameters
- Manages Pulumi stack state
- Handles cloud resource provisioning

## 🚀 Quick Start - Local Development

### 1. Basic Local Setup

```bash
# Copy example configuration
cp examples/configs/local-deployments.yaml system.yaml

# Start minimal local deployment
make dev

# Access Superset
open http://localhost:8088
```

### 2. Local with PostgreSQL

```yaml
# In system.yaml, enable local-postgres stack
stacks:
  local-postgres:
    enabled: true
```

```bash
# Start with PostgreSQL
docker-compose -f docker/docker-compose.yaml \
  -f docker/docker-compose.local.yaml up -d

# Initialize database
docker exec -it superset_app superset db upgrade
docker exec -it superset_app superset init
```

### 3. Local with Full Monitoring

```bash
# Start with monitoring stack
docker-compose -f docker/docker-compose.yaml \
  -f docker/docker-compose.local.yaml \
  --profile monitoring up -d

# Access services:
# - Superset: http://localhost:8088
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000
```

## 📝 Local Stack Examples

### Minimal Development Stack
Perfect for quick development and testing:

```yaml
stacks:
  local-dev:
    type: minimal
    environment: local
    enabled: true
    superset:
      version: "latest"
      port: 8088
      dev_mode: true
    database:
      type: sqlite
      path: ./data/superset.db
    cache:
      type: none
```

### Standard Local Stack
More realistic with PostgreSQL and Redis:

```yaml
stacks:
  local-standard:
    type: standard
    environment: local
    enabled: true
    superset:
      version: "5.0.0"
      port: 8088
    database:
      type: postgresql
      host: "postgres"
      port: 5432
      name: "superset"
      user: "superset"
      password: "${DB_PASSWORD:-superset123}"
    cache:
      type: redis
      host: "redis"
      port: 6379
```

### Production-like Local Stack
Test production features locally:

```yaml
stacks:
  local-prod-test:
    type: production
    environment: local
    enabled: true
    superset:
      version: "5.0.0"
      replicas: 3
    database:
      type: postgresql
      host: "postgres"
      high_availability: false  # Can't do HA locally
    cache:
      type: redis
      host: "redis"
    monitoring:
      enabled: true
```

## 🔧 Docker Compose Profiles

Use profiles to enable additional services:

| Profile | Services | Use Case | Command |
|---------|----------|----------|----------|
| `postgres` | PostgreSQL | Real database | `--profile postgres` |
| `worker` | Celery workers | Async tasks | `--profile worker` |
| `monitoring` | Prometheus, Grafana | Metrics | `--profile monitoring` |
| `cloudflare` | CF Tunnel | Secure access | `--profile cloudflare` |
| `free-tier` | All emulators | Test GCP limits | `-f docker-compose.free-tier.yaml` |

### Examples:

```bash
# Basic setup
docker-compose up

# With monitoring
docker-compose --profile monitoring up

# With all tools
docker-compose --profile monitoring --profile tools --profile email up

# Everything
docker-compose --profile monitoring --profile tools \
  --profile email --profile performance up
```

## 🌐 Service URLs

When running locally, services are available at:

### Core Services
- **Superset**: http://localhost:8088 (admin/admin)
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Monitoring Stack
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

### Free Tier Emulation Services
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Firestore Emulator**: http://localhost:8080
- **Pub/Sub Emulator**: http://localhost:8085
- **Traefik Dashboard**: http://localhost:8090

## 🔐 Environment Variables

Create a `.env` file for local development:

```bash
# Database
DB_PASSWORD=superset123
EXTERNAL_DB_PASSWORD=external123

# Redis
REDIS_PASSWORD=redis123

# Superset
SUPERSET_SECRET_KEY=$(openssl rand -base64 32)
SUPERSET_ADMIN_USERNAME=admin
SUPERSET_ADMIN_PASSWORD=admin
SUPERSET_VERSION=5.0.0

# Monitoring
GRAFANA_PASSWORD=admin
PROMETHEUS_RETENTION=7d

# Tools
PGADMIN_EMAIL=admin@localhost
PGADMIN_PASSWORD=admin
```

## 🏃 Common Workflows

### 1. Development Workflow

```bash
# Start services
make dev

# Watch logs
docker-compose logs -f superset

# Restart after code changes
docker-compose restart superset

# Clean up
docker-compose down -v
```

### 2. Testing Multiple Instances

```bash
# Configure multi-instance in system.yaml
# Start with load balancer
docker-compose --profile multi-instance up -d

# Scale Superset
docker-compose up -d --scale superset=3
```

### 3. Database Migration Testing

```bash
# Create backup
docker exec superset_postgres pg_dump -U superset superset > backup.sql

# Test migration
docker exec -it superset_app superset db upgrade

# Rollback if needed
docker exec superset_postgres psql -U superset superset < backup.sql
```

### 4. Performance Testing

```bash
# Start with performance profile
docker-compose --profile performance up -d

# Open Locust UI
open http://localhost:8089

# Configure test:
# - Number of users: 100
# - Spawn rate: 10
# - Host: http://superset:8088
```

## 📊 Resource Management

### Monitoring Resource Usage

```bash
# Real-time stats
docker stats

# Check specific container
docker stats superset_app

# For free tier emulation - check limits
./scripts/check-limits.sh
```

### Optimizing for Low Resources

1. **Disable unnecessary features**:
   ```python
   # superset_config.py
   FEATURE_FLAGS = {
       'ALERTS_REPORTS': False,      # No Celery needed
       'SCHEDULED_QUERIES': False,   # No Celery needed
       'THUMBNAILS': False,          # Save memory
   }
   ```

2. **Reduce worker processes**:
   ```bash
   SUPERSET_WORKERS=1
   GUNICORN_WORKERS=2
   GUNICORN_THREADS=2
   ```

3. **Use SQLite for free tier**:
   ```yaml
   DATABASE_URL=sqlite:////app/superset_home/superset.db
   ```

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :8088
kill -9 <PID>

# Or use different port
SUPERSET_PORT=8089 make dev
```

### Container Issues

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs superset
docker-compose logs postgres

# Enter container
docker exec -it superset_app bash
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
docker exec -it superset_postgres psql -U superset -d superset

# Check Redis connection
docker exec -it superset_redis redis-cli ping
```

### Reset Everything

```bash
# Stop and remove everything
docker-compose down -v

# Remove all data
rm -rf ./data/*

# Start fresh
make dev
```

## 📊 Monitoring Local Performance

With monitoring profile enabled:

1. **Prometheus Queries**:
   - `rate(superset_request_duration_seconds_sum[5m])` - Request rate
   - `superset_database_query_duration_seconds` - Query performance
   - `container_memory_usage_bytes{name="superset_app"}` - Memory usage

2. **Grafana Dashboards**:
   - Import dashboard from `monitoring/grafana/dashboards/`
   - Default login: admin/admin
   - Data source: Prometheus (http://prometheus:9090)

## 🔄 Switching Between Local and Cloud

The same system.yaml can contain both local and cloud configurations:

```yaml
stacks:
  # Local development
  dev:
    type: minimal
    environment: local
    enabled: true
    # ... local config
    
  # Cloud staging
  staging:
    type: standard
    environment: gcp
    enabled: false  # Enable when deploying to cloud
    # ... cloud config
```

Switch between them by:
1. Setting `enabled: true` for the desired stack
2. Using appropriate deployment command:
   - Local: `make dev` or `docker-compose up`
   - Cloud: `make deploy ENV=staging`

## 📚 Next Steps

### Recommended Path

1. **Start with minimal local** → Test Superset features
2. **Try free tier emulation** → Understand resource limits  
3. **Deploy to GCP free tier** → Production for $0/month
4. **Scale to standard/production** → As your needs grow

### Additional Resources

- [GCP Free Tier Guide](GCP_FREE_TIER_GUIDE.md) - Deploy for $0/month
- [Configuration Examples](EXAMPLES.md) - All deployment scenarios
- [Architecture Guide](ARCHITECTURE.md) - System design details
- [FAQ](FAQ.md) - Common questions answered

### Advanced Configurations

1. Review [examples/configs/local-deployments.yaml](../examples/configs/local-deployments.yaml) for more scenarios
2. Customize `docker/docker-compose.local.yaml` for your needs
3. Add custom Superset configuration in `docker/local/superset_config.py`
4. Set up pre-commit hooks for configuration validation