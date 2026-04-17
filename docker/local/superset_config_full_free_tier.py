"""
Superset configuration for FULL GCP Free Tier emulation
This configuration includes all free tier services and limits
"""

import os
import logging
from datetime import timedelta
from celery.schedules import crontab

# =============================================================================
# CORE CONFIGURATION
# =============================================================================

# Flask App Configuration
ROW_LIMIT = 5000  # Firestore-like limits
SUPERSET_WEBSERVER_THREADS = 2
SUPERSET_WEBSERVER_TIMEOUT = 300
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None

# Security
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'CHANGE_ME_IN_PRODUCTION')
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

# =============================================================================
# DATABASE CONFIGURATION (Emulating Firestore limits)
# =============================================================================

SQLALCHEMY_DATABASE_URI = os.environ.get(
    'DATABASE_URL',
    'sqlite:////app/superset_home/superset-free.db'
)

# SQLite optimizations
if SQLALCHEMY_DATABASE_URI.startswith('sqlite'):
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'check_same_thread': False,
        },
        'pool_pre_ping': True,
        'pool_recycle': 3600,
    }
    
    # Apply Firestore-like limits
    from sqlalchemy import event
    from sqlalchemy.engine import Engine
    
    # Track daily operations
    daily_reads = 0
    daily_writes = 0
    daily_deletes = 0
    
    @event.listens_for(Engine, "before_execute")
    def receive_before_execute(conn, clauseelement, multiparams, params, execution_options):
        global daily_reads, daily_writes, daily_deletes
        
        # Simple operation counting (would need reset logic for daily limits)
        statement = str(clauseelement)
        if statement.upper().startswith('SELECT'):
            daily_reads += 1
            if daily_reads > 50000:
                logging.warning("Firestore read limit exceeded!")
        elif statement.upper().startswith(('INSERT', 'UPDATE')):
            daily_writes += 1
            if daily_writes > 20000:
                logging.warning("Firestore write limit exceeded!")
        elif statement.upper().startswith('DELETE'):
            daily_deletes += 1
            if daily_deletes > 20000:
                logging.warning("Firestore delete limit exceeded!")
    
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()

# =============================================================================
# CACHE CONFIGURATION (No Redis in free tier)
# =============================================================================

CACHE_CONFIG = {
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'superset_',
}

# Results backend - use database with size limits
RESULTS_BACKEND = None  # Will use database

# =============================================================================
# CLOUD STORAGE EMULATION (MinIO)
# =============================================================================

# Configure for MinIO (emulating Cloud Storage)
if os.environ.get('MINIO_ENDPOINT'):
    # Upload configuration
    UPLOAD_FOLDER = '/app/cloud-storage/uploads/'
    IMG_UPLOAD_FOLDER = '/app/cloud-storage/images/'
    
    # Limit uploads to match free tier
    CSV_UPLOAD_MAX_SIZE = 50 * 1024 * 1024  # 50MB max
    
    # Track storage usage (5GB limit)
    MAX_STORAGE_BYTES = 5 * 1024 * 1024 * 1024  # 5GB

# =============================================================================
# PUB/SUB CONFIGURATION (Emulated)
# =============================================================================

PUBSUB_PROJECT_ID = os.environ.get('GCP_PROJECT', 'local-free-tier')
PUBSUB_EMULATOR_HOST = os.environ.get('PUBSUB_EMULATOR_HOST')

# Event publishing configuration
EVENT_PUBLISHER = {
    'enabled': bool(PUBSUB_EMULATOR_HOST),
    'project_id': PUBSUB_PROJECT_ID,
    'topic': 'superset-events',
    'max_messages_per_month': 10 * 1024 * 1024 * 1024,  # 10GB/month
}

# =============================================================================
# CLOUD RUN LIMITS EMULATION
# =============================================================================

# Request limits (2M requests/month)
MAX_REQUESTS_PER_MONTH = 2000000
MAX_REQUESTS_PER_DAY = MAX_REQUESTS_PER_MONTH // 30
MAX_REQUESTS_PER_HOUR = MAX_REQUESTS_PER_DAY // 24

