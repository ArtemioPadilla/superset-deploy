# Superset Deployment Configuration Examples

This directory contains example configurations for various deployment scenarios. Each example is designed to demonstrate best practices for specific use cases.

## Available Examples

### 1. Multi-Environment (`multi-environment.yaml`)
Shows how to configure development, staging, and production environments in a single configuration file.

**Use this when:**
- You need consistent deployments across multiple environments
- You want to manage all environments from a single configuration
- You need different resource allocations per environment

**Key features:**
- Environment-specific resource allocation
- Progressive feature enablement (dev → staging → production)
- Environment variable usage for secrets
- Cloudflare tunnel integration for secure access

### 2. Multi-Project (`multi-project.yaml`)
Demonstrates deploying Superset to multiple GCP projects with different credentials and configurations.

**Use this when:**
- You have separate GCP projects for different teams/departments
- You need billing isolation between environments
- You require different service accounts per deployment
- You want to implement a disaster recovery setup

**Key features:**
- Multiple GCP project configurations
- Different credentials per project
- Stack inheritance for DR scenarios
- Project-specific service accounts

### 3. Free Tier (`free-tier.yaml`)
Optimized configuration to minimize or eliminate GCP costs.

**Use this when:**
- You're experimenting with Superset
- You have a personal project with minimal usage
- You need to stay within GCP's free tier limits
- Cost optimization is the primary concern

**Key features:**
- Cloud Run scales to zero configuration
- SQLite option for true free tier
- Cloudflare tunnel to avoid load balancer costs
- Minimal resource allocations
- Cost optimization tips and warnings

### 4. High Availability (`high-availability.yaml`)
Production-grade configuration with maximum reliability and uptime.

**Use this when:**
- Running mission-critical analytics workloads
- You need 99.9%+ uptime
- You have large numbers of concurrent users
- Data loss is unacceptable

**Key features:**
- Multi-replica deployments with autoscaling
- High availability database and cache
- Cross-region backup replication
- Comprehensive monitoring and alerting
- Network segmentation and security hardening
- Performance optimizations

## Usage

1. Copy the example that best matches your use case:
   ```bash
   cp examples/configs/multi-environment.yaml system.yaml
   ```

2. Update the configuration with your specific values:
   - Replace placeholder project IDs
   - Set appropriate environment variables
   - Adjust resource allocations
   - Configure your domains

3. Set required environment variables:
   ```bash
   export GCP_PROJECT=your-project-id
   export DB_PASSWORD=$(openssl rand -base64 32)
   export REDIS_PASSWORD=$(openssl rand -base64 32)
   ```

4. Validate your configuration:
   ```bash
   make validate
   ```

5. Deploy:
   ```bash
   make deploy ENV=your-environment
   ```

## Configuration Tips

### Environment Variables
Most examples use environment variables for sensitive data. Set these before deployment:
- `GCP_PROJECT_*` - GCP project IDs
- `DB_PASSWORD_*` - Database passwords
- `REDIS_PASSWORD_*` - Redis passwords
- `CF_TUNNEL_*` - Cloudflare tunnel credentials
- `*_WEBHOOK_URL` - Monitoring webhooks

### Resource Allocation
- **Development**: 0.5-1 CPU, 1-2Gi memory
- **Staging**: 1-2 CPU, 2-4Gi memory
- **Production**: 2-4 CPU, 4-8Gi memory (per replica)

### Cost Optimization
- Use Cloud Run for automatic scaling to zero
- Choose `db-f1-micro` for development databases
- Disable monitoring and backups for development
- Use Cloudflare tunnels instead of load balancers
- Set appropriate retention periods

### Security Best Practices
- Always use environment variables for secrets
- Enable VPC for production deployments
- Use Secret Manager for production secrets
- Configure OAuth for user authentication
- Enable MFA for production access
- Implement network segmentation

## Extending Examples

These examples can be extended by:
1. Using stack inheritance (`extends` field)
2. Overriding specific values
3. Combining features from multiple examples
4. Adding custom validation rules

## Need Help?

- Check the [main README](../../README.md) for detailed documentation
- Run `make validate` to check for configuration errors
- Review validation warnings for optimization suggestions