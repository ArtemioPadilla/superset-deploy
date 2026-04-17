"""Configuration loader for system.yaml."""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic import ValidationError

from .models import SystemConfig, StackConfig
from .validators import expand_environment_variables, validate_sensitive_field


def load_system_config(config_path: str) -> SystemConfig:
    """Load and parse system.yaml configuration with Pydantic validation.
    
    Args:
        config_path: Path to system.yaml file
        
    Returns:
        Validated SystemConfig object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValidationError: If configuration is invalid
        yaml.YAMLError: If YAML syntax is invalid
    """
    # Check if file exists
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    # Load YAML
    with open(config_path, 'r') as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML syntax in {config_path}: {e}")
    
    if not data:
        raise ValueError(f"Configuration file is empty: {config_path}")
    
    # Expand environment variables in the configuration
    data = expand_config_env_vars(data)
    
    # Process stack inheritance before validation
    data = process_stack_inheritance(data)
    
    try:
        # Create and validate SystemConfig
        config = SystemConfig(**data)
        
        # Apply global defaults to stacks
        config = apply_global_defaults(config)
        
        # Print any warnings from validation
        print_validation_warnings(config)
        
        return config
        
    except ValidationError as e:
        # Format validation errors nicely
        print("\n❌ Configuration validation failed:")
        for error in e.errors():
            field_path = " -> ".join(str(x) for x in error['loc'])
            print(f"  • {field_path}: {error['msg']}")
        raise


def expand_config_env_vars(data: Any, strict: bool = False) -> Any:
    """Recursively expand environment variables in configuration.
    
    Args:
        data: Configuration data (dict, list, or scalar)
        strict: If True, raise error for missing variables
        
    Returns:
        Configuration with expanded environment variables
        
    Raises:
        ValueError: If strict=True and variables are missing
    """
    if isinstance(data, dict):
        return {key: expand_config_env_vars(value, strict) for key, value in data.items()}
    elif isinstance(data, list):
        return [expand_config_env_vars(item, strict) for item in data]
    elif isinstance(data, str):
        try:
            return expand_environment_variables(data, strict)
        except ValueError as e:
            # Add context about where the error occurred
            raise ValueError(f"Error expanding environment variables: {e}")
    else:
        return data


