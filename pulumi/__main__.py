"""Main Pulumi program for Apache Superset deployment."""

import os
import sys
import pulumi
from pulumi import Config
import yaml

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.loader import load_system_config
from config.validator import validate_stack_config
from stacks.minimal import MinimalStack
from stacks.standard import StandardStack
from stacks.production import ProductionStack


def main():
    """Main entry point for Pulumi deployment."""
    # Get configuration
    config = Config()
    env = config.require("environment")
    
    # Load system configuration
    system_config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "system.yaml"
    )
    
    if not os.path.exists(system_config_path):
        raise FileNotFoundError(
            f"system.yaml not found at {system_config_path}. "
            "Please create it from system.yaml.example"
        )
    
    system_config = load_system_config(system_config_path)
    
    # Get stack configuration
    stack_name = pulumi.get_stack()
    env_name = stack_name.split("-")[-1]  # Extract env from stack name
    
    if env_name not in system_config.stacks:
        raise ValueError(f"Stack '{env_name}' not found in system.yaml")
    
    stack_config = system_config.stacks[env_name]
    
    # Validate configuration
    validation_errors = validate_stack_config(stack_config)
    if validation_errors:
        raise ValueError(f"Configuration validation failed: {validation_errors}")
    
    # Check if stack is enabled
    if not stack_config.get("enabled", True):
        pulumi.log.warn(f"Stack '{env_name}' is disabled in system.yaml")
        return
    
    # Deploy appropriate stack based on type
    stack_type = stack_config.get("type", "minimal")
    
    pulumi.log.info(f"Deploying {stack_type} stack for {env_name} environment")
    
    if stack_type == "minimal":
        stack = MinimalStack(env_name, stack_config, system_config.global_config)
    elif stack_type == "standard":
        stack = StandardStack(env_name, stack_config, system_config.global_config)
    elif stack_type == "production":
        stack = ProductionStack(env_name, stack_config, system_config.global_config)
    else:
        raise ValueError(f"Unknown stack type: {stack_type}")
    
    # Export stack outputs
    outputs = stack.deploy()
    for key, value in outputs.items():
        pulumi.export(key, value)


if __name__ == "__main__":
    main()