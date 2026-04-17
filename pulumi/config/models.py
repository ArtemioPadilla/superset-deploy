"""Pydantic models for configuration validation."""

from typing import Dict, List, Optional, Literal, Union, Any
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
import re
import os


# Known Superset versions (can be extended or fetched dynamically)
KNOWN_SUPERSET_VERSIONS = [
    "2.1.0", "2.1.1", "2.1.2", "2.1.3",
    "3.0.0", "3.0.1", "3.0.2", "3.0.3", "3.0.4",
    "3.1.0", "3.1.1",
    "4.0.0", "4.0.1", "4.0.2",
    "latest", "dev"
]

# GCP regions
GCP_REGIONS = [
    "us-central1", "us-east1", "us-east4", "us-west1", "us-west2", "us-west3", "us-west4",
    "europe-west1", "europe-west2", "europe-west3", "europe-west4", "europe-west6",
    "europe-north1", "europe-central2",
    "asia-east1", "asia-east2", "asia-northeast1", "asia-northeast2", "asia-northeast3",
    "asia-south1", "asia-south2", "asia-southeast1", "asia-southeast2",
    "australia-southeast1", "australia-southeast2",
    "southamerica-east1", "southamerica-west1",
    "northamerica-northeast1", "northamerica-northeast2"
]

# Cloud SQL tiers
CLOUD_SQL_TIERS = {
    "free": ["db-f1-micro"],
    "shared": ["db-g1-small"],
    "standard": [
        "db-n1-standard-1", "db-n1-standard-2", "db-n1-standard-4",
        "db-n1-standard-8", "db-n1-standard-16", "db-n1-standard-32",
        "db-n1-standard-64", "db-n1-standard-96"
    ],
    "highmem": [
        "db-n1-highmem-2", "db-n1-highmem-4", "db-n1-highmem-8",
        "db-n1-highmem-16", "db-n1-highmem-32", "db-n1-highmem-64",
        "db-n1-highmem-96"
    ]
}


class ResourceConfig(BaseModel):
    """Resource configuration for containers."""
    cpu: str = Field("1", description="CPU allocation (e.g., '0.5', '1', '2')")
    memory: str = Field("2Gi", description="Memory allocation (e.g., '512Mi', '2Gi')")
    
    @field_validator('cpu')
    def validate_cpu(cls, v):
        try:
            cpu_value = float(v)
            if cpu_value <= 0 or cpu_value > 96:
                raise ValueError("CPU must be between 0 and 96")
        except ValueError as e:
            if "could not convert" in str(e):
                raise ValueError(f"Invalid CPU value: {v}. Must be a number.")
            raise
        return v
    
    @field_validator('memory')
    def validate_memory(cls, v):
        if not re.match(r'^\d+(\.\d+)?(Mi|Gi)$', v):
            raise ValueError(f"Invalid memory format: {v}. Use format like '512Mi' or '2Gi'")
        return v


class AutoscalingConfig(BaseModel):
    """Autoscaling configuration."""
    enabled: bool = False
    min_replicas: int = Field(1, ge=1, le=100)
    max_replicas: int = Field(10, ge=1, le=100)
    cpu_threshold: int = Field(70, ge=10, le=95)
    
    @model_validator(mode='after')
    def validate_replicas_range(self):
        if self.min_replicas > self.max_replicas:
            raise ValueError(f"min_replicas ({self.min_replicas}) cannot be greater than max_replicas ({self.max_replicas})")
        return self


class SupersetDefaults(BaseModel):
    """Global Superset defaults."""
    default_version: str = Field("3.0.0", description="Default Superset version")
    default_admin_email: str = Field("admin@example.com", description="Default admin email")
    
    @field_validator('default_version')
    def validate_version(cls, v):
        if v not in KNOWN_SUPERSET_VERSIONS:
            # Allow custom versions but warn
            print(f"Warning: Superset version '{v}' is not in known versions. Proceed with caution.")
        return v


class SupersetConfig(BaseModel):
    """Superset-specific configuration."""
    version: Optional[str] = Field(None, description="Superset version to deploy")
    port: int = Field(8088, ge=1024, le=65535, description="Port for Superset")
    replicas: int = Field(1, ge=1, le=100, description="Number of replicas")
    dev_mode: bool = Field(False, description="Enable development mode")
    resources: ResourceConfig = Field(default_factory=ResourceConfig)
    autoscaling: Optional[AutoscalingConfig] = None
    plugins: List[str] = Field(default_factory=list, description="Superset plugins to install")
    
    @field_validator('version')
    def validate_version(cls, v):
        if v and v not in KNOWN_SUPERSET_VERSIONS:
            print(f"Warning: Superset version '{v}' is not in known versions. Proceed with caution.")
        return v


class BackupConfig(BaseModel):
    """Backup configuration."""
    enabled: bool = True
    time: str = Field("02:00", description="Backup time in HH:MM format")
    location: Optional[str] = None
    retention_days: int = Field(7, ge=1, le=365)
    
    @field_validator('time')
    def validate_time(cls, v):
        if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', v):
            raise ValueError(f"Invalid time format: {v}. Use HH:MM format.")
        return v


