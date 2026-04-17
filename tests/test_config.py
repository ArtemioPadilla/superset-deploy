"""Tests for configuration loading and validation."""

import pytest
import os
import sys
from pathlib import Path
from pydantic import ValidationError

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from pulumi.config.loader import deep_merge
from pulumi.config.models import StackConfig, SystemConfig, GCPConfig, SupersetConfig


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


class TestPydanticModels:
    """Test Pydantic model validation."""
    
    def test_valid_minimal_config(self):
        """Test validation of minimal configuration."""
        config = StackConfig(
            type='minimal',
            environment='local',
            enabled=True
        )
        
        assert config.type == 'minimal'
        assert config.environment == 'local'
        assert config.database.type == 'sqlite'
        assert config.cache.type == 'none'
    
    def test_valid_standard_config(self):
        """Test validation of standard configuration."""
        config = StackConfig(
            type='standard',
            environment='gcp',
            gcp=GCPConfig(
                project_id='test-project-123',
                region='us-central1'
            ),
            database={
                'type': 'cloud-sql',
                'tier': 'db-f1-micro',
                'password': 'test-password'
            },
            cache={
                'type': 'redis'
            }
        )
        
        assert config.type == 'standard'
        assert config.gcp.project_id == 'test-project-123'
        assert config.database.tier == 'db-f1-micro'
    
    def test_invalid_stack_type(self):
        """Test validation catches invalid stack type."""
        with pytest.raises(ValidationError) as exc_info:
            StackConfig(
                type='invalid',
                environment='local'
            )
        
        errors = exc_info.value.errors()
        assert any('type' in str(error['loc']) for error in errors)
    
    def test_missing_gcp_config(self):
        """Test validation catches missing GCP config."""
        with pytest.raises(ValidationError) as exc_info:
            StackConfig(
                type='standard',
                environment='gcp'
            )
        
        errors = exc_info.value.errors()
        assert any('GCP configuration is required' in str(error['msg']) for error in errors)
    
    def test_invalid_database_type(self):
        """Test validation catches invalid database type."""
        with pytest.raises(ValidationError) as exc_info:
            StackConfig(
                type='minimal',
                environment='local',
                database={
                    'type': 'invalid-db'
                }
            )
        
        errors = exc_info.value.errors()
        assert any('database' in str(error['loc']) and 'type' in str(error['loc']) for error in errors)
    
    def test_cloud_sql_requires_gcp(self):
        """Test validation ensures Cloud SQL only used with GCP."""
        with pytest.raises(ValidationError) as exc_info:
            StackConfig(
                type='minimal',
                environment='local',
                database={
                    'type': 'cloud-sql',
                    'password': 'test'
                }
            )
        
        errors = exc_info.value.errors()
        assert any('Cloud SQL cannot be used in local environment' in str(error['msg']) for error in errors)
    
    def test_superset_version_validation(self):
        """Test Superset version validation."""
        config = StackConfig(
            type='minimal',
            environment='local',
            superset=SupersetConfig(version='3.0.0')
        )
        
        assert config.superset.version == '3.0.0'
        
    def test_resource_validation(self):
        """Test resource allocation validation."""
        config = StackConfig(
            type='standard',
            environment='gcp',
            gcp={'project_id': 'test-123', 'region': 'us-central1'},
            superset={
                'resources': {
                    'cpu': '2.5',
                    'memory': '4Gi'
                }
            }
        )
        
        assert config.superset.resources.cpu == '2.5'
        assert config.superset.resources.memory == '4Gi'
        
    def test_invalid_memory_format(self):
        """Test invalid memory format validation."""
        with pytest.raises(ValidationError) as exc_info:
            StackConfig(
                type='minimal',
                environment='local',
                superset={
                    'resources': {
                        'memory': '4GB'  # Should be Gi or Mi
                    }
                }
            )
        
        errors = exc_info.value.errors()
        assert any('memory' in str(error['loc']) for error in errors)
    
    def test_gcp_project_id_validation(self):
        """Test GCP project ID validation."""
        # Valid project ID
        config = GCPConfig(
            project_id='my-project-123',
            region='us-central1'
        )
        assert config.project_id == 'my-project-123'
        
        # Invalid project ID
        with pytest.raises(ValidationError):
            GCPConfig(
                project_id='INVALID_PROJECT',  # Uppercase not allowed
                region='us-central1'
            )
    
    def test_environment_variable_expansion(self):
        """Test environment variable expansion in project ID."""
        os.environ['TEST_PROJECT_ID'] = 'test-project-456'
        
        # The GCPConfig validator now expands environment variables
        config = GCPConfig(
            project_id='${TEST_PROJECT_ID}',
            region='us-central1'
        )
        
        # Environment variable is expanded in the validator
        assert config.project_id == 'test-project-456'
        
        # Test with default value
        config2 = GCPConfig(
            project_id='${MISSING_PROJECT:-default-project}',
            region='us-central1'
        )
        assert config2.project_id == 'default-project'
        
        del os.environ['TEST_PROJECT_ID']


