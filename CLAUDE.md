# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains a modular Apache Superset deployment solution using Pulumi Infrastructure as Code (IaC). It supports both local Docker development and Google Cloud Platform (GCP) deployments, optimized for free tier usage and scalable to production environments.

## Key Commands

### Setup and Development
```bash
# Initial setup
make setup

# Deploy a stack (ENV can be: dev, staging, production)
make deploy ENV=dev

# Destroy a stack
make destroy ENV=dev

# Validate configuration
make validate

# Run tests
make test

# Local development
make dev

# Local development with Cloudflare Tunnel
make setup-tunnel
make dev-tunnel
```

### Pulumi Commands
```bash
# Select stack
pulumi stack select <stack-name>

# Preview changes
pulumi preview

# Deploy changes
pulumi up

# View stack outputs
pulumi stack output
```

### Docker Commands
```bash
# Start local Superset
docker-compose -f docker/docker-compose.yaml up

# Build custom Superset image
docker build -t superset-custom:latest docker/production/

# Run with specific profile
docker-compose --profile monitoring up
```

## Architecture

### Stack Configuration System
The deployment system is driven by `system.yaml` which defines multiple stacks with different complexity levels:
- **minimal**: Basic Superset + SQLite for local development
- **standard**: Superset + PostgreSQL + Redis for staging
- **production**: Full stack with monitoring, backups, and high availability

### Pulumi Component Structure
```
pulumi/
├── components/         # Reusable infrastructure components
│   ├── superset/      # Superset deployment logic
│   ├── database/      # Database provisioning (PostgreSQL, Cloud SQL)
│   ├── cache/         # Caching layer (Redis, Memcached)
│   ├── cloudflare/    # Cloudflare Tunnel for zero-trust access
│   ├── monitoring/    # Observability stack (Prometheus, Grafana)
│   └── security/      # Authentication, SSL, secrets management
└── stacks/            # Stack definitions combining components
```

### GCP Architecture Patterns
- **Cloud Run**: For serverless Superset deployment (scales to zero)
- **GKE**: For Kubernetes-based production deployments
- **Cloud SQL**: Managed PostgreSQL with automated backups
- **Memory Store**: Managed Redis for caching
- **Cloud Storage**: For static assets and backups
- **Secret Manager**: For secure credential storage

## Development Guidelines

### Adding New Components
1. Create component class in `pulumi/components/<component_name>/`
2. Define configuration schema in `pulumi/config/schemas.py`
3. Update stack definitions to include new component
4. Add corresponding Docker configuration for local testing
5. Update system.yaml.example with new options

### Testing Approach
- Unit tests for Pulumi components using `pulumi.runtime.test`
- Integration tests using Docker Compose
- Configuration validation tests
- GCP deployment tests in isolated project

### Configuration Management
- Environment variables are loaded from `.env` files
- Pulumi config for infrastructure settings
- `system.yaml` for high-level stack definitions
- Secrets stored in GCP Secret Manager or local `.env`

## Important Patterns

### Resource Naming Convention
```python
# Format: {project}-{env}-{component}-{resource}
# Example: superset-prod-db-instance
```

### Cloudflare Tunnel Integration
When implementing Cloudflare Tunnel:
1. Services should use internal-only ingress (no public IPs)
2. Cloudflare connector runs as a separate service
3. Access policies are defined in `system.yaml`
4. Tunnel credentials stored in Secret Manager
5. Use profiles in docker-compose for optional tunnel

### Environment Detection
```python
# Check if running locally vs GCP
if os.getenv("ENVIRONMENT") == "local":
    # Use Docker resources
else:
    # Use GCP resources
```

### Free Tier Optimization
- Use Cloud Run with minimum instances = 0
- Configure Cloud SQL with shared core (f1-micro)
- Implement caching to reduce database load
- Use Firestore for session storage (free tier generous)

## Common Tasks

### Update Superset Version
1. Update version in `system.yaml`
2. Update Docker image tags in `docker/`
3. Test locally with `make dev`
4. Deploy to staging with `make deploy ENV=staging`

### Add New Environment
1. Define environment in `system.yaml`
2. Create Pulumi stack: `pulumi stack init <env>`
3. Configure stack: `pulumi config set gcp:project <project-id>`
4. Deploy: `make deploy ENV=<env>`

### Enable Monitoring
1. Set `monitoring: true` in `system.yaml`
2. Configure Prometheus endpoints in `pulumi/components/monitoring/`
3. Deploy Grafana dashboards from `monitoring/dashboards/`

## Troubleshooting

### Local Development Issues
- Check Docker daemon is running
- Verify port 8088 is not in use
- Review logs: `docker-compose logs superset`

### Cloudflare Tunnel Issues
- Verify tunnel credentials: `cloudflared tunnel list`
- Check tunnel status: `docker-compose logs cloudflared`
- Validate DNS records: `dig +short your-domain.com`
- Test tunnel connection: `cloudflared tunnel info tunnel-name`
- Review access policies in Cloudflare Zero Trust dashboard

### GCP Deployment Issues
- Verify GCP credentials: `gcloud auth list`
- Check project permissions
- Review Cloud Run logs: `gcloud run services logs read`
- Validate Pulumi state: `pulumi stack export`

### Database Connection Issues
- Check connection string format
- Verify network connectivity (VPC, firewall rules)
- Test with `psql` or `mysql` client
- Review Cloud SQL proxy logs if using