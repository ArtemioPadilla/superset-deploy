"""
Superset 5.0.0 configuration optimized for GCP Free Tier
This configuration minimizes resource usage while maintaining functionality
"""

import os
from celery.schedules import crontab

# Flask App Configuration
ROW_LIMIT = 5000
SUPERSET_WEBSERVER_THREADS = 2
SUPERSET_WEBSERVER_TIMEOUT = 300
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None

# Flask-WTF flag for CSRF
WTF_CSRF_EXEMPT_LIST = []

# Add endpoints that need to be exempt from CSRF protection
WTF_CSRF_METHODS = []

# Superset specific config
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'CHANGE_ME_IN_PRODUCTION')
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'DATABASE_URL',
    'sqlite:////app/superset_home/superset-free.db'
)

# SQLite optimizations for better performance - Fixed for v5.0.0
if SQLALCHEMY_DATABASE_URI.startswith('sqlite'):
    # SQLite doesn't use connection pooling, so we need minimal options
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'check_same_thread': False,
        }
    }
    # Execute PRAGMA statements for optimization
    from sqlalchemy import event
    from sqlalchemy.engine import Engine
    
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()

# Disable Redis cache for free tier
CACHE_CONFIG = {
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'superset_',
}

# Results backend - use database instead of Redis
RESULTS_BACKEND = None  # Will use database

# Disable Celery for free tier
class CeleryConfig:
    broker_url = None
    imports = []
    result_backend = None
    worker_prefetch_multiplier = 1
    task_acks_late = False
    beat_schedule = {}

CELERY_CONFIG = CeleryConfig

# Security optimizations
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
PERMANENT_SESSION_LIFETIME = 3600  # 1 hour sessions

# Feature flags optimized for free tier
FEATURE_FLAGS = {
    "DASHBOARD_CROSS_FILTERS": True,
    "DASHBOARD_RBAC": True,
    "EMBEDDABLE_CHARTS": True,
    "SCHEDULED_QUERIES": False,  # Requires Celery
    "ESTIMATE_QUERY_COST": False,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "ENABLE_JAVASCRIPT_CONTROLS": False,  # Security
    "THUMBNAILS": False,  # Requires Celery
    "ALERT_REPORTS": False,  # Requires Celery
    "DASHBOARD_CACHE": False,  # No Redis
    "EXPLORE_DRAG_AND_DROP": True,
    "ENABLE_EXPLORE_JSON_CSRF_PROTECTION": True,
    "ENABLE_DND_WITH_CLICK_UX": True,
}

# Map Projections
MAPBOX_API_KEY = os.environ.get('MAPBOX_API_KEY', '')

# Disable features that consume resources
ENABLE_PROXY_FIX = True
ENABLE_CHUNK_ENCODING = False

# SQL Lab settings
SQL_MAX_ROW = 10000
DISPLAY_MAX_ROW = 1000

# Optimize for low memory
SUPERSET_WORKERS = 1
SUPERSET_CELERY_WORKERS = 0

# Log configuration
LOG_FORMAT = '%(asctime)s:%(levelname)s:%(name)s:%(message)s'
LOG_LEVEL = 'INFO'

# Disable CORS (flask-cors module not available in v5.0.0)
ENABLE_CORS = False

# Free tier specific limits
FREE_TIER_MAX_DASHBOARDS = 50
FREE_TIER_MAX_CHARTS = 200
FREE_TIER_MAX_DATASETS = 100

# Add custom CSS for free tier branding (optional)
APP_NAME = "Superset Free Tier"

# Disable unused database drivers to save memory
# Keep only essential ones
ALLOWED_DATABASES = ['sqlite', 'postgresql', 'mysql']