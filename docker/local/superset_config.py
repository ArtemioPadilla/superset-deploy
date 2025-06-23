import os
from celery.schedules import crontab

# Superset specific config
ROW_LIMIT = 5000
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'your-secret-key-here')

# Flask App Builder configuration
# Your App secret key will be used for securely signing the session cookie
# and encrypting sensitive information on the database
# Make sure you are changing this key for your deployment with a strong key.
# You can generate a strong key using `openssl rand -base64 42`
# Alternatively you can set it with `SUPERSET_SECRET_KEY` environment variable.

# The SQLAlchemy connection string to your database backend
# This connection defines the path to the database that stores your
# superset metadata (slices, connections, tables, dashboards, ...).
# Note that the connection information to connect to the datasources
# you want to explore are managed directly in the web UI
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:////app/superset_home/superset.db')

# Flask-WTF flag for CSRF
WTF_CSRF_ENABLED = True
# Add endpoints that need to be exempt from CSRF protection
WTF_CSRF_EXEMPT_LIST = []
# A CSRF token that expires in 1 year
WTF_CSRF_TIME_LIMIT = 60 * 60 * 24 * 365

# Set this API key to enable Mapbox visualizations
MAPBOX_API_KEY = os.environ.get('MAPBOX_API_KEY', '')

# Redis configuration for caching
REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')

CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'superset_',
    'CACHE_REDIS_URL': REDIS_URL,
}

# Celery configuration
class CeleryConfig:
    broker_url = REDIS_URL
    imports = (
        'superset.sql_lab',
        'superset.tasks',
    )
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
            'schedule': crontab(minute='*', hour='*'),
        },
        'reports.prune_log': {
            'task': 'reports.prune_log',
            'schedule': crontab(minute=10, hour=0),
        },
    }

CELERY_CONFIG = CeleryConfig

# Feature flags
FEATURE_FLAGS = {
    'ALERT_REPORTS': True,
    'DASHBOARD_NATIVE_FILTERS': True,
    'DASHBOARD_NATIVE_FILTERS_SET': True,
    'DASHBOARD_CROSS_FILTERS': True,
    'DASHBOARD_RBAC': True,
    'EMBEDDABLE_CHARTS': True,
    'SCHEDULED_QUERIES': True,
    'ESTIMATE_QUERY_COST': True,
    'ENABLE_TEMPLATE_PROCESSING': True,
    'ENABLE_TEMPLATE_REMOVE_FILTERS': True,
    'GLOBAL_ASYNC_QUERIES': True,
    'THUMBNAILS': True,
    'LISTVIEWS_DEFAULT_CARD_VIEW': True,
    'ENABLE_REACT_CRUD_VIEWS': True,
    'ENABLE_JAVASCRIPT_CONTROLS': False,  # Security: disable by default
}

# Thumbnail configuration
THUMBNAIL_REDIS_URL = REDIS_URL
THUMBNAIL_CACHE_DEFAULT_TIMEOUT = 24 * 60 * 60  # 24 hours
THUMBNAIL_SELENIUM_USER = 'admin'

# Email configuration
SMTP_HOST = os.environ.get('SMTP_HOST', 'localhost')
SMTP_STARTTLS = os.environ.get('SMTP_STARTTLS', 'true').lower() == 'true'
SMTP_SSL = os.environ.get('SMTP_SSL', 'false').lower() == 'true'
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_MAIL_FROM = os.environ.get('SMTP_MAIL_FROM', 'superset@example.com')

# WebDriver configuration for screenshots
WEBDRIVER_TYPE = "chrome"
WEBDRIVER_OPTION_ARGS = [
    "--headless",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
]

# Async queries
GLOBAL_ASYNC_QUERIES_REDIS_CONFIG = {
    "host": REDIS_URL.split("//")[1].split(":")[0],
    "port": int(REDIS_URL.split(":")[-1].split("/")[0]),
    "db": int(REDIS_URL.split("/")[-1]),
}

# SQL Lab configuration
SQL_MAX_ROW = 100000
DISPLAY_MAX_ROW = 10000
SQLLAB_CTAS_NO_LIMIT = True

# Security
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# OAuth configuration (optional)
if os.environ.get('OAUTH_ENABLED', 'false').lower() == 'true':
    from flask_appbuilder.security.manager import AUTH_OAUTH
    AUTH_TYPE = AUTH_OAUTH
    OAUTH_PROVIDERS = []
    
    if os.environ.get('GOOGLE_CLIENT_ID'):
        OAUTH_PROVIDERS.append({
            'name': 'google',
            'icon': 'fa-google',
            'token_key': 'access_token',
            'remote_app': {
                'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
                'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
                'api_base_url': 'https://www.googleapis.com/oauth2/v2/',
                'client_kwargs': {'scope': 'email profile'},
                'request_token_url': None,
                'access_token_url': 'https://accounts.google.com/o/oauth2/token',
                'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
            }
        })

# Load examples
LOAD_EXAMPLES = os.environ.get('SUPERSET_LOAD_EXAMPLES', 'yes').lower() == 'yes'

# Custom configuration can be added here