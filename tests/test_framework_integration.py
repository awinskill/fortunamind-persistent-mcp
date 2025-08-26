"""
Simple integration test for framework proxy

Tests the actual framework proxy functionality without complex mocking.
"""

import pytest
import os
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from framework_proxy import FrameworkProxy, get_framework


def test_framework_proxy_basic_functionality():
    """Test basic framework proxy functionality"""
    
    # Test that we can create a proxy (even if framework doesn't exist)
    try:
        proxy = FrameworkProxy("/nonexistent/path")
        assert False, "Should have raised RuntimeError for nonexistent path"
    except RuntimeError as e:
        assert "Framework not found" in str(e)
    
    # Test self-reference prevention
    current_project = Path(__file__).parent.parent
    try:
        proxy = FrameworkProxy(str(current_project))
        assert False, "Should have raised RuntimeError for self-reference"
    except RuntimeError as e:
        assert "Framework path points to current project" in str(e)


def test_environment_variable_usage():
    """Test that environment variable is used correctly"""
    
    # Save original env var
    original_path = os.environ.get('FORTUNAMIND_FRAMEWORK_PATH')
    
    try:
        # Test with custom path via environment variable
        test_path = '/Users/andywinskill/Documents/Programming/AIAgents/MCP/coinbase-mcp'
        os.environ['FORTUNAMIND_FRAMEWORK_PATH'] = test_path
        
        # Clear any cached proxy
        import framework_proxy
        framework_proxy._proxy = None
        
        # Only test if path actually exists
        if Path(test_path).exists():
            proxy = get_framework()
            assert str(proxy.framework_path) == test_path
        else:
            pytest.skip(f"Framework not found at {test_path}")
            
    finally:
        # Restore original environment variable
        if original_path:
            os.environ['FORTUNAMIND_FRAMEWORK_PATH'] = original_path
        elif 'FORTUNAMIND_FRAMEWORK_PATH' in os.environ:
            del os.environ['FORTUNAMIND_FRAMEWORK_PATH']


def test_real_framework_access():
    """Test access to real framework if available"""
    
    framework_path = os.getenv(
        'FORTUNAMIND_FRAMEWORK_PATH',
        '/Users/andywinskill/Documents/Programming/AIAgents/MCP/coinbase-mcp'
    )
    
    framework_path_obj = Path(framework_path)
    
    if not framework_path_obj.exists():
        pytest.skip(f"Framework not found at {framework_path}")
    
    # Test creating proxy
    proxy = FrameworkProxy(framework_path)
    
    # Verify basic properties
    assert proxy.framework_path.exists()
    assert (proxy.framework_path / 'src').exists()
    
    # Verify we're not pointing at ourselves
    current_path = Path(__file__).parent.parent
    assert proxy.framework_path.resolve() != current_path.resolve()
    
    # Test that it has expected structure
    src_path = proxy.framework_path / 'src'
    assert src_path.exists(), f"Expected src directory at {src_path}"


def test_safety_features():
    """Test safety features of the framework proxy"""
    
    # Test 1: Cannot point at current project
    current_project = Path(__file__).parent.parent
    
    with pytest.raises(RuntimeError, match="Framework path points to current project"):
        FrameworkProxy(str(current_project))
    
    # Test 2: Must point at existing path
    with pytest.raises(RuntimeError, match="Framework not found"):
        FrameworkProxy("/definitely/does/not/exist")
    
    # Test 3: Path validation works
    # This should work with a different, existing directory
    temp_dir = Path("/tmp")
    if temp_dir.exists():
        # This should work (different path that exists)
        # But will fail module imports later, which is expected
        proxy = FrameworkProxy(str(temp_dir))
        assert proxy.framework_path == temp_dir


if __name__ == "__main__":
    pytest.main([__file__, "-v"])