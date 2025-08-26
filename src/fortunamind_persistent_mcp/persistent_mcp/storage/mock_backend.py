"""
Mock Storage Backend

Simple in-memory storage backend for demo deployments when Supabase is not available.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid

# Note: Template pattern temporarily disabled due to circular imports
# from core.storage_template import InMemoryStorageTemplate
from .interface import StorageInterface, StorageRecord, QueryFilter, DataType
from fortunamind_persistent_mcp.config import Settings

logger = logging.getLogger(__name__)


class MockStorageBackend(StorageInterface):
    """
    Mock storage backend using the template pattern
    
    Extends InMemoryStorageTemplate with enhanced functionality for demo purposes.
    Provides comprehensive storage functionality without external dependencies.
    Data is not persisted between application restarts.
    """
    
    def __init__(self, settings: Settings):
        """Initialize mock storage backend"""
        self.settings = settings
        self._initialized = False
        
        # Legacy data structure for backward compatibility
        self.data: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.warning("Using mock storage backend - data will not persist between restarts")
    
    async def initialize(self) -> None:
        """Initialize mock storage (no-op)"""
        if self._initialized:
            return
        
        self._initialized = True
        logger.info("Mock storage backend initialized")
    
    async def cleanup(self) -> None:
        """Cleanup mock storage"""
        self.data.clear()
        self._initialized = False
    
    async def health_check(self) -> Dict[str, Any]:
        """Mock health check - always healthy"""
        return {
            "status": "healthy",
            "backend": "MockStorageBackend",
            "initialized": self._initialized,
            "data_keys": len(self.data)
        }
    
    async def store_journal_entry(
        self, 
        user_id_hash: str, 
        entry_data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> str:
        """Store journal entry in memory"""
        entry_id = str(uuid.uuid4())
        entry = {
            "id": entry_id,
            "user_id_hash": user_id_hash,
            "data": entry_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        key = f"journal_{user_id_hash}"
        if key not in self.data:
            self.data[key] = []
        self.data[key].append(entry)
        
        logger.debug(f"Stored mock journal entry: {entry_id}")
        return entry_id
    
    async def get_journal_entries(
        self, 
        user_id_hash: str, 
        since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get journal entries from memory"""
        key = f"journal_{user_id_hash}"
        entries = self.data.get(key, [])
        
        # Apply time filtering if since is provided
        if since:
            filtered_entries = []
            for entry in entries:
                entry_time = datetime.fromisoformat(entry["created_at"].replace("Z", "+00:00"))
                if entry_time >= since:
                    filtered_entries.append(entry)
            entries = filtered_entries
        
        # Apply limit
        if limit:
            entries = entries[:limit]
        
        # Return as Dict format as expected by interface
        result_entries = []
        for entry in entries:
            result_entries.append({
                "id": entry["id"],
                "user_id_hash": entry["user_id_hash"],
                "data": entry["data"],
                "created_at": entry["created_at"],
                "updated_at": entry["updated_at"]
            })
        
        logger.debug(f"Retrieved {len(result_entries)} mock journal entries")
        return result_entries
    
    async def store_technical_indicator(
        self,
        user_id_hash: str,
        symbol: str,
        indicator_type: str,
        data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> str:
        """Store technical indicator data in memory"""
        entry_id = str(uuid.uuid4())
        entry = {
            "id": entry_id,
            "user_id_hash": user_id_hash,
            "symbol": symbol,
            "indicator_type": indicator_type,
            "data": data,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        key = f"indicators_{user_id_hash}_{symbol}"
        if key not in self.data:
            self.data[key] = []
        self.data[key].append(entry)
        
        logger.debug(f"Stored mock technical indicator: {symbol}/{indicator_type}")
        return entry_id
    
    async def get_technical_indicators(
        self,
        user_id_hash: str,
        symbol: str,
        indicator_type: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get technical indicators from memory"""
        all_records = []
        
        # Search for indicators for this user and symbol
        key = f"indicators_{user_id_hash}_{symbol}"
        entries = self.data.get(key, [])
        
        for entry in entries:
            if indicator_type and entry.get("indicator_type") != indicator_type:
                continue
            
            # Apply time filtering if since is provided
            if since:
                entry_time = datetime.fromisoformat(entry["created_at"].replace("Z", "+00:00"))
                if entry_time < since:
                    continue
            
            all_records.append({
                "id": entry["id"],
                "user_id_hash": entry["user_id_hash"],
                "symbol": entry["symbol"],
                "indicator_type": entry["indicator_type"],
                "data": entry["data"],
                "created_at": entry["created_at"],
                "updated_at": entry["updated_at"]
            })
        
        # Sort by created_at (newest first)
        all_records.sort(key=lambda x: x["created_at"], reverse=True)
        
        logger.debug(f"Retrieved {len(all_records)} mock technical indicators")
        return all_records
    
    async def store_portfolio_snapshot(
        self,
        user_id_hash: str,
        portfolio_data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> str:
        """Store portfolio snapshot in memory"""
        entry_id = str(uuid.uuid4())
        entry = {
            "id": entry_id,
            "user_id_hash": user_id_hash,
            "data": portfolio_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        key = f"portfolio_{user_id_hash}"
        if key not in self.data:
            self.data[key] = []
        self.data[key].append(entry)
        
        logger.debug(f"Stored mock portfolio snapshot: {entry_id}")
        return entry_id
    
    async def get_portfolio_snapshots(
        self,
        user_id_hash: str,
        limit: Optional[int] = None
    ) -> List[StorageRecord]:
        """Get portfolio snapshots from memory"""
        key = f"portfolio_{user_id_hash}"
        entries = self.data.get(key, [])
        
        # Apply limit (newest first)
        if limit:
            entries = entries[-limit:]
        
        # Convert to StorageRecord format
        records = []
        for entry in reversed(entries):  # Newest first
            records.append(StorageRecord(
                id=entry["id"],
                user_id_hash=entry["user_id_hash"],
                data=entry["data"],
                created_at=datetime.fromisoformat(entry["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(entry["updated_at"].replace("Z", "+00:00"))
            ))
        
        logger.debug(f"Retrieved {len(records)} mock portfolio snapshots")
        return records
    
    async def store_data(
        self,
        user_id_hash: str,
        data_type: DataType,
        data: Dict[str, Any]
    ) -> str:
        """Generic data storage in memory"""
        entry_id = str(uuid.uuid4())
        entry = {
            "id": entry_id,
            "user_id_hash": user_id_hash,
            "data_type": data_type.value,
            "data": data,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        key = f"generic_{user_id_hash}_{data_type.value}"
        if key not in self.data:
            self.data[key] = []
        self.data[key].append(entry)
        
        logger.debug(f"Stored mock data: {data_type.value}")
        return entry_id
    
    async def get_data(
        self,
        user_id_hash: str,
        data_type: DataType,
        filters: Optional[List[QueryFilter]] = None,
        limit: Optional[int] = None
    ) -> List[StorageRecord]:
        """Generic data retrieval from memory"""
        key = f"generic_{user_id_hash}_{data_type.value}"
        entries = self.data.get(key, [])
        
        # Apply basic filtering (simplified)
        if filters:
            for filter_obj in filters:
                if filter_obj.operator == "eq":
                    entries = [e for e in entries if e.get("data", {}).get(filter_obj.field) == filter_obj.value]
        
        # Apply limit
        if limit:
            entries = entries[:limit]
        
        # Convert to StorageRecord format
        records = []
        for entry in entries:
            records.append(StorageRecord(
                id=entry["id"],
                user_id_hash=entry["user_id_hash"],
                data=entry["data"],
                created_at=datetime.fromisoformat(entry["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(entry["updated_at"].replace("Z", "+00:00"))
            ))
        
        logger.debug(f"Retrieved {len(records)} mock {data_type.value} records")
        return records
    
    # === Missing CRUD Operations ===
    
    async def store_record(self, record: StorageRecord) -> str:
        """Store a generic record"""
        entry_id = str(uuid.uuid4())
        entry = {
            "id": entry_id,
            "user_id_hash": record.user_id_hash,
            "data_type": record.data_type.value,
            "data": record.data,
            "metadata": record.metadata or {},
            "tags": record.tags or [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": record.expires_at.isoformat() if record.expires_at else None
        }
        
        key = f"records_{record.user_id_hash}_{record.data_type.value}"
        if key not in self.data:
            self.data[key] = []
        self.data[key].append(entry)
        
        logger.debug(f"Stored mock record: {record.data_type.value}")
        return entry_id
    
    async def get_record(self, user_id_hash: str, record_id: str) -> Optional[StorageRecord]:
        """Get a specific record by ID"""
        for key, entries in self.data.items():
            if key.startswith(f"records_{user_id_hash}_"):
                for entry in entries:
                    if entry["id"] == record_id:
                        return StorageRecord(
                            user_id_hash=entry["user_id_hash"],
                            data_type=DataType(entry["data_type"]),
                            data=entry["data"],
                            timestamp=datetime.fromisoformat(entry["created_at"].replace("Z", "+00:00")),
                            record_id=entry["id"],
                            metadata=entry.get("metadata", {}),
                            tags=entry.get("tags", []),
                            expires_at=datetime.fromisoformat(entry["expires_at"].replace("Z", "+00:00")) if entry.get("expires_at") else None
                        )
        return None
    
    async def query_records(self, user_id_hash: str, filter_criteria: QueryFilter) -> List[StorageRecord]:
        """Query records with filtering"""
        all_records = []
        
        # Search all record keys for this user
        for key, entries in self.data.items():
            if key.startswith(f"records_{user_id_hash}_"):
                for entry in entries:
                    # Apply data type filter
                    if filter_criteria.data_type and entry.get("data_type") != filter_criteria.data_type.value:
                        continue
                    
                    # Apply time filters
                    created_at = datetime.fromisoformat(entry["created_at"].replace("Z", "+00:00"))
                    if filter_criteria.start_time and created_at < filter_criteria.start_time:
                        continue
                    if filter_criteria.end_time and created_at > filter_criteria.end_time:
                        continue
                    
                    # Apply tag filters
                    if filter_criteria.tags:
                        entry_tags = set(entry.get("tags", []))
                        filter_tags = set(filter_criteria.tags)
                        if not entry_tags.intersection(filter_tags):
                            continue
                    
                    all_records.append(StorageRecord(
                        user_id_hash=entry["user_id_hash"],
                        data_type=DataType(entry["data_type"]),
                        data=entry["data"],
                        timestamp=created_at,
                        record_id=entry["id"],
                        metadata=entry.get("metadata", {}),
                        tags=entry.get("tags", []),
                        expires_at=datetime.fromisoformat(entry["expires_at"].replace("Z", "+00:00")) if entry.get("expires_at") else None
                    ))
        
        # Sort by timestamp (newest first) and apply limit/offset
        all_records.sort(key=lambda x: x.timestamp, reverse=True)
        
        if filter_criteria.offset:
            all_records = all_records[filter_criteria.offset:]
        if filter_criteria.limit:
            all_records = all_records[:filter_criteria.limit]
        
        logger.debug(f"Retrieved {len(all_records)} mock records via query")
        return all_records
    
    async def update_record(self, user_id_hash: str, record_id: str, updates: Dict[str, Any]) -> bool:
        """Update a record"""
        for key, entries in self.data.items():
            if key.startswith(f"records_{user_id_hash}_"):
                for entry in entries:
                    if entry["id"] == record_id:
                        # Update allowed fields
                        if "data" in updates:
                            entry["data"].update(updates["data"])
                        if "metadata" in updates:
                            entry["metadata"].update(updates["metadata"])
                        if "tags" in updates:
                            entry["tags"] = updates["tags"]
                        entry["updated_at"] = datetime.now(timezone.utc).isoformat()
                        
                        logger.debug(f"Updated mock record: {record_id}")
                        return True
        return False
    
    async def delete_record(self, user_id_hash: str, record_id: str) -> bool:
        """Delete a record"""
        for key, entries in self.data.items():
            if key.startswith(f"records_{user_id_hash}_"):
                for i, entry in enumerate(entries):
                    if entry["id"] == record_id:
                        del entries[i]
                        logger.debug(f"Deleted mock record: {record_id}")
                        return True
        return False
    
    # === Missing Specialized Operations ===
    
    async def get_latest_portfolio(self, user_id_hash: str) -> Optional[Dict[str, Any]]:
        """Get the most recent portfolio snapshot"""
        key = f"portfolio_{user_id_hash}"
        entries = self.data.get(key, [])
        
        if not entries:
            return None
        
        # Return the most recent entry
        latest = max(entries, key=lambda x: x["created_at"])
        return latest["data"]
    
    # === Missing User Preference Operations ===
    
    async def store_user_preference(self, user_id_hash: str, key: str, value: Any, category: Optional[str] = None) -> None:
        """Store user preference"""
        pref_key = f"prefs_{user_id_hash}"
        if pref_key not in self.data:
            self.data[pref_key] = {}
        
        # Store with category if provided
        if category:
            if category not in self.data[pref_key]:
                self.data[pref_key][category] = {}
            self.data[pref_key][category][key] = value
        else:
            self.data[pref_key][key] = value
        
        logger.debug(f"Stored mock user preference: {key}")
    
    async def get_user_preference(self, user_id_hash: str, key: str, default: Any = None) -> Any:
        """Get user preference"""
        pref_key = f"prefs_{user_id_hash}"
        prefs = self.data.get(pref_key, {})
        
        # Try direct key first
        if key in prefs:
            return prefs[key]
        
        # Search in categories
        for category_data in prefs.values():
            if isinstance(category_data, dict) and key in category_data:
                return category_data[key]
        
        return default
    
    async def get_user_preferences(self, user_id_hash: str, category: Optional[str] = None) -> Dict[str, Any]:
        """Get all user preferences"""
        pref_key = f"prefs_{user_id_hash}"
        prefs = self.data.get(pref_key, {})
        
        if category:
            return prefs.get(category, {})
        return prefs
    
    # === Missing Analytics Operations ===
    
    async def get_storage_stats(self, user_id_hash: str) -> Dict[str, Any]:
        """Get storage statistics for user"""
        stats = {
            "total_records": 0,
            "data_types": {},
            "storage_size_kb": 0,
            "oldest_record": None,
            "newest_record": None
        }
        
        # Count records by type
        for key, entries in self.data.items():
            if key.startswith(f"records_{user_id_hash}_") or key.startswith(f"journal_{user_id_hash}") or key.startswith(f"portfolio_{user_id_hash}") or key.startswith(f"indicators_{user_id_hash}"):
                stats["total_records"] += len(entries)
                
                # Extract data type from key
                if "_journal_" in key:
                    data_type = "journal_entry"
                elif "_portfolio_" in key:
                    data_type = "portfolio_snapshot"
                elif "_indicators_" in key:
                    data_type = "technical_indicator"
                else:
                    data_type = "generic"
                
                stats["data_types"][data_type] = stats["data_types"].get(data_type, 0) + len(entries)
                
                # Track oldest/newest
                for entry in entries:
                    created_at = entry["created_at"]
                    if not stats["oldest_record"] or created_at < stats["oldest_record"]:
                        stats["oldest_record"] = created_at
                    if not stats["newest_record"] or created_at > stats["newest_record"]:
                        stats["newest_record"] = created_at
        
        # Rough storage size calculation
        import sys
        stats["storage_size_kb"] = sys.getsizeof(str(self.data)) / 1024
        
        logger.debug(f"Generated mock storage stats for user: {user_id_hash}")
        return stats
    
    async def cleanup_expired_records(self) -> int:
        """Clean up expired records and return count"""
        count = 0
        now = datetime.now(timezone.utc)
        
        # Check all records for expiry
        for key, entries in list(self.data.items()):
            expired_indices = []
            for i, entry in enumerate(entries):
                if entry.get("expires_at"):
                    expires_at = datetime.fromisoformat(entry["expires_at"].replace("Z", "+00:00"))
                    if expires_at < now:
                        expired_indices.append(i)
            
            # Remove expired records (in reverse order to maintain indices)
            for i in reversed(expired_indices):
                del entries[i]
                count += 1
            
            # Remove empty keys
            if not entries:
                del self.data[key]
        
        if count > 0:
            logger.info(f"Cleaned up {count} expired mock records")
        return count