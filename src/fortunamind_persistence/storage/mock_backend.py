"""
Mock Storage Backend

In-memory storage implementation for testing and development.
Provides the same interface as production storage without external dependencies.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import structlog
from collections import defaultdict

from .interfaces import PersistentStorageInterface, StorageRecord, RecordType

logger = structlog.get_logger(__name__)


class MockStorage(PersistentStorageInterface):
    """
    In-memory storage implementation for testing and development.
    
    Provides full interface compatibility with production storage
    but stores everything in memory. Data is lost on restart.
    """
    
    def __init__(self):
        """Initialize mock storage with empty data structures"""
        # Journal entries by user_id
        self.journal_entries: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # User preferences by user_id
        self.user_preferences: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Generic storage records by user_id  
        self.storage_records: Dict[str, List[StorageRecord]] = defaultdict(list)
        
        # Metadata
        self._initialized = False
        self._stats = {
            'operations': 0,
            'last_operation': None
        }
        
        logger.info("Mock storage initialized")
    
    async def initialize(self) -> bool:
        """Initialize mock storage (always succeeds)"""
        self._initialized = True
        logger.debug("Mock storage initialized successfully")
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Mock health check (always healthy)"""
        return {
            "status": "healthy",
            "backend": "mock",
            "initialized": self._initialized,
            "operations": self._stats['operations'],
            "last_operation": self._stats['last_operation'],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _record_operation(self, operation: str):
        """Record operation for stats"""
        self._stats['operations'] += 1
        self._stats['last_operation'] = {
            'type': operation,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def store_journal_entry(
        self,
        user_id: str,
        entry: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a trading journal entry"""
        self._record_operation('store_journal_entry')
        
        entry_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        journal_entry = {
            'id': entry_id,
            'user_id': user_id,
            'entry': entry,
            'metadata': metadata or {},
            'created_at': now.isoformat(),
            'updated_at': now.isoformat()
        }
        
        self.journal_entries[user_id].append(journal_entry)
        
        logger.debug(
            "Mock journal entry stored",
            user_id_hash=user_id[:8],
            entry_id=entry_id
        )
        
        return entry_id
    
    async def get_journal_entries(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve journal entries for a user"""
        self._record_operation('get_journal_entries')
        
        entries = self.journal_entries[user_id].copy()
        
        # Apply date filters
        if start_date or end_date:
            filtered_entries = []
            for entry in entries:
                entry_date = datetime.fromisoformat(entry['created_at'])
                
                if start_date and entry_date < start_date:
                    continue
                if end_date and entry_date > end_date:
                    continue
                
                filtered_entries.append(entry)
            entries = filtered_entries
        
        # Sort by created_at descending
        entries.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Apply pagination
        entries = entries[offset:offset + limit]
        
        logger.debug(
            "Mock journal entries retrieved",
            user_id_hash=user_id[:8],
            count=len(entries)
        )
        
        return entries
    
    async def update_journal_entry(
        self,
        user_id: str,
        entry_id: str,
        entry: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update an existing journal entry"""
        self._record_operation('update_journal_entry')
        
        entries = self.journal_entries[user_id]
        
        for journal_entry in entries:
            if journal_entry['id'] == entry_id:
                journal_entry['entry'] = entry
                journal_entry['metadata'] = metadata or {}
                journal_entry['updated_at'] = datetime.utcnow().isoformat()
                
                logger.debug(
                    "Mock journal entry updated",
                    user_id_hash=user_id[:8],
                    entry_id=entry_id
                )
                
                return True
        
        return False
    
    async def delete_journal_entry(
        self,
        user_id: str,
        entry_id: str
    ) -> bool:
        """Delete a journal entry"""
        self._record_operation('delete_journal_entry')
        
        entries = self.journal_entries[user_id]
        
        for i, journal_entry in enumerate(entries):
            if journal_entry['id'] == entry_id:
                entries.pop(i)
                
                logger.debug(
                    "Mock journal entry deleted",
                    user_id_hash=user_id[:8],
                    entry_id=entry_id
                )
                
                return True
        
        return False
    
    async def store_user_preference(
        self,
        user_id: str,
        key: str,
        value: Any
    ) -> bool:
        """Store a user preference"""
        self._record_operation('store_user_preference')
        
        self.user_preferences[user_id][key] = value
        
        logger.debug(
            "Mock user preference stored",
            user_id_hash=user_id[:8],
            key=key
        )
        
        return True
    
    async def get_user_preference(
        self,
        user_id: str,
        key: str,
        default: Any = None
    ) -> Any:
        """Get a user preference"""
        self._record_operation('get_user_preference')
        
        return self.user_preferences[user_id].get(key, default)
    
    async def get_user_preferences(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get all user preferences"""
        self._record_operation('get_user_preferences')
        
        return self.user_preferences[user_id].copy()
    
    async def store_record(
        self,
        record: StorageRecord
    ) -> str:
        """Store a generic record"""
        self._record_operation('store_record')
        
        # Create a copy to avoid mutation
        record_copy = StorageRecord(
            id=record.id,
            user_id=record.user_id,
            record_type=record.record_type,
            data=record.data.copy(),
            created_at=record.created_at,
            updated_at=record.updated_at or record.created_at,
            metadata=record.metadata.copy() if record.metadata else None
        )
        
        self.storage_records[record.user_id].append(record_copy)
        
        logger.debug(
            "Mock record stored",
            user_id_hash=record.user_id[:8],
            record_id=record.id,
            record_type=record.record_type.value
        )
        
        return record.id
    
    async def get_record(
        self,
        user_id: str,
        record_id: str
    ) -> Optional[StorageRecord]:
        """Get a specific record"""
        self._record_operation('get_record')
        
        for record in self.storage_records[user_id]:
            if record.id == record_id:
                # Return a copy to avoid mutation
                return StorageRecord(
                    id=record.id,
                    user_id=record.user_id,
                    record_type=record.record_type,
                    data=record.data.copy(),
                    created_at=record.created_at,
                    updated_at=record.updated_at,
                    metadata=record.metadata.copy() if record.metadata else None
                )
        
        return None
    
    async def query_records(
        self,
        user_id: str,
        record_type: Optional[RecordType] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[StorageRecord]:
        """Query records with filters"""
        self._record_operation('query_records')
        
        records = self.storage_records[user_id].copy()
        
        # Apply record type filter
        if record_type:
            records = [r for r in records if r.record_type == record_type]
        
        # Apply additional filters (simple key-value matching in data)
        if filters:
            filtered_records = []
            for record in records:
                match = True
                for key, value in filters.items():
                    if key not in record.data or record.data[key] != value:
                        match = False
                        break
                if match:
                    filtered_records.append(record)
            records = filtered_records
        
        # Sort by created_at descending
        records.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        records = records[offset:offset + limit]
        
        # Return copies to avoid mutation
        result = []
        for record in records:
            result.append(StorageRecord(
                id=record.id,
                user_id=record.user_id,
                record_type=record.record_type,
                data=record.data.copy(),
                created_at=record.created_at,
                updated_at=record.updated_at,
                metadata=record.metadata.copy() if record.metadata else None
            ))
        
        return result
    
    async def update_record(
        self,
        user_id: str,
        record_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update a record"""
        self._record_operation('update_record')
        
        for record in self.storage_records[user_id]:
            if record.id == record_id:
                record.data = data.copy()
                record.metadata = metadata.copy() if metadata else None
                record.updated_at = datetime.utcnow()
                
                logger.debug(
                    "Mock record updated",
                    user_id_hash=user_id[:8],
                    record_id=record_id
                )
                
                return True
        
        return False
    
    async def delete_record(
        self,
        user_id: str,
        record_id: str
    ) -> bool:
        """Delete a record"""
        self._record_operation('delete_record')
        
        records = self.storage_records[user_id]
        
        for i, record in enumerate(records):
            if record.id == record_id:
                records.pop(i)
                
                logger.debug(
                    "Mock record deleted",
                    user_id_hash=user_id[:8],
                    record_id=record_id
                )
                
                return True
        
        return False
    
    async def get_storage_stats(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get storage statistics for a user"""
        self._record_operation('get_storage_stats')
        
        journal_count = len(self.journal_entries[user_id])
        preferences_count = len(self.user_preferences[user_id])
        records_count = len(self.storage_records[user_id])
        
        # Count records by type
        records_by_type = {}
        for record in self.storage_records[user_id]:
            record_type = record.record_type.value
            records_by_type[record_type] = records_by_type.get(record_type, 0) + 1
        
        return {
            'journal_entries': journal_count,
            'preferences': preferences_count,
            'storage_records': records_count,
            'records_by_type': records_by_type,
            'total_operations': self._stats['operations'],
            'backend': 'mock',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def cleanup_expired_records(
        self,
        retention_days: int = 365
    ) -> int:
        """Clean up expired records (mock implementation)"""
        self._record_operation('cleanup_expired_records')
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        cleaned_count = 0
        
        # Clean up storage records
        for user_id in list(self.storage_records.keys()):
            original_count = len(self.storage_records[user_id])
            self.storage_records[user_id] = [
                r for r in self.storage_records[user_id] 
                if r.created_at > cutoff_date
            ]
            cleaned_count += original_count - len(self.storage_records[user_id])
        
        # Clean up journal entries
        for user_id in list(self.journal_entries.keys()):
            original_count = len(self.journal_entries[user_id])
            self.journal_entries[user_id] = [
                e for e in self.journal_entries[user_id]
                if datetime.fromisoformat(e['created_at']) > cutoff_date
            ]
            cleaned_count += original_count - len(self.journal_entries[user_id])
        
        logger.info(
            "Mock cleanup completed",
            cleaned_count=cleaned_count,
            retention_days=retention_days
        )
        
        return cleaned_count
    
    def clear_all_data(self):
        """Clear all data (useful for testing)"""
        self.journal_entries.clear()
        self.user_preferences.clear()
        self.storage_records.clear()
        self._stats['operations'] = 0
        self._stats['last_operation'] = None
        
        logger.debug("All mock data cleared")
    
    def get_user_count(self) -> int:
        """Get total number of users with data"""
        all_users = set()
        all_users.update(self.journal_entries.keys())
        all_users.update(self.user_preferences.keys()) 
        all_users.update(self.storage_records.keys())
        return len(all_users)
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information about stored data"""
        return {
            'users_with_journal_entries': len(self.journal_entries),
            'users_with_preferences': len(self.user_preferences),
            'users_with_records': len(self.storage_records),
            'total_journal_entries': sum(len(entries) for entries in self.journal_entries.values()),
            'total_preferences': sum(len(prefs) for prefs in self.user_preferences.values()),
            'total_records': sum(len(records) for records in self.storage_records.values()),
            'stats': self._stats.copy()
        }