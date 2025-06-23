"""Configuration loader for system.yaml."""

import os
import yaml
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class SystemConfig:
    """System configuration container."""
    global_config: Dict[str, Any]
    stacks: Dict[str, Dict[str, Any]]


def load_system_config(config_path: str) -> SystemConfig:
    """Load and parse system.yaml configuration."""
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Process stack inheritance
    stacks = data.get('stacks', {})
    processed_stacks = {}
    
    for stack_name, stack_config in stacks.items():
        # Handle inheritance
        if 'extends' in stack_config:
            parent_name = stack_config['extends']
            if parent_name not in stacks:
                raise ValueError(f"Parent stack '{parent_name}' not found for '{stack_name}'")
            
            # Deep merge parent and child configs
            parent_config = stacks[parent_name].copy()
            merged_config = deep_merge(parent_config, stack_config)
            merged_config.pop('extends', None)  # Remove extends key
            processed_stacks[stack_name] = merged_config
        else:
            processed_stacks[stack_name] = stack_config
    
    return SystemConfig(
        global_config=data.get('global', {}),
        stacks=processed_stacks
    )


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def get_env_value(key: str, default: Any = None) -> Any:
    """Get value from environment variable with optional default."""
    return os.environ.get(key, default)