# Superset Configuration Files

This directory contains Apache Superset configuration files for different deployment scenarios.

## Configuration Files

### 1. `superset_config_minimal.py`
- **Use case**: Quick local development, testing
- **Database**: SQLite (built-in)
- **Cache**: SimpleCache (in-memory)
- **Features**: Basic features only
- **Resource usage**: Minimal

### 2. `superset_config_standard.py`
- **Use case**: Production-like environment with external dependencies
- **Database**: PostgreSQL
- **Cache**: Redis
- **Features**: Full feature set including Celery, alerts, thumbnails
- **Resource usage**: Standard

### 3. `superset_config_v5.py`
- **Use case**: Free tier deployments optimized for Apache Superset 5.0.0
- **Database**: SQLite with performance optimizations
- **Cache**: SimpleCache
- **Features**: Limited features to reduce resource usage
- **Resource usage**: Optimized for 1GB RAM

## Usage

The appropriate configuration file is selected based on your docker-compose setup:

```bash
# Minimal setup (uses superset_config_minimal.py)
docker-compose -f docker/docker-compose.minimal.yaml up

# Standard setup (uses superset_config_standard.py)
docker-compose -f docker/docker-compose.yaml up

# Free tier setup (uses superset_config_v5.py)
docker-compose -f docker/docker-compose.yaml -f docker/docker-compose.free-tier.yaml up
```

## Key Differences

| Feature | Minimal | Standard | Free Tier (v5) |
|---------|---------|----------|----------------|
| Database | SQLite | PostgreSQL | SQLite |
| Cache | SimpleCache | Redis | SimpleCache |
| Celery | ❌ | ✅ | ❌ |
| Alerts | ❌ | ✅ | ❌ |
| Thumbnails | ❌ | ✅ | ❌ |
| Async Queries | ❌ | ✅ | ❌ |
| Memory Usage | ~500MB | ~2GB | ~1GB |

## Environment Variables

All configurations support these environment variables:

- `SUPERSET_SECRET_KEY`: Flask secret key (required for production)
- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection string (standard config only)
- `LOG_LEVEL`: Logging level (default: INFO)
- `MAPBOX_API_KEY`: For map visualizations

## Security Notes

1. Always use strong secret keys in production
2. Enable HTTPS in production (set `TALISMAN_CONFIG.force_https = True`)
3. Configure proper CORS origins for your domain
4. Disable JavaScript controls for security

## Deprecated Files

The following files are deprecated and will be removed in future versions:
- `superset_config.py` - Use `superset_config_standard.py` instead
- `superset_config_free_tier.py` - Use `superset_config_v5.py` instead
- `superset_config_full_free_tier.py` - Overly complex, use `superset_config_v5.py` instead