"""
Integration tests for FrameworkPersistenceAdapter

Tests the complete integration between all persistence components.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime

from fortunamind_persistence.adapters.framework_adapter import FrameworkPersistenceAdapter
from fortunamind_persistence.identity import EmailIdentity
from fortunamind_persistence.subscription import SubscriptionValidator, SubscriptionTier
from fortunamind_persistence.storage.mock_backend import MockStorage
from fortunamind_persistence.rate_limiting import RateLimiter


class TestFrameworkPersistenceAdapter:
    """Integration tests for the complete adapter"""
    
    @pytest.fixture
    async def adapter(self):
        """Create a fully configured adapter for testing"""
        # Use mock components for testing
        storage = MockStorage()
        await storage.initialize()
        
        validator = SubscriptionValidator()
        await validator.initialize()
        
        rate_limiter = RateLimiter()
        
        adapter = FrameworkPersistenceAdapter(
            subscription_validator=validator,
            storage_backend=storage,
            rate_limiter=rate_limiter
        )
        
        return adapter
    
    @pytest.mark.asyncio
    async def test_create_auth_context_valid(self, adapter):
        """Test creating auth context with valid credentials"""
        email = "test@example.com"
        subscription_key = "fm_sub_valid123"
        coinbase_credentials = {
            'api_key': 'test-api-key',
            'api_secret': 'test-api-secret'
        }
        
        auth_context = await adapter.create_auth_context_from_credentials(
            email=email,
            subscription_key=subscription_key,
            coinbase_credentials=coinbase_credentials
        )
        
        assert auth_context is not None
        assert auth_context.api_key == 'test-api-key'
        assert auth_context.api_secret == 'test-api-secret'
        assert auth_context.source == 'persistent_mcp'
        assert len(auth_context.user_id_hash) == 64  # SHA-256 hex string
    
    @pytest.mark.asyncio
    async def test_create_auth_context_without_coinbase(self, adapter):
        """Test creating auth context without Coinbase credentials"""
        email = "test@example.com"
        subscription_key = "fm_sub_valid123"
        
        auth_context = await adapter.create_auth_context_from_credentials(
            email=email,
            subscription_key=subscription_key,
            coinbase_credentials=None
        )
        
        assert auth_context is not None
        assert auth_context.api_key == subscription_key
        assert auth_context.api_secret == ''
        assert auth_context.source == 'persistent_mcp'
    
    @pytest.mark.asyncio
    async def test_create_auth_context_invalid_subscription(self, adapter):
        """Test creating auth context with invalid subscription"""
        email = "test@example.com"
        subscription_key = "invalid_key"  # Wrong format
        
        with pytest.raises(ValueError, match="Invalid subscription"):
            await adapter.create_auth_context_from_credentials(
                email=email,
                subscription_key=subscription_key
            )
    
    @pytest.mark.asyncio
    async def test_create_auth_context_invalid_email(self, adapter):
        """Test creating auth context with invalid email"""
        email = "not-an-email"
        subscription_key = "fm_sub_valid123"
        
        with pytest.raises(ValueError, match="Invalid subscription"):
            await adapter.create_auth_context_from_credentials(
                email=email,
                subscription_key=subscription_key
            )
    
    @pytest.mark.asyncio
    async def test_validate_and_get_user_context(self, adapter):
        """Test complete user context validation and retrieval"""
        email = "test@example.com"
        subscription_key = "fm_sub_context_test"
        
        user_context = await adapter.validate_and_get_user_context(email, subscription_key)
        
        assert user_context['is_valid'] is True
        assert 'user_id' in user_context
        assert user_context['email'] == email
        assert 'tier' in user_context
        assert 'subscription_data' in user_context
        assert len(user_context['user_id']) == 64  # SHA-256 hex
    
    @pytest.mark.asyncio
    async def test_validate_and_get_user_context_invalid(self, adapter):
        """Test user context with invalid subscription"""
        email = "test@example.com"
        subscription_key = "invalid_format"
        
        with pytest.raises(ValueError):
            await adapter.validate_and_get_user_context(email, subscription_key)
    
    @pytest.mark.asyncio
    async def test_check_feature_access(self, adapter):
        """Test feature access checking"""
        # Get valid user context
        email = "test@example.com"
        subscription_key = "fm_sub_feature_test"
        user_context = await adapter.validate_and_get_user_context(email, subscription_key)
        
        # Test feature access (depends on tier definitions)
        has_access = await adapter.check_feature_access(user_context, 'journal_persistence')
        assert isinstance(has_access, bool)
        
        # Test non-existent feature
        has_access_fake = await adapter.check_feature_access(user_context, 'fake_feature')
        assert has_access_fake is False
    
    @pytest.mark.asyncio 
    async def test_check_rate_limit(self, adapter):
        """Test rate limiting integration"""
        # Get valid user context
        email = "ratelimit@example.com"
        subscription_key = "fm_sub_ratelimit_test"
        user_context = await adapter.validate_and_get_user_context(email, subscription_key)
        
        # First request should be allowed
        within_limits = await adapter.check_rate_limit(user_context, 'api_call')
        assert within_limits is True
        
        # Record the request for next check
        # (In real usage, this would be done automatically)
    
    @pytest.mark.asyncio
    async def test_store_journal_entry_with_validation(self, adapter):
        """Test complete journal entry storage with validation"""
        email = "journal@example.com"
        subscription_key = "fm_sub_journal_test"
        entry = "Test journal entry for integration testing"
        metadata = {"test": True, "timestamp": datetime.now().isoformat()}
        
        result = await adapter.store_journal_entry_with_validation(
            email=email,
            subscription_key=subscription_key,
            entry=entry,
            metadata=metadata
        )
        
        assert result['success'] is True
        assert 'entry_id' in result
        assert 'tier' in result
        assert result['entry_id']  # Should have an ID
    
    @pytest.mark.asyncio
    async def test_store_journal_entry_invalid_subscription(self, adapter):
        """Test journal storage with invalid subscription"""
        email = "journal@example.com"
        subscription_key = "invalid_key"
        entry = "Test entry"
        
        result = await adapter.store_journal_entry_with_validation(
            email=email,
            subscription_key=subscription_key,
            entry=entry
        )
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_journal_entries_with_validation(self, adapter):
        """Test journal entry retrieval with validation"""
        email = "retrieval@example.com"
        subscription_key = "fm_sub_retrieval_test"
        
        # First store some entries
        await adapter.store_journal_entry_with_validation(
            email=email,
            subscription_key=subscription_key,
            entry="First entry"
        )
        await adapter.store_journal_entry_with_validation(
            email=email,
            subscription_key=subscription_key,
            entry="Second entry"
        )
        
        # Now retrieve them
        result = await adapter.get_journal_entries_with_validation(
            email=email,
            subscription_key=subscription_key,
            limit=10
        )
        
        assert result['success'] is True
        assert 'entries' in result
        assert result['count'] >= 2
        assert len(result['entries']) >= 2
    
    @pytest.mark.asyncio
    async def test_get_journal_entries_invalid_subscription(self, adapter):
        """Test journal retrieval with invalid subscription"""
        email = "retrieval@example.com"
        subscription_key = "invalid_key"
        
        result = await adapter.get_journal_entries_with_validation(
            email=email,
            subscription_key=subscription_key
        )
        
        assert result['success'] is False
        assert result['entries'] == []
    
    @pytest.mark.asyncio
    async def test_get_user_stats(self, adapter):
        """Test user statistics retrieval"""
        email = "stats@example.com"
        subscription_key = "fm_sub_stats_test"
        
        # Store some data first
        await adapter.store_journal_entry_with_validation(
            email=email,
            subscription_key=subscription_key,
            entry="Stats test entry"
        )
        
        # Get stats
        result = await adapter.get_user_stats(email, subscription_key)
        
        assert result['success'] is True
        assert 'user_id_hash' in result
        assert 'tier' in result
        assert 'storage' in result
        assert 'rate_limits' in result
        assert 'timestamp' in result
    
    @pytest.mark.asyncio
    async def test_get_user_stats_invalid_subscription(self, adapter):
        """Test user stats with invalid subscription"""
        email = "stats@example.com"
        subscription_key = "invalid_key"
        
        result = await adapter.get_user_stats(email, subscription_key)
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_health_check(self, adapter):
        """Test adapter health check"""
        health = await adapter.health_check()
        
        assert 'timestamp' in health
        assert 'overall' in health
        assert 'components' in health
        assert 'storage' in health['components']
        assert 'subscription_validator' in health['components']
    
    @pytest.mark.asyncio
    async def test_email_normalization_consistency(self, adapter):
        """Test that email normalization works consistently across operations"""
        # These emails should be treated as the same user
        emails = [
            "test@example.com",
            "TEST@EXAMPLE.COM",
            "  test@example.com  "
        ]
        subscription_key = "fm_sub_consistency_test"
        
        user_contexts = []
        for email in emails:
            context = await adapter.validate_and_get_user_context(email, subscription_key)
            user_contexts.append(context)
        
        # All should have the same user_id
        user_ids = [ctx['user_id'] for ctx in user_contexts]
        assert len(set(user_ids)) == 1, f"Expected same user_id, got: {user_ids}"
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, adapter):
        """Test concurrent operations on the adapter"""
        email = "concurrent@example.com"
        subscription_key = "fm_sub_concurrent_test"
        
        # Create multiple concurrent operations
        tasks = []
        
        # Validation tasks
        for i in range(5):
            task = adapter.validate_and_get_user_context(email, subscription_key)
            tasks.append(task)
        
        # Storage tasks
        for i in range(5):
            task = adapter.store_journal_entry_with_validation(
                email=email,
                subscription_key=subscription_key,
                entry=f"Concurrent entry {i}"
            )
            tasks.append(task)
        
        # Execute all concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check that no exceptions occurred
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Unexpected exceptions: {exceptions}"
        
        # Validation results should be consistent
        validation_results = results[:5]
        user_ids = [r['user_id'] for r in validation_results]
        assert len(set(user_ids)) == 1, "User IDs should be consistent"
    
    @pytest.mark.asyncio
    async def test_extract_email_from_auth_context(self, adapter):
        """Test extracting email from framework auth context"""
        # Create a mock auth context
        class MockAuthContext:
            def __init__(self, signature):
                self.signature = signature
        
        auth_context = MockAuthContext("test@example.com")
        email = adapter.extract_email_from_auth_context(auth_context)
        assert email == "test@example.com"
        
        # Test with None signature
        auth_context_none = MockAuthContext(None)
        email_none = adapter.extract_email_from_auth_context(auth_context_none)
        assert email_none is None
    
    @pytest.mark.asyncio
    async def test_extract_user_id_from_auth_context(self, adapter):
        """Test extracting user ID from framework auth context"""
        class MockAuthContext:
            def __init__(self, user_id_hash):
                self.user_id_hash = user_id_hash
        
        test_user_id = "a1b2c3d4e5f6"
        auth_context = MockAuthContext(test_user_id)
        
        extracted_id = adapter.extract_user_id_from_auth_context(auth_context)
        assert extracted_id == test_user_id
    
    @pytest.mark.asyncio
    async def test_data_isolation_between_users(self, adapter):
        """Test that different users' data is properly isolated"""
        # Create two different users
        user1_email = "user1@example.com"
        user2_email = "user2@example.com"
        subscription_key = "fm_sub_isolation_test"
        
        # Store data for each user
        result1 = await adapter.store_journal_entry_with_validation(
            email=user1_email,
            subscription_key=subscription_key,
            entry="User 1 entry"
        )
        
        result2 = await adapter.store_journal_entry_with_validation(
            email=user2_email,
            subscription_key=subscription_key,
            entry="User 2 entry"
        )
        
        assert result1['success'] is True
        assert result2['success'] is True
        
        # Retrieve data for each user
        entries1 = await adapter.get_journal_entries_with_validation(
            email=user1_email,
            subscription_key=subscription_key
        )
        
        entries2 = await adapter.get_journal_entries_with_validation(
            email=user2_email,
            subscription_key=subscription_key
        )
        
        # Each user should only see their own data
        assert entries1['success'] is True
        assert entries2['success'] is True
        
        user1_entries = [e for e in entries1['entries'] if 'User 1' in e['entry']]
        user2_entries = [e for e in entries2['entries'] if 'User 2' in e['entry']]
        
        assert len(user1_entries) >= 1
        assert len(user2_entries) >= 1
        
        # Verify no cross-contamination
        user1_has_user2_data = any('User 2' in e['entry'] for e in entries1['entries'])
        user2_has_user1_data = any('User 1' in e['entry'] for e in entries2['entries'])
        
        assert not user1_has_user2_data, "User 1 should not see User 2's data"
        assert not user2_has_user1_data, "User 2 should not see User 1's data"