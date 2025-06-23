"""Security component for managing secrets, SSL, and authentication."""

import pulumi
import pulumi_gcp as gcp
from typing import Dict, Any
import secrets
import base64


class SecurityManager:
    """Security manager for secrets, SSL certificates, and authentication."""
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        project_id: str,
        labels: Dict[str, str] = None
    ):
        """Initialize security manager."""
        self.name = name
        self.config = config
        self.project_id = project_id
        self.labels = labels or {}
        
    def deploy(self) -> Dict[str, Any]:
        """Deploy security resources and return outputs."""
        outputs = {}
        
        # Generate or retrieve Superset secret key
        secret_key = self._manage_secret_key()
        outputs['secret_key'] = secret_key
        
        # Set up SSL if enabled
        ssl_config = self.config.get('ssl', {})
        if ssl_config.get('enabled', False):
            ssl_outputs = self._setup_ssl(ssl_config)
            outputs.update(ssl_outputs)
        
        # Set up OAuth if enabled
        oauth_config = self.config.get('oauth', {})
        if oauth_config.get('enabled', False):
            oauth_outputs = self._setup_oauth(oauth_config)
            outputs.update(oauth_outputs)
        
        return outputs
    
    def _manage_secret_key(self) -> pulumi.Output[str]:
        """Generate and store Superset secret key in Secret Manager."""
        # Generate a secure secret key
        secret_value = base64.b64encode(secrets.token_bytes(32)).decode('utf-8')
        
        # Create secret in Secret Manager
        secret = gcp.secretmanager.Secret(
            f'{self.name}-superset-key',
            secret_id=f'{self.name}-superset-key',
            project=self.project_id,
            labels=self.labels,
            replication={
                'automatic': {}
            }
        )
        
        # Create secret version
        secret_version = gcp.secretmanager.SecretVersion(
            f'{self.name}-superset-key-version',
            secret=secret.id,
            secret_data=secret_value,
        )
        
        # Return the secret value (marked as secret in Pulumi)
        return pulumi.Output.secret(secret_value)
    
    def _setup_ssl(self, ssl_config: Dict[str, Any]) -> Dict[str, Any]:
        """Set up SSL certificates."""
        outputs = {}
        
        if ssl_config.get('managed', True):
            # Use Google-managed SSL certificate
            cert = gcp.compute.ManagedSslCertificate(
                f'{self.name}-ssl-cert',
                name=f'{self.name}-ssl-cert',
                project=self.project_id,
                managed={
                    'domains': ssl_config.get('domains', [f'{self.name}.example.com'])
                }
            )
            outputs['ssl_certificate'] = cert.id
            outputs['ssl_certificate_name'] = cert.name
        
        return outputs
    
    def _setup_oauth(self, oauth_config: Dict[str, Any]) -> Dict[str, Any]:
        """Set up OAuth configuration."""
        outputs = {}
        providers = oauth_config.get('providers', [])
        
        # Store OAuth secrets
        for provider in providers:
            if provider == 'google':
                # Google OAuth secrets would typically come from environment
                # or be manually configured in Secret Manager
                outputs['oauth_google_configured'] = True
            elif provider == 'github':
                outputs['oauth_github_configured'] = True
        
        return outputs