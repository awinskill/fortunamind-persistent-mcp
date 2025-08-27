"""
Storage Module

Provides persistent storage interfaces and implementations for FortunaMind services.
Includes Supabase backend, caching, and mock storage for testing.
"""

from .interfaces import PersistentStorageInterface, StorageRecord
from .supabase_backend import SupabaseStorage
from .mock_backend import MockStorage

__all__ = [
    "PersistentStorageInterface",
    "StorageRecord", 
    "SupabaseStorage",
    "MockStorage"
]