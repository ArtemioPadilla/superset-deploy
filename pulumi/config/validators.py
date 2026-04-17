"""Custom validators for configuration."""

import re
import os
from typing import List, Optional, Dict, Any
from pathlib import Path
import requests
from functools import lru_cache


import json
from datetime import datetime, timedelta


# Cache file for Docker Hub versions
CACHE_FILE = os.path.expanduser("~/.cache/superset-deploy/docker-hub-versions.json")
CACHE_DURATION = timedelta(hours=24)


def _load_cached_versions() -> Optional[List[str]]:
    """Load cached versions from disk if available and not expired."""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache is expired
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cached_time < CACHE_DURATION:
                return cache_data['versions']
    except Exception:
        pass
    return None


def _save_cached_versions(versions: List[str]):
    """Save versions to cache file."""
    try:
        cache_dir = os.path.dirname(CACHE_FILE)
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'versions': versions
        }
        
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
    except Exception:
        pass


@lru_cache(maxsize=1)
def get_available_superset_versions(use_cache: bool = True) -> List[str]:
    """Fetch available Superset versions from Docker Hub with caching.
    
    Args:
        use_cache: Whether to use cached results if available
        
    Returns:
        List of available version tags
    """
    # Default versions for offline/fallback
    default_versions = [
        "4.0.2", "4.0.1", "4.0.0",
        "3.1.1", "3.1.0", 
        "3.0.4", "3.0.3", "3.0.2", "3.0.1", "3.0.0",
        "2.1.3", "2.1.2", "2.1.1", "2.1.0",
        "latest", "dev"
    ]
    
    # Check cache first
    if use_cache:
        cached_versions = _load_cached_versions()
        if cached_versions:
            return cached_versions
    
    try:
        # Query Docker Hub API for apache/superset tags
        response = requests.get(
            "https://hub.docker.com/v2/repositories/apache/superset/tags",
            params={"page_size": 100, "ordering": "-last_updated"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            all_tags = []
            
            # Get all pages (up to 3 pages for 300 tags)
            for _ in range(3):
                tags = [tag['name'] for tag in data.get('results', [])]
                all_tags.extend(tags)
                
                # Check for next page
                next_url = data.get('next')
                if not next_url:
                    break
                
                response = requests.get(next_url, timeout=5)
                if response.status_code != 200:
                    break
                data = response.json()
            
            # Filter out non-version tags
            version_pattern = re.compile(r'^\d+\.\d+\.\d+(-\w+)?$|^latest$|^dev$')
            versions = [tag for tag in all_tags if version_pattern.match(tag)]
            
            # Sort versions properly (numeric sort for version numbers)
            def version_key(v):
                if v in ['latest', 'dev']:
                    return (999, 0, 0)  # Put special versions first
                try:
                    parts = v.split('-')[0].split('.')
                    return tuple(int(p) for p in parts)
                except:
                    return (0, 0, 0)
            
            versions = sorted(set(versions), key=version_key, reverse=True)
            
            # Save to cache
            _save_cached_versions(versions)
            
            return versions
            
    except requests.exceptions.Timeout:
        print("Warning: Docker Hub API request timed out. Using cached or default versions.")
    except requests.exceptions.ConnectionError:
        print("Warning: Cannot connect to Docker Hub. Using cached or default versions.")
    except Exception as e:
        print(f"Warning: Error fetching Superset versions: {e}")
    
    # Try to load from cache even if expired
    cached_versions = _load_cached_versions()
    if cached_versions:
        print("Using expired cache due to API failure.")
        return cached_versions
    
    # Return default list if everything fails
    return default_versions


def validate_superset_version(version: str, allow_custom: bool = True) -> tuple[bool, Optional[str]]:
    """Validate Superset version.
    
    Args:
        version: Version string to validate
        allow_custom: Whether to allow custom versions
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    available_versions = get_available_superset_versions()
    
    if version in available_versions:
        return True, None
    
    if allow_custom:
        # Check if it looks like a valid version
        if re.match(r'^\d+\.\d+\.\d+(-\w+)?$|^latest$|^dev$', version):
            return True, f"Warning: Version '{version}' not found in Docker Hub. Proceeding with custom version."
        else:
            return False, f"Invalid version format: '{version}'. Expected format: X.Y.Z, 'latest', or 'dev'"
    else:
        return False, f"Version '{version}' not available. Available versions: {', '.join(available_versions[:10])}..."


def validate_gcp_project_id(project_id: str) -> tuple[bool, Optional[str]]:
    """Validate GCP project ID format.
    
    Args:
        project_id: GCP project ID to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Handle environment variable substitution
    if project_id.startswith('${') and project_id.endswith('}'):
        return True, None  # Will be validated at runtime
    
    # GCP project ID rules:
    # - 6-30 characters
    # - Lowercase letters, digits, hyphens
    # - Must start with a letter
    # - Cannot end with a hyphen
    if not re.match(r'^[a-z][a-z0-9-]{4,28}[a-z0-9]$', project_id):
        return False, (
            f"Invalid GCP project ID '{project_id}'. "
            "Must be 6-30 characters, start with a letter, "
            "and contain only lowercase letters, numbers, and hyphens."
        )
    
    return True, None


def validate_resource_allocation(cpu: str, memory: str, stack_type: str) -> List[str]:
    """Validate resource allocations for a given stack type.
    
    Args:
        cpu: CPU allocation string
        memory: Memory allocation string
        stack_type: Type of stack (minimal, standard, production)
        
    Returns:
        List of warning messages
    """
    warnings = []
    
    # Parse CPU
    try:
        cpu_value = float(cpu)
    except ValueError:
        return [f"Invalid CPU value: {cpu}"]
    
    # Parse memory
    memory_match = re.match(r'^(\d+(?:\.\d+)?)(Mi|Gi)$', memory)
    if not memory_match:
        return [f"Invalid memory format: {memory}"]
    
    memory_value = float(memory_match.group(1))
    memory_unit = memory_match.group(2)
    memory_mb = memory_value * 1024 if memory_unit == 'Gi' else memory_value
    
    # Check recommendations based on stack type
    if stack_type == 'minimal':
        if cpu_value > 1:
            warnings.append(f"CPU allocation ({cpu}) seems high for minimal stack. Consider using 0.5-1 CPU.")
        if memory_mb > 2048:
            warnings.append(f"Memory allocation ({memory}) seems high for minimal stack. Consider using 512Mi-2Gi.")
    
    elif stack_type == 'standard':
        if cpu_value < 0.5:
            warnings.append(f"CPU allocation ({cpu}) might be too low for standard stack. Consider using 1-2 CPUs.")
        if memory_mb < 1024:
            warnings.append(f"Memory allocation ({memory}) might be too low for standard stack. Consider using 2Gi-4Gi.")
    
    elif stack_type == 'production':
        if cpu_value < 1:
            warnings.append(f"CPU allocation ({cpu}) is too low for production. Minimum recommended: 2 CPUs.")
        if memory_mb < 2048:
            warnings.append(f"Memory allocation ({memory}) is too low for production. Minimum recommended: 4Gi.")
    
    return warnings


def validate_cloud_sql_tier_for_environment(tier: str, high_availability: bool, stack_type: str) -> List[str]:
    """Validate Cloud SQL tier selection.
    
    Args:
        tier: Cloud SQL machine type
        high_availability: Whether HA is enabled
        stack_type: Type of stack
        
    Returns:
        List of warning messages
    """
    warnings = []
    
    free_tiers = ["db-f1-micro"]
    shared_tiers = ["db-g1-small"]
    
    if tier in free_tiers:
        if high_availability:
            warnings.append(f"Free tier '{tier}' does not support high availability.")
        if stack_type == 'production':
            warnings.append(f"Free tier '{tier}' is not recommended for production use.")
    
    elif tier in shared_tiers:
        if stack_type == 'production':
            warnings.append(f"Shared tier '{tier}' is not recommended for production. Consider standard tier.")
    
    # Check if tier exists
    if not any(tier.startswith(prefix) for prefix in ['db-f1-', 'db-g1-', 'db-n1-', 'db-n2-', 'db-e2-']):
        warnings.append(f"Unknown Cloud SQL tier prefix: {tier}")
    
    return warnings


def validate_backup_configuration(backup_config: Dict[str, Any], stack_type: str) -> List[str]:
    """Validate backup configuration.
    
    Args:
        backup_config: Backup configuration dict
        stack_type: Type of stack
        
    Returns:
        List of warning messages
    """
    warnings = []
    
    if not backup_config.get('enabled') and stack_type == 'production':
        warnings.append("Backups are disabled for production stack. This is not recommended.")
    
    retention_days = backup_config.get('retention_days', 7)
    if stack_type == 'production' and retention_days < 30:
        warnings.append(f"Backup retention ({retention_days} days) might be too short for production. Consider 30+ days.")
    
    if backup_config.get('enabled') and not backup_config.get('destination'):
        if stack_type in ['standard', 'production']:
            warnings.append("No backup destination specified. Backups will use default location.")
    
    return warnings


def validate_monitoring_configuration(monitoring_config: Dict[str, Any], stack_type: str) -> List[str]:
    """Validate monitoring configuration.
    
    Args:
        monitoring_config: Monitoring configuration dict
        stack_type: Type of stack
        
    Returns:
        List of warning messages
    """
    warnings = []
    
    if not monitoring_config.get('enabled') and stack_type == 'production':
        warnings.append("Monitoring is disabled for production stack. This is strongly discouraged.")
    
    if monitoring_config.get('enabled'):
        prometheus_config = monitoring_config.get('prometheus', {})
        retention_days = prometheus_config.get('retention_days', 30)
        
        if retention_days < 7:
            warnings.append(f"Prometheus retention ({retention_days} days) is very short. Consider at least 7 days.")
        
        storage_size = prometheus_config.get('storage_size', 10)
        if stack_type == 'production' and storage_size < 50:
            warnings.append(f"Prometheus storage ({storage_size}GB) might be insufficient for production.")
    
    return warnings


def expand_environment_variables(value: str, strict: bool = False) -> str:
    """Expand environment variables in configuration values.
    
    Args:
        value: String that may contain ${VAR} or ${VAR:-default}
        strict: If True, raise error for missing variables without defaults
        
    Returns:
        Expanded string
        
    Raises:
        ValueError: If strict=True and a variable is not found
    """
    if not isinstance(value, str):
        return value
    
    # Pattern to match ${VAR} or ${VAR:-default}
    pattern = re.compile(r'\$\{([^}:]+)(?::-([^}]*))?\}')
    missing_vars = []
    
    def replacer(match):
        var_name = match.group(1)
        default_value = match.group(2)
        
        if var_name in os.environ:
            return os.environ[var_name]
        elif default_value is not None:
            return default_value
        else:
            missing_vars.append(var_name)
            # Return the original pattern if not strict
            return match.group(0) if not strict else None
    
    result = pattern.sub(replacer, value)
    
    if strict and missing_vars:
        raise ValueError(
            f"Environment variable{'s' if len(missing_vars) > 1 else ''} not found: "
            f"{', '.join(missing_vars)}. "
            f"Set {'them' if len(missing_vars) > 1 else 'it'} or provide default values."
        )
    
    return result


def validate_network_configuration(vpc_config: Dict[str, Any], stack_type: str) -> List[str]:
    """Validate network/VPC configuration.
    
    Args:
        vpc_config: VPC configuration dict
        stack_type: Type of stack
        
    Returns:
        List of warning messages
    """
    warnings = []
    
    if stack_type == 'production' and not vpc_config.get('enabled'):
        warnings.append("VPC is disabled for production stack. Consider enabling for better security.")
    
    if vpc_config.get('enabled'):
        cidr_range = vpc_config.get('cidr_range', '10.0.0.0/16')
        # Simple CIDR validation
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$', cidr_range):
            warnings.append(f"Invalid CIDR range format: {cidr_range}")
    
    return warnings


def check_version_compatibility(superset_version: str, plugin_list: List[str]) -> List[str]:
    """Check compatibility between Superset version and plugins.
    
    Args:
        superset_version: Superset version
        plugin_list: List of plugins
        
    Returns:
        List of warning messages
    """
    warnings = []
    
    # Define known compatibility issues
    compatibility_map = {
        "superset-plugin-chart-echarts": {"min_version": "2.0.0"},
        "superset-plugin-chart-handlebars": {"min_version": "2.1.0"},
    }
    
    if superset_version in ['latest', 'dev']:
        return warnings  # Skip compatibility check for latest/dev
    
    try:
        version_parts = [int(x) for x in superset_version.split('.')]
        
        for plugin in plugin_list:
            if plugin in compatibility_map:
                min_version = compatibility_map[plugin].get('min_version', '0.0.0')
                min_parts = [int(x) for x in min_version.split('.')]
                
                if version_parts < min_parts:
                    warnings.append(
                        f"Plugin '{plugin}' requires Superset {min_version} or higher. "
                        f"Current version: {superset_version}"
                    )
    except ValueError:
        # Could not parse version
        pass
    
    return warnings


def validate_sensitive_field(field_name: str, value: Optional[str], stack_type: str) -> List[str]:
    """Validate sensitive configuration fields.
    
    Args:
        field_name: Name of the field being validated
        value: Field value
        stack_type: Type of stack (minimal, standard, production)
        
    Returns:
        List of warning messages
    """
    warnings = []
    
    if not value:
        return warnings
    
    # Check for weak/default passwords
    weak_passwords = ['admin', 'password', 'test', '123456', 'default']
    if field_name in ['password', 'secret_key'] and value.lower() in weak_passwords:
        if stack_type == 'production':
            warnings.append(f"Weak {field_name} detected. This is a security risk for production.")
        else:
            warnings.append(f"Weak {field_name} detected. Consider using a stronger value.")
    
    # Check for exposed secrets in plain text
    if field_name in ['secret_key', 'password', 'token', 'api_key']:
        # Check if it looks like an environment variable reference
        if not value.startswith('${'):
            if stack_type == 'production':
                warnings.append(
                    f"{field_name} is stored in plain text. "
                    f"Consider using environment variables: ${{{field_name.upper()}}}"
                )
    
    # Check secret key strength
    if field_name == 'secret_key' and len(value) < 32:
        warnings.append(
            f"Secret key is too short ({len(value)} chars). "
            "Recommended minimum: 32 characters for production."
        )
    
    # Check for common test/demo values
    if re.match(r'^(test|demo|example)', value, re.IGNORECASE):
        if stack_type in ['standard', 'production']:
            warnings.append(f"{field_name} appears to be a test value. Use a real value for {stack_type}.")
    
    return warnings


def validate_url_format(url: str) -> tuple[bool, Optional[str]]:
    """Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return True, None
    
    # Basic URL pattern
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        return False, f"Invalid URL format: {url}"
    
    return True, None


def validate_cidr_format(cidr: str) -> tuple[bool, Optional[str]]:
    """Validate CIDR format and range.
    
    Args:
        cidr: CIDR notation string (e.g., "10.0.0.0/16")
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # CIDR pattern
    cidr_pattern = re.compile(
        r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})/(\d{1,2})$'
    )
    
    match = cidr_pattern.match(cidr)
    if not match:
        return False, f"Invalid CIDR format: {cidr}. Expected format: x.x.x.x/y"
    
    # Validate IP octets
    octets = [int(match.group(i)) for i in range(1, 5)]
    for i, octet in enumerate(octets):
        if octet > 255:
            return False, f"Invalid IP octet {octet} in position {i+1}. Must be 0-255."
    
    # Validate subnet mask
    subnet = int(match.group(5))
    if subnet > 32:
        return False, f"Invalid subnet mask /{subnet}. Must be 0-32."
    
    # Validate that host bits are zero
    ip_int = (octets[0] << 24) + (octets[1] << 16) + (octets[2] << 8) + octets[3]
    host_bits = 32 - subnet
    if host_bits > 0:
        host_mask = (1 << host_bits) - 1
        if ip_int & host_mask != 0:
            return False, f"Invalid CIDR: {cidr}. Host bits must be zero."
    
    return True, None


