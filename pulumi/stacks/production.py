"""Production stack implementation with full features."""

import pulumi
from pulumi import Output
import pulumi_gcp as gcp
from typing import Dict, Any

from .base import BaseStack
from ..components.database import CloudSQLDatabase
from ..components.cache import RedisCache
from ..components.superset import SupersetGKE
from ..components.monitoring import MonitoringStack
from ..components.security import SecurityManager
from ..components.cloudflare import CloudflareTunnel


class ProductionStack(BaseStack):
    """Production stack with high availability, monitoring, and backups."""
    
    def deploy(self) -> Dict[str, Any]:
        """Deploy production stack on GCP with GKE."""
        pulumi.log.info(f"Deploying production stack: {self.name}")
        
        # Get GCP configuration
        gcp_config = self.config.get('gcp', {})
        project_id = gcp_config.get('project_id')
        region = gcp_config.get('region', 'us-central1')
        zone = gcp_config.get('zone', f'{region}-a')
        
        if not project_id:
            raise ValueError("GCP project_id is required for production stack")
        
        # Create VPC network
        network = gcp.compute.Network(
            self.get_resource_name('network'),
            name=self.get_resource_name('network'),
            auto_create_subnetworks=False,
            project=project_id
        )
        
        # Create subnets
        subnet = gcp.compute.Subnetwork(
            self.get_resource_name('subnet'),
            name=self.get_resource_name('subnet'),
            network=network.id,
            ip_cidr_range='10.0.0.0/20',
            region=region,
            project=project_id,
            secondary_ip_ranges=[
                {
                    'rangeName': 'pods',
                    'ipCidrRange': '10.1.0.0/16'
                },
                {
                    'rangeName': 'services',
                    'ipCidrRange': '10.2.0.0/20'
                }
            ]
        )
        
        # Deploy security components
        security_config = self.config.get('security', {})
        security = SecurityManager(
            name=self.get_resource_name('security'),
            config=security_config,
            project_id=project_id,
            labels=self.get_labels()
        )
        security_outputs = security.deploy()
        
        # Deploy database with HA
        db_config = self.config.get('database', {})
        db_config['high_availability'] = True
        database = CloudSQLDatabase(
            name=self.get_resource_name('db'),
            config=db_config,
            project_id=project_id,
            region=region,
            network=network,
            labels=self.get_labels()
        )
        db_outputs = database.deploy()
        
        # Deploy cache with HA
        cache_config = self.config.get('cache', {})
        cache_config['high_availability'] = True
        cache = RedisCache(
            name=self.get_resource_name('redis'),
            config=cache_config,
            project_id=project_id,
            region=region,
            network=network,
            labels=self.get_labels()
        )
        cache_outputs = cache.deploy()
        
        # Create GKE cluster
        cluster = gcp.container.Cluster(
            self.get_resource_name('gke'),
            name=self.get_resource_name('gke'),
            location=region,
            initial_node_count=1,
            remove_default_node_pool=True,
            network=network.name,
            subnetwork=subnet.name,
            ip_allocation_policy={
                'cluster_secondary_range_name': 'pods',
                'services_secondary_range_name': 'services'
            },
            private_cluster_config={
                'enable_private_nodes': True,
                'enable_private_endpoint': False,
                'master_ipv4_cidr_block': '172.16.0.0/28'
            },
            master_auth={
                'client_certificate_config': {
                    'issue_client_certificate': False
                }
            },
            workload_identity_config={
                'workload_pool': f'{project_id}.svc.id.goog'
            },
            project=project_id
        )
        
        # Create node pool
        node_pool = gcp.container.NodePool(
            self.get_resource_name('node-pool'),
            name=self.get_resource_name('node-pool'),
            cluster=cluster.name,
            location=region,
            initial_node_count=3,
            autoscaling={
                'min_node_count': 2,
                'max_node_count': 10
            },
            node_config={
                'machine_type': 'n2-standard-4',
                'disk_size_gb': 100,
                'disk_type': 'pd-ssd',
                'preemptible': False,
                'oauth_scopes': [
                    'https://www.googleapis.com/auth/cloud-platform'
                ],
                'workload_metadata_config': {
                    'mode': 'GKE_METADATA'
                }
            },
            management={
                'auto_repair': True,
                'auto_upgrade': True
            },
            project=project_id
        )
        
        # Deploy Superset on GKE
        superset = SupersetGKE(
            name=self.get_resource_name('superset'),
            config=self.superset_config,
            cluster=cluster,
            database_url=db_outputs['connection_string'],
            redis_url=cache_outputs['url'],
            secret_key=security_outputs['secret_key'],
            project_id=project_id,
            labels=self.get_labels()
        )
        superset_outputs = superset.deploy()
        
        # Deploy monitoring stack if enabled
        monitoring_outputs = {}
        if self.config.get('monitoring', {}).get('enabled', False):
            monitoring = MonitoringStack(
                name=self.get_resource_name('monitoring'),
                config=self.config.get('monitoring', {}),
                cluster=cluster,
                project_id=project_id,
                labels=self.get_labels()
            )
            monitoring_outputs = monitoring.deploy()
        
        # Set up backups if enabled
        backup_config = self.config.get('backup', {})
        if backup_config.get('enabled', False):
            # Create backup bucket
            backup_bucket = gcp.storage.Bucket(
                self.get_resource_name('backup-bucket'),
                name=f'{project_id}-{self.name}-backups',
                location=region,
                storage_class='NEARLINE',
                lifecycle_rules=[{
                    'action': {'type': 'Delete'},
                    'condition': {
                        'age': backup_config.get('retention_days', 30)
                    }
                }],
                project=project_id,
                labels=self.get_labels()
            )
        
        # Export outputs
        self.export_outputs({
            'environment': 'gcp-production',
            'project_id': project_id,
            'region': region,
            'cluster_name': cluster.name,
            'cluster_endpoint': cluster.endpoint,
            'superset_url': superset_outputs['url'],
            'database_instance': db_outputs['instance_name'],
            'database_connection_name': db_outputs['connection_name'],
            'cache_instance': cache_outputs['instance_name'],
            'monitoring_url': monitoring_outputs.get('grafana_url'),
            'backup_bucket': backup_bucket.url if backup_config.get('enabled') else None,
            'instructions': Output.concat(
                'Production stack deployed successfully!\n',
                'Superset URL: ', superset_outputs['url'], '\n',
                'Grafana URL: ', monitoring_outputs.get('grafana_url', 'Not enabled'), '\n',
                'To connect to cluster: gcloud container clusters get-credentials ',
                cluster.name, ' --region=', region, ' --project=', project_id
            )
        })
        
        return self.outputs