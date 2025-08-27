"""
Tests for SubscriptionValidator class

Tests subscription validation, caching, and tier management.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from fortunamind_persistence.subscription.validator import (
    SubscriptionValidator, 
    ValidationResult,
    SubscriptionData,
    SubscriptionTier
)


class TestSubscriptionValidator:
    """Test cases for SubscriptionValidator functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = SubscriptionValidator()
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test validator initialization"""
        await self.validator.initialize()
        assert hasattr(self.validator, 'cache')
        assert hasattr(self.validator, 'identity')
    
    @pytest.mark.asyncio
    async def test_validate_subscription_key_format(self):
        """Test subscription key format validation"""
        # Valid formats
        valid_keys = [
            "fm_sub_abc123def456",
            "fm_sub_1234567890abcdef",
            "fm_sub_test_key_123"
        ]
        
        for key in valid_keys:
            result = await self.validator.validate("test@example.com", key)
            # Should not fail on format (may fail on lookup)
            assert isinstance(result, ValidationResult)
    
    @pytest.mark.asyncio
    async def test_validate_invalid_format(self):
        """Test validation with invalid subscription key format"""
        invalid_keys = [
            "invalid-key",
            "sub_abc123",  # Wrong prefix
            "fm_wrong_abc123",  # Wrong format
            "",
            None
        ]
        
        for key in invalid_keys:
            result = await self.validator.validate("test@example.com", key)
            assert not result.is_valid
            assert "format" in result.error_message.lower() or "invalid" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_validate_invalid_email(self):
        """Test validation with invalid email"""
        invalid_emails = [
            "not-an-email",
            "@example.com",
            "test@",
            "",
            None
        ]
        
        for email in invalid_emails:
            result = await self.validator.validate(email, "fm_sub_valid123")
            assert not result.is_valid
            assert "email" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_validate_mock_mode(self):
        """Test validation in mock mode (development)"""
        # In mock mode, any fm_sub_ key should be valid
        result = await self.validator.validate("test@example.com", "fm_sub_mock123")
        
        assert result.is_valid
        assert result.tier == SubscriptionTier.PREMIUM
        assert result.subscription_data is not None
        assert result.subscription_data.is_mock is True
    
    @pytest.mark.asyncio
    async def test_caching_behavior(self):
        """Test that validation results are cached"""
        email = "test@example.com"
        key = "fm_sub_cache_test"
        
        # First call
        result1 = await self.validator.validate(email, key)
        
        # Second call (should use cache)
        result2 = await self.validator.validate(email, key)
        
        # Results should be identical
        assert result1.is_valid == result2.is_valid
        assert result1.tier == result2.tier
        
        # Check cache was used (should be faster second time, but hard to test timing)
        cache_key = self.validator._generate_cache_key(email, key)
        assert cache_key in self.validator.cache.cache
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test cache expiration behavior"""
        with patch.object(self.validator, 'cache_ttl_minutes', 0.01):  # Very short TTL
            email = "test@example.com"
            key = "fm_sub_expire_test"
            
            # First call
            result1 = await self.validator.validate(email, key)
            
            # Wait for cache to expire
            await asyncio.sleep(0.1)
            
            # Second call should not use expired cache
            result2 = await self.validator.validate(email, key)
            
            # Results should still be consistent
            assert result1.is_valid == result2.is_valid
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Test cache key generation"""
        # Same inputs should generate same cache key
        key1 = self.validator._generate_cache_key("test@example.com", "fm_sub_123")
        key2 = self.validator._generate_cache_key("test@example.com", "fm_sub_123")
        assert key1 == key2
        
        # Different inputs should generate different cache keys
        key3 = self.validator._generate_cache_key("different@example.com", "fm_sub_123")
        assert key1 != key3
        
        key4 = self.validator._generate_cache_key("test@example.com", "fm_sub_456")
        assert key1 != key4
    
    @pytest.mark.asyncio
    async def test_email_normalization_in_validation(self):
        """Test that email normalization affects validation consistently"""
        key = "fm_sub_normalize_test"
        
        # These should all use the same cache entry due to normalization
        email_variants = [
            "test@example.com",
            "TEST@EXAMPLE.COM",
            "  test@example.com  "
        ]
        
        results = []
        for email in email_variants:
            result = await self.validator.validate(email, key)
            results.append(result)
        
        # All results should be identical
        for i in range(1, len(results)):
            assert results[0].is_valid == results[i].is_valid
            assert results[0].tier == results[i].tier
    
    def test_subscription_data_creation(self):
        """Test SubscriptionData model creation"""
        data = SubscriptionData(
            email="test@example.com",
            subscription_key="fm_sub_test123",
            tier=SubscriptionTier.PREMIUM,
            expires_at=datetime.now() + timedelta(days=30)
        )
        
        assert data.email == "test@example.com"
        assert data.subscription_key == "fm_sub_test123"
        assert data.tier == SubscriptionTier.PREMIUM
        assert not data.is_mock  # Should default to False
        
        # Test mock data
        mock_data = SubscriptionData(
            email="test@example.com",
            subscription_key="fm_sub_mock123",
            tier=SubscriptionTier.PREMIUM,
            is_mock=True
        )
        assert mock_data.is_mock is True
    
    def test_validation_result_creation(self):
        """Test ValidationResult model creation"""
        # Valid result
        subscription_data = SubscriptionData(
            email="test@example.com",
            subscription_key="fm_sub_test123",
            tier=SubscriptionTier.PREMIUM
        )
        
        result = ValidationResult(
            is_valid=True,
            tier=SubscriptionTier.PREMIUM,
            subscription_data=subscription_data
        )
        
        assert result.is_valid is True
        assert result.tier == SubscriptionTier.PREMIUM
        assert result.subscription_data == subscription_data
        assert result.error_message is None
        
        # Invalid result
        error_result = ValidationResult(
            is_valid=False,
            error_message="Test error"
        )
        
        assert error_result.is_valid is False
        assert error_result.tier is None
        assert error_result.subscription_data is None
        assert error_result.error_message == "Test error"
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check functionality"""
        await self.validator.initialize()
        
        health = await self.validator.health_check()
        
        assert "status" in health
        assert "cache_size" in health
        assert "last_validation" in health
        assert isinstance(health["cache_size"], int)
    
    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test cleanup functionality"""
        await self.validator.initialize()
        
        # Add some items to cache
        await self.validator.validate("test@example.com", "fm_sub_cleanup_test")
        
        # Cleanup should not raise errors
        await self.validator.cleanup()
    
    @pytest.mark.asyncio
    async def test_clear_cache(self):
        """Test cache clearing"""
        await self.validator.initialize()
        
        # Add item to cache
        await self.validator.validate("test@example.com", "fm_sub_clear_test")
        assert len(self.validator.cache.cache) > 0
        
        # Clear cache
        self.validator.clear_cache()
        assert len(self.validator.cache.cache) == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_validation(self):
        """Test concurrent validation calls"""
        await self.validator.initialize()
        
        email = "concurrent@example.com"
        key = "fm_sub_concurrent_test"
        
        # Make multiple concurrent calls
        tasks = [
            self.validator.validate(email, key)
            for _ in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result.is_valid == first_result.is_valid
            assert result.tier == first_result.tier
    
    @pytest.mark.asyncio
    async def test_different_tiers_mock(self):
        """Test different subscription tiers in mock mode"""
        # Mock mode should return premium by default
        result = await self.validator.validate("test@example.com", "fm_sub_tier_test")
        assert result.tier == SubscriptionTier.PREMIUM
        
        # All tiers should be valid in mock mode
        for tier in SubscriptionTier:
            result = await self.validator.validate(f"test_{tier.value}@example.com", f"fm_sub_{tier.value}")
            assert result.is_valid
    
    @pytest.mark.asyncio 
    async def test_subscription_expiry_mock(self):
        """Test subscription expiry handling in mock mode"""
        result = await self.validator.validate("test@example.com", "fm_sub_expiry_test")
        
        if result.subscription_data and result.subscription_data.expires_at:
            # Mock subscriptions should have reasonable expiry
            assert result.subscription_data.expires_at > datetime.now()
    
    def test_tier_enum_values(self):
        """Test subscription tier enum values"""
        # Ensure all expected tiers exist
        expected_tiers = ["FREE", "BASIC", "PREMIUM", "ENTERPRISE"]
        actual_tiers = [tier.name for tier in SubscriptionTier]
        
        for tier in expected_tiers:
            assert tier in actual_tiers
        
        # Test string values
        assert SubscriptionTier.FREE.value == "free"
        assert SubscriptionTier.PREMIUM.value == "premium"
    
    @pytest.mark.parametrize("email,key,should_be_valid", [
        ("valid@example.com", "fm_sub_valid123", True),
        ("valid@gmail.com", "fm_sub_gmail_test", True),  
        ("invalid-email", "fm_sub_valid123", False),
        ("valid@example.com", "invalid_key", False),
        ("valid@example.com", "", False),
        ("", "fm_sub_valid123", False),
    ])
    @pytest.mark.asyncio
    async def test_validation_parametrized(self, email, key, should_be_valid):
        """Parametrized test for various validation scenarios"""
        result = await self.validator.validate(email, key)
        assert result.is_valid == should_be_valid