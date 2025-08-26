"""
Mock Storage Backend

Simple in-memory storage backend for demo deployments when Supabase is not available.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid

from .interface import StorageInterface, StorageRecord, QueryFilter, DataType
from config import Settings

logger = logging.getLogger(__name__)


class MockStorageBackend(StorageInterface):
    """
    In-memory mock storage backend for demo purposes
    
    Provides basic storage functionality without external dependencies.
    Data is not persisted between application restarts.
    """
    
    def __init__(self, settings: Settings):
        """Initialize mock storage backend"""
        self.settings = settings
        self.data: Dict[str, List[Dict[str, Any]]] = {}
        self._initialized = False
        
        logger.warning("Using mock storage backend - data will not persist between restarts")
    
    async def initialize(self) -> None:
        """Initialize mock storage (no-op)"""
        if self._initialized:
            return
        
        self._initialized = True
        logger.info("Mock storage backend initialized")
    
    async def health_check(self) -> bool:
        """Mock health check - always healthy"""
        return True
    
    async def store_journal_entry(
        self, 
        user_id_hash: str, 
        entry_data: Dict[str, Any]
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
        limit: Optional[int] = None,
        filters: Optional[List[QueryFilter]] = None
    ) -> List[StorageRecord]:
        """Get journal entries from memory"""
        key = f"journal_{user_id_hash}"
        entries = self.data.get(key, [])
        
        # Apply basic filtering (simplified)
        if filters:
            for filter_obj in filters:
                if filter_obj.field == "symbol" and filter_obj.operator == "eq":
                    entries = [e for e in entries if e.get("data", {}).get("symbol") == filter_obj.value]
        
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
        
        logger.debug(f"Retrieved {len(records)} mock journal entries")
        return records
    
    async def store_technical_indicator(
        self,
        user_id_hash: str,
        symbol: str,
        indicator_type: str,
        data: Dict[str, Any]
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
        symbol: Optional[str] = None,
        indicator_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[StorageRecord]:
        """Get technical indicators from memory"""
        all_records = []
        
        # Search all indicator keys for this user
        for key, entries in self.data.items():
            if key.startswith(f"indicators_{user_id_hash}"):
                for entry in entries:
                    if symbol and entry.get("symbol") != symbol:
                        continue
                    if indicator_type and entry.get("indicator_type") != indicator_type:
                        continue
                    
                    all_records.append(StorageRecord(
                        id=entry["id"],
                        user_id_hash=entry["user_id_hash"],
                        data={
                            "symbol": entry["symbol"],
                            "indicator_type": entry["indicator_type"],
                            **entry["data"]
                        },
                        created_at=datetime.fromisoformat(entry["created_at"].replace("Z", "+00:00")),
                        updated_at=datetime.fromisoformat(entry["updated_at"].replace("Z", "+00:00"))
                    ))
        
        # Sort by created_at (newest first) and apply limit
        all_records.sort(key=lambda x: x.created_at, reverse=True)
        if limit:
            all_records = all_records[:limit]
        
        logger.debug(f"Retrieved {len(all_records)} mock technical indicators")
        return all_records
    
    async def store_portfolio_snapshot(
        self,
        user_id_hash: str,
        portfolio_data: Dict[str, Any]
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