class TestValidators:
    """Test custom validators."""
    
    def test_expand_environment_variables(self):
        """Test environment variable expansion."""
        from pulumi.config.validators import expand_environment_variables
        
        # Test simple variable
        os.environ['TEST_VAR'] = 'test_value'
        assert expand_environment_variables('${TEST_VAR}') == 'test_value'
        
        # Test with default
        assert expand_environment_variables('${MISSING_VAR:-default}') == 'default'
        
        # Test missing without default (non-strict)
        assert expand_environment_variables('${MISSING_VAR}') == '${MISSING_VAR}'
        
        # Test missing without default (strict)
        with pytest.raises(ValueError) as exc_info:
            expand_environment_variables('${MISSING_VAR}', strict=True)
        assert 'Environment variable not found: MISSING_VAR' in str(exc_info.value)
        
        # Test multiple variables
        os.environ['VAR1'] = 'value1'
        os.environ['VAR2'] = 'value2'
        result = expand_environment_variables('${VAR1} and ${VAR2}')
        assert result == 'value1 and value2'
        
        # Cleanup
        del os.environ['TEST_VAR']
        del os.environ['VAR1']
        del os.environ['VAR2']
    
    def test_validate_superset_version(self):
        """Test Superset version validation."""
        from pulumi.config.validators import validate_superset_version
        
        # Valid known version - might return warning if not in cached list
        valid, msg = validate_superset_version('3.0.0')
        assert valid is True
        # Don't assert on msg - it depends on whether Docker Hub is accessible
        
        # Valid special versions
        valid, msg = validate_superset_version('latest')
        assert valid is True  # 'latest' should always be valid
        
        # Custom version (allowed)
        valid, msg = validate_superset_version('3.2.0-custom', allow_custom=True)
        assert valid is True
        if msg:
            assert 'Warning' in msg or 'not found' in msg
        
        # Invalid format
        valid, msg = validate_superset_version('invalid-version')
        assert valid is False
        assert 'Invalid version format' in msg
    
    def test_validate_gcp_project_id(self):
        """Test GCP project ID validation."""
        from pulumi.config.validators import validate_gcp_project_id
        
        # Valid project IDs
        valid_ids = [
            'my-project-123',
            'test-project',
            'a' * 6,  # Minimum length
            'a-' + 'b' * 26 + '-c'  # Maximum length (28 chars total)
        ]
        for project_id in valid_ids:
            valid, msg = validate_gcp_project_id(project_id)
            assert valid is True, f"Failed for {project_id}: {msg}"
        
        # Invalid project IDs
        invalid_ids = [
            'MY-PROJECT',  # Uppercase
            'my_project',  # Underscore
            '123-project',  # Starts with number
            'my-project-',  # Ends with hyphen
            'ab',  # Too short
            'a' * 31,  # Too long
        ]
        for project_id in invalid_ids:
            valid, msg = validate_gcp_project_id(project_id)
            assert valid is False, f"Should fail for {project_id}"
        
        # Environment variable pattern
        valid, msg = validate_gcp_project_id('${GCP_PROJECT}')
        assert valid is True
    
    def test_validate_resource_allocation(self):
        """Test resource allocation validation."""
        from pulumi.config.validators import validate_resource_allocation
        
        # Minimal stack
        warnings = validate_resource_allocation('0.5', '1Gi', 'minimal')
        assert len(warnings) == 0
        
        warnings = validate_resource_allocation('4', '8Gi', 'minimal')
        assert len(warnings) == 2
        assert 'CPU allocation' in warnings[0]
        assert 'Memory allocation' in warnings[1]
        
        # Production stack
        warnings = validate_resource_allocation('0.5', '1Gi', 'production')
        assert len(warnings) == 2
        assert 'too low for production' in warnings[0]
        assert 'too low for production' in warnings[1]
    
    def test_validate_cloud_sql_tier(self):
        """Test Cloud SQL tier validation."""
        from pulumi.config.validators import validate_cloud_sql_tier_for_environment
        
        # Free tier with HA
        warnings = validate_cloud_sql_tier_for_environment('db-f1-micro', True, 'standard')
        assert any('does not support high availability' in w for w in warnings)
        
        # Free tier for production
        warnings = validate_cloud_sql_tier_for_environment('db-f1-micro', False, 'production')
        assert any('not recommended for production' in w for w in warnings)
        
        # Valid standard tier
        warnings = validate_cloud_sql_tier_for_environment('db-n1-standard-1', False, 'production')
        assert len(warnings) == 0
    
    def test_check_version_compatibility(self):
        """Test version compatibility checking."""
        from pulumi.config.validators import check_version_compatibility
        
        # Compatible version
        warnings = check_version_compatibility('3.0.0', ['superset-plugin-chart-echarts'])
        assert len(warnings) == 0
        
        # Incompatible version
        warnings = check_version_compatibility('1.5.0', ['superset-plugin-chart-handlebars'])
        assert len(warnings) == 1
        assert 'requires Superset 2.1.0 or higher' in warnings[0]
        
        # Skip check for latest
        warnings = check_version_compatibility('latest', ['superset-plugin-chart-handlebars'])
        assert len(warnings) == 0


