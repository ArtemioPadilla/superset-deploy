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
                    'authorized_networks': [] if self.network else self._get_authorized_networks(),
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
        
        # Generate or retrieve password from Secret Manager
        password = self._get_or_create_db_password()
        
        # Create user
        user = gcp.sql.User(
            f'{self.name}-user',
            name='superset',
            instance=instance.name,
            password=password,
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
    
    def _get_authorized_networks(self):
        """Get authorized networks for Cloud SQL instance."""
        # Check if we have specific IPs configured
        allowed_ips = self.config.get('allowed_ips', [])
        
        if allowed_ips:
            # Use configured IPs
            return [
                {'name': f'allowed-{i}', 'value': ip}
                for i, ip in enumerate(allowed_ips)
            ]
        else:
            # For development, allow current IP only
            # In production, this should be empty or use specific IPs
            import urllib.request
            try:
                # Get current public IP
                current_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
                pulumi.log.warn(f"Allowing access from current IP only: {current_ip}/32")
                return [{
                    'name': 'current-ip',
                    'value': f'{current_ip}/32'
                }]
            except:
                # If we can't get current IP, don't allow any public access
                pulumi.log.warn("Could not determine current IP. No public access will be allowed.")
                return []
    
    def _get_or_create_db_password(self):
        """Generate or retrieve database password from Secret Manager."""
        # Import here to avoid circular dependency
        from pulumi_gcp import secretmanager
        import secrets
        import string
        
        # Generate a secure password
        alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
        password = ''.join(secrets.choice(alphabet) for _ in range(32))
        
        # Create secret in Secret Manager
        secret = secretmanager.Secret(
            f'{self.name}-db-password-secret',
            secret_id=f'{self.name}-db-password',
            project=self.project_id,
            replication=secretmanager.SecretReplicationArgs(
                automatic=secretmanager.SecretReplicationAutomaticArgs()
            ),
            labels=self.labels,
        )
        
        # Create secret version
        secret_version = secretmanager.SecretVersion(
            f'{self.name}-db-password-version',
            secret=secret.id,
            secret_data=password,
        )
        
        # Return the secret value
        return pulumi.Output.secret(password)