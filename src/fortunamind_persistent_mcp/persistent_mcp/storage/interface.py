"""
Storage Backend Interface

Defines the contract for persistent storage implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class DataType(str, Enum):
    """Data types for storage operations"""
    PORTFOLIO_SNAPSHOT = "portfolio_snapshot"
    TECHNICAL_INDICATOR = "technical_indicator" 
    JOURNAL_ENTRY = "journal_entry"
    USER_PREFERENCE = "user_preference"
    ALERT_CONFIG = "alert_config"
    SECURITY_EVENT = "security_event"


@dataclass
class StorageRecord:
    """Standardized storage record"""
    user_id_hash: str
    data_type: DataType
    data: Dict[str, Any]
    timestamp: datetime
    record_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


@dataclass
class QueryFilter:
    """Storage query filter"""
    data_type: Optional[DataType] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    tags: Optional[List[str]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class StorageInterface(ABC):
    """Abstract interface for storage backends"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the storage backend"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup storage backend resources"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check storage backend health"""
        pass
    
    # === CRUD Operations ===
    
    @abstractmethod
    async def store_record(self, record: StorageRecord) -> str:
        """
        Store a record and return its ID
        
        Args:
            record: The record to store
            
        Returns:
            The unique record ID
        """
        pass
    
    @abstractmethod
    async def get_record(self, user_id_hash: str, record_id: str) -> Optional[StorageRecord]:
        """
        Get a specific record by ID
        
        Args:
            user_id_hash: User identifier hash
            record_id: Record identifier
            
        Returns:
            The record if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def query_records(
        self, 
        user_id_hash: str, 
        filter_criteria: QueryFilter
    ) -> List[StorageRecord]:
        """
        Query records with filtering
        
        Args:
            user_id_hash: User identifier hash
            filter_criteria: Query filter criteria
            
        Returns:
            List of matching records
        """
        pass
    
    @abstractmethod
    async def update_record(
        self, 
        user_id_hash: str, 
        record_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update a record
        
        Args:
            user_id_hash: User identifier hash
            record_id: Record identifier
            updates: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_record(self, user_id_hash: str, record_id: str) -> bool:
        """
        Delete a record
        
        Args:
            user_id_hash: User identifier hash
            record_id: Record identifier
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    # === Specialized Operations ===
    
    @abstractmethod
    async def store_portfolio_snapshot(
        self,
        user_id_hash: str,
        portfolio_data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> str:
        """Store portfolio snapshot with specialized handling"""
        pass
    
    @abstractmethod
    async def get_latest_portfolio(self, user_id_hash: str) -> Optional[Dict[str, Any]]:
        """Get the most recent portfolio snapshot"""
        pass
    
    @abstractmethod
    async def store_technical_indicator(
        self,
        user_id_hash: str,
        symbol: str,
        indicator_type: str,
        data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> str:
        """Store technical indicator data"""
        pass
    
    @abstractmethod
    async def get_technical_indicators(
        self,
        user_id_hash: str,
        symbol: str,
        indicator_type: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get technical indicator history"""
        pass
    
    @abstractmethod
    async def store_journal_entry(
        self,
        user_id_hash: str,
        entry_data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> str:
        """Store trading journal entry"""
        pass
    
    @abstractmethod
    async def get_journal_entries(
        self,
        user_id_hash: str,
        since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get trading journal entries"""
        pass
    
    @abstractmethod
    async def store_user_preference(
        self,
        user_id_hash: str,
        key: str,
        value: Any,
        category: Optional[str] = None
    ) -> None:
        """Store user preference"""
        pass
    
    @abstractmethod
    async def get_user_preference(
        self,
        user_id_hash: str,
        key: str,
        default: Any = None
    ) -> Any:
        """Get user preference"""
        pass
    
    @abstractmethod
    async def get_user_preferences(
        self,
        user_id_hash: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all user preferences"""
        pass
    
    # === Analytics Operations ===
    
    @abstractmethod
    async def get_storage_stats(self, user_id_hash: str) -> Dict[str, Any]:
        """Get storage statistics for user"""
        pass
    
    @abstractmethod
    async def cleanup_expired_records(self) -> int:
        """Clean up expired records and return count"""
        pass


# Alias for backward compatibility
StorageBackend = StorageInterface