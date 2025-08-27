"""
Storage Interfaces

Abstract interfaces for persistent storage that all implementations must follow.
Provides consistent API across different storage backends.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import uuid


class RecordType(Enum):
    """Types of records that can be stored"""
    JOURNAL_ENTRY = "journal_entry"
    USER_PREFERENCE = "user_preference" 
    PERFORMANCE_DATA = "performance_data"
    TRADE_PLAN = "trade_plan"
    ALERT = "alert"
    CUSTOM = "custom"


@dataclass
class StorageRecord:
    """
    Generic storage record that can hold any type of data.
    
    All storage operations use this structure for consistency.
    """
    id: str
    user_id: str
    record_type: RecordType
    data: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.updated_at is None:
            self.updated_at = self.created_at


class PersistentStorageInterface(ABC):
    """
    Abstract interface for persistent storage backends.
    
    All implementations must provide user isolation and support
    the full range of storage operations defined here.
    """
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the storage backend.
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check storage backend health.
        
        Returns:
            Dict with health status information
        """
        pass
    
    # Journal operations
    @abstractmethod
    async def store_journal_entry(
        self,
        user_id: str,
        entry: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a trading journal entry.
        
        Args:
            user_id: User's unique identifier
            entry: Journal entry text
            metadata: Optional metadata (tags, exchange, etc.)
            
        Returns:
            Entry ID
        """
        pass
    
    @abstractmethod
    async def get_journal_entries(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve journal entries for a user.
        
        Args:
            user_id: User's unique identifier
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            
        Returns:
            List of journal entries
        """
        pass
    
    @abstractmethod
    async def update_journal_entry(
        self,
        user_id: str,
        entry_id: str,
        entry: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing journal entry.
        
        Args:
            user_id: User's unique identifier
            entry_id: Entry to update
            entry: New entry text
            metadata: Updated metadata
            
        Returns:
            True if updated successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_journal_entry(
        self,
        user_id: str,
        entry_id: str
    ) -> bool:
        """
        Delete a journal entry.
        
        Args:
            user_id: User's unique identifier
            entry_id: Entry to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        pass
    
    # User preferences
    @abstractmethod
    async def store_user_preference(
        self,
        user_id: str,
        key: str,
        value: Any
    ) -> bool:
        """
        Store a user preference.
        
        Args:
            user_id: User's unique identifier
            key: Preference key
            value: Preference value (will be JSON serialized)
            
        Returns:
            True if stored successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_user_preference(
        self,
        user_id: str,
        key: str,
        default: Any = None
    ) -> Any:
        """
        Get a user preference.
        
        Args:
            user_id: User's unique identifier
            key: Preference key
            default: Default value if not found
            
        Returns:
            Preference value or default
        """
        pass
    
    @abstractmethod
    async def get_user_preferences(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get all user preferences.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Dict of all preferences
        """
        pass
    
    # Generic record operations
    @abstractmethod
    async def store_record(
        self,
        record: StorageRecord
    ) -> str:
        """
        Store a generic record.
        
        Args:
            record: StorageRecord to store
            
        Returns:
            Record ID
        """
        pass
    
    @abstractmethod
    async def get_record(
        self,
        user_id: str,
        record_id: str
    ) -> Optional[StorageRecord]:
        """
        Get a specific record.
        
        Args:
            user_id: User's unique identifier
            record_id: Record ID to retrieve
            
        Returns:
            StorageRecord if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def query_records(
        self,
        user_id: str,
        record_type: Optional[RecordType] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[StorageRecord]:
        """
        Query records with filters.
        
        Args:
            user_id: User's unique identifier
            record_type: Filter by record type
            filters: Additional filters to apply
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of matching StorageRecords
        """
        pass
    
    @abstractmethod
    async def update_record(
        self,
        user_id: str,
        record_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a record.
        
        Args:
            user_id: User's unique identifier
            record_id: Record ID to update
            data: New data
            metadata: Updated metadata
            
        Returns:
            True if updated successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_record(
        self,
        user_id: str,
        record_id: str
    ) -> bool:
        """
        Delete a record.
        
        Args:
            user_id: User's unique identifier
            record_id: Record ID to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        pass
    
    # Analytics and reporting
    @abstractmethod
    async def get_storage_stats(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get storage statistics for a user.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Dict with storage statistics
        """
        pass
    
    @abstractmethod
    async def cleanup_expired_records(
        self,
        retention_days: int = 365
    ) -> int:
        """
        Clean up expired records.
        
        Args:
            retention_days: Number of days to retain records
            
        Returns:
            Number of records cleaned up
        """
        pass
    
    # Context managers for transactions
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # Override in implementations if cleanup needed
        pass


class CacheableStorageInterface(PersistentStorageInterface):
    """
    Extended interface for storage backends that support caching.
    """
    
    @abstractmethod
    async def invalidate_cache(
        self,
        user_id: str,
        cache_key: Optional[str] = None
    ):
        """
        Invalidate cached data for a user.
        
        Args:
            user_id: User's unique identifier
            cache_key: Specific cache key to invalidate, or None for all
        """
        pass
    
    @abstractmethod
    async def warm_cache(
        self,
        user_id: str,
        record_types: Optional[List[RecordType]] = None
    ):
        """
        Pre-load commonly accessed data into cache.
        
        Args:
            user_id: User's unique identifier  
            record_types: Types of records to cache, or None for all
        """
        pass