class DatabaseBackupConfig(BackupConfig):
    """Database-specific backup configuration."""
    frequency: Optional[str] = Field(None, description="Cron expression for backup frequency")


class DatabaseConfig(BaseModel):
    """Database configuration."""
    type: Literal["sqlite", "postgresql", "cloud-sql"] = "sqlite"
    path: Optional[str] = Field(None, description="Path for SQLite database")
    host: Optional[str] = None
    port: Optional[int] = Field(5432, ge=1, le=65535)
    name: Optional[str] = "superset"
    user: Optional[str] = "superset"
    password: Optional[str] = None
    tier: Optional[str] = Field(None, description="Cloud SQL machine type")
    disk_size: int = Field(10, ge=10, le=65536, description="Disk size in GB")
    disk_type: Literal["pd-standard", "pd-ssd", "pd-balanced"] = "pd-standard"
    high_availability: bool = False
    backup: Optional[DatabaseBackupConfig] = Field(default_factory=DatabaseBackupConfig)
    
    @field_validator('tier')
    def validate_tier(cls, v, info):
        if v and info.data.get('type') == 'cloud-sql':
            all_tiers = [tier for tiers in CLOUD_SQL_TIERS.values() for tier in tiers]
            if v not in all_tiers:
                raise ValueError(f"Invalid Cloud SQL tier: {v}")
            if v in CLOUD_SQL_TIERS['free'] and info.data.get('high_availability'):
                raise ValueError(f"Free tier '{v}' does not support high availability")
        return v
    
    @model_validator(mode='after')
    def validate_database_config(self):
        if self.type == 'sqlite':
            if not self.path:
                self.path = './data/superset.db'
        elif self.type in ['postgresql', 'cloud-sql']:
            if not self.password:
                raise ValueError(f"Password is required for {self.type}")
        return self


class CacheConfig(BaseModel):
    """Cache configuration."""
    type: Literal["none", "redis", "memcached"] = "none"
    host: Optional[str] = None
    port: Optional[int] = Field(6379, ge=1, le=65535)
    password: Optional[str] = None
    tier: Literal["basic", "standard"] = "basic"
    memory_size_gb: int = Field(1, ge=1, le=300)
    high_availability: bool = False


class GCPConfig(BaseModel):
    """GCP-specific configuration."""
    project_id: str = Field(..., description="GCP project ID")
    region: str = Field("us-central1", description="GCP region")
    zone: Optional[str] = Field(None, description="GCP zone")
    credentials_path: Optional[Path] = Field(None, description="Path to service account key")
    service_account: Optional[str] = Field(None, description="Service account email")
    
    @field_validator('project_id')
    def validate_project_id(cls, v):
        # Allow environment variable substitution
        if v.startswith('${') and v.endswith('}'):
            env_var = v[2:-1].split(':-')[0]
            default = v[2:-1].split(':-')[1] if ':-' in v else None
            v = os.environ.get(env_var, default)
            if not v:
                raise ValueError(f"Environment variable {env_var} is not set")
        
        if not re.match(r'^[a-z][a-z0-9-]{4,28}[a-z0-9]$', v):
            raise ValueError(f"Invalid GCP project ID: {v}")
        return v
    
    @field_validator('region')
    def validate_region(cls, v):
        if v not in GCP_REGIONS:
            raise ValueError(f"Invalid GCP region: {v}. Must be one of: {', '.join(GCP_REGIONS)}")
        return v
    
    @field_validator('zone')
    def validate_zone(cls, v, info):
        if v:
            region = info.data.get('region')
            if region and not v.startswith(region):
                raise ValueError(f"Zone {v} does not match region {region}")
        return v
    
    @field_validator('credentials_path')
    def validate_credentials_path(cls, v):
        if v:
            path = Path(v).expanduser()
            if not path.exists():
                raise ValueError(f"Credentials file not found: {v}")
            return path
        return v


class SSLConfig(BaseModel):
    """SSL configuration."""
    enabled: bool = True
    managed: bool = True
    domains: List[str] = Field(default_factory=list)


class OAuthConfig(BaseModel):
    """OAuth configuration."""
    enabled: bool = False
    providers: List[Literal["google", "github", "azure", "okta"]] = Field(default_factory=list)


class VPCConfig(BaseModel):
    """VPC configuration."""
    enabled: bool = False
    private_ip: bool = True
    cidr_range: str = "10.0.0.0/16"
    
    @field_validator('cidr_range')
    def validate_cidr(cls, v):
        from ..config.validators import validate_cidr_format
        valid, error = validate_cidr_format(v)
        if not valid:
            raise ValueError(error)
        return v


class SecurityConfig(BaseModel):
    """Security configuration."""
    ssl: SSLConfig = Field(default_factory=SSLConfig)
    oauth: OAuthConfig = Field(default_factory=OAuthConfig)
    vpc: VPCConfig = Field(default_factory=VPCConfig)
    secrets_backend: Literal["local", "secret-manager"] = "local"


