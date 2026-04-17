"""
Minimal Superset configuration for quick start
No external dependencies required
"""

import os

# Flask App Configuration
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'thisISaSECRET_1234')

# SQLite database
SQLALCHEMY_DATABASE_URI = 'sqlite:////app/superset_home/superset.db'

# Basic configuration
ROW_LIMIT = 5000
SUPERSET_WEBSERVER_THREADS = 2

# Flask-WTF flag for CSRF
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None

# Set this API key to enable Mapbox visualizations
MAPBOX_API_KEY = ''

# Disable example loading in production
ENABLE_PROXY_FIX = True

# Enable/disable features
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
}

# Cache configuration - use simple cache (no Redis)
CACHE_CONFIG = {
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
}

# No Celery/Redis needed for basic setup
class CeleryConfig:
    broker_url = None
    imports = []
    result_backend = None
    worker_prefetch_multiplier = 1
    task_acks_late = False

CELERY_CONFIG = CeleryConfig

print("Superset is starting with minimal configuration...")