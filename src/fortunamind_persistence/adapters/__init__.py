"""
Adapters Module

Provides integration adapters for connecting the persistence library
with various frameworks and systems.
"""

from .framework_adapter import FrameworkPersistenceAdapter

__all__ = [
    "FrameworkPersistenceAdapter"
]