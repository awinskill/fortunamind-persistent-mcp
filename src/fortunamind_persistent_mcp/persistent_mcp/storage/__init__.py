"""
Storage Backend Interfaces and Implementations

Provides persistent storage capabilities for the FortunaMind MCP server.
"""

from .interface import StorageBackend, StorageInterface
from .supabase_backend import SupabaseStorageBackend
from .mock_backend import MockStorageBackend

__all__ = [
    "StorageBackend",
    "StorageInterface", 
    "SupabaseStorageBackend",
    "MockStorageBackend",
]