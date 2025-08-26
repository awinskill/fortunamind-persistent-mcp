"""
Supabase Storage Backend

Implementation of persistent storage using Supabase PostgreSQL with Row Level Security.
"""

import logging
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import asdict

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

from .interface import StorageInterface, StorageRecord, QueryFilter, DataType
from config import Settings

logger = logging.getLogger(__name__)


class SupabaseStorageBackend(StorageInterface):
    """
    Supabase-based storage backend with Row Level Security
    
    Provides secure, scalable persistence using PostgreSQL through Supabase.
    All data is automatically isolated by user_id_hash using RLS policies.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize Supabase storage backend
        
        Args:
            settings: Application settings containing Supabase configuration
        """
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase client not available. Install with: pip install supabase")
        
        self.settings = settings
        self.client: Optional[Client] = None
        self._initialized = False
        
        logger.info("Supabase storage backend created")
    
    async def initialize(self) -> None:
        """Initialize Supabase connection and verify schema"""
        if self._initialized:
            return
        
        logger.info("Initializing Supabase storage backend...")
        
        # Create Supabase client
        self.client = create_client(
            self.settings.supabase_url,
            self.settings.supabase_service_role_key  # Use service role for server operations
        )
        
        # Verify connection
        await self._verify_connection()
        
        # Ensure required tables exist
        await self._ensure_schema()
        
        self._initialized = True
        logger.info("✅ Supabase storage backend initialized")
    
    async def cleanup(self) -> None:
        """Cleanup Supabase resources"""
        logger.info("Cleaning up Supabase storage backend...")
        
        # Supabase client doesn't require explicit cleanup
        self.client = None
        self._initialized = False
        
        logger.info("✅ Supabase cleanup complete")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Supabase connection health"""
        if not self.client:
            return {
                "status": "unhealthy",
                "error": "Not initialized"
            }
        
        try:
            # Simple query to test connection
            result = self.client.table("storage_records").select("count", count="exact").limit(0).execute()
            
            return {
                "status": "healthy",
                "backend": "supabase",
                "url": self.settings.supabase_url,
                "total_records": result.count or 0
            }
            
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return {
                "status": "unhealthy", 
                "error": str(e)
            }
    
    async def _verify_connection(self) -> None:
        """Verify Supabase connection"""
        try:
            # Test basic connectivity
            result = self.client.table("storage_records").select("count", count="exact").limit(0).execute()
            logger.info("✅ Supabase connection verified")
            
        except Exception as e:
            logger.error(f"Supabase connection failed: {e}")
            raise ConnectionError(f"Failed to connect to Supabase: {e}")
    
    async def _ensure_schema(self) -> None:
        """Ensure required database schema exists"""
        # Note: In production, schema should be managed via migrations
        # This is a development convenience method
        
        logger.info("Verifying database schema...")
        
        try:
            # Try to access the main table
            self.client.table("storage_records").select("id").limit(1).execute()
            logger.info("✅ Database schema verified")
            
        except Exception as e:
            logger.warning(f"Schema verification failed: {e}")
            logger.warning("Ensure database migrations have been run")
    
    # === CRUD Operations ===
    
    async def store_record(self, record: StorageRecord) -> str:
        """Store a record and return its ID"""
        if not self.client:
            raise RuntimeError("Storage backend not initialized")
        
        # Generate ID if not provided
        record_id = record.record_id or str(uuid.uuid4())
        
        # Prepare data for storage
        storage_data = {
            "id": record_id,
            "user_id_hash": record.user_id_hash,
            "data_type": record.data_type.value,
            "data": json.dumps(record.data),
            "timestamp": record.timestamp.isoformat(),
            "metadata": json.dumps(record.metadata) if record.metadata else None,
            "tags": record.tags,
            "expires_at": record.expires_at.isoformat() if record.expires_at else None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Insert record (RLS will ensure user isolation)
            result = self.client.table("storage_records").insert(storage_data).execute()
            
            if not result.data:
                raise RuntimeError("Failed to store record")
            
            logger.debug(f"Stored record {record_id} for user {record.user_id_hash[:8]}...")
            return record_id
            
        except Exception as e:
            logger.error(f"Failed to store record: {e}")
            raise
    
    async def get_record(self, user_id_hash: str, record_id: str) -> Optional[StorageRecord]:
        """Get a specific record by ID"""
        if not self.client:
            raise RuntimeError("Storage backend not initialized")
        
        try:
            result = self.client.table("storage_records").select("*").eq(
                "id", record_id
            ).eq("user_id_hash", user_id_hash).single().execute()
            
            if not result.data:
                return None
            
            return self._convert_to_storage_record(result.data)
            
        except Exception as e:
            logger.debug(f"Record {record_id} not found: {e}")
            return None
    
    async def query_records(
        self, 
        user_id_hash: str, 
        filter_criteria: QueryFilter
    ) -> List[StorageRecord]:
        """Query records with filtering"""
        if not self.client:
            raise RuntimeError("Storage backend not initialized")
        
        try:
            # Start query
            query = self.client.table("storage_records").select("*").eq("user_id_hash", user_id_hash)
            
            # Apply filters
            if filter_criteria.data_type:
                query = query.eq("data_type", filter_criteria.data_type.value)
            
            if filter_criteria.start_time:
                query = query.gte("timestamp", filter_criteria.start_time.isoformat())
            
            if filter_criteria.end_time:
                query = query.lte("timestamp", filter_criteria.end_time.isoformat())
            
            if filter_criteria.tags:
                # Use array overlap operator for tags
                query = query.overlaps("tags", filter_criteria.tags)
            
            # Apply ordering (newest first)
            query = query.order("timestamp", desc=True)
            
            # Apply pagination
            if filter_criteria.limit:
                query = query.limit(filter_criteria.limit)
            
            if filter_criteria.offset:
                query = query.offset(filter_criteria.offset)
            
            # Execute query
            result = query.execute()
            
            # Convert results
            records = [self._convert_to_storage_record(row) for row in result.data]
            
            logger.debug(f"Retrieved {len(records)} records for user {user_id_hash[:8]}...")
            return records
            
        except Exception as e:
            logger.error(f"Failed to query records: {e}")
            return []
    
    async def update_record(
        self, 
        user_id_hash: str, 
        record_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update a record"""
        if not self.client:
            raise RuntimeError("Storage backend not initialized")
        
        try:
            # Prepare updates with timestamp
            update_data = updates.copy()
            update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            # Update record (RLS ensures user isolation)
            result = self.client.table("storage_records").update(update_data).eq(
                "id", record_id
            ).eq("user_id_hash", user_id_hash).execute()
            
            success = bool(result.data)
            if success:
                logger.debug(f"Updated record {record_id} for user {user_id_hash[:8]}...")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update record: {e}")
            return False
    
    async def delete_record(self, user_id_hash: str, record_id: str) -> bool:
        """Delete a record"""
        if not self.client:
            raise RuntimeError("Storage backend not initialized")
        
        try:
            # Delete record (RLS ensures user isolation)
            result = self.client.table("storage_records").delete().eq(
                "id", record_id
            ).eq("user_id_hash", user_id_hash).execute()
            
            success = bool(result.data)
            if success:
                logger.debug(f"Deleted record {record_id} for user {user_id_hash[:8]}...")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete record: {e}")
            return False
    
    # === Specialized Operations ===
    
    async def store_portfolio_snapshot(
        self,
        user_id_hash: str,
        portfolio_data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> str:
        """Store portfolio snapshot with specialized handling"""
        record = StorageRecord(
            user_id_hash=user_id_hash,
            data_type=DataType.PORTFOLIO_SNAPSHOT,
            data=portfolio_data,
            timestamp=timestamp or datetime.now(timezone.utc),
            tags=["portfolio", "snapshot"],
            metadata={"source": "unified_portfolio_tool"}
        )
        
        return await self.store_record(record)
    
    async def get_latest_portfolio(self, user_id_hash: str) -> Optional[Dict[str, Any]]:
        """Get the most recent portfolio snapshot"""
        filter_criteria = QueryFilter(
            data_type=DataType.PORTFOLIO_SNAPSHOT,
            limit=1
        )
        
        records = await self.query_records(user_id_hash, filter_criteria)
        
        if records:
            return records[0].data
        
        return None
    
    async def store_technical_indicator(
        self,
        user_id_hash: str,
        symbol: str,
        indicator_type: str,
        data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> str:
        """Store technical indicator data"""
        record = StorageRecord(
            user_id_hash=user_id_hash,
            data_type=DataType.TECHNICAL_INDICATOR,
            data=data,
            timestamp=timestamp or datetime.now(timezone.utc),
            tags=["technical_indicator", symbol.upper(), indicator_type],
            metadata={
                "symbol": symbol.upper(),
                "indicator_type": indicator_type,
                "source": "technical_indicators_tool"
            }
        )
        
        return await self.store_record(record)
    
    async def get_technical_indicators(
        self,
        user_id_hash: str,
        symbol: str,
        indicator_type: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get technical indicator history"""
        # Build tags filter
        tags = ["technical_indicator", symbol.upper()]
        if indicator_type:
            tags.append(indicator_type)
        
        filter_criteria = QueryFilter(
            data_type=DataType.TECHNICAL_INDICATOR,
            tags=tags,
            start_time=since,
            limit=100  # Reasonable limit for indicators
        )
        
        records = await self.query_records(user_id_hash, filter_criteria)
        
        return [
            {
                **record.data,
                "timestamp": record.timestamp,
                "record_id": record.record_id
            }
            for record in records
        ]
    
    async def store_journal_entry(
        self,
        user_id_hash: str,
        entry_data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> str:
        """Store trading journal entry"""
        record = StorageRecord(
            user_id_hash=user_id_hash,
            data_type=DataType.JOURNAL_ENTRY,
            data=entry_data,
            timestamp=timestamp or datetime.now(timezone.utc),
            tags=["journal", "trading"] + entry_data.get("tags", []),
            metadata={"source": "trading_journal_tool"}
        )
        
        return await self.store_record(record)
    
    async def get_journal_entries(
        self,
        user_id_hash: str,
        since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get trading journal entries"""
        filter_criteria = QueryFilter(
            data_type=DataType.JOURNAL_ENTRY,
            start_time=since,
            limit=limit or 50
        )
        
        records = await self.query_records(user_id_hash, filter_criteria)
        
        return [
            {
                **record.data,
                "timestamp": record.timestamp,
                "record_id": record.record_id
            }
            for record in records
        ]
    
    async def store_user_preference(
        self,
        user_id_hash: str,
        key: str,
        value: Any,
        category: Optional[str] = None
    ) -> None:
        """Store user preference"""
        record = StorageRecord(
            user_id_hash=user_id_hash,
            data_type=DataType.USER_PREFERENCE,
            data={"key": key, "value": value, "category": category},
            timestamp=datetime.now(timezone.utc),
            tags=["preference"] + ([category] if category else []),
            metadata={"preference_key": key}
        )
        
        # Try to update existing preference first
        existing = await self.query_records(
            user_id_hash, 
            QueryFilter(data_type=DataType.USER_PREFERENCE, tags=["preference"])
        )
        
        # Find existing preference with same key
        for record_obj in existing:
            if record_obj.data.get("key") == key:
                await self.update_record(
                    user_id_hash, 
                    record_obj.record_id, 
                    {"data": json.dumps(record.data)}
                )
                return
        
        # Store new preference
        await self.store_record(record)
    
    async def get_user_preference(
        self,
        user_id_hash: str,
        key: str,
        default: Any = None
    ) -> Any:
        """Get user preference"""
        filter_criteria = QueryFilter(
            data_type=DataType.USER_PREFERENCE,
            tags=["preference"]
        )
        
        records = await self.query_records(user_id_hash, filter_criteria)
        
        for record in records:
            if record.data.get("key") == key:
                return record.data.get("value", default)
        
        return default
    
    async def get_user_preferences(
        self,
        user_id_hash: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all user preferences"""
        tags = ["preference"]
        if category:
            tags.append(category)
        
        filter_criteria = QueryFilter(
            data_type=DataType.USER_PREFERENCE,
            tags=tags
        )
        
        records = await self.query_records(user_id_hash, filter_criteria)
        
        preferences = {}
        for record in records:
            key = record.data.get("key")
            value = record.data.get("value")
            if key is not None:
                preferences[key] = value
        
        return preferences
    
    # === Analytics Operations ===
    
    async def get_storage_stats(self, user_id_hash: str) -> Dict[str, Any]:
        """Get storage statistics for user"""
        if not self.client:
            raise RuntimeError("Storage backend not initialized")
        
        try:
            # Get record counts by type
            stats = {}
            
            for data_type in DataType:
                result = self.client.table("storage_records").select(
                    "count", count="exact"
                ).eq("user_id_hash", user_id_hash).eq(
                    "data_type", data_type.value
                ).execute()
                
                stats[data_type.value] = result.count or 0
            
            # Get total storage usage (approximate)
            total_result = self.client.table("storage_records").select(
                "count", count="exact"
            ).eq("user_id_hash", user_id_hash).execute()
            
            stats["total_records"] = total_result.count or 0
            
            # Get oldest and newest records
            oldest = self.client.table("storage_records").select(
                "timestamp"
            ).eq("user_id_hash", user_id_hash).order("timestamp").limit(1).execute()
            
            newest = self.client.table("storage_records").select(
                "timestamp"
            ).eq("user_id_hash", user_id_hash).order("timestamp", desc=True).limit(1).execute()
            
            if oldest.data:
                stats["oldest_record"] = oldest.data[0]["timestamp"]
            
            if newest.data:
                stats["newest_record"] = newest.data[0]["timestamp"]
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {"error": str(e)}
    
    async def cleanup_expired_records(self) -> int:
        """Clean up expired records and return count"""
        if not self.client:
            raise RuntimeError("Storage backend not initialized")
        
        try:
            # Delete records where expires_at < now
            now = datetime.now(timezone.utc).isoformat()
            
            result = self.client.table("storage_records").delete().lt(
                "expires_at", now
            ).execute()
            
            count = len(result.data) if result.data else 0
            
            if count > 0:
                logger.info(f"Cleaned up {count} expired records")
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired records: {e}")
            return 0
    
    def _convert_to_storage_record(self, row: Dict[str, Any]) -> StorageRecord:
        """Convert database row to StorageRecord"""
        return StorageRecord(
            record_id=row["id"],
            user_id_hash=row["user_id_hash"],
            data_type=DataType(row["data_type"]),
            data=json.loads(row["data"]) if isinstance(row["data"], str) else row["data"],
            timestamp=datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")),
            metadata=json.loads(row["metadata"]) if row.get("metadata") and isinstance(row["metadata"], str) else row.get("metadata"),
            tags=row.get("tags", []),
            expires_at=datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00")) if row.get("expires_at") else None
        )