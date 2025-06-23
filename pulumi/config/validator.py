"""Configuration validator for stack configurations."""

from typing import Dict, Any, List


def validate_stack_config(config: Dict[str, Any]) -> List[str]:
    """Validate stack configuration and return list of errors."""
    errors = []
    
    # Required fields
    if 'type' not in config:
        errors.append("Stack type is required")
    elif config['type'] not in ['minimal', 'standard', 'production']:
        errors.append(f"Invalid stack type: {config['type']}")
    
    if 'environment' not in config:
        errors.append("Environment is required")
    elif config['environment'] not in ['local', 'gcp']:
        errors.append(f"Invalid environment: {config['environment']}")
    
    # GCP-specific validation
    if config.get('environment') == 'gcp':
        gcp_config = config.get('gcp', {})
        if not gcp_config.get('project_id'):
            errors.append("GCP project_id is required for GCP deployments")
        if not gcp_config.get('region'):
            errors.append("GCP region is required for GCP deployments")
    
    # Superset configuration validation
    superset_config = config.get('superset', {})
    if superset_config:
        if 'replicas' in superset_config:
            replicas = superset_config['replicas']
            if not isinstance(replicas, int) or replicas < 1:
                errors.append("Superset replicas must be a positive integer")
        
        if 'resources' in superset_config:
            resources = superset_config['resources']
            if 'cpu' in resources:
                try:
                    float(resources['cpu'])
                except ValueError:
                    errors.append(f"Invalid CPU value: {resources['cpu']}")
            
            if 'memory' in resources:
                if not resources['memory'].endswith(('Mi', 'Gi')):
                    errors.append(f"Invalid memory format: {resources['memory']}")
    
    # Database configuration validation
    db_config = config.get('database', {})
    if db_config:
        db_type = db_config.get('type')
        if db_type not in ['sqlite', 'postgresql', 'cloud-sql']:
            errors.append(f"Invalid database type: {db_type}")
        
        if db_type == 'cloud-sql' and config.get('environment') != 'gcp':
            errors.append("Cloud SQL can only be used in GCP environment")
    
    # Cache configuration validation
    cache_config = config.get('cache', {})
    if cache_config:
        cache_type = cache_config.get('type')
        if cache_type not in ['none', 'redis', 'memcached']:
            errors.append(f"Invalid cache type: {cache_type}")
    
    return errors


def validate_system_config(config: Dict[str, Any]) -> List[str]:
    """Validate the entire system configuration."""
    errors = []
    
    if 'stacks' not in config:
        errors.append("No stacks defined in configuration")
        return errors
    
    # Validate each stack
    for stack_name, stack_config in config['stacks'].items():
        stack_errors = validate_stack_config(stack_config)
        for error in stack_errors:
            errors.append(f"Stack '{stack_name}': {error}")
    
    return errors