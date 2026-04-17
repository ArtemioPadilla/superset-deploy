"""
Superset configuration optimized for GCP Free Tier
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

# SQLite optimizations for better performance
if SQLALCHEMY_DATABASE_URI.startswith('sqlite'):
    # Enable Write-Ahead Logging for better concurrency
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'check_same_thread': False,
        },
        'pool_pre_ping': True,
        'pool_recycle': 3600,
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
    'ENABLE_TEMPLATE_PROCESSING': True,
    'ENABLE_PROXY_FIX': True,
    'GLOBAL_ASYNC_QUERIES': False,  # No async queries without Celery
    'VERSIONED_EXPORT': True,
    'DASHBOARD_NATIVE_FILTERS': True,
    'DASHBOARD_CROSS_FILTERS': True,
    'DASHBOARD_NATIVE_FILTERS_SET': True,
    'DASHBOARD_FILTERS_EXPERIMENTAL': True,
    'DISABLE_DATASET_SOURCE_EDIT': False,
    'DYNAMIC_PLUGINS': True,
    'ENABLE_JAVASCRIPT_CONTROLS': False,  # Security
    'ALERTS_REPORTS': False,  # Requires Celery
    'SCHEDULED_QUERIES': False,  # Requires Celery
    'ESTIMATE_QUERY_COST': False,  # Not needed for SQLite
    'ENABLE_SQL_VALIDATOR': False,  # Save resources
    'THUMBNAIL_CACHE_TTL': 0,  # Disable thumbnails
    'LISTVIEWS_DEFAULT_CARD_VIEW': False,  # List view uses less resources
}

# Disable unnecessary features
ENABLE_PROXY_FIX = True
ENABLE_CHUNK_ENCODING = False

# Map URL configuration (for Cloud Run)
ENABLE_PROXY_FIX = True
PREFERRED_URL_SCHEME = 'https'

# Talisman security headers
TALISMAN_ENABLED = True
TALISMAN_CONFIG = {
    'force_https': True,
    'force_https_permanent': False,
    'frame_options': 'SAMEORIGIN',
    'content_security_policy': {
        'default-src': ["'self'"],
        'img-src': ["'self'", 'data:', 'https:'],
        'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
        'style-src': ["'self'", "'unsafe-inline'"],
        'font-src': ["'self'", 'data:'],
    },
}

# Logging configuration
ENABLE_TIME_ROTATE = False
LOG_LEVEL = 'WARNING'  # Reduce logging verbosity

# SQL Lab configuration
SQL_MAX_ROW = 10000  # Limit max rows
SQL_QUERY_MUTATOR = None
SQLLAB_TIMEOUT = 300  # 5 minutes
SQLLAB_ASYNC_TIME_LIMIT_SEC = 0  # No async queries

# Dashboard configuration
DASHBOARD_TEMPLATE_ID = None
DASHBOARD_AUTO_REFRESH_MODE = 'fetch'  # More efficient
DASHBOARD_AUTO_REFRESH_TIMEOUT = 300  # 5 minutes

# Data upload configuration - minimal
UPLOAD_FOLDER = '/app/superset_home/uploads/'
IMG_UPLOAD_FOLDER = '/app/superset_home/uploads/'
CSV_UPLOAD_MAX_SIZE = 50 * 1024 * 1024  # 50MB max

# Mapbox - disabled for free tier
MAPBOX_API_KEY = ''

# CORS - configure if needed
ENABLE_CORS = False
CORS_OPTIONS = {}

# Optimize database connections
SQLALCHEMY_POOL_SIZE = 5  # Small pool for limited resources
SQLALCHEMY_POOL_TIMEOUT = 30
SQLALCHEMY_MAX_OVERFLOW = 5

# Disable expensive operations
ENABLE_SCHEDULED_EMAIL_REPORTS = False
ENABLE_ALERTS = False
THUMBNAIL_SELENIUM_USER = None  # No selenium/thumbnails

# Default cache timeout
DATA_CACHE_CONFIG = {
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,  # 24 hours
    'CACHE_KEY_PREFIX': 'superset_data_',
}

# Filter state cache
FILTER_STATE_CACHE_CONFIG = {
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,  # 24 hours
    'CACHE_KEY_PREFIX': 'superset_filter_',
}

# Explore form data cache
EXPLORE_FORM_DATA_CACHE_CONFIG = {
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,  # 24 hours
    'CACHE_KEY_PREFIX': 'superset_explore_',
}

print("Superset configured for GCP Free Tier - Optimized for minimal resource usage")