def process_stack_inheritance(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process stack inheritance (extends) before validation.
    
    Args:
        data: Raw configuration data
        
    Returns:
        Configuration with inheritance resolved
    """
    stacks = data.get('stacks', {})
    processed_stacks = {}
    
    # First pass: identify dependencies
    dependencies = {}
    for stack_name, stack_config in stacks.items():
        if isinstance(stack_config, dict) and 'extends' in stack_config:
            dependencies[stack_name] = stack_config['extends']
    
    # Resolve dependencies in order
    resolved = set()
    
    def resolve_stack(stack_name: str) -> Dict[str, Any]:
        if stack_name in resolved:
            return processed_stacks[stack_name]
        
        if stack_name not in stacks:
            raise ValueError(f"Stack '{stack_name}' not found")
        
        stack_config = stacks[stack_name].copy()
        
        if stack_name in dependencies:
            parent_name = dependencies[stack_name]
            if parent_name == stack_name:
                raise ValueError(f"Stack '{stack_name}' cannot extend itself")
            
            # Resolve parent first
            parent_config = resolve_stack(parent_name)
            
            # Deep merge parent and child
            merged_config = deep_merge(parent_config, stack_config)
            merged_config.pop('extends', None)
            processed_stacks[stack_name] = merged_config
        else:
            processed_stacks[stack_name] = stack_config
        
        resolved.add(stack_name)
        return processed_stacks[stack_name]
    
    # Resolve all stacks
    for stack_name in stacks:
        resolve_stack(stack_name)
    
    data['stacks'] = processed_stacks
    return data


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        override: Dictionary to merge into base
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def apply_global_defaults(config: SystemConfig) -> SystemConfig:
    """Apply global defaults to stack configurations.
    
    Args:
        config: SystemConfig object
        
    Returns:
        SystemConfig with defaults applied
    """
    global_defaults = config.global_config
    
    for stack_name, stack in config.stacks.items():
        # Apply global Superset version if not specified
        if not stack.superset.version:
            stack.superset.version = global_defaults.superset.default_version
        
        # Apply global monitoring retention if not specified
        if stack.monitoring.enabled and 'retention_days' not in stack.monitoring.prometheus:
            stack.monitoring.prometheus['retention_days'] = global_defaults.monitoring.retention_days
        
        # Apply global backup retention if not specified
        if stack.backup.enabled and not stack.backup.retention_days:
            stack.backup.retention_days = global_defaults.backup.retention_days
    
    return config


def print_validation_warnings(config: SystemConfig):
    """Print any validation warnings for the configuration.
    
    Args:
        config: Validated SystemConfig
    """
    from .validators import (
        validate_resource_allocation,
        validate_cloud_sql_tier_for_environment,
        validate_backup_configuration,
        validate_monitoring_configuration,
        validate_network_configuration,
        check_version_compatibility
    )
    
    warnings = []
    
    for stack_name, stack in config.stacks.items():
        if not stack.enabled:
            continue
        
        # Check resource allocations
        resource_warnings = validate_resource_allocation(
            stack.superset.resources.cpu,
            stack.superset.resources.memory,
            stack.type
        )
        for warning in resource_warnings:
            warnings.append(f"Stack '{stack_name}': {warning}")
        
        # Check Cloud SQL tier
        if stack.database.type == 'cloud-sql' and stack.database.tier:
            tier_warnings = validate_cloud_sql_tier_for_environment(
                stack.database.tier,
                stack.database.high_availability,
                stack.type
            )
            for warning in tier_warnings:
                warnings.append(f"Stack '{stack_name}': {warning}")
        
        # Check backup configuration
        backup_warnings = validate_backup_configuration(
            stack.backup.model_dump(),
            stack.type
        )
        for warning in backup_warnings:
            warnings.append(f"Stack '{stack_name}': {warning}")
        
        # Check monitoring configuration
        monitoring_warnings = validate_monitoring_configuration(
            stack.monitoring.model_dump(),
            stack.type
        )
        for warning in monitoring_warnings:
            warnings.append(f"Stack '{stack_name}': {warning}")
        
        # Check network configuration
        if stack.security and stack.security.vpc:
            network_warnings = validate_network_configuration(
                stack.security.vpc.model_dump(),
                stack.type
            )
            for warning in network_warnings:
                warnings.append(f"Stack '{stack_name}': {warning}")
        
        # Check version compatibility with plugins
        if stack.superset.plugins:
            compat_warnings = check_version_compatibility(
                stack.superset.version,
                stack.superset.plugins
            )
            for warning in compat_warnings:
                warnings.append(f"Stack '{stack_name}': {warning}")
        
        # Check sensitive fields for security issues
        if stack.database.password:
            security_warnings = validate_sensitive_field(
                'password',
                stack.database.password,
                stack.type
            )
            for warning in security_warnings:
                warnings.append(f"Stack '{stack_name}' database: {warning}")
        
        if stack.cache.password:
            security_warnings = validate_sensitive_field(
                'password',
                stack.cache.password,
                stack.type
            )
            for warning in security_warnings:
                warnings.append(f"Stack '{stack_name}' cache: {warning}")
        
        # Check Cloudflare credentials
        if stack.cloudflare.enabled and stack.cloudflare.tunnel_secret:
            security_warnings = validate_sensitive_field(
                'token',
                stack.cloudflare.tunnel_secret,
                stack.type
            )
            for warning in security_warnings:
                warnings.append(f"Stack '{stack_name}' Cloudflare: {warning}")
    
    # Print warnings if any
    if warnings:
        print("\n⚠️  Configuration warnings:")
        for warning in warnings:
            print(f"  • {warning}")
        print()


def get_env_value(key: str, default: Any = None) -> Any:
    """Get value from environment variable with optional default.
    
    Args:
        key: Environment variable name
        default: Default value if not set
        
    Returns:
        Environment variable value or default
    """
    return os.environ.get(key, default)