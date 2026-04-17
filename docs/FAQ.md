# ❓ Frequently Asked Questions

Quick answers to common questions about Apache Superset Deploy.

## 📋 Table of Contents

- [General Questions](#general-questions)
- [Free Tier Questions](#free-tier-questions)
- [Deployment Questions](#deployment-questions)
- [Cost Questions](#cost-questions)
- [Technical Questions](#technical-questions)
- [Troubleshooting Questions](#troubleshooting-questions)
- [Security Questions](#security-questions)
- [Migration Questions](#migration-questions)

## 🌟 General Questions

### What is Apache Superset Deploy?
A complete Infrastructure as Code solution for deploying Apache Superset on Google Cloud Platform or locally, with built-in support for GCP Free Tier, multiple environments, and production-ready configurations.

### Who should use this?
- **Individuals**: Personal dashboards and learning
- **Startups**: Cost-effective BI solution
- **Enterprises**: Scalable, secure analytics platform
- **Developers**: Easy local development setup

### What are the main benefits?
- 🆓 Free tier deployment option ($0/month)
- 🚀 5-minute quick start
- 🔒 Built-in security with Cloudflare
- 📊 Multiple deployment options
- 💰 Cost-optimized configurations
- 🔄 Easy environment management

### Do I need to know Pulumi/Terraform?
No! The Makefile abstracts all complexity. Basic commands:
```bash
./quick-start.sh  # Interactive menu - choose your setup!
make dev          # Direct minimal setup
make full-stack   # Direct full stack setup
make deploy       # Cloud deployment (requires setup)
```

### Do I need to configure anything to start?
No! Just run `./quick-start.sh` and choose your deployment type:
- **Option 1**: Minimal - SQLite only, no configuration needed
- **Option 2**: Full Stack - PostgreSQL + Redis + monitoring (production-like)
- **Option 3**: Free Tier - SQLite + cloud emulators (matches GCP free tier limits)

The script handles everything automatically!

### What's the difference between Full Stack and Free Tier?
- **Full Stack**: Includes PostgreSQL and Redis for a production-like environment
- **Free Tier**: Uses SQLite (no PostgreSQL/Redis) because GCP free tier doesn't include Cloud SQL or Memorystore
- **Free Tier** adds: Resource limits (1GB RAM), cloud emulators (Firestore, Cloud Storage)
- Choose **Full Stack** to learn production setup, **Free Tier** to test GCP deployment
- 📖 [Full clarification on what's actually free](FREE_TIER_CLARIFICATION.md)

## 💰 Free Tier Questions

### Can I really run Superset for free?
Yes! Using GCP Free Tier resources:
- Cloud Run (2M requests/month)
- Cloud Storage (5GB)
- Firestore (1GB database)
- Total: $0/month if within limits

### What are the free tier limitations?
- **Runtime**: ~50 hours/month with 2GB RAM
- **Storage**: 5GB total
- **Database**: 1GB Firestore, 50K reads/day
- **Users**: Good for 10-50 users
- **No**: Redis, Cloud SQL, Load Balancer

### How do I stay within free tier?
1. **Enable scale-to-zero**: `min_replicas: 0`
2. **Use SQLite/Firestore**: No Cloud SQL
3. **Limit resources**: 1 CPU, 2GB RAM max
4. **Monitor usage**: Set budget alerts at $1

### What happens if I exceed free tier?
- Gradual charges begin (not sudden bills)
- Typically $0.10-1.00/day over limits
- Set budget alerts to monitor
- Easy to scale back down

## 🚀 Deployment Questions

### How long does deployment take?
- **Local minimal**: 3 minutes
- **Local free tier**: 5 minutes
- **GCP free tier**: 10 minutes (first time)
- **GCP standard**: 15 minutes
- **GCP production**: 30 minutes

### What GCP regions support free tier?
Only US regions qualify:
- `us-central1` (Iowa)
- `us-east1` (South Carolina)
- `us-west1` (Oregon)

### Can I deploy to multiple environments?
Yes! Configure in `system.yaml`:
```yaml
stacks:
  dev:
    enabled: true
  staging:
    enabled: true
  production:
    enabled: true
```

### How do I switch between environments?
```bash
make deploy ENV=dev
make deploy ENV=staging
make deploy ENV=production
```

### Can I use my existing GCP project?
Yes! Just set your project ID:
```yaml
gcp:
  project_id: "your-existing-project"
```

## 💵 Cost Questions

### How much does each tier cost?

| Tier | Monthly Cost | What's Included |
|------|--------------|-----------------|
| Free | $0 | Cloud Run, Storage, Firestore |
| Standard | ~$50 | + Cloud SQL, Redis |
| Production | ~$200 | + HA, Monitoring, Backups |
| Enterprise | $500+ | + Multi-region, SLA |

### How can I estimate my costs?
```bash
# Use the built-in calculator
./scripts/estimate-costs.sh

# Or check current usage
./scripts/check-costs.sh
```

### How do I optimize costs?
1. **Use scale-to-zero**: Saves 70-90%
2. **Right-size resources**: Start small
3. **Use preemptible nodes**: Save 80% on compute
4. **Enable only needed features**: Monitoring, backups
5. **Clean up unused resources**: Storage, snapshots

### Can I set spending limits?
```bash
# Set budget alert
gcloud billing budgets create \
  --display-name="Superset Limit" \
  --budget-amount=50USD
```

## 🔧 Technical Questions

### What Python version should I use?
Python 3.8-3.11, with 3.11 recommended:
```bash
python --version  # Should show 3.8-3.11
```

### Can I use existing database?
Yes! Configure external database:
```yaml
database:
  type: postgresql
  host: "your-database-host"
  port: 5432
  name: "superset"
  user: "superset_user"
  password: "${DB_PASSWORD}"
```

### How do I add custom Python packages?
Create `requirements-local.txt`:
```txt
pandas==1.5.0
prophet==1.1
custom-package==1.0
```

Then rebuild:
```bash
docker-compose build --no-cache
```

### Can I customize Superset config?
Yes! Edit `docker/local/superset_config.py`:
```python
# Custom configuration
FEATURE_FLAGS = {
    'ENABLE_TEMPLATE_PROCESSING': True,
}
```

### How do I enable OAuth?
```python
# In superset_config.py
from flask_appbuilder.security.manager import AUTH_OAUTH

AUTH_TYPE = AUTH_OAUTH
OAUTH_PROVIDERS = [{
    'name': 'google',
    'token_key': 'access_token',
    'client_id': 'YOUR_CLIENT_ID',
    'client_secret': 'YOUR_CLIENT_SECRET',
}]
```

## 🔍 Troubleshooting Questions

### Port 8088 is already in use
```bash
# Find process
lsof -i :8088

# Kill it
kill -9 <PID>

# Or use different port
SUPERSET_PORT=8089 ./quick-start.sh
```

### I see warnings about missing environment variables
These warnings are harmless! Variables like `CLOUDFLARE_TUNNEL_TOKEN` are only needed for optional features. The quick start uses SQLite and doesn't need:
- PostgreSQL configuration
- Redis configuration  
- Cloudflare tunnel
- GCP credentials

### Docker/Podman not found
```bash
# macOS
brew install --cask docker

# Linux
sudo apt-get install docker.io

# Start Docker
open -a Docker  # macOS
sudo systemctl start docker  # Linux
```

### Apple Silicon (M1/M2/M3) Issues
Superset doesn't have native ARM64 images yet. The setup handles this automatically by:
- Using `platform: linux/amd64` in docker-compose
- Running in emulation mode (Rosetta 2)
- May take 2-3 minutes to start initially

**If startup is slow:**
```bash
# Check progress
docker logs -f superset_app

# Be patient - first run downloads and initializes
```

### GCP authentication fails
```bash
# Re-authenticate
gcloud auth login
gcloud auth application-default login

# Check current account
gcloud config list
```

### Superset won't start / "No such file or directory" error
This usually means the Docker image had issues. Fix:
```bash
# Clean up and retry
docker-compose -f docker/docker-compose.minimal.yaml down -v
docker system prune -a  # Warning: removes all unused images
./quick-start.sh
```

### Database connection errors
1. Check connection string format
2. Verify network connectivity
3. Check credentials
4. Test with psql/mysql client:
```bash
psql -h hostname -U username -d database
```

### Deployment fails with "API not enabled"
```bash
# Enable required API
gcloud services enable SERVICE_NAME.googleapis.com

# Enable all at once
gcloud services enable run.googleapis.com \
  cloudbuild.googleapis.com storage.googleapis.com
```

## 🔒 Security Questions

### Is this production-ready?
Yes, with proper configuration:
- ✅ HTTPS/SSL enabled
- ✅ Cloudflare WAF available
- ✅ Secret Manager integration
- ✅ VPC isolation (standard+)
- ✅ IAM/RBAC support

### How do I secure my deployment?
1. **Use strong secrets**: Auto-generated
2. **Enable HTTPS**: Always in production
3. **Use Cloudflare**: Zero-trust access
4. **Enable OAuth**: For user authentication
5. **VPC isolation**: For databases

### Where are secrets stored?
- **Local**: `.env` files (gitignored)
- **GCP**: Secret Manager (encrypted)
- **Never**: In code or configs

### Can I use my own SSL certificates?
Yes, three options:
1. **Managed**: GCP auto-provisions (recommended)
2. **Custom**: Upload to load balancer
3. **Cloudflare**: Use Cloudflare SSL

### Is Cloudflare Tunnel really free?
Yes! Cloudflare Tunnel is completely free for production use:
- **Free tier**: Up to 1000 tunnels
- **No bandwidth charges**: Unlike the old Argo Tunnel
- **Production ready**: Not just for testing
- **Saves money**: Replaces $18/month Load Balancer
- **Setup**: Run `./scripts/setup-tunnel.sh`

## 🔄 Migration Questions

### Can I migrate from existing Superset?
Yes! Steps:
1. Export dashboards/charts
2. Backup database
3. Deploy new instance
4. Import data
5. Update DNS

### How do I upgrade Superset version?
```yaml
# In system.yaml
superset:
  version: "5.0.0"  # New version
```
Then: `make deploy ENV=your-env`

### Can I migrate between cloud providers?
While this solution is GCP-focused, the patterns work for:
- AWS (ECS/EKS instead of Cloud Run/GKE)
- Azure (Container Instances/AKS)
- Requires adapting Pulumi code

### How do I backup before migration?
```bash
# Local backup
docker exec superset_db pg_dump -U superset > backup.sql

# GCP backup
gcloud sql backups create --instance=superset-db
```

### Can I rollback deployments?
Yes! Pulumi maintains state:
```bash
# View history
pulumi stack history

# Rollback
pulumi stack export > backup.json
pulumi destroy
pulumi stack import < previous-state.json
pulumi up
```

## 💡 Best Practices Questions

### What's the recommended deployment path?
1. Start with local minimal
2. Test with free tier
3. Move to standard when needed
4. Scale to production as you grow

### How often should I update?
- **Superset**: Monthly security updates
- **Dependencies**: Quarterly
- **Infrastructure**: As needed
- **Backups**: Daily (automated)

### What monitoring should I enable?
**Minimum**:
- Uptime checks
- Error rate alerts
- Budget alerts

**Recommended**:
- CPU/Memory metrics
- Query performance
- User activity
- Storage usage

### How do I handle multiple teams?
Options:
1. **Row-level security**: In Superset
2. **Separate databases**: Per team
3. **Multiple deployments**: Full isolation
4. **Projects**: GCP project per team

## 🆘 Getting Help

### Where can I get support?
1. **Documentation**: Check guides in `/docs`
2. **Examples**: Review `/examples/configs`
3. **Issues**: [GitHub Issues](https://github.com/artemiopadilla/superset-deploy/issues)
4. **Discussions**: [GitHub Discussions](https://github.com/artemiopadilla/superset-deploy/discussions)

### How do I report bugs?
Create issue with:
- Error message
- `system.yaml` (sanitized)
- Deployment command used
- `make validate` output

### Can I contribute?
Yes! We welcome:
- Bug fixes
- Documentation improvements
- New deployment examples
- Feature requests

### Why is version 3.0.0 not working?
Apache Superset 3.0.0 was not released to Docker Hub. Use:
- **5.0.0** (latest stable - default)
- **4.0.2** (previous stable version)
- **3.1.0** (older stable version)

### Is commercial support available?
Currently community-supported. For enterprise:
- Consider Preset (Superset creators)
- Hire consultants familiar with this stack
- Engage cloud provider support

---

**Still have questions?**
- 📖 Review full [Documentation](../README.md)
- 💬 Ask in [Discussions](https://github.com/artemiopadilla/superset-deploy/discussions)
- 🐛 Report [Issues](https://github.com/artemiopadilla/superset-deploy/issues)