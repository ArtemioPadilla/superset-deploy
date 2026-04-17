# Apache Superset Deploy

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Apache Superset](https://img.shields.io/badge/Apache%20Superset-5.0.0-orange)](https://superset.apache.org/)
[![Pulumi](https://img.shields.io/badge/Pulumi-IaC-purple)](https://www.pulumi.com/)
[![GCP](https://img.shields.io/badge/GCP-Compatible-blue)](https://cloud.google.com/)
[![Cloudflare](https://img.shields.io/badge/Cloudflare-Zero%20Trust-orange)](https://www.cloudflare.com/zero-trust/)

Easy deployment of Apache Superset on local Docker or Google Cloud Platform (GCP) using Pulumi Infrastructure as Code. This solution supports multiple deployment configurations from simple local development to production-ready deployments with monitoring, backups, and high availability.

## 🚀 Quick Start

Get Superset running in under 2 minutes!

### Interactive Quick Start (Recommended)
```bash
# Clone and run the interactive installer
git clone https://github.com/artemiopadilla/superset-deploy
cd superset-deploy
./quick-start.sh

# Choose your deployment:
# 1) Minimal - Fastest, SQLite only
# 2) Full Stack - PostgreSQL + Redis + Monitoring  
# 3) Free Tier - Emulate GCP limits locally
```

### Direct Commands (if you know what you want)
```bash
# Minimal setup (fastest)
make dev

# Full stack with monitoring
make full-stack

# GCP Free Tier deployment
make deploy ENV=gcp-free-tier
```

📖 **[Full Quick Start Guide](docs/QUICK_START.md)** | 💰 **[Free Tier Guide](docs/GCP_FREE_TIER_GUIDE.md)** | ❓ **[FAQ](docs/FAQ.md)**

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Local Development](#local-development)
  - [Cloud Deployment](#cloud-deployment)
- [Configuration](#configuration)
  - [Stack Types](#stack-types)
  - [system.yaml Configuration](#systemyaml-configuration)
- [Architecture](#architecture)
- [Commands](#commands)
- [Cost Optimization](#cost-optimization)
- [Cloudflare Zero Trust Access](#cloudflare-zero-trust-access)
- [Security](#security)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

- 🆓 **FREE Deployment Option**: Run Superset for $0/month using GCP Free Tier
- 🚀 **Multiple Deployment Targets**: Local Docker, Cloud Run (serverless), GKE (Kubernetes)
- 📊 **Flexible Stack Configurations**: Minimal, Standard, and Production deployments
- 🔧 **Infrastructure as Code**: Fully automated with Pulumi
- 💰 **Cost Optimized**: From $0 (free tier) to enterprise deployments
- 🔒 **Zero Trust Security**: Cloudflare Tunnel integration for secure access without public endpoints
- 📈 **Production Ready**: Monitoring, backups, high availability options
- 🎯 **Multi-Environment**: Deploy multiple instances with different configurations
- 🌐 **Global Access**: Cloudflare's edge network for fast, secure access worldwide
- ✅ **Type-Safe Configuration**: Pydantic validation with clear error messages
- 🔄 **Version Management**: Deploy different Superset versions per environment
- 🏢 **Multi-Account Support**: Deploy to multiple GCP projects with isolated configurations

## Prerequisites

- Python 3.8-3.11 (3.11 recommended for best compatibility)
- Docker and Docker Compose
- GCP Account (for cloud deployments - free tier available)
- Make (usually pre-installed on Linux/macOS)

**Note**: Pulumi and other dependencies are installed automatically by `make setup`.

## Configuration

The project uses a powerful Pydantic-based configuration system that provides:
- **Type-safe validation** with clear error messages
- **Multiple Superset versions** support per stack
- **Multi-GCP project** deployments
- **Environment variable** substitution
- **Inheritance** between stack configurations

### Configuration Validation

All configurations are validated using Pydantic models with detailed error messages:

```bash
# Validate your configuration
make validate

# Example validation error output:
❌ Validation failed with the following errors:
  • stacks -> production -> gcp -> project_id: Invalid GCP project ID format
  • stacks -> staging -> superset -> version: Version 2.9.0 not found on Docker Hub
```

### Stack Types

#### 1. Minimal Stack (Local Development / Free Tier)
- Apache Superset with SQLite
- No external dependencies
- Perfect for local development and testing
- **Can run for $0/month on GCP Free Tier**
- Runs on Docker locally or Cloud Run in GCP

#### 2. Standard Stack (Staging/Small Business)
- Apache Superset on Cloud Run
- Cloud SQL PostgreSQL database
- Redis cache for better performance
- SSL enabled
- ~$50/month on GCP
- Suitable for small to medium businesses

#### 3. Production Stack (Enterprise)
- Apache Superset on GKE
- High-availability Cloud SQL
- Redis with replication
- Full monitoring stack (Prometheus + Grafana)
- Automated backups
- Auto-scaling enabled
- ~$200+/month on GCP

### system.yaml Configuration

The `system.yaml` file defines all your deployment stacks:

```yaml
# Global defaults (inherited by all stacks unless overridden)
global:
  superset:
    default_version: "5.0.0"  # Default version for all stacks

stacks:
  dev:
    type: minimal
    environment: local
    enabled: true
    superset:
      version: "5.0.0"  # Override version for dev
    
  staging:
    type: standard
    environment: gcp
    enabled: true
    superset:
      version: "${SUPERSET_VERSION:-5.0.0}"  # Use env var or default
    gcp:
      project_id: "${GCP_STAGING_PROJECT}"  # From environment
      region: "us-central1"
      service_account: "superset-staging@${GCP_STAGING_PROJECT}.iam.gserviceaccount.com"
    database:
      tier: "db-f1-micro"  # Free tier eligible
    
  production:
    type: production
    environment: gcp
    enabled: true
    gcp:
      project_id: "prod-project-123"  # Different GCP project
      region: "us-east1"
      credentials_path: "/path/to/prod-key.json"  # Separate credentials
    superset:
      version: "5.0.0"  # Stable version for production
      resources:
        cpu: "4"
        memory: "8Gi"
    monitoring:
      enabled: true
    backup:
      enabled: true
```

### Multi-GCP Project Deployment

Deploy Superset to multiple GCP projects with isolated configurations:

```yaml
# Example: Deploy to different GCP projects per environment
stacks:
  # Development in personal GCP project
  dev-personal:
    type: minimal
    environment: gcp
    gcp:
      project_id: "personal-dev-project"
      credentials_path: "~/.gcp/personal-key.json"
    
  # Staging in company staging project
  staging:
    type: standard
    environment: gcp
    gcp:
      project_id: "company-staging-project"
      credentials_path: "~/.gcp/staging-key.json"
      service_account: "superset@company-staging-project.iam.gserviceaccount.com"
    
  # Production in company production project
  production:
    type: production
    environment: gcp
    gcp:
      project_id: "company-prod-project"
      credentials_path: "~/.gcp/prod-key.json"
      service_account: "superset@company-prod-project.iam.gserviceaccount.com"
```

### Superset Version Management

Specify different Superset versions for each stack:

```yaml
# Version specification examples
stacks:
  # Latest version for development
  dev:
    superset:
      version: "latest"
  
  # Specific version for testing
  test:
    superset:
      version: "5.0.0"
  
  # Version from environment variable
  staging:
    superset:
      version: "${SUPERSET_VERSION:-5.0.0}"
  
  # Stable version for production
  production:
    superset:
      version: "5.0.0"
```

See `system.yaml.example` for complete configuration options and more examples.

### Environment Variables

Key environment variables (see `.env.example` for complete list):

```bash
# Superset Configuration
SUPERSET_SECRET_KEY=             # Strong secret key (auto-generated if not set)
SUPERSET_ADMIN_USERNAME=admin    # Initial admin username
SUPERSET_ADMIN_PASSWORD=admin    # Initial admin password
SUPERSET_VERSION=5.0.0          # Override Superset version

# Cloudflare Tunnel
CLOUDFLARE_TUNNEL_TOKEN=         # Tunnel authentication token
CLOUDFLARE_TUNNEL_ID=            # Tunnel identifier
CLOUDFLARE_HOSTNAME=             # Your domain name

# GCP Configuration (supports multiple projects)
GCP_PROJECT_ID=                  # Default GCP project ID
GCP_STAGING_PROJECT=             # Staging project ID
GCP_PROD_PROJECT=                # Production project ID
GCP_REGION=us-central1          # Deployment region

# Database (for cloud deployments)
DATABASE_HOST=                   # Database hostname
DATABASE_PASSWORD=               # Database password
```

### Configuration Best Practices

1. **Version Management**:
   - Use specific versions in production for stability
   - Use "latest" or newer versions in development for testing
   - Test version upgrades in staging before production

2. **Multi-Project Setup**:
   - Use separate GCP projects for isolation
   - Configure different service accounts per environment
   - Store credentials securely (use Secret Manager in production)

3. **Environment Variables**:
   - Use `${VAR_NAME}` syntax in system.yaml
   - Supports defaults: `${VAR_NAME:-default_value}`
   - Great for CI/CD pipelines and secrets

## Architecture

### Deployment Options Overview

| Type | Infrastructure | Database | Cache | Cost/Month | Best For |
|------|---------------|----------|-------|------------|----------|
| Local Minimal | Docker | SQLite | None | $0 | Development |
| GCP Free Tier | Cloud Run | SQLite/Firestore | None | $0 | Personal/Small Team |
| GCP Standard | Cloud Run | Cloud SQL | Redis | ~$50 | Small Business |
| GCP Production | GKE | Cloud SQL HA | Redis HA | $200+ | Enterprise |

### Free Tier Architecture (NEW!)
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│ Cloud Run   │────▶│  Firestore  │
└─────────────┘     │  (scale-to-0)│     │   (1GB)     │
                    └─────────────┘     └─────────────┘
                            │
                            ▼
                    ┌─────────────┐
                    │Cloud Storage│
                    │    (5GB)    │
                    └─────────────┘
```

📖 **[Full Architecture Guide](docs/ARCHITECTURE.md)**

### Production Architecture
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│   Ingress   │────▶│     GKE     │
└─────────────┘     │  with SSL   │     │  Superset   │
                    └─────────────┘     │   Cluster   │
                                       └─────────────┘
                                              │
                    ┌─────────────────────────┴─────────────────┐
                    ▼                                           ▼
            ┌─────────────┐                             ┌─────────────┐
            │  Cloud SQL  │                             │ Memory Store│
            │     (HA)    │                             │  Redis (HA) │
            └─────────────┘                             └─────────────┘
                    │                                           │
                    ▼                                           ▼
            ┌─────────────┐                             ┌─────────────┐
            │   Backups   │                             │ Monitoring  │
            │   Storage   │                             │ Prometheus  │
            └─────────────┘                             └─────────────┘
```

## Commands

### Make Commands

```bash
make help          # Show available commands
make setup         # Initial project setup (installs dev dependencies)
make install-full  # Install all dependencies including Pulumi
make validate      # Validate configuration
make deploy        # Deploy stack (specify ENV)
make destroy       # Destroy stack (specify ENV)
make dev           # Start local development
make dev-down      # Stop local development
make dev-tunnel    # Start local development with Cloudflare tunnel
make setup-tunnel  # Setup Cloudflare tunnel
make test          # Run tests
make logs          # Show logs for environment
make status        # Show status of environment
```

### Direct Pulumi Commands

```bash
cd pulumi
pulumi stack ls              # List all stacks
pulumi stack select dev      # Select a stack
pulumi preview              # Preview changes
pulumi up                   # Apply changes
pulumi destroy              # Destroy resources
pulumi stack output         # Show stack outputs
```

## Cost Optimization

### 🆓 Run Superset for FREE!

Using GCP Free Tier, you can run Superset at **$0/month**:

| Resource | Free Tier Limit | Superset Usage |
|----------|----------------|----------------|
| Cloud Run | 2M requests/month | ✅ More than enough |
| Memory | 360,000 GB-seconds | ✅ ~50 hours/month |
| CPU | 180,000 vCPU-seconds | ✅ ~50 hours/month |
| Storage | 5GB (US regions) | ✅ Sufficient |
| Firestore | 1GB, 50K reads/day | ✅ Perfect for metadata |

**Quick Free Tier Setup:**
```bash
# Initialize free tier
./scripts/init-free-tier.sh

# Deploy to GCP
make deploy ENV=gcp-free-tier
```

### Cost Estimates by Tier

| Configuration | Monthly Cost | Users | Features |
|--------------|-------------|-------|----------|
| Free Tier | $0 | 1-50 | Basic dashboards, SQLite |
| Standard | ~$50 | 50-200 | PostgreSQL, Redis, backups |
| Production | ~$200 | 200-1000 | HA, monitoring, scaling |
| Enterprise | $500+ | 1000+ | Multi-region, SLA, support |

### Cost Saving Tips

1. **Always use scale-to-zero** for non-production
2. **Start with free tier** and scale only when needed
3. **Set budget alerts** at $1, $10, $50
4. **Use preemptible nodes** for workers (80% savings)
5. **Clean up unused resources** regularly

## Cloudflare Zero Trust Access

This deployment includes Cloudflare Tunnel integration for secure, zero-trust access to Superset without exposing public endpoints.

### Benefits

- **No Public IPs**: Services remain private, accessed only through Cloudflare's network
- **Built-in DDoS Protection**: Cloudflare's global network protects against attacks
- **Zero Trust Authentication**: Enforce identity-based access with email, SSO, or service tokens
- **Reduced Costs**: Eliminate load balancer and static IP costs
- **Global Performance**: Access through Cloudflare's edge network
- **Unified Access**: Same secure method for local and cloud deployments

### Setup Cloudflare Tunnel

1. **Install and Configure**:
```bash
# Interactive setup script
make setup-tunnel

# Or manual setup
cloudflared tunnel login
cloudflared tunnel create superset-production
```

2. **Configure Access Policies** in `system.yaml`:
```yaml
cloudflare:
  enabled: true
  tunnel_name: "superset-production"
  hostname: "superset.company.com"
  access_policies:
    - name: "employees"
      include:
        - email_domain: "company.com"
        - github_org: "company-org"
```

3. **Deploy with Tunnel**:
```bash
# Local development
make dev-tunnel

# Cloud deployment (tunnel auto-configured)
make deploy ENV=staging
```

### Access Control

Configure fine-grained access policies:

- **Email Domain**: Allow users from specific email domains
- **GitHub Organizations**: Integrate with GitHub org membership
- **Service Tokens**: For API and automation access
- **IP Ranges**: Restrict access to specific networks
- **Device Posture**: Require managed devices
- **Multi-factor Authentication**: Enforce MFA requirements

## Security

### Built-in Security Features

- **Zero Trust Access**: Cloudflare Tunnel eliminates public endpoints
- **Secrets Management**: GCP Secret Manager integration
- **SSL/TLS**: End-to-end encryption with Cloudflare and Google certificates
- **OAuth Integration**: Google and GitHub OAuth support
- **VPC Isolation**: Private networking for production
- **IAM Integration**: Workload Identity for GKE
- **Encryption**: At-rest and in-transit encryption

### Security Best Practices

1. Always use strong secret keys (generated automatically)
2. Enable OAuth for production deployments
3. Use VPC peering for database connections
4. Regular security updates via automated pipelines
5. Enable audit logging for compliance

## Monitoring

### Metrics Collection

- Superset application metrics
- Database performance metrics
- Cache hit/miss rates
- Resource utilization
- Request latency and errors

### Dashboards

Pre-configured Grafana dashboards for:
- Superset performance
- Database health
- Cache performance
- Kubernetes cluster (production)
- Cost tracking

## Troubleshooting

### Common Issues

#### Configuration Errors

**Issue**: Validation errors when running `make validate`
```bash
# Example: Invalid GCP project ID
❌ stacks -> production -> gcp -> project_id: Invalid GCP project ID format

# Solution: GCP project IDs must be lowercase with hyphens
# Valid: my-project-123
# Invalid: MyProject123, my_project_123
```

**Issue**: Superset version not found
```bash
❌ stacks -> staging -> superset -> version: Version 2.9.0 not found on Docker Hub

# Solution: Check available versions
curl -s https://hub.docker.com/v2/repositories/apache/superset/tags | jq -r '.results[].name' | sort -V
```

**Issue**: Environment variable not found
```bash
❌ Error expanding environment variables: Environment variable GCP_STAGING_PROJECT not found

# Solution: Set the variable or provide a default
export GCP_STAGING_PROJECT=my-staging-project
# Or in system.yaml: ${GCP_STAGING_PROJECT:-default-project}
```

#### Local Development

**Issue**: Port 8088 already in use
```bash
# Find and kill the process
lsof -i :8088
kill -9 <PID>
```

**Issue**: Docker daemon not running
```bash
# Start Docker
sudo systemctl start docker  # Linux
open -a Docker              # macOS
```

#### Cloud Deployment

**Issue**: GCP authentication error
```bash
# Re-authenticate
gcloud auth login
gcloud auth application-default login
```

**Issue**: Pulumi state issues
```bash
# Export and import state
pulumi stack export > backup.json
pulumi stack import < backup.json
```

### Debug Commands

```bash
# Check Docker logs
docker-compose -f docker/docker-compose.yaml logs -f superset

# Check Cloudflare tunnel logs
docker-compose -f docker/docker-compose.yaml logs -f cloudflared

# Check Cloud Run logs
gcloud run services logs read superset-staging --project=YOUR_PROJECT

# Check GKE pod logs
kubectl logs -n superset -l app=superset

# Test database connection
docker exec -it superset_db psql -U superset -d superset

# Test Cloudflare tunnel
cloudflared tunnel info <tunnel-name>
cloudflared tunnel list

# Check tunnel metrics
curl http://localhost:2000/metrics  # When tunnel is running
```

### Cloudflare Tunnel Issues

**Issue**: Tunnel won't connect
```bash
# Check tunnel status
cloudflared tunnel list
cloudflared tunnel info <tunnel-name>

# Verify credentials
ls -la docker/cloudflared/credentials.json

# Test tunnel manually
cloudflared tunnel run <tunnel-name>
```

**Issue**: Access denied errors
- Check Cloudflare Zero Trust dashboard
- Verify access policies match your email/organization
- Check if service tokens are configured correctly
- Review audit logs in Cloudflare dashboard

**Issue**: DNS not resolving
```bash
# Check DNS records
dig +short your-domain.com
nslookup your-domain.com

# Verify Cloudflare DNS
cloudflared tunnel route dns <tunnel-name> <hostname>
```

## 📚 Documentation

### Getting Started
- 🚀 **[Quick Start Guide](docs/QUICK_START.md)** - Get running in 5 minutes
- 💰 **[GCP Free Tier Guide](docs/GCP_FREE_TIER_GUIDE.md)** - Deploy for $0/month
- ☁️ **[GCP Deployment Guide](docs/GCP_DEPLOYMENT_GUIDE.md)** - Full cloud deployment
- 🏗️ **[Architecture Overview](docs/ARCHITECTURE.md)** - System design and patterns

### Configuration & Examples
- 📋 **[Configuration Guide](docs/PULUMI_CONFIG_GUIDE.md)** - Pulumi configuration details
- 📚 **[Examples](docs/EXAMPLES.md)** - Sample configurations for all use cases
- 🏠 **[Local Development](docs/LOCAL_DEPLOYMENT_GUIDE.md)** - Local setup guide

### Help & Support
- ❓ **[FAQ](docs/FAQ.md)** - Frequently asked questions
- 🐍 **[Python Compatibility](docs/PYTHON_COMPATIBILITY.md)** - Python version guide
- 🔧 **[Troubleshooting](#troubleshooting)** - Common issues and solutions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/artemiopadilla/superset-deploy/issues)
- Documentation: [Full documentation](https://github.com/artemiopadilla/superset-deploy/wiki)
- Apache Superset: [Official documentation](https://superset.apache.org/)

## Roadmap

- [ ] Helm chart support for Kubernetes deployments
- [ ] AWS deployment support (ECS, EKS)
- [ ] Azure deployment support (Container Instances, AKS)
- [ ] Automated backup and restore procedures
- [ ] CI/CD pipeline templates (GitHub Actions, GitLab CI)
- [ ] Terragrunt support as alternative to Pulumi
- [ ] Multi-region deployment support
- [ ] Advanced monitoring with custom dashboards
- [ ] Superset plugin management system
- [ ] Automated security scanning

## Acknowledgments

- Apache Superset team for the amazing BI tool
- Pulumi for infrastructure as code platform
- Google Cloud Platform for cloud services
- Cloudflare for zero-trust security solutions

## Related Projects

- [Apache Superset](https://github.com/apache/superset) - The main Superset project
- [Superset Docker](https://hub.docker.com/r/apache/superset) - Official Docker images
- [Pulumi Examples](https://github.com/pulumi/examples) - Infrastructure as Code examples
- [Cloudflare Tunnel Examples](https://github.com/cloudflare/cloudflared) - Cloudflare tunnel documentation