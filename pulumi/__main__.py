"""Main Pulumi program for Apache Superset deployment."""

import os
import sys
import pulumi
from pulumi import Config
from pydantic import ValidationError

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.loader import load_system_config
from stacks.minimal import MinimalStack
from stacks.standard import StandardStack
from stacks.production import ProductionStack


def main():
    """Main entry point for Pulumi deployment."""
    # Get configuration
    config = Config()
    env = config.require("environment")
    
    try:
        # Load system configuration with Pydantic validation
        system_config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "system.yaml"
        )
        
        if not os.path.exists(system_config_path):
            raise FileNotFoundError(
                f"system.yaml not found at {system_config_path}. "
                "Please create it from system.yaml.example"
            )
        
        # Load and validate configuration
        system_config = load_system_config(system_config_path)
        
        # Get stack configuration
        stack_name = pulumi.get_stack()
        env_name = stack_name.split("-")[-1]  # Extract env from stack name
        
        stack = system_config.get_stack(env_name)
        if not stack:
            raise ValueError(f"Stack '{env_name}' not found in system.yaml")
        
        # Check if stack is enabled
        if not stack.enabled:
            pulumi.log.warn(f"Stack '{env_name}' is disabled in system.yaml")
            return
            
        # Log deployment information
        pulumi.log.info(f"Deploying stack '{env_name}':")
        pulumi.log.info(f"  Type: {stack.type}")
        pulumi.log.info(f"  Environment: {stack.environment}")
        pulumi.log.info(f"  Superset Version: {stack.superset.version}")
        if stack.environment == 'gcp':
            pulumi.log.info(f"  GCP Project: {stack.gcp.project_id}")
            pulumi.log.info(f"  GCP Region: {stack.gcp.region}")
    
        # Deploy appropriate stack based on type
        pulumi.log.info(f"Deploying {stack.type} stack for {env_name} environment")
        
        # Convert Pydantic model to dict for legacy compatibility
        stack_dict = stack.dict()
        global_dict = system_config.global_config.dict()
        
        if stack.type == "minimal":
            stack_instance = MinimalStack(env_name, stack_dict, global_dict)
        elif stack.type == "standard":
            stack_instance = StandardStack(env_name, stack_dict, global_dict)
        elif stack.type == "production":
            stack_instance = ProductionStack(env_name, stack_dict, global_dict)
        else:
            raise ValueError(f"Unknown stack type: {stack.type}")
        
        # Export stack outputs
        outputs = stack_instance.deploy()
        for key, value in outputs.items():
            pulumi.export(key, value)
            
    except ValidationError as e:
        pulumi.log.error("Configuration validation failed:")
        for error in e.errors():
            field_path = " -> ".join(str(x) for x in error['loc'])
            pulumi.log.error(f"  {field_path}: {error['msg']}")
        raise
    except Exception as e:
        pulumi.log.error(f"Deployment failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()