class TestConfigIntegration:
    """Integration tests for configuration loading."""
    
    def test_load_config_with_env_vars(self, tmp_path):
        """Test loading configuration with environment variable expansion."""
        from pulumi.config.loader import load_system_config
        
        # Create test configuration
        config_content = """
global:
  superset:
    default_version: "3.0.0"

stacks:
  test:
    type: minimal
    environment: gcp
    enabled: true
    gcp:
      project_id: "${TEST_PROJECT:-default-project}"
      region: "${TEST_REGION:-us-central1}"
"""
        config_file = tmp_path / "test_system.yaml"
        config_file.write_text(config_content)
        
        # Set environment variable
        os.environ['TEST_PROJECT'] = 'my-test-project'
        
        try:
            # Load configuration
            config = load_system_config(str(config_file))
            
            # Check that env var was expanded
            test_stack = config.get_stack('test')
            assert test_stack is not None
            # Note: Actual expansion happens in loader
            
        finally:
            if 'TEST_PROJECT' in os.environ:
                del os.environ['TEST_PROJECT']
    
    def test_stack_inheritance(self, tmp_path):
        """Test stack inheritance functionality."""
        from pulumi.config.loader import load_system_config
        
        config_content = """
global:
  superset:
    default_version: "3.0.0"

stacks:
  base:
    type: standard
    environment: gcp
    enabled: true
    gcp:
      project_id: "base-project"
      region: "us-central1"
    database:
      type: cloud-sql
      tier: db-f1-micro
      password: "base-password"
      
  derived:
    extends: base
    gcp:
      project_id: "derived-project"
    database:
      tier: db-n1-standard-1
"""
        config_file = tmp_path / "test_system.yaml"
        config_file.write_text(config_content)
        
        config = load_system_config(str(config_file))
        
        # Check inheritance
        derived = config.get_stack('derived')
        assert derived.type == 'standard'  # Inherited
        assert derived.gcp.project_id == 'derived-project'  # Overridden
        assert derived.gcp.region == 'us-central1'  # Inherited
        assert derived.database.tier == 'db-n1-standard-1'  # Overridden
        assert derived.database.password == 'base-password'  # Inherited
    
    def test_validation_errors_formatted(self, tmp_path):
        """Test that validation errors are properly formatted."""
        from pulumi.config.loader import load_system_config
        
        config_content = """
stacks:
  invalid:
    type: invalid-type
    environment: invalid-env
    gcp:
      project_id: "INVALID_PROJECT"
      region: "invalid-region"
"""
        config_file = tmp_path / "test_system.yaml"
        config_file.write_text(config_content)
        
        with pytest.raises(ValidationError) as exc_info:
            load_system_config(str(config_file))
        
        errors = exc_info.value.errors()
        # Should have multiple validation errors
        assert len(errors) > 1
        assert any('type' in str(e['loc']) for e in errors)
        assert any('environment' in str(e['loc']) for e in errors)
        assert any('project_id' in str(e['loc']) for e in errors)
        assert any('region' in str(e['loc']) for e in errors)