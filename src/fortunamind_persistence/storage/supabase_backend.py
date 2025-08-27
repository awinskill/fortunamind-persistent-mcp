"""
Supabase Storage Backend

Production-ready storage implementation using Supabase PostgreSQL with
Row Level Security for user isolation.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import structlog

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = Any

from .interfaces import PersistentStorageInterface, StorageRecord, RecordType

logger = structlog.get_logger(__name__)


class SupabaseStorage(PersistentStorageInterface):
    """
    Supabase-based storage implementation with Row Level Security.
    
    Uses PostgreSQL with RLS policies to ensure user data isolation.
    Provides production-ready persistence for FortunaMind services.
    """
    
    def __init__(self):
        """
        Initialize Supabase storage.
        
        Reads configuration from environment variables:
        - SUPABASE_URL: Supabase project URL
        - SUPABASE_ANON_KEY: Supabase anonymous key (for RLS-protected operations)
        
        For development, these can be set in .env file.
        For production, use secure environment variables in Render.
        """
        if not SUPABASE_AVAILABLE:
            raise ImportError(
                "Supabase not available. Install with: pip install supabase"
            )
        
        import os
        
        # Read from environment variables (secure)
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_ANON_KEY')
        
        # Validate required environment variables
        if not self.url:
            raise ValueError(
                "SUPABASE_URL environment variable is required. "
                "Please set it to your Supabase project URL."
            )
        
        if not self.key:
            raise ValueError(
                "SUPABASE_ANON_KEY environment variable is required. "
                "Please set it to your Supabase anonymous key."
            )
        
        self.client: Optional[Client] = None
        self._initialized = False
        
        logger.info(
            "Supabase storage configured from environment",
            url_prefix=self.url[:30] + "..." if len(self.url) > 30 else self.url
        )
    
    async def initialize(self) -> bool:
        """
        Initialize the Supabase client and verify connection.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Create Supabase client (url and key already validated in __init__)
            self.client = create_client(self.url, self.key)
            
            # Test connection with a simple query to a table we know exists
            # Use user_subscriptions since it's guaranteed to exist after migration
            try:
                result = self.client.table('user_subscriptions').select('count').limit(1).execute()
                logger.debug("Supabase connection test successful")
            except Exception as e:
                # If tables don't exist yet, that's OK - migration hasn't run
                logger.debug("Supabase tables may not exist yet (migration needed)", error=str(e))
            
            self._initialized = True
            
            logger.info(
                "Supabase storage initialized successfully",
                url_prefix=self.url[:30] + "..." if len(self.url) > 30 else self.url
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to initialize Supabase storage", error=str(e))
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check Supabase connection health.
        
        Returns:
            Dict with health status information
        """
        if not self._initialized or not self.client:
            return {
                "status": "unhealthy",
                "error": "Not initialized",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            # Test with a simple query on our actual table
            start_time = datetime.utcnow()
            result = self.client.table('user_subscriptions').select('count').limit(1).execute()
            end_time = datetime.utcnow()
            
            return {
                "status": "healthy",
                "response_time_ms": int((end_time - start_time).total_seconds() * 1000),
                "connection": "ok",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy", 
                "error": str(e),
                "connection": "failed",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _set_rls_context(self, user_id: str):
        """
        Set Row Level Security context for the current user.
        
        This ensures all database operations are scoped to the specific user.
        """
        if not self.client:
            raise RuntimeError("Storage not initialized")
        
        # Set the app.user_id setting for RLS policies
        self.client.rpc('set_config', {
            'setting_name': 'app.user_id',
            'new_value': user_id,
            'is_local': True
        }).execute()
    
    async def store_journal_entry(
        self,
        user_id: str,
        entry: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a trading journal entry"""
        self._set_rls_context(user_id)
        
        entry_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        try:
            result = self.client.table('trading_journal').insert({
                'id': entry_id,
                'user_id': user_id,
                'entry': entry,
                'metadata': json.dumps(metadata or {}),
                'created_at': now.isoformat(),
                'updated_at': now.isoformat()
            }).execute()
            
            logger.debug(
                "Journal entry stored",
                user_id_hash=user_id[:8],
                entry_id=entry_id
            )
            
            return entry_id
            
        except Exception as e:
            logger.error(
                "Failed to store journal entry",
                error=str(e),
                user_id_hash=user_id[:8]
            )
            raise
    
    async def get_journal_entries(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve journal entries for a user"""
        self._set_rls_context(user_id)
        
        try:
            query = self.client.table('trading_journal')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .offset(offset)
            
            # Add date filters if provided
            if start_date:
                query = query.gte('created_at', start_date.isoformat())
            if end_date:
                query = query.lte('created_at', end_date.isoformat())
            
            result = query.execute()
            
            # Process results
            entries = []
            for row in result.data:
                entry = dict(row)
                # Parse metadata JSON
                if entry.get('metadata'):
                    try:
                        entry['metadata'] = json.loads(entry['metadata'])
                    except json.JSONDecodeError:
                        entry['metadata'] = {}
                entries.append(entry)
            
            logger.debug(
                "Retrieved journal entries",
                user_id_hash=user_id[:8],
                count=len(entries)
            )
            
            return entries
            
        except Exception as e:
            logger.error(
                "Failed to retrieve journal entries",
                error=str(e),
                user_id_hash=user_id[:8]
            )
            raise
    
    async def update_journal_entry(
        self,
        user_id: str,
        entry_id: str,
        entry: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update an existing journal entry"""
        self._set_rls_context(user_id)
        
        try:
            result = self.client.table('trading_journal')\
                .update({
                    'entry': entry,
                    'metadata': json.dumps(metadata or {}),
                    'updated_at': datetime.utcnow().isoformat()
                })\
                .eq('id', entry_id)\
                .eq('user_id', user_id)\
                .execute()
            
            success = len(result.data) > 0
            
            logger.debug(
                "Journal entry update",
                user_id_hash=user_id[:8],
                entry_id=entry_id,
                success=success
            )
            
            return success
            
        except Exception as e:
            logger.error(
                "Failed to update journal entry",
                error=str(e),
                user_id_hash=user_id[:8],
                entry_id=entry_id
            )
            return False
    
    async def delete_journal_entry(
        self,
        user_id: str,
        entry_id: str
    ) -> bool:
        """Delete a journal entry"""
        self._set_rls_context(user_id)
        
        try:
            result = self.client.table('trading_journal')\
                .delete()\
                .eq('id', entry_id)\
                .eq('user_id', user_id)\
                .execute()
            
            success = len(result.data) > 0
            
            logger.debug(
                "Journal entry deletion",
                user_id_hash=user_id[:8],
                entry_id=entry_id,
                success=success
            )
            
            return success
            
        except Exception as e:
            logger.error(
                "Failed to delete journal entry",
                error=str(e),
                user_id_hash=user_id[:8],
                entry_id=entry_id
            )
            return False
    
    async def store_user_preference(
        self,
        user_id: str,
        key: str,
        value: Any
    ) -> bool:
        """Store a user preference"""
        self._set_rls_context(user_id)
        
        try:
            # Use upsert to handle both insert and update
            result = self.client.table('user_preferences')\
                .upsert({
                    'user_id': user_id,
                    'preference_key': key,
                    'preference_value': json.dumps(value),
                    'updated_at': datetime.utcnow().isoformat()
                })\
                .execute()
            
            success = len(result.data) > 0
            
            logger.debug(
                "User preference stored",
                user_id_hash=user_id[:8],
                key=key,
                success=success
            )
            
            return success
            
        except Exception as e:
            logger.error(
                "Failed to store user preference",
                error=str(e),
                user_id_hash=user_id[:8],
                key=key
            )
            return False
    
    async def get_user_preference(
        self,
        user_id: str,
        key: str,
        default: Any = None
    ) -> Any:
        """Get a user preference"""
        self._set_rls_context(user_id)
        
        try:
            result = self.client.table('user_preferences')\
                .select('preference_value')\
                .eq('user_id', user_id)\
                .eq('preference_key', key)\
                .execute()
            
            if result.data:
                try:
                    return json.loads(result.data[0]['preference_value'])
                except json.JSONDecodeError:
                    return default
            
            return default
            
        except Exception as e:
            logger.error(
                "Failed to get user preference",
                error=str(e),
                user_id_hash=user_id[:8],
                key=key
            )
            return default
    
    async def get_user_preferences(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get all user preferences"""
        self._set_rls_context(user_id)
        
        try:
            result = self.client.table('user_preferences')\
                .select('preference_key, preference_value')\
                .eq('user_id', user_id)\
                .execute()
            
            preferences = {}
            for row in result.data:
                try:
                    preferences[row['preference_key']] = json.loads(row['preference_value'])
                except json.JSONDecodeError:
                    # Skip invalid JSON
                    continue
            
            return preferences
            
        except Exception as e:
            logger.error(
                "Failed to get user preferences",
                error=str(e),
                user_id_hash=user_id[:8]
            )
            return {}
    
    async def store_record(
        self,
        record: StorageRecord
    ) -> str:
        """Store a generic record"""
        self._set_rls_context(record.user_id)
        
        try:
            result = self.client.table('storage_records')\
                .insert({
                    'id': record.id,
                    'user_id': record.user_id,
                    'record_type': record.record_type.value,
                    'data': json.dumps(record.data),
                    'metadata': json.dumps(record.metadata or {}),
                    'created_at': record.created_at.isoformat(),
                    'updated_at': record.updated_at.isoformat() if record.updated_at else record.created_at.isoformat()
                })\
                .execute()
            
            logger.debug(
                "Generic record stored",
                user_id_hash=record.user_id[:8],
                record_id=record.id,
                record_type=record.record_type.value
            )
            
            return record.id
            
        except Exception as e:
            logger.error(
                "Failed to store generic record",
                error=str(e),
                user_id_hash=record.user_id[:8],
                record_id=record.id
            )
            raise
    
    async def get_record(
        self,
        user_id: str,
        record_id: str
    ) -> Optional[StorageRecord]:
        """Get a specific record"""
        self._set_rls_context(user_id)
        
        try:
            result = self.client.table('storage_records')\
                .select('*')\
                .eq('id', record_id)\
                .eq('user_id', user_id)\
                .execute()
            
            if not result.data:
                return None
            
            row = result.data[0]
            return self._row_to_storage_record(row)
            
        except Exception as e:
            logger.error(
                "Failed to get record",
                error=str(e),
                user_id_hash=user_id[:8],
                record_id=record_id
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
        self._set_rls_context(user_id)
        
        try:
            query = self.client.table('storage_records')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .offset(offset)
            
            if record_type:
                query = query.eq('record_type', record_type.value)
            
            result = query.execute()
            
            records = []
            for row in result.data:
                record = self._row_to_storage_record(row)
                if record:
                    records.append(record)
            
            return records
            
        except Exception as e:
            logger.error(
                "Failed to query records",
                error=str(e),
                user_id_hash=user_id[:8]
            )
            return []
    
    async def update_record(
        self,
        user_id: str,
        record_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update a record"""
        self._set_rls_context(user_id)
        
        try:
            result = self.client.table('storage_records')\
                .update({
                    'data': json.dumps(data),
                    'metadata': json.dumps(metadata or {}),
                    'updated_at': datetime.utcnow().isoformat()
                })\
                .eq('id', record_id)\
                .eq('user_id', user_id)\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(
                "Failed to update record",
                error=str(e),
                user_id_hash=user_id[:8],
                record_id=record_id
            )
            return False
    
    async def delete_record(
        self,
        user_id: str,
        record_id: str
    ) -> bool:
        """Delete a record"""
        self._set_rls_context(user_id)
        
        try:
            result = self.client.table('storage_records')\
                .delete()\
                .eq('id', record_id)\
                .eq('user_id', user_id)\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(
                "Failed to delete record",
                error=str(e),
                user_id_hash=user_id[:8],
                record_id=record_id
            )
            return False
    
    async def get_storage_stats(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get storage statistics for a user"""
        self._set_rls_context(user_id)
        
        try:
            # Get journal entry count
            journal_result = self.client.table('trading_journal')\
                .select('id', count='exact')\
                .eq('user_id', user_id)\
                .execute()
            
            # Get preferences count
            prefs_result = self.client.table('user_preferences')\
                .select('preference_key', count='exact')\
                .eq('user_id', user_id)\
                .execute()
            
            # Get generic records count by type
            records_result = self.client.table('storage_records')\
                .select('record_type', count='exact')\
                .eq('user_id', user_id)\
                .execute()
            
            return {
                'journal_entries': journal_result.count or 0,
                'preferences': prefs_result.count or 0,
                'storage_records': records_result.count or 0,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(
                "Failed to get storage stats",
                error=str(e),
                user_id_hash=user_id[:8]
            )
            return {}
    
    async def cleanup_expired_records(
        self,
        retention_days: int = 365
    ) -> int:
        """Clean up expired records"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        try:
            # Note: This would typically be done by an admin/system user
            result = self.client.table('storage_records')\
                .delete()\
                .lt('created_at', cutoff_date.isoformat())\
                .execute()
            
            count = len(result.data) if result.data else 0
            
            logger.info(
                "Cleaned up expired records",
                count=count,
                retention_days=retention_days
            )
            
            return count
            
        except Exception as e:
            logger.error(
                "Failed to cleanup expired records",
                error=str(e)
            )
            return 0
    
    def _row_to_storage_record(self, row: Dict[str, Any]) -> Optional[StorageRecord]:
        """Convert database row to StorageRecord"""
        try:
            return StorageRecord(
                id=row['id'],
                user_id=row['user_id'],
                record_type=RecordType(row['record_type']),
                data=json.loads(row['data']) if row['data'] else {},
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
                metadata=json.loads(row['metadata']) if row['metadata'] else None
            )
        except Exception as e:
            logger.error("Failed to convert row to StorageRecord", error=str(e))
            return None