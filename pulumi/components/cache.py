"""Cache component for Redis/Memcached deployment."""

import pulumi
import pulumi_gcp as gcp
from typing import Dict, Any, Optional


class RedisCache:
    """Redis cache component using Cloud Memorystore."""
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        project_id: str,
        region: str,
        network: Optional[gcp.compute.Network] = None,
        labels: Dict[str, str] = None
    ):
        """Initialize Redis cache component."""
        self.name = name
        self.config = config
        self.project_id = project_id
        self.region = region
        self.network = network
        self.labels = labels or {}
        
    def deploy(self) -> Dict[str, Any]:
        """Deploy Redis instance and return connection details."""
        # Redis configuration
        tier = self.config.get('tier', 'basic')
        memory_size_gb = self.config.get('memory_size_gb', 1)
        high_availability = self.config.get('high_availability', False)
        
        # Determine Redis tier
        if high_availability:
            redis_tier = 'STANDARD_HA'
        else:
            redis_tier = 'BASIC' if tier == 'basic' else 'STANDARD_HA'
        
        # Create Redis instance
        redis_instance = gcp.redis.Instance(
            self.name,
            name=self.name,
            tier=redis_tier,
            memory_size_gb=memory_size_gb,
            region=self.region,
            location_id=f'{self.region}-a',  # Use first zone in region
            redis_version='REDIS_6_X',
            display_name=f'Superset Redis Cache - {self.name}',
            authorized_network=self.network.id if self.network else None,
            labels=self.labels,
            project=self.project_id,
            redis_configs={
                'maxmemory-policy': 'allkeys-lru',  # LRU eviction for cache
                'notify-keyspace-events': 'Ex',     # Enable keyspace notifications
            },
        )
        
        # Build Redis URL
        redis_url = pulumi.Output.all(
            redis_instance.host,
            redis_instance.port
        ).apply(
            lambda args: f'redis://{args[0]}:{args[1]}/0'
        )
        
        return {
            'instance_name': redis_instance.name,
            'host': redis_instance.host,
            'port': redis_instance.port,
            'url': redis_url,
            'current_location_id': redis_instance.current_location_id,
        }