def validate_cron_expression(expression: str) -> tuple[bool, Optional[str]]:
    """Validate cron expression format.
    
    Args:
        expression: Cron expression string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Simple cron validation (5 or 6 fields)
    parts = expression.strip().split()
    
    if len(parts) not in [5, 6]:
        return False, f"Invalid cron expression: {expression}. Expected 5 or 6 fields."
    
    # Field ranges
    field_ranges = [
        (0, 59),   # minute
        (0, 23),   # hour
        (1, 31),   # day of month
        (1, 12),   # month
        (0, 6),    # day of week
    ]
    
    for i, (part, (min_val, max_val)) in enumerate(zip(parts[:5], field_ranges)):
        # Handle special characters
        if part in ['*', '?']:
            continue
        
        # Handle ranges (e.g., "1-5")
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                if start < min_val or end > max_val or start > end:
                    raise ValueError
            except ValueError:
                field_names = ['minute', 'hour', 'day', 'month', 'day of week']
                return False, f"Invalid {field_names[i]} range: {part}"
            continue
        
        # Handle lists (e.g., "1,3,5")
        if ',' in part:
            try:
                values = [int(v) for v in part.split(',')]
                if any(v < min_val or v > max_val for v in values):
                    raise ValueError
            except ValueError:
                field_names = ['minute', 'hour', 'day', 'month', 'day of week']
                return False, f"Invalid {field_names[i]} list: {part}"
            continue
        
        # Handle step values (e.g., "*/5")
        if '/' in part:
            continue  # More complex validation needed
        
        # Handle simple values
        try:
            value = int(part)
            if value < min_val or value > max_val:
                raise ValueError
        except ValueError:
            field_names = ['minute', 'hour', 'day', 'month', 'day of week']
            return False, f"Invalid {field_names[i]} value: {part}"
    
    return True, None