# Resource limits
MAX_GB_SECONDS_PER_MONTH = 360000  # 360K GB-seconds
MAX_VCPU_SECONDS_PER_MONTH = 180000  # 180K vCPU-seconds

# Concurrency limits
SUPERSET_WORKERS = 1  # Single worker
CONCURRENT_REQUESTS = 80  # Cloud Run default

# =============================================================================
# CELERY CONFIGURATION (Disabled for free tier)
# =============================================================================

class CeleryConfig:
    broker_url = None
    imports = []
    result_backend = None
    worker_prefetch_multiplier = 1
    task_acks_late = False
    beat_schedule = {}

CELERY_CONFIG = CeleryConfig

# =============================================================================
# FEATURE FLAGS (Optimized for free tier)
# =============================================================================

FEATURE_FLAGS = {
    'ENABLE_TEMPLATE_PROCESSING': True,
    'ENABLE_PROXY_FIX': True,
    'GLOBAL_ASYNC_QUERIES': False,  # No async without Celery
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
    'ESTIMATE_QUERY_COST': False,
    'ENABLE_SQL_VALIDATOR': False,
    'THUMBNAIL_CACHE_TTL': 0,  # Disable thumbnails
    'LISTVIEWS_DEFAULT_CARD_VIEW': False,
    'ENABLE_REACT_CRUD_VIEWS': True,
    'ENABLE_EXPLORE_DRAG_AND_DROP': True,
    'ENABLE_EXPLORE_JSON_CSRF_PROTECTION': True,
    'ENABLE_ADVANCED_DATA_TYPES': True,
}

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================

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

# Web Risk API emulation
WEB_RISK_ENABLED = True
WEB_RISK_SEARCH_LIMIT_MONTH = 100000  # 100K searches/month
WEB_RISK_SUBMIT_LIMIT_MONTH = 100  # 100 submits/month

# reCAPTCHA configuration
RECAPTCHA_ENABLED = True
RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY', '')
RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY', '')
RECAPTCHA_ASSESSMENTS_LIMIT_MONTH = 10000  # 10K/month

# =============================================================================
# LOGGING AND MONITORING
# =============================================================================

LOG_LEVEL = 'WARNING'  # Reduce log volume
ENABLE_TIME_ROTATE = False

# Prometheus metrics
ENABLE_PROMETHEUS_EXPORTER = True
PROMETHEUS_EXPORTER_PORT = 8088  # Same port (path-based)
PROMETHEUS_EXPORTER_PATH = '/metrics'

# Cloud Logging emulation
CLOUD_LOGGING_ENABLED = True
CLOUD_LOGGING_PROJECT = PUBSUB_PROJECT_ID

# =============================================================================
# BIGQUERY INTEGRATION (1TB queries/month free)
# =============================================================================

BIGQUERY_ENABLED = os.environ.get('BIGQUERY_ENABLED', 'false').lower() == 'true'
BIGQUERY_PROJECT = PUBSUB_PROJECT_ID
BIGQUERY_DATASET = 'superset_analytics'
BIGQUERY_QUERY_LIMIT_GB_MONTH = 1024  # 1TB/month free
BIGQUERY_STORAGE_LIMIT_GB = 10  # 10GB storage free

# =============================================================================
# ADDITIONAL FREE TIER SERVICES
# =============================================================================

# Cloud Build integration (2,500 minutes/month)
CLOUD_BUILD_ENABLED = False
CLOUD_BUILD_MINUTES_MONTH = 2500

# Artifact Registry (0.5GB/month)
ARTIFACT_REGISTRY_QUOTA_GB = 0.5

# Cloud Functions integration (2M invocations/month)
CLOUD_FUNCTIONS_ENABLED = False
CLOUD_FUNCTIONS_INVOCATIONS_MONTH = 2000000

