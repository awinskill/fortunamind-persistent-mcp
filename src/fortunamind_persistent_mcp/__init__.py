"""
FortunaMind Persistent MCP Server

A premium MCP server that provides advanced technical analysis tools 
and personal trading journal capabilities for FortunaMind subscribers.

Designed for crypto-curious professionals who want to learn and improve 
their investment decisions systematically.
"""

__version__ = "1.0.0"
__author__ = "FortunaMind Team"
__email__ = "dev@fortunamind.com"

# Main exports for clean package interface
from .main import main
from .config import get_settings, Settings

try:
    from .persistent_mcp.server import PersistentMCPServer
except ImportError:
    # Handle circular import during package loading
    PersistentMCPServer = None

__all__ = [
    "main", 
    "get_settings", 
    "Settings", 
    "PersistentMCPServer",
    "__version__",
]

# Version info
VERSION_INFO = {
    "version": __version__,
    "name": "FortunaMind Persistent MCP Server",
    "description": "Educational trading tools with persistent storage",
    "target_users": "Crypto-curious professionals (35-65)",
    "key_features": [
        "Technical indicators in plain English",
        "Learning-focused trading journal",
        "Privacy-first design",
        "Enterprise-grade security"
    ]
}