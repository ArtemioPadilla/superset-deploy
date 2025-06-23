"""Tests for configuration loading and validation."""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from pulumi.config.loader import load_system_config, deep_merge
from pulumi.config.validator import validate_stack_config


class TestConfigLoader:
    """Test configuration loading functionality."""
    
    def test_deep_merge(self):
        """Test deep merge functionality."""
        base = {
            'a': 1,
            'b': {'c': 2, 'd': 3},
            'e': [1, 2, 3]
        }
        override = {
            'a': 10,
            'b': {'c': 20, 'f': 4},
            'g': 5
        }
        
        result = deep_merge(base, override)
        
        assert result['a'] == 10
        assert result['b']['c'] == 20
        assert result['b']['d'] == 3
        assert result['b']['f'] == 4
        assert result['g'] == 5
        assert result['e'] == [1, 2, 3]


class TestConfigValidator:
    """Test configuration validation."""
    
    def test_valid_minimal_config(self):
        """Test validation of minimal configuration."""
        config = {
            'type': 'minimal',
            'environment': 'local',
            'enabled': True
        }
        
        errors = validate_stack_config(config)
        assert len(errors) == 0
    
    def test_valid_standard_config(self):
        """Test validation of standard configuration."""
        config = {
            'type': 'standard',
            'environment': 'gcp',
            'gcp': {
                'project_id': 'test-project',
                'region': 'us-central1'
            },
            'database': {
                'type': 'cloud-sql',
                'tier': 'db-f1-micro'
            },
            'cache': {
                'type': 'redis'
            }
        }
        
        errors = validate_stack_config(config)
        assert len(errors) == 0
    
    def test_invalid_stack_type(self):
        """Test validation catches invalid stack type."""
        config = {
            'type': 'invalid',
            'environment': 'local'
        }
        
        errors = validate_stack_config(config)
        assert len(errors) > 0
        assert any('Invalid stack type' in error for error in errors)
    
    def test_missing_gcp_config(self):
        """Test validation catches missing GCP config."""
        config = {
            'type': 'standard',
            'environment': 'gcp'
        }
        
        errors = validate_stack_config(config)
        assert len(errors) > 0
        assert any('project_id is required' in error for error in errors)
    
    def test_invalid_database_type(self):
        """Test validation catches invalid database type."""
        config = {
            'type': 'minimal',
            'environment': 'local',
            'database': {
                'type': 'invalid-db'
            }
        }
        
        errors = validate_stack_config(config)
        assert len(errors) > 0
        assert any('Invalid database type' in error for error in errors)
    
    def test_cloud_sql_requires_gcp(self):
        """Test validation ensures Cloud SQL only used with GCP."""
        config = {
            'type': 'minimal',
            'environment': 'local',
            'database': {
                'type': 'cloud-sql'
            }
        }
        
        errors = validate_stack_config(config)
        assert len(errors) > 0
        assert any('Cloud SQL can only be used in GCP' in error for error in errors)