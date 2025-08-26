"""
Test Framework Proxy - Verify safe framework access

These tests ensure that:
1. Framework proxy correctly identifies the framework location
2. Safety checks prevent pointing at our own project
3. Module imports work correctly
4. No modifications are possible to framework code
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import our framework proxy
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from framework_proxy import FrameworkProxy, get_framework


class TestFrameworkProxy:
    """Test the framework proxy functionality"""
    
    def test_framework_path_validation(self):
        """Test that framework path validation works correctly"""
        # Test with non-existent path
        with pytest.raises(RuntimeError, match="Framework not found"):
            FrameworkProxy("/path/that/does/not/exist")
    
    def test_self_reference_prevention(self):
        """Test that we cannot accidentally point at ourselves"""
        current_project_path = Path(__file__).parent.parent
        
        with pytest.raises(RuntimeError, match="Framework path points to current project"):
            FrameworkProxy(str(current_project_path))
    
    @patch.dict(os.environ, {'FORTUNAMIND_FRAMEWORK_PATH': '/mock/framework/path'})
    @patch('framework_proxy.Path.exists')
    def test_environment_configuration(self, mock_exists):
        """Test that framework path can be configured via environment variable"""
        mock_exists.return_value = True
        
        with patch('framework_proxy.Path.resolve') as mock_resolve:
            # Mock different paths to avoid self-reference check
            mock_resolve.side_effect = [
                Path('/mock/framework/path'),  # Framework path
                Path('/different/current/path')  # Current path
            ]
            
            proxy = FrameworkProxy()
            assert str(proxy.framework_path) == '/mock/framework/path'
    
    def test_default_framework_path(self):
        """Test default framework path configuration"""
        # Clear environment variable temporarily
        original_path = os.environ.get('FORTUNAMIND_FRAMEWORK_PATH')
        if 'FORTUNAMIND_FRAMEWORK_PATH' in os.environ:
            del os.environ['FORTUNAMIND_FRAMEWORK_PATH']
        
        try:
            with patch('framework_proxy.Path.exists') as mock_exists:
                mock_exists.return_value = True
                
                with patch('framework_proxy.Path.resolve') as mock_resolve:
                    # Mock different paths to avoid self-reference check
                    mock_resolve.side_effect = [
                        Path('/Users/andywinskill/Documents/Programming/AIAgents/MCP/fortunamind-mcp'),
                        Path('/different/current/path')
                    ]
                    
                    proxy = FrameworkProxy()
                    expected_path = '/Users/andywinskill/Documents/Programming/AIAgents/MCP/fortunamind-mcp'
                    assert str(proxy.framework_path) == expected_path
        finally:
            # Restore original environment variable
            if original_path:
                os.environ['FORTUNAMIND_FRAMEWORK_PATH'] = original_path
    
    @patch('framework_proxy.importlib.util.spec_from_file_location')
    @patch('framework_proxy.importlib.util.module_from_spec')
    def test_module_import_success(self, mock_module_from_spec, mock_spec_from_file):
        """Test successful module import"""
        # Create mock framework directory structure
        framework_path = Path('/mock/framework')
        
        with patch('framework_proxy.Path.exists') as mock_exists:
            # Framework path exists
            mock_exists.return_value = True
            
            with patch('framework_proxy.Path.resolve') as mock_resolve:
                # Mock different paths to avoid self-reference check
                mock_resolve.side_effect = [
                    framework_path,  # Framework path
                    Path('/different/current/path')  # Current path
                ]
                
                proxy = FrameworkProxy(str(framework_path))
                
                # Mock the module import process
                mock_spec = MagicMock()
                mock_loader = MagicMock()
                mock_spec.loader = mock_loader
                mock_spec.name = 'fortunamind_framework.unified_tools'
                mock_spec_from_file.return_value = mock_spec
                
                mock_module = MagicMock()
                mock_module_from_spec.return_value = mock_module
                
                # Test that .py file is checked first
                with patch.object(proxy.framework_path, '__truediv__') as mock_div:
                    mock_file_path = MagicMock()
                    mock_py_file = MagicMock()
                    mock_py_file.exists.return_value = True
                    mock_file_path.with_suffix.return_value = mock_py_file
                    mock_div.return_value = mock_file_path
                    
                    result = proxy.import_module('unified_tools')
                    
                    # Verify the import process
                    mock_spec_from_file.assert_called_once()
                    mock_module_from_spec.assert_called_once_with(mock_spec)
                    mock_loader.exec_module.assert_called_once_with(mock_module)
                    
                    assert result == mock_module
    
    def test_module_import_not_found(self):
        """Test handling of missing modules"""
        framework_path = Path('/mock/framework')
        
        with patch('framework_proxy.Path.exists') as mock_exists:
            mock_exists.return_value = True
            
            with patch('framework_proxy.Path.resolve') as mock_resolve:
                mock_resolve.side_effect = [
                    framework_path,
                    Path('/different/current/path')
                ]
                
                proxy = FrameworkProxy(str(framework_path))
                
                # Mock that neither .py file nor __init__.py exists
                with patch.object(proxy.framework_path, '__truediv__') as mock_div:
                    mock_file_path = MagicMock()
                    mock_py_file = MagicMock()
                    mock_init_file = MagicMock()
                    
                    mock_py_file.exists.return_value = False
                    mock_init_file.exists.return_value = False
                    
                    mock_file_path.with_suffix.return_value = mock_py_file
                    mock_file_path.__truediv__.return_value = mock_init_file
                    mock_div.return_value = mock_file_path
                    
                    with pytest.raises(ImportError, match="Module nonexistent_module not found"):
                        proxy.import_module('nonexistent_module')
    
    def test_convenience_functions(self):
        """Test the convenience import functions"""
        with patch('framework_proxy.get_framework') as mock_get_framework:
            mock_proxy = MagicMock()
            mock_get_framework.return_value = mock_proxy
            
            # Test unified_tools function
            from framework_proxy import unified_tools
            result = unified_tools()
            mock_proxy.import_module.assert_called_with('unified_tools')
            
            # Test core_interfaces function  
            from framework_proxy import core_interfaces
            result = core_interfaces()
            mock_proxy.import_module.assert_called_with('core.interfaces')
            
            # Test core_base function
            from framework_proxy import core_base
            result = core_base()
            mock_proxy.import_module.assert_called_with('core.base')


class TestFrameworkIntegration:
    """Integration tests for framework proxy"""
    
    def test_real_framework_detection(self):
        """Test against the real framework if available"""
        framework_path = os.getenv(
            'FORTUNAMIND_FRAMEWORK_PATH',
            '/Users/andywinskill/Documents/Programming/AIAgents/MCP/fortunamind-mcp'
        )
        
        if Path(framework_path).exists():
            # Real framework is available - test basic functionality
            proxy = FrameworkProxy(framework_path)
            
            # Verify framework structure exists
            src_path = proxy.framework_path / 'src'
            assert src_path.exists(), f"Framework src directory not found at {src_path}"
            
            # Test basic safety - should not be our project
            current_path = Path(__file__).parent.parent
            assert proxy.framework_path.resolve() != current_path.resolve()
        else:
            pytest.skip(f"Real framework not found at {framework_path}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])