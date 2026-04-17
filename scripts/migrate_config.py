#!/usr/bin/env python3
"""Configuration migration tool for Apache Superset deployment.

This tool helps migrate from old configuration formats to the new Pydantic-based format.
"""

import argparse
import json
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from pulumi.config.loader import load_system_config
from pulumi.config.models import SystemConfig
from pydantic import ValidationError


def migrate_v1_to_v2(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate from v1 (simple) to v2 (Pydantic) configuration format.
    
    Args:
        old_config: Old configuration dictionary
        
    Returns:
        Migrated configuration dictionary
    """
    new_config = {
        'global': {
            'superset': {
                'default_version': old_config.get('default_superset_version', '3.0.0'),
                'default_admin_email': old_config.get('default_admin_email', 'admin@example.com')
            },
            'monitoring': {
                'retention_days': old_config.get('monitoring_retention_days', 30)
            },
            'backup': {
                'retention_days': old_config.get('backup_retention_days', 7)
            }
        },
        'stacks': {}
    }
    
    # Migrate stacks
    for stack_name, stack_config in old_config.get('stacks', {}).items():
        new_stack = {
            'type': stack_config.get('type', 'minimal'),
            'environment': stack_config.get('environment', 'local'),
            'enabled': stack_config.get('enabled', True)
        }
        
        # GCP configuration
        if stack_config.get('environment') == 'gcp':
            new_stack['gcp'] = {
                'project_id': stack_config.get('gcp_project_id', ''),
                'region': stack_config.get('gcp_region', 'us-central1'),
                'zone': stack_config.get('gcp_zone'),
                'credentials_path': stack_config.get('gcp_credentials_path'),
                'service_account': stack_config.get('gcp_service_account')
            }
        
        # Superset configuration
        new_stack['superset'] = {
            'version': stack_config.get('superset_version'),
            'port': stack_config.get('superset_port', 8088),
            'replicas': stack_config.get('replicas', 1),
            'dev_mode': stack_config.get('dev_mode', False)
        }
        
        # Resources
        if 'resources' in stack_config:
            new_stack['superset']['resources'] = {
                'cpu': stack_config['resources'].get('cpu', '1'),
                'memory': stack_config['resources'].get('memory', '2Gi')
            }
        
        # Autoscaling
        if 'autoscaling' in stack_config:
            new_stack['superset']['autoscaling'] = {
                'enabled': stack_config['autoscaling'].get('enabled', False),
                'min_replicas': stack_config['autoscaling'].get('min_replicas', 1),
                'max_replicas': stack_config['autoscaling'].get('max_replicas', 10),
                'cpu_threshold': stack_config['autoscaling'].get('cpu_threshold', 70)
            }
        
        # Database configuration
        db_type = stack_config.get('database_type', 'sqlite')
        new_stack['database'] = {
            'type': db_type
        }
        
        if db_type == 'sqlite':
            new_stack['database']['path'] = stack_config.get('sqlite_path', './data/superset.db')
        elif db_type in ['postgresql', 'cloud-sql']:
            new_stack['database'].update({
                'host': stack_config.get('database_host'),
                'port': stack_config.get('database_port', 5432),
                'name': stack_config.get('database_name', 'superset'),
                'user': stack_config.get('database_user', 'superset'),
                'password': stack_config.get('database_password')
            })
            
            if db_type == 'cloud-sql':
                new_stack['database'].update({
                    'tier': stack_config.get('cloud_sql_tier', 'db-f1-micro'),
                    'disk_size': stack_config.get('disk_size', 10),
                    'disk_type': stack_config.get('disk_type', 'pd-standard'),
                    'high_availability': stack_config.get('high_availability', False)
                })
                
                if 'backup' in stack_config:
                    new_stack['database']['backup'] = {
                        'enabled': stack_config['backup'].get('enabled', True),
                        'time': stack_config['backup'].get('time', '02:00'),
                        'retention_days': stack_config['backup'].get('retention_days', 7)
                    }
        
        # Cache configuration
        cache_type = stack_config.get('cache_type', 'none')
        new_stack['cache'] = {
            'type': cache_type
        }
        
        if cache_type in ['redis', 'memcached']:
            new_stack['cache'].update({
                'host': stack_config.get('cache_host'),
                'port': stack_config.get('cache_port', 6379 if cache_type == 'redis' else 11211),
                'password': stack_config.get('cache_password'),
                'tier': stack_config.get('cache_tier', 'basic'),
                'memory_size_gb': stack_config.get('cache_memory_size_gb', 1),
                'high_availability': stack_config.get('cache_high_availability', False)
            })
        
        # Security configuration
        new_stack['security'] = {
            'ssl': {
                'enabled': stack_config.get('ssl_enabled', True),
                'managed': stack_config.get('ssl_managed', True),
                'domains': stack_config.get('ssl_domains', [])
            },
            'oauth': {
                'enabled': stack_config.get('oauth_enabled', False),
                'providers': stack_config.get('oauth_providers', [])
            },
            'vpc': {
                'enabled': stack_config.get('vpc_enabled', False),
                'private_ip': stack_config.get('vpc_private_ip', True),
                'cidr_range': stack_config.get('vpc_cidr_range', '10.0.0.0/16')
            },
            'secrets_backend': stack_config.get('secrets_backend', 'local')
        }
        
        # Cloudflare configuration
        if 'cloudflare' in stack_config:
            cf = stack_config['cloudflare']
            new_stack['cloudflare'] = {
                'enabled': cf.get('enabled', False),
                'tunnel_name': cf.get('tunnel_name'),
                'tunnel_id': cf.get('tunnel_id'),
                'tunnel_secret': cf.get('tunnel_secret'),
                'account_id': cf.get('account_id'),
                'hostname': cf.get('hostname'),
                'monitoring_hostname': cf.get('monitoring_hostname'),
                'metrics_hostname': cf.get('metrics_hostname'),
                'deployment_type': cf.get('deployment_type', 'cloudrun'),
                'access_policies': cf.get('access_policies', [])
            }
        
        # Monitoring configuration
        if 'monitoring' in stack_config:
            mon = stack_config['monitoring']
            new_stack['monitoring'] = {
                'enabled': mon.get('enabled', False),
                'prometheus': mon.get('prometheus', {}),
                'grafana': mon.get('grafana', {}),
                'alerting': mon.get('alerting', {})
            }
        
        # Backup configuration
        if 'backup' in stack_config and stack_config['backup'].get('enabled'):
            new_stack['backup'] = {
                'enabled': True,
                'frequency': stack_config['backup'].get('frequency', '0 2 * * *'),
                'destination': stack_config['backup'].get('destination'),
                'retention_days': stack_config['backup'].get('retention_days', 30)
            }
        
        new_config['stacks'][stack_name] = new_stack
    
    return new_config


def validate_migrated_config(config_dict: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate the migrated configuration.
    
    Args:
        config_dict: Configuration dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Try to create SystemConfig object
        config = SystemConfig(**config_dict)
        return True, None
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field_path = " -> ".join(str(x) for x in error['loc'])
            errors.append(f"{field_path}: {error['msg']}")
        return False, "\n".join(errors)


def main():
    parser = argparse.ArgumentParser(
        description='Migrate Apache Superset deployment configuration to new format'
    )
    parser.add_argument(
        'input_file',
        help='Path to old configuration file'
    )
    parser.add_argument(
        '-o', '--output',
        default='system.yaml',
        help='Output file path (default: system.yaml)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate migration without writing output'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Create backup of existing output file'
    )
    parser.add_argument(
        '--format',
        choices=['yaml', 'json'],
        default='yaml',
        help='Output format (default: yaml)'
    )
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Load old configuration
    try:
        with open(args.input_file, 'r') as f:
            if args.input_file.endswith('.json'):
                old_config = json.load(f)
            else:
                old_config = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading input file: {e}")
        sys.exit(1)
    
    # Migrate configuration
    print("Migrating configuration...")
    new_config = migrate_v1_to_v2(old_config)
    
    # Validate migrated configuration
    print("Validating migrated configuration...")
    is_valid, error_msg = validate_migrated_config(new_config)
    
    if not is_valid:
        print("\n❌ Validation failed:")
        print(error_msg)
        print("\nThe migrated configuration has validation errors.")
        print("Please fix these issues manually in the output file.")
        
        if not args.dry_run:
            response = input("\nDo you want to save the file anyway? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)
    else:
        print("✅ Configuration validated successfully!")
    
    # Handle dry run
    if args.dry_run:
        print("\nDry run - no files written.")
        print("\nMigrated configuration:")
        if args.format == 'json':
            print(json.dumps(new_config, indent=2))
        else:
            print(yaml.dump(new_config, default_flow_style=False, sort_keys=False))
        return
    
    # Backup existing file if requested
    if args.backup and os.path.exists(args.output):
        backup_path = f"{args.output}.backup"
        print(f"Creating backup: {backup_path}")
        os.rename(args.output, backup_path)
    
    # Write output file
    try:
        with open(args.output, 'w') as f:
            if args.format == 'json':
                json.dump(new_config, f, indent=2)
            else:
                yaml.dump(new_config, f, default_flow_style=False, sort_keys=False)
        
        print(f"\n✅ Configuration migrated successfully to: {args.output}")
        
        # Print next steps
        print("\nNext steps:")
        print("1. Review the migrated configuration")
        print("2. Update any environment variable references")
        print("3. Test with: make validate")
        print("4. Deploy with: make deploy ENV=<environment>")
        
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()