"""Minimal stack implementation for local development."""

import pulumi
from pulumi import Output
from typing import Dict, Any

from .base import BaseStack


class MinimalStack(BaseStack):
    """Minimal stack for local development with SQLite."""
    
    def deploy(self) -> Dict[str, Any]:
        """Deploy minimal stack (local Docker only)."""
        pulumi.log.info(f"Deploying minimal stack: {self.name}")
        
        # For minimal stack, we primarily rely on docker-compose
        # Pulumi just manages configuration and outputs
        
        # Get configuration
        superset_port = self.superset_config.get('port', 8088)
        superset_version = self.superset_config.get('version', '3.0.0')
        
        # Export configuration for docker-compose
        self.export_outputs({
            'environment': 'local',
            'superset_url': f'http://localhost:{superset_port}',
            'superset_version': superset_version,
            'database_type': 'sqlite',
            'cache_type': 'none',
            'instructions': Output.concat(
                'To start the local development environment:\n',
                '1. Run: make dev\n',
                '2. Access Superset at: http://localhost:', str(superset_port), '\n',
                '3. Default credentials: admin/admin\n',
                '4. To stop: make dev-down'
            )
        })
        
        return self.outputs