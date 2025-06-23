#!/usr/bin/env python3
"""Validate system.yaml configuration."""

import sys
import os
import yaml
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from pulumi.config.validator import validate_system_config


def main():
    """Main validation function."""
    # Find system.yaml
    config_path = Path(__file__).parent.parent / "system.yaml"
    
    if not config_path.exists():
        print(f"❌ Error: system.yaml not found at {config_path}")
        print("💡 Tip: Copy system.yaml.example to system.yaml and configure it")
        sys.exit(1)
    
    print(f"🔍 Validating {config_path}...")
    
    try:
        # Load configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate
        errors = validate_system_config(config)
        
        if errors:
            print("\n❌ Validation failed with the following errors:")
            for error in errors:
                print(f"  • {error}")
            sys.exit(1)
        else:
            print("✅ Configuration is valid!")
            
            # Show enabled stacks
            stacks = config.get('stacks', {})
            enabled_stacks = [
                name for name, stack in stacks.items() 
                if stack.get('enabled', True)
            ]
            
            if enabled_stacks:
                print(f"\n📦 Enabled stacks: {', '.join(enabled_stacks)}")
            else:
                print("\n⚠️  Warning: No stacks are enabled")
            
    except yaml.YAMLError as e:
        print(f"❌ Error: Invalid YAML syntax: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()