"""Cloudflare Tunnel component for zero-trust access."""

import pulumi
import pulumi_gcp as gcp
from typing import Dict, Any, Optional, List
import json
import base64
import yaml


class CloudflareTunnel:
    """Cloudflare Tunnel component for secure access to Superset."""
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        project_id: str,
        region: str,
        target_service: str,
        target_port: int = 8088,
        additional_routes: Optional[List[Dict[str, Any]]] = None,
        labels: Dict[str, str] = None
    ):
        """Initialize Cloudflare Tunnel component.
        
        Args:
            name: Resource name
            config: Cloudflare configuration
            project_id: GCP project ID
            region: GCP region
            target_service: Target service URL (e.g., Cloud Run URL)
            target_port: Target service port
            additional_routes: Additional routes to configure
            labels: Resource labels
        """
        self.name = name
        self.config = config
        self.project_id = project_id
        self.region = region
        self.target_service = target_service
        self.target_port = target_port
        self.additional_routes = additional_routes or []
        self.labels = labels or {}
        
    def deploy(self) -> Dict[str, Any]:
        """Deploy Cloudflare Tunnel connector on GCP."""
        outputs = {}
        
        # Get tunnel configuration
        tunnel_name = self.config.get('tunnel_name', f'{self.name}-tunnel')
        tunnel_secret = self.config.get('tunnel_secret')
        tunnel_id = self.config.get('tunnel_id')
        account_id = self.config.get('account_id')
        
        # Store tunnel credentials in Secret Manager
        if tunnel_secret:
            tunnel_creds = {
                'AccountTag': account_id,
                'TunnelSecret': tunnel_secret,
                'TunnelID': tunnel_id
            }
            
            secret = gcp.secretmanager.Secret(
                f'{self.name}-tunnel-creds',
                secret_id=f'{self.name}-tunnel-creds',
                project=self.project_id,
                labels=self.labels,
                replication={'automatic': {}}
            )
            
            secret_version = gcp.secretmanager.SecretVersion(
                f'{self.name}-tunnel-creds-version',
                secret=secret.id,
                secret_data=json.dumps(tunnel_creds)
            )
            
            outputs['tunnel_secret'] = secret.id
        
        # Create service account for Cloudflare connector
        service_account = gcp.serviceaccount.Account(
            f'{self.name}-cloudflared-sa',
            account_id=f'{self.name}-cloudflared',
            display_name='Cloudflare Tunnel Service Account',
            project=self.project_id
        )
        
        # Grant necessary permissions
        secret_accessor = gcp.secretmanager.SecretIamMember(
            f'{self.name}-secret-accessor',
            secret_id=secret.id,
            role='roles/secretmanager.secretAccessor',
            member=pulumi.Output.concat('serviceAccount:', service_account.email),
            project=self.project_id
        )
        
        # Build tunnel configuration
        tunnel_config = self._build_tunnel_config()
        
        # Deploy Cloudflare connector on Cloud Run
        if self.config.get('deployment_type', 'cloudrun') == 'cloudrun':
            connector = self._deploy_cloudrun_connector(
                service_account,
                tunnel_config,
                secret_version.id if tunnel_secret else None
            )
            outputs['connector_url'] = connector['url']
            outputs['connector_service'] = connector['service_name']
        else:
            # Deploy on GKE if specified
            connector = self._deploy_gke_connector(
                service_account,
                tunnel_config,
                secret_version.id if tunnel_secret else None
            )
            outputs['connector_deployment'] = connector['deployment_name']
        
        # Configure access policies
        if self.config.get('access_policies'):
            access_outputs = self._configure_access_policies()
            outputs.update(access_outputs)
        
        # Export tunnel information
        outputs['tunnel_name'] = tunnel_name
        outputs['tunnel_id'] = tunnel_id
        outputs['hostnames'] = self._get_configured_hostnames()
        
        return outputs
    
    def _build_tunnel_config(self) -> str:
        """Build Cloudflare Tunnel configuration."""
        # Main hostname from config
        main_hostname = self.config.get('hostname', f'{self.name}.example.com')
        
        # Build ingress rules
        ingress_rules = [
            {
                'hostname': main_hostname,
                'service': self.target_service,
                'originRequest': {
                    'noTLSVerify': True,
                    'connectTimeout': '30s',
                    'tcpKeepAlive': '30s',
                    'keepAliveConnections': 4
                }
            }
        ]
        
        # Add additional routes
        for route in self.additional_routes:
            ingress_rules.append({
                'hostname': route['hostname'],
                'service': route['service'],
                'originRequest': route.get('originRequest', {
                    'noTLSVerify': True,
                    'connectTimeout': '30s'
                })
            })
        
        # Add catch-all rule
        ingress_rules.append({'service': 'http_status:404'})
        
        config = {
            'tunnel': self.config.get('tunnel_id'),
            'credentials-file': '/etc/cloudflared/creds/credentials.json',
            'metrics': '0.0.0.0:2000',
            'loglevel': 'info',
            'ingress': ingress_rules
        }
        
        return base64.b64encode(yaml.dump(config).encode()).decode()
    
    def _deploy_cloudrun_connector(
        self,
        service_account: gcp.serviceaccount.Account,
        tunnel_config: str,
        secret_id: Optional[pulumi.Output[str]]
    ) -> Dict[str, Any]:
        """Deploy Cloudflare connector on Cloud Run."""
        # Create Cloud Run service for cloudflared
        service = gcp.cloudrun.Service(
            f'{self.name}-cloudflared',
            name=f'{self.name}-cloudflared',
            location=self.region,
            project=self.project_id,
            template={
                'metadata': {
                    'annotations': {
                        'autoscaling.knative.dev/minScale': '1',
                        'autoscaling.knative.dev/maxScale': '3',
                        'run.googleapis.com/execution-environment': 'gen2',
                    },
                    'labels': self.labels,
                },
                'spec': {
                    'containers': [{
                        'image': 'cloudflare/cloudflared:latest',
                        'command': ['cloudflared'],
                        'args': ['tunnel', '--config', '/etc/cloudflared/config.yaml', 'run'],
                        'resources': {
                            'limits': {
                                'cpu': '0.5',
                                'memory': '512Mi',
                            }
                        },
                        'envs': [
                            {'name': 'TUNNEL_TOKEN', 'value': self.config.get('tunnel_token', '')},
                        ],
                        'volumeMounts': [
                            {
                                'name': 'config',
                                'mountPath': '/etc/cloudflared',
                            },
                            {
                                'name': 'creds',
                                'mountPath': '/etc/cloudflared/creds',
                            }
                        ] if secret_id else [],
                    }],
                    'volumes': [
                        {
                            'name': 'config',
                            'configMap': {
                                'name': f'{self.name}-cloudflared-config',
                                'items': [{
                                    'key': 'config.yaml',
                                    'path': 'config.yaml'
                                }]
                            }
                        },
                        {
                            'name': 'creds',
                            'secret': {
                                'secretName': f'{self.name}-tunnel-creds',
                                'items': [{
                                    'key': 'credentials.json',
                                    'path': 'credentials.json'
                                }]
                            }
                        }
                    ] if secret_id else [],
                    'serviceAccountName': service_account.email,
                },
            },
            metadata={
                'annotations': {
                    'run.googleapis.com/ingress': 'internal',  # Internal only
                }
            },
        )
        
        return {
            'service_name': service.name,
            'url': service.statuses[0].url,
        }
    
    def _deploy_gke_connector(
        self,
        service_account: gcp.serviceaccount.Account,
        tunnel_config: str,
        secret_id: Optional[pulumi.Output[str]]
    ) -> Dict[str, Any]:
        """Deploy Cloudflare connector on GKE."""
        # Placeholder for GKE deployment
        # Would create Deployment, Service, ConfigMap, etc.
        return {
            'deployment_name': f'{self.name}-cloudflared',
        }
    
    def _configure_access_policies(self) -> Dict[str, Any]:
        """Configure Cloudflare Access policies."""
        # This would integrate with Cloudflare API to set up:
        # - Access applications
        # - Policy rules (email domains, GitHub orgs, etc.)
        # - Service tokens for API access
        
        policies = self.config.get('access_policies', [])
        outputs = {}
        
        for policy in policies:
            # Placeholder for policy creation
            outputs[f'policy_{policy["name"]}'] = 'configured'
        
        return outputs
    
    def _get_configured_hostnames(self) -> List[str]:
        """Get list of configured hostnames."""
        hostnames = [self.config.get('hostname', f'{self.name}.example.com')]
        
        for route in self.additional_routes:
            if 'hostname' in route:
                hostnames.append(route['hostname'])
        
        return hostnames