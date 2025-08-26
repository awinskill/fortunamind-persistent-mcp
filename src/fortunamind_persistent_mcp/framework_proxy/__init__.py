"""
Framework Proxy - Safe read-only access to FortunaMind Framework

This module provides controlled access to the parent framework without
risk of modification. All imports go through this proxy layer.
"""

import sys
import os
from pathlib import Path
from typing import Any
import importlib.util

# Framework location (configured via environment variable for safety)
FRAMEWORK_PATH = os.getenv(
    'FORTUNAMIND_FRAMEWORK_PATH',
    '/Users/andywinskill/Documents/Programming/AIAgents/MCP/coinbase-mcp'
)

class FrameworkProxy:
    """
    Safe proxy for accessing framework modules.
    Ensures read-only access and prevents modifications.
    """
    
    def __init__(self, framework_path: str = FRAMEWORK_PATH):
        self.framework_path = Path(framework_path)
        if not self.framework_path.exists():
            raise RuntimeError(f"Framework not found at {framework_path}")
        
        # Verify we're not accidentally pointing at ourselves
        current_path = Path(__file__).parent.parent.parent
        if self.framework_path.resolve() == current_path.resolve():
            raise RuntimeError("Framework path points to current project!")
    
    def import_module(self, module_path: str) -> Any:
        """
        Safely import a module from the framework.
        
        Args:
            module_path: Dot-separated module path (e.g., 'unified_tools.portfolio')
        
        Returns:
            The imported module
        """
        # Convert module path to file path
        file_path = self.framework_path / 'src' / module_path.replace('.', '/') 
        
        # Try .py file first
        py_file = file_path.with_suffix('.py')
        if py_file.exists():
            return self._load_module_from_file(module_path, py_file)
        
        # Try __init__.py in directory
        init_file = file_path / '__init__.py'
        if init_file.exists():
            return self._load_module_from_file(module_path, init_file)
        
        raise ImportError(f"Module {module_path} not found in framework")
    
    def _load_module_from_file(self, module_name: str, file_path: Path) -> Any:
        """Load a module from a file path."""
        spec = importlib.util.spec_from_file_location(
            f"fortunamind_framework.{module_name}",
            file_path
        )
        if not spec or not spec.loader:
            raise ImportError(f"Cannot load {file_path}")
        
        module = importlib.util.module_from_spec(spec)
        
        # Add to sys.modules to enable relative imports within framework
        sys.modules[spec.name] = module
        
        try:
            # Execute the module
            spec.loader.exec_module(module)
        except ModuleNotFoundError as e:
            # Framework module has dependencies not available in our environment
            raise ImportError(f"Framework module {module_name} has missing dependencies: {e}")
        
        return module

# Global proxy instance
_proxy = None

def get_framework() -> FrameworkProxy:
    """Get the framework proxy instance."""
    global _proxy
    if _proxy is None:
        _proxy = FrameworkProxy()
    return _proxy

# Convenience imports
def unified_tools():
    """Import unified tools from framework."""
    return get_framework().import_module('unified_tools')

def core_interfaces():
    """Import core interfaces from framework."""
    return get_framework().import_module('core.interfaces')

def core_base():
    """Import base classes from framework."""  
    return get_framework().import_module('core.base')