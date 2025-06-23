"""Database component for Cloud SQL deployment."""

import pulumi
import pulumi_gcp as gcp
from typing import Dict, Any, Optional


class CloudSQLDatabase:
    """Cloud SQL PostgreSQL database component."""
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        project_id: str,
        region: str,
        network: Optional[gcp.compute.Network] = None,
        labels: Dict[str, str] = None
    ):
        """Initialize Cloud SQL database component."""
        self.name = name
        self.config = config
        self.project_id = project_id
        self.region = region
        self.network = network
        self.labels = labels or {}
        
    def deploy(self) -> Dict[str, Any]:
        """Deploy Cloud SQL instance and return connection details."""
        # Database instance configuration
        tier = self.config.get('tier', 'db-f1-micro')
        disk_size = self.config.get('disk_size', 10)
        disk_type = self.config.get('disk_type', 'pd-standard')
        high_availability = self.config.get('high_availability', False)
        
        # Create Cloud SQL instance
        instance = gcp.sql.DatabaseInstance(
            self.name,
            name=self.name,
            database_version='POSTGRES_15',
            region=self.region,
            project=self.project_id,
            settings={
                'tier': tier,
                'disk_size': disk_size,
                'disk_type': disk_type,
                'disk_autoresize': True,
                'disk_autoresize_limit': disk_size * 10,  # 10x initial size
                'backup_configuration': {
                    'enabled': self.config.get('backup', {}).get('enabled', True),
                    'start_time': self.config.get('backup', {}).get('time', '02:00'),
                    'location': self.config.get('backup', {}).get('location', self.region),
                    'point_in_time_recovery_enabled': high_availability,
                    'transaction_log_retention_days': 7 if high_availability else 1,
                },
                'ip_configuration': {
                    'ipv4_enabled': not bool(self.network),  # Public IP only if no VPC
                    'private_network': self.network.id if self.network else None,
                    'authorized_networks': [] if self.network else [{
                        'name': 'allow-all',
                        'value': '0.0.0.0/0'  # WARNING: For development only!
                    }],
                },
                'availability_type': 'REGIONAL' if high_availability else 'ZONAL',
                'user_labels': self.labels,
                'insights_config': {
                    'query_insights_enabled': True,
                    'query_string_length': 1024,
                    'record_application_tags': True,
                    'record_client_address': True,
                },
            },
            deletion_protection=high_availability,  # Protect production databases
        )
        
        # Create database
        database = gcp.sql.Database(
            f'{self.name}-db',
            name='superset',
            instance=instance.name,
            project=self.project_id,
        )
        
        # Create user
        user = gcp.sql.User(
            f'{self.name}-user',
            name='superset',
            instance=instance.name,
            password=pulumi.Output.secret('superset-db-password'),  # Should use secret manager
            project=self.project_id,
        )
        
        # Build connection string
        if self.network:
            # Private IP connection
            connection_string = pulumi.Output.all(
                instance.private_ip_address,
                database.name,
                user.name,
                user.password
            ).apply(
                lambda args: f'postgresql://{args[2]}:{args[3]}@{args[0]}:5432/{args[1]}'
            )
        else:
            # Public IP connection
            connection_string = pulumi.Output.all(
                instance.public_ip_address,
                database.name,
                user.name,
                user.password
            ).apply(
                lambda args: f'postgresql://{args[2]}:{args[3]}@{args[0]}:5432/{args[1]}'
            )
        
        return {
            'instance_name': instance.name,
            'connection_name': instance.connection_name,
            'connection_string': connection_string,
            'database_name': database.name,
            'username': user.name,
        }