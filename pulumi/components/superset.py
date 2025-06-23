"""Superset deployment components for different platforms."""

import pulumi
import pulumi_gcp as gcp
import pulumi_docker as docker
from typing import Dict, Any, Optional
import json
import base64


class SupersetCloudRun:
    """Deploy Superset on Cloud Run (serverless)."""
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        project_id: str,
        region: str,
        database_url: pulumi.Output[str],
        redis_url: Optional[pulumi.Output[str]] = None,
        secret_key: pulumi.Output[str] = None,
        network: Optional[gcp.compute.Network] = None,
        subnet: Optional[gcp.compute.Subnetwork] = None,
        labels: Dict[str, str] = None
    ):
        """Initialize Cloud Run Superset deployment."""
        self.name = name
        self.config = config
        self.project_id = project_id
        self.region = region
        self.database_url = database_url
        self.redis_url = redis_url
        self.secret_key = secret_key
        self.network = network
        self.subnet = subnet
        self.labels = labels or {}
        
    def deploy(self) -> Dict[str, Any]:
        """Deploy Superset on Cloud Run."""
        # Configuration
        version = self.config.get('version', '3.0.0')
        cpu = self.config.get('resources', {}).get('cpu', '1')
        memory = self.config.get('resources', {}).get('memory', '2Gi')
        min_instances = 0 if self.name.endswith('-dev') else 1  # Scale to zero for dev
        max_instances = self.config.get('autoscaling', {}).get('max_replicas', 100)
        
        # Build custom Superset image if needed
        image = f'apache/superset:{version}'
        
        # Create Cloud Run service
        service = gcp.cloudrun.Service(
            self.name,
            name=self.name,
            location=self.region,
            project=self.project_id,
            template={
                'metadata': {
                    'annotations': {
                        'autoscaling.knative.dev/minScale': str(min_instances),
                        'autoscaling.knative.dev/maxScale': str(max_instances),
                        'run.googleapis.com/execution-environment': 'gen2',
                    },
                    'labels': self.labels,
                },
                'spec': {
                    'containers': [{
                        'image': image,
                        'ports': [{'containerPort': 8088}],
                        'resources': {
                            'limits': {
                                'cpu': cpu,
                                'memory': memory,
                            }
                        },
                        'envs': [
                            {'name': 'SUPERSET_SECRET_KEY', 'value': self.secret_key},
                            {'name': 'DATABASE_URL', 'value': self.database_url},
                            {'name': 'REDIS_URL', 'value': self.redis_url or ''},
                            {'name': 'SUPERSET_LOAD_EXAMPLES', 'value': 'no'},
                            {'name': 'GUNICORN_CMD_ARGS', 'value': '--bind=0.0.0.0:8088 --workers=2'},
                        ],
                        'livenessProbe': {
                            'httpGet': {
                                'path': '/health',
                                'port': 8088,
                            },
                            'initialDelaySeconds': 30,
                            'periodSeconds': 30,
                        },
                    }],
                    'serviceAccountName': f'{self.name}@{self.project_id}.iam.gserviceaccount.com',
                },
            },
            traffics=[{
                'percent': 100,
                'latest_revision': True,
            }],
            metadata={
                'annotations': {
                    'run.googleapis.com/ingress': 'internal-and-cloud-load-balancing',  # Internal + LB only
                }
            },
        )
        
        # Note: No public IAM policy needed when using Cloudflare Tunnel
        # Access is controlled through Cloudflare Zero Trust
        
        return {
            'service_name': service.name,
            'url': service.statuses[0].url,
        }


class SupersetGKE:
    """Deploy Superset on Google Kubernetes Engine."""
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        cluster: gcp.container.Cluster,
        database_url: pulumi.Output[str],
        redis_url: pulumi.Output[str],
        secret_key: pulumi.Output[str],
        project_id: str,
        labels: Dict[str, str] = None
    ):
        """Initialize GKE Superset deployment."""
        self.name = name
        self.config = config
        self.cluster = cluster
        self.database_url = database_url
        self.redis_url = redis_url
        self.secret_key = secret_key
        self.project_id = project_id
        self.labels = labels or {}
        
    def deploy(self) -> Dict[str, Any]:
        """Deploy Superset on GKE using Kubernetes resources."""
        # This is a simplified version - in production, you'd use Helm charts
        # or more sophisticated Kubernetes manifests
        
        # For now, return placeholder outputs
        # Full implementation would create:
        # - Namespace
        # - ConfigMaps
        # - Secrets
        # - Deployments
        # - Services
        # - Ingress
        # - HPA (Horizontal Pod Autoscaler)
        
        return {
            'url': pulumi.Output.concat('https://superset-', self.name, '.example.com'),
            'namespace': 'superset',
        }