class CloudflareAccessPolicy(BaseModel):
    """Cloudflare access policy."""
    name: str
    include: List[Dict[str, Union[str, List[str]]]] = Field(default_factory=list)
    exclude: List[Dict[str, Union[str, List[str]]]] = Field(default_factory=list)
    require: List[Dict[str, Union[str, bool]]] = Field(default_factory=list)


class CloudflareConfig(BaseModel):
    """Cloudflare tunnel configuration."""
    enabled: bool = False
    tunnel_name: Optional[str] = None
    tunnel_id: Optional[str] = None
    tunnel_secret: Optional[str] = None
    account_id: Optional[str] = None
    hostname: Optional[str] = None
    monitoring_hostname: Optional[str] = None
    metrics_hostname: Optional[str] = None
    deployment_type: Literal["cloudrun", "gke"] = "cloudrun"
    access_policies: List[CloudflareAccessPolicy] = Field(default_factory=list)
    
    @field_validator('hostname', 'monitoring_hostname', 'metrics_hostname')
    def validate_hostnames(cls, v):
        if v:
            # Allow simple hostnames without protocol
            if not v.startswith('http'):
                return v  # Simple hostname is OK
            # If it has protocol, validate as URL
            from ..config.validators import validate_url_format
            valid, error = validate_url_format(v)
            if not valid:
                raise ValueError(error)
        return v


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""
    enabled: bool = False
    prometheus: Dict[str, Any] = Field(default_factory=dict)
    grafana: Dict[str, Any] = Field(default_factory=dict)
    alerting: Dict[str, Any] = Field(default_factory=dict)


class StackBackupConfig(BaseModel):
    """Stack-level backup configuration."""
    enabled: bool = False
    frequency: str = Field("0 2 * * *", description="Cron expression")
    destination: Optional[str] = None
    retention_days: int = Field(30, ge=1, le=365)
    
    @field_validator('frequency')
    def validate_frequency(cls, v):
        from ..config.validators import validate_cron_expression
        valid, error = validate_cron_expression(v)
        if not valid:
            raise ValueError(error)
        return v


class StackFeatures(BaseModel):
    """Feature flags for Superset."""
    sql_lab: bool = True
    dashboard_emails: bool = True
    alerts: bool = True
    reports: bool = True


class StackConfig(BaseModel):
    """Individual stack configuration."""
    type: Literal["minimal", "standard", "production"]
    environment: Literal["local", "gcp"]
    enabled: bool = True
    extends: Optional[str] = Field(None, description="Parent stack to inherit from")
    gcp: Optional[GCPConfig] = None
    superset: SupersetConfig = Field(default_factory=SupersetConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    cloudflare: CloudflareConfig = Field(default_factory=CloudflareConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    backup: StackBackupConfig = Field(default_factory=StackBackupConfig)
    features: Optional[StackFeatures] = None
    
    @model_validator(mode='after')
    def validate_stack_config(self):
        # Validate GCP config for GCP environments
        if self.environment == 'gcp' and not self.gcp:
            raise ValueError("GCP configuration is required for GCP environments")
        
        # Validate database type for environments
        if self.environment == 'local' and self.database.type == 'cloud-sql':
            raise ValueError("Cloud SQL cannot be used in local environment")
        
        # Set appropriate defaults based on stack type
        if self.type == 'minimal':
            if not self.database:
                self.database = DatabaseConfig(type='sqlite')
            if not self.cache:
                self.cache = CacheConfig(type='none')
        
        return self


class MonitoringDefaults(BaseModel):
    """Global monitoring defaults."""
    retention_days: int = Field(30, ge=1, le=365)


class BackupDefaults(BaseModel):
    """Global backup defaults."""
    retention_days: int = Field(7, ge=1, le=365)


class GlobalConfig(BaseModel):
    """Global configuration applied to all stacks."""
    superset: SupersetDefaults = Field(default_factory=SupersetDefaults)
    monitoring: MonitoringDefaults = Field(default_factory=MonitoringDefaults)
    backup: BackupDefaults = Field(default_factory=BackupDefaults)


class SystemConfig(BaseModel):
    """Root configuration model."""
    global_config: GlobalConfig = Field(default_factory=GlobalConfig, alias="global")
    stacks: Dict[str, StackConfig] = Field(default_factory=dict)
    
    model_config = ConfigDict(populate_by_name=True)
    
    @model_validator(mode='after')
    def process_inheritance(self):
        """Process stack inheritance after all stacks are loaded."""
        # Apply global defaults
        for stack_name, stack in self.stacks.items():
            # Apply global Superset version if not specified
            if not stack.superset.version:
                stack.superset.version = self.global_config.superset.default_version
        
        return self
    
    def get_stack(self, name: str) -> Optional[StackConfig]:
        """Get a stack configuration by name."""
        return self.stacks.get(name)
    
    def get_enabled_stacks(self) -> Dict[str, StackConfig]:
        """Get all enabled stacks."""
        return {name: stack for name, stack in self.stacks.items() if stack.enabled}