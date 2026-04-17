"""Configuration validator using Pydantic models."""

from typing import Dict, Any, List
from pydantic import ValidationError

from .loader import load_system_config
from .models import SystemConfig


def validate_stack_config(config: Dict[str, Any]) -> List[str]:
    """Legacy validator - now uses Pydantic models internally.
    
    This function is kept for backward compatibility with existing code.
    New code should use load_system_config() which includes validation.
    
    Args:
        config: Stack configuration dictionary
        
    Returns:
        List of error messages (empty if valid)
    """
    from .models import StackConfig
    
    try:
        # Try to create a StackConfig with the provided data
        StackConfig(**config)
        return []
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field_path = " -> ".join(str(x) for x in error['loc'])
            errors.append(f"{field_path}: {error['msg']}")
        return errors


def validate_system_config(config: Dict[str, Any]) -> List[str]:
    """Legacy validator - now uses Pydantic models internally.
    
    This function is kept for backward compatibility with existing code.
    New code should use load_system_config() which includes validation.
    
    Args:
        config: Full system configuration dictionary
        
    Returns:
        List of error messages (empty if valid)
    """
    try:
        # Try to create a SystemConfig with the provided data
        SystemConfig(**config)
        return []
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field_path = " -> ".join(str(x) for x in error['loc'])
            errors.append(f"{field_path}: {error['msg']}")
        return errors