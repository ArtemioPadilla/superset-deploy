"""
Superset configuration for standard deployments (PostgreSQL + Redis)
Compatible with Apache Superset 5.0.0+
"""

import os
from celery.schedules import crontab

# Flask App Configuration
ROW_LIMIT = 5000
SUPERSET_WEBSERVER_THREADS = 4
SUPERSET_WEBSERVER_TIMEOUT = 120
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None

# Flask-WTF flag for CSRF
WTF_CSRF_EXEMPT_LIST = []
WTF_CSRF_METHODS = []

# Superset specific config
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'CHANGE_ME_IN_PRODUCTION')

# Database configuration
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'DATABASE_URL',
    'postgresql://superset:superset@db:5432/superset'
)

# PostgreSQL specific settings
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 3600,
    'pool_size': 20,
    'max_overflow': 40,
}

# Redis configuration
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
REDIS_URL = os.environ.get('REDIS_URL', f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0')

# Cache configuration using Redis
CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'superset_',
    'CACHE_REDIS_URL': REDIS_URL,
}

# Results backend using Redis
RESULTS_BACKEND = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_KEY_PREFIX': 'superset_results_',
    'CACHE_DEFAULT_TIMEOUT': 86400,  # 24 hours
    'CACHE_REDIS_URL': REDIS_URL,
}

# Celery configuration
class CeleryConfig:
    broker_url = REDIS_URL
    imports = ('superset.sql_lab', 'superset.tasks', 'superset.tasks.thumbnails')
    result_backend = REDIS_URL
    worker_prefetch_multiplier = 10
    task_acks_late = True
    task_annotations = {
        'sql_lab.get_sql_results': {
            'rate_limit': '100/s',
        },
    }
    beat_schedule = {
        'reports.scheduler': {
            'task': 'reports.scheduler',
            'schedule': crontab(minute='*/15'),
        },
        'reports.prune_log': {
            'task': 'reports.prune_log',
            'schedule': crontab(minute=0, hour=0),
        },
    }

CELERY_CONFIG = CeleryConfig

# Security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
PERMANENT_SESSION_LIFETIME = 3600

# Feature flags
FEATURE_FLAGS = {
    "DASHBOARD_CROSS_FILTERS": True,
    "DASHBOARD_RBAC": True,
    "EMBEDDABLE_CHARTS": True,
    "SCHEDULED_QUERIES": True,
    "ESTIMATE_QUERY_COST": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "ENABLE_JAVASCRIPT_CONTROLS": False,
    "THUMBNAILS": True,
    "ALERT_REPORTS": True,
    "DASHBOARD_CACHE": True,
    "EXPLORE_DRAG_AND_DROP": True,
    "ENABLE_EXPLORE_JSON_CSRF_PROTECTION": True,
    "ENABLE_DND_WITH_CLICK_UX": True,
}

# Map Projections
MAPBOX_API_KEY = os.environ.get('MAPBOX_API_KEY', '')

# Thumbnail generation
THUMBNAIL_SELENIUM_USER = 'admin'
THUMBNAIL_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_KEY_PREFIX': 'superset_thumbnails_',
    'CACHE_DEFAULT_TIMEOUT': 86400,  # 24 hours
    'CACHE_REDIS_URL': REDIS_URL,
}

# SQL Lab settings
SQL_MAX_ROW = 100000
DISPLAY_MAX_ROW = 10000
SQLLAB_TIMEOUT = 300
SQLLAB_ASYNC_TIME_LIMIT_SEC = 3600
SQLLAB_QUERY_COST_ESTIMATE_TIMEOUT = 120

# Data upload
UPLOAD_FOLDER = '/app/superset_home/uploads/'
CSV_UPLOAD_MAX_SIZE = 50 * 1024 * 1024  # 50MB

# CORS
ENABLE_CORS = True
CORS_OPTIONS = {
    'supports_credentials': True,
    'allow_headers': ['*'],
    'resources': ['*'],
    'origins': ['http://localhost:3000', 'http://localhost:8088'],
}

# Additional cache configurations
DATA_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,
    'CACHE_KEY_PREFIX': 'superset_data_',
    'CACHE_REDIS_URL': REDIS_URL,
}

FILTER_STATE_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,
    'CACHE_KEY_PREFIX': 'superset_filter_',
    'CACHE_REDIS_URL': REDIS_URL,
}

EXPLORE_FORM_DATA_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,
    'CACHE_KEY_PREFIX': 'superset_explore_',
    'CACHE_REDIS_URL': REDIS_URL,
}

# Talisman security headers
TALISMAN_ENABLED = True
TALISMAN_CONFIG = {
    'force_https': False,  # Set to True in production
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

# Logging
LOG_FORMAT = '%(asctime)s:%(levelname)s:%(name)s:%(message)s'
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

print("Superset configured for standard deployment with PostgreSQL and Redis")