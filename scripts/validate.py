#!/usr/bin/env python3
"""Validate system.yaml configuration."""

import sys
import os
from pathlib import Path
from pydantic import ValidationError

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from pulumi.config.loader import load_system_config


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
        # Load and validate configuration using Pydantic
        config = load_system_config(str(config_path))
        
        print("✅ Configuration is valid!")
        
        # Show configuration summary
        print("\n📊 Configuration Summary:")
        print(f"  Global Superset version: {config.global_config.superset.default_version}")
        print(f"  Number of stacks: {len(config.stacks)}")
        
        # Show enabled stacks
        enabled_stacks = config.get_enabled_stacks()
        
        if enabled_stacks:
            print(f"\n📦 Enabled stacks:")
            for name, stack in enabled_stacks.items():
                print(f"  • {name}:")
                print(f"    - Type: {stack.type}")
                print(f"    - Environment: {stack.environment}")
                print(f"    - Superset version: {stack.superset.version}")
                if stack.environment == 'gcp':
                    print(f"    - GCP project: {stack.gcp.project_id}")
                    print(f"    - GCP region: {stack.gcp.region}")
        else:
            print("\n⚠️  Warning: No stacks are enabled")
            
        # Show any validation warnings
        print("\n💡 Note: Check console output above for any configuration warnings")
            
    except ValidationError as e:
        print("\n❌ Validation failed with the following errors:")
        for error in e.errors():
            field_path = " -> ".join(str(x) for x in error['loc'])
            print(f"  • {field_path}: {error['msg']}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()