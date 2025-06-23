"""Base stack class for all deployment types."""

from abc import ABC, abstractmethod
from typing import Dict, Any
import pulumi


class BaseStack(ABC):
    """Abstract base class for all stack types."""
    
    def __init__(self, name: str, config: Dict[str, Any], global_config: Dict[str, Any]):
        """Initialize base stack.
        
        Args:
            name: Stack name
            config: Stack-specific configuration
            global_config: Global configuration
        """
        self.name = name
        self.config = config
        self.global_config = global_config
        self.outputs = {}
        
        # Merge global config with stack config
        self.superset_config = {
            **global_config.get('superset', {}),
            **config.get('superset', {})
        }
    
    @abstractmethod
    def deploy(self) -> Dict[str, Any]:
        """Deploy the stack and return outputs.
        
        Returns:
            Dictionary of stack outputs
        """
        pass
    
    def get_resource_name(self, resource_type: str) -> str:
        """Generate consistent resource names.
        
        Args:
            resource_type: Type of resource (e.g., 'db', 'redis', 'superset')
            
        Returns:
            Formatted resource name
        """
        return f"{self.name}-{resource_type}"
    
    def get_labels(self) -> Dict[str, str]:
        """Get common labels for all resources.
        
        Returns:
            Dictionary of labels
        """
        return {
            'environment': self.name,
            'managed-by': 'pulumi',
            'project': 'superset-deploy',
            'stack-type': self.config.get('type', 'unknown')
        }
    
    def export_outputs(self, outputs: Dict[str, Any]):
        """Add outputs to be exported.
        
        Args:
            outputs: Dictionary of outputs to add
        """
        self.outputs.update(outputs)