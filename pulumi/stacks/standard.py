"""Standard stack implementation for staging/development on GCP."""

import pulumi
from pulumi import Output
import pulumi_gcp as gcp
from typing import Dict, Any

from .base import BaseStack
from ..components.database import CloudSQLDatabase
from ..components.cache import RedisCache
from ..components.superset import SupersetCloudRun
from ..components.security import SecurityManager
from ..components.cloudflare import CloudflareTunnel


class StandardStack(BaseStack):
    """Standard stack with PostgreSQL and Redis on GCP."""
    
    def deploy(self) -> Dict[str, Any]:
        """Deploy standard stack on GCP."""
        pulumi.log.info(f"Deploying standard stack: {self.name}")
        
        # Get GCP configuration
        gcp_config = self.config.get('gcp', {})
        project_id = gcp_config.get('project_id')
        region = gcp_config.get('region', 'us-central1')
        zone = gcp_config.get('zone', f'{region}-a')
        
        if not project_id:
            raise ValueError("GCP project_id is required for standard stack")
        
        # Create network if not using default
        network = None
        subnet = None
        if self.config.get('security', {}).get('vpc', {}).get('enabled', False):
            network = gcp.compute.Network(
                self.get_resource_name('network'),
                name=self.get_resource_name('network'),
                auto_create_subnetworks=False,
                project=project_id
            )
            
            subnet = gcp.compute.Subnetwork(
                self.get_resource_name('subnet'),
                name=self.get_resource_name('subnet'),
                network=network.id,
                ip_cidr_range='10.0.0.0/24',
                region=region,
                project=project_id
            )
        
        # Deploy database
        db_config = self.config.get('database', {})
        database = CloudSQLDatabase(
            name=self.get_resource_name('db'),
            config=db_config,
            project_id=project_id,
            region=region,
            network=network,
            labels=self.get_labels()
        )
        db_outputs = database.deploy()
        
        # Deploy cache
        cache_config = self.config.get('cache', {})
        if cache_config.get('type') == 'redis':
            cache = RedisCache(
                name=self.get_resource_name('redis'),
                config=cache_config,
                project_id=project_id,
                region=region,
                network=network,
                labels=self.get_labels()
            )
            cache_outputs = cache.deploy()
        else:
            cache_outputs = {'url': None}
        
        # Deploy security components
        security_config = self.config.get('security', {})
        security = SecurityManager(
            name=self.get_resource_name('security'),
            config=security_config,
            project_id=project_id,
            labels=self.get_labels()
        )
        security_outputs = security.deploy()
        
        # Deploy Superset on Cloud Run
        superset = SupersetCloudRun(
            name=self.get_resource_name('superset'),
            config=self.superset_config,
            project_id=project_id,
            region=region,
            database_url=db_outputs['connection_string'],
            redis_url=cache_outputs.get('url'),
            secret_key=security_outputs['secret_key'],
            network=network,
            subnet=subnet,
            labels=self.get_labels()
        )
        superset_outputs = superset.deploy()
        
        # Deploy Cloudflare Tunnel if enabled
        cloudflare_outputs = {}
        cloudflare_config = self.config.get('cloudflare', {})
        if cloudflare_config.get('enabled', False):
            # Configure additional routes for monitoring if enabled
            additional_routes = []
            if self.config.get('monitoring', {}).get('enabled', False):
                additional_routes.extend([
                    {
                        'hostname': cloudflare_config.get('monitoring_hostname', f'monitoring-{self.name}.example.com'),
                        'service': 'http://grafana:3000'
                    },
                    {
                        'hostname': cloudflare_config.get('metrics_hostname', f'metrics-{self.name}.example.com'),
                        'service': 'http://prometheus:9090'
                    }
                ])
            
            cloudflare = CloudflareTunnel(
                name=self.get_resource_name('cloudflare'),
                config=cloudflare_config,
                project_id=project_id,
                region=region,
                target_service=superset_outputs['url'],
                additional_routes=additional_routes,
                labels=self.get_labels()
            )
            cloudflare_outputs = cloudflare.deploy()
        
        # Export outputs
        self.export_outputs({
            'environment': 'gcp',
            'project_id': project_id,
            'region': region,
            'superset_url': superset_outputs['url'],
            'superset_service': superset_outputs['service_name'],
            'database_instance': db_outputs['instance_name'],
            'database_connection_name': db_outputs['connection_name'],
            'cache_instance': cache_outputs.get('instance_name'),
            'cloudflare_tunnel': cloudflare_outputs.get('tunnel_name'),
            'cloudflare_hostnames': cloudflare_outputs.get('hostnames', []),
            'access_url': cloudflare_outputs.get('hostnames', [None])[0] if cloudflare_config.get('enabled') else superset_outputs['url'],
            'instructions': Output.concat(
                'Standard stack deployed successfully!\n',
                'Superset URL: ', superset_outputs['url'], '\n',
                'To view logs: gcloud run services logs read ', superset_outputs['service_name'],
                ' --project=', project_id
            )
        })
        
        return self.outputs