# Apache Superset Deploy

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Apache Superset](https://img.shields.io/badge/Apache%20Superset-3.0.0-orange)](https://superset.apache.org/)
[![Pulumi](https://img.shields.io/badge/Pulumi-IaC-purple)](https://www.pulumi.com/)
[![GCP](https://img.shields.io/badge/GCP-Compatible-blue)](https://cloud.google.com/)
[![Cloudflare](https://img.shields.io/badge/Cloudflare-Zero%20Trust-orange)](https://www.cloudflare.com/zero-trust/)

Easy deployment of Apache Superset on local Docker or Google Cloud Platform (GCP) using Pulumi Infrastructure as Code. This solution supports multiple deployment configurations from simple local development to production-ready deployments with monitoring, backups, and high availability.

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

- 🚀 **Multiple Deployment Targets**: Local Docker, Cloud Run (serverless), GKE (Kubernetes)
- 📊 **Flexible Stack Configurations**: Minimal, Standard, and Production deployments
- 🔧 **Infrastructure as Code**: Fully automated with Pulumi
- 💰 **GCP Free Tier Compatible**: Optimized for cost-effective deployments
- 🔒 **Zero Trust Security**: Cloudflare Tunnel integration for secure access without public endpoints
- 📈 **Production Ready**: Monitoring, backups, high availability options
- 🎯 **Multi-Environment**: Deploy multiple instances with different configurations
- 🌐 **Global Access**: Cloudflare's edge network for fast, secure access worldwide

## Quick Start

### Prerequisites

- Python 3.8+
- Docker and Docker Compose
- Node.js and npm (optional, for Pulumi)
- GCP Account (for cloud deployments)
- Pulumi CLI (installed automatically)

### Local Development

```bash
# Clone the repository
git clone https://github.com/artemiopadilla/superset-deploy
cd superset-deploy

# Run setup
make setup

# Configure your deployment
cp system.yaml.example system.yaml
# Edit system.yaml with your configuration

# Start local development
make dev

# Access Superset at http://localhost:8088
# Default credentials: admin/admin

# Or with Cloudflare Tunnel (secure access)
make setup-tunnel
make dev-tunnel
# Access via your configured domain
```

### Cloud Deployment

```bash
# Configure GCP credentials
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Update system.yaml with your GCP project details
vim system.yaml

# Deploy to staging
make deploy ENV=staging

# Deploy to production
make deploy ENV=production
```

## Configuration

### Stack Types

#### 1. Minimal Stack (Local Development)
- Apache Superset with SQLite
- No external dependencies
- Perfect for local development and testing
- Runs entirely in Docker

#### 2. Standard Stack (Staging/Testing)
- Apache Superset on Cloud Run
- Cloud SQL PostgreSQL database
- Redis cache for better performance
- SSL enabled
- Suitable for staging environments

#### 3. Production Stack (High Availability)
- Apache Superset on GKE
- High-availability Cloud SQL
- Redis with replication
- Full monitoring stack (Prometheus + Grafana)
- Automated backups
- Auto-scaling enabled

### system.yaml Configuration

The `system.yaml` file defines all your deployment stacks:

```yaml
stacks:
  dev:
    type: minimal
    environment: local
    enabled: true
    
  staging:
    type: standard
    environment: gcp
    gcp:
      project_id: "your-project"
      region: "us-central1"
    database:
      tier: "db-f1-micro"  # Free tier eligible
    
  production:
    type: production
    environment: gcp
    monitoring:
      enabled: true
    backup:
      enabled: true
```

See `system.yaml.example` for full configuration options.

### Environment Variables

Key environment variables (see `.env.example` for complete list):

```bash
# Superset Configuration
SUPERSET_SECRET_KEY=             # Strong secret key (auto-generated if not set)
SUPERSET_ADMIN_USERNAME=admin    # Initial admin username
SUPERSET_ADMIN_PASSWORD=admin    # Initial admin password

# Cloudflare Tunnel
CLOUDFLARE_TUNNEL_TOKEN=         # Tunnel authentication token
CLOUDFLARE_TUNNEL_ID=            # Tunnel identifier
CLOUDFLARE_HOSTNAME=             # Your domain name

# GCP Configuration
GCP_PROJECT_ID=                  # Your GCP project ID
GCP_REGION=us-central1          # Deployment region

# Database (for cloud deployments)
DATABASE_HOST=                   # Database hostname
DATABASE_PASSWORD=               # Database password
```

## Architecture

### Local Architecture
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│  Superset   │────▶│   SQLite    │
└─────────────┘     └─────────────┘     └─────────────┘
                            │
                            ▼
                    ┌─────────────┐
                    │    Redis    │
                    └─────────────┘
```

### Cloud Architecture (Standard)
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│ Cloud Run   │────▶│  Cloud SQL  │
└─────────────┘     │  Superset   │     │ PostgreSQL  │
                    └─────────────┘     └─────────────┘
                            │
                            ▼
                    ┌─────────────┐
                    │ Memory Store│
                    │    Redis    │
                    └─────────────┘
```

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
make setup         # Initial project setup
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

### GCP Free Tier Usage

- **Cloud Run**: Up to 2 million requests/month free
- **Cloud SQL**: Shared core (f1-micro) instance
- **Firestore**: 1GB storage, 50K reads/day free
- **Cloud Storage**: 5GB storage free
- **Network**: 1GB egress to China/Australia free

### Cost Saving Tips

1. Use Cloud Run for development/staging (scales to zero)
2. Enable Cloud SQL backups only for production
3. Use preemptible nodes for GKE workers
4. Set up budget alerts in GCP
5. Use resource quotas to prevent overspending

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