# Workflows (5K steps, 2K HTTP calls/month)
WORKFLOWS_ENABLED = False
WORKFLOWS_STEPS_MONTH = 5000
WORKFLOWS_HTTP_CALLS_MONTH = 2000

# Secret Manager (6 active versions, 10K operations/month)
SECRET_MANAGER_ENABLED = True
SECRET_MANAGER_VERSIONS_LIMIT = 6
SECRET_MANAGER_OPERATIONS_MONTH = 10000

# =============================================================================
# SQL LAB CONFIGURATION
# =============================================================================

SQL_MAX_ROW = 10000
SQL_QUERY_MUTATOR = None
SQLLAB_TIMEOUT = 300
SQLLAB_ASYNC_TIME_LIMIT_SEC = 0  # No async queries

# =============================================================================
# DASHBOARD CONFIGURATION
# =============================================================================

DASHBOARD_TEMPLATE_ID = None
DASHBOARD_AUTO_REFRESH_MODE = 'fetch'
DASHBOARD_AUTO_REFRESH_TIMEOUT = 300

# =============================================================================
# DATA UPLOAD CONFIGURATION
# =============================================================================

UPLOAD_FOLDER = '/app/superset_home/uploads/'
IMG_UPLOAD_FOLDER = '/app/superset_home/uploads/'
CSV_UPLOAD_MAX_SIZE = 50 * 1024 * 1024  # 50MB

# =============================================================================
# MAP CONFIGURATION
# =============================================================================

MAPBOX_API_KEY = ''  # No Mapbox in free tier

# =============================================================================
# CORS CONFIGURATION
# =============================================================================

ENABLE_CORS = False
CORS_OPTIONS = {}

# =============================================================================
# DATABASE CONNECTION OPTIMIZATION
# =============================================================================

SQLALCHEMY_POOL_SIZE = 5
SQLALCHEMY_POOL_TIMEOUT = 30
SQLALCHEMY_MAX_OVERFLOW = 5

# =============================================================================
# EXPENSIVE OPERATIONS (DISABLED)
# =============================================================================

ENABLE_SCHEDULED_EMAIL_REPORTS = False
ENABLE_ALERTS = False
THUMBNAIL_SELENIUM_USER = None

# =============================================================================
# CACHE CONFIGURATIONS
# =============================================================================

DATA_CACHE_CONFIG = {
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,  # 24 hours
    'CACHE_KEY_PREFIX': 'superset_data_',
}

FILTER_STATE_CACHE_CONFIG = {
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,
    'CACHE_KEY_PREFIX': 'superset_filter_',
}

EXPLORE_FORM_DATA_CACHE_CONFIG = {
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,
    'CACHE_KEY_PREFIX': 'superset_explore_',
}

# =============================================================================
# USAGE TRACKING (for staying within limits)
# =============================================================================

class UsageTracker:
    """Track usage to stay within free tier limits"""
    
    def __init__(self):
        self.requests_today = 0
        self.gb_seconds_today = 0
        self.vcpu_seconds_today = 0
        self.storage_bytes_used = 0
        
    def check_limits(self):
        """Check if we're approaching free tier limits"""
        if self.requests_today > MAX_REQUESTS_PER_DAY * 0.8:
            logging.warning(f"Approaching daily request limit: {self.requests_today}/{MAX_REQUESTS_PER_DAY}")
        
        monthly_gb_seconds = self.gb_seconds_today * 30
        if monthly_gb_seconds > MAX_GB_SECONDS_PER_MONTH * 0.8:
            logging.warning(f"Approaching monthly GB-seconds limit: {monthly_gb_seconds}/{MAX_GB_SECONDS_PER_MONTH}")

# Initialize usage tracker
usage_tracker = UsageTracker()

print("Superset configured for FULL GCP Free Tier emulation")
print(f"Project: {PUBSUB_PROJECT_ID}")
print(f"Firestore emulator: {os.environ.get('FIRESTORE_EMULATOR_HOST', 'Not configured')}")
print(f"Pub/Sub emulator: {PUBSUB_EMULATOR_HOST or 'Not configured'}")