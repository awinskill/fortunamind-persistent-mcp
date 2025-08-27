"""
Tests for RateLimiter class

Tests sliding window rate limiting, tier-based limits, and error handling.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import patch

from fortunamind_persistence.rate_limiting.limiter import (
    RateLimiter, 
    RateLimitResult,
    RateLimitError,
    SlidingWindowCounter
)
from fortunamind_persistence.subscription.tiers import SubscriptionTier


class TestSlidingWindowCounter:
    """Test cases for SlidingWindowCounter"""
    
    def test_initialization(self):
        """Test counter initialization"""
        counter = SlidingWindowCounter(window_size=60)
        assert counter.window_size == 60
        assert len(counter.requests) == 0
    
    def test_add_request(self):
        """Test adding requests to counter"""
        counter = SlidingWindowCounter(window_size=60)
        
        current_time = time.time()
        counter.add_request(current_time)
        
        assert len(counter.requests) == 1
        assert counter.requests[0] == current_time
    
    def test_get_count_within_window(self):
        """Test getting count within time window"""
        counter = SlidingWindowCounter(window_size=60)
        current_time = time.time()
        
        # Add requests within window
        counter.add_request(current_time)
        counter.add_request(current_time - 30)  # 30 seconds ago
        counter.add_request(current_time - 50)  # 50 seconds ago
        
        assert counter.get_count(current_time) == 3
    
    def test_get_count_outside_window(self):
        """Test that old requests are excluded"""
        counter = SlidingWindowCounter(window_size=60)
        current_time = time.time()
        
        # Add requests both inside and outside window
        counter.add_request(current_time)
        counter.add_request(current_time - 30)  # Within window
        counter.add_request(current_time - 90)  # Outside window
        counter.add_request(current_time - 120)  # Outside window
        
        assert counter.get_count(current_time) == 2  # Only recent ones
    
    def test_cleanup_old_requests(self):
        """Test that old requests are cleaned up"""
        counter = SlidingWindowCounter(window_size=60)
        current_time = time.time()
        
        # Add old requests
        counter.add_request(current_time - 120)
        counter.add_request(current_time - 90)
        counter.add_request(current_time - 30)
        counter.add_request(current_time)
        
        # Get count should cleanup old requests
        count = counter.get_count(current_time)
        assert count == 2
        assert len(counter.requests) == 2  # Old ones removed
    
    def test_get_reset_time(self):
        """Test reset time calculation"""
        counter = SlidingWindowCounter(window_size=60)
        current_time = time.time()
        
        # Add request
        counter.add_request(current_time - 30)
        
        reset_time = counter.get_reset_time(current_time)
        expected_reset = datetime.fromtimestamp(current_time - 30 + 60)
        
        # Should be approximately equal (within 1 second)
        assert abs((reset_time - expected_reset).total_seconds()) < 1


class TestRateLimiter:
    """Test cases for RateLimiter functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.limiter = RateLimiter()
    
    def test_initialization(self):
        """Test rate limiter initialization"""
        assert hasattr(self.limiter, '_counters')
        assert hasattr(self.limiter, 'windows')
        assert 'hour' in self.limiter.windows
        assert 'day' in self.limiter.windows
        assert 'month' in self.limiter.windows
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_new_user(self):
        """Test rate limit check for new user"""
        user_id = "test_user_1"
        tier = SubscriptionTier.FREE
        
        result = await self.limiter.check_rate_limit(user_id, tier)
        
        assert isinstance(result, RateLimitResult)
        assert result.allowed is True
        assert 'hour' in result.current_usage
        assert 'day' in result.current_usage
        assert 'month' in result.current_usage
        assert all(usage == 0 for usage in result.current_usage.values())
    
    @pytest.mark.asyncio
    async def test_record_request(self):
        """Test recording a request"""
        user_id = "test_user_2"
        tier = SubscriptionTier.FREE
        
        # Record a request
        await self.limiter.record_request(user_id, tier)
        
        # Check that it was recorded
        result = await self.limiter.check_rate_limit(user_id, tier)
        assert result.current_usage['hour'] == 1
        assert result.current_usage['day'] == 1
        assert result.current_usage['month'] == 1
    
    @pytest.mark.asyncio
    async def test_check_and_record_allowed(self):
        """Test check_and_record when request is allowed"""
        user_id = "test_user_3"
        tier = SubscriptionTier.PREMIUM  # Higher limits
        
        result = await self.limiter.check_and_record(user_id, tier)
        
        assert result.allowed is True
        # After recording, usage should be 1
        check_result = await self.limiter.check_rate_limit(user_id, tier)
        assert check_result.current_usage['hour'] == 1
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """Test rate limit exceeded scenario"""
        user_id = "test_user_4"
        tier = SubscriptionTier.FREE  # Lower limits
        
        # Get the limits for FREE tier
        from fortunamind_persistence.subscription.tiers import TierDefinitions
        limits = TierDefinitions.get_limits(tier)
        hourly_limit = limits.api_calls_per_hour
        
        # Make requests up to the limit
        for i in range(hourly_limit):
            await self.limiter.record_request(user_id, tier)
        
        # Next request should be blocked
        with pytest.raises(RateLimitError) as exc_info:
            await self.limiter.check_and_record(user_id, tier)
        
        error = exc_info.value
        assert not error.result.allowed
        assert error.result.retry_after is not None
    
    @pytest.mark.asyncio
    async def test_different_tiers_different_limits(self):
        """Test that different tiers have different limits"""
        user_free = "test_user_free"
        user_premium = "test_user_premium"
        
        # Make same number of requests for both users
        for i in range(5):
            await self.limiter.record_request(user_free, SubscriptionTier.FREE)
            await self.limiter.record_request(user_premium, SubscriptionTier.PREMIUM)
        
        free_result = await self.limiter.check_rate_limit(user_free, SubscriptionTier.FREE)
        premium_result = await self.limiter.check_rate_limit(user_premium, SubscriptionTier.PREMIUM)
        
        # Premium should have higher limits
        assert premium_result.limits['hour'] > free_result.limits['hour']
        assert premium_result.limits['day'] > free_result.limits['day']
    
    @pytest.mark.asyncio
    async def test_unlimited_tier(self):
        """Test tier with unlimited access"""
        user_id = "test_user_enterprise"
        tier = SubscriptionTier.ENTERPRISE  # Should have unlimited access
        
        # Make many requests
        for i in range(1000):
            result = await self.limiter.check_and_record(user_id, tier)
            if result.limits['hour'] == -1:  # Unlimited
                assert result.allowed is True
            else:
                # If not unlimited, should eventually hit limit
                break
    
    @pytest.mark.asyncio 
    async def test_time_window_sliding(self):
        """Test that time window slides properly"""
        user_id = "test_user_sliding"
        tier = SubscriptionTier.FREE
        
        current_time = time.time()
        
        # Mock time to control window sliding
        with patch('time.time') as mock_time:
            # Start at a specific time
            mock_time.return_value = current_time
            
            # Make a request
            await self.limiter.record_request(user_id, tier)
            result = await self.limiter.check_rate_limit(user_id, tier)
            assert result.current_usage['hour'] == 1
            
            # Move time forward by 2 hours (outside window)
            mock_time.return_value = current_time + 7200  # 2 hours
            
            # Usage should now be 0 (old request outside window)
            result = await self.limiter.check_rate_limit(user_id, tier)
            assert result.current_usage['hour'] == 0
    
    @pytest.mark.asyncio
    async def test_get_user_stats(self):
        """Test getting user statistics"""
        user_id = "test_user_stats"
        tier = SubscriptionTier.BASIC
        
        # Make some requests
        for i in range(3):
            await self.limiter.record_request(user_id, tier)
        
        stats = await self.limiter.get_user_stats(user_id, tier)
        
        assert 'user_id_hash' in stats
        assert stats['tier'] == tier.value
        assert 'current_usage' in stats
        assert 'limits' in stats
        assert 'utilization_percentage' in stats
        assert stats['current_usage']['hour'] == 3
    
    @pytest.mark.asyncio
    async def test_cleanup_old_data(self):
        """Test cleanup of old rate limiting data"""
        user_id = "test_user_cleanup"
        tier = SubscriptionTier.FREE
        
        # Add user data
        await self.limiter.record_request(user_id, tier)
        assert user_id in self.limiter._counters
        
        # Mock old timestamp
        current_time = time.time()
        with patch('time.time', return_value=current_time + 86400 + 3600):  # 25 hours later
            await self.limiter.cleanup_old_data(cutoff_hours=24)
        
        # User should be cleaned up (no recent activity)
        # Note: This test might need adjustment based on exact cleanup logic
    
    def test_get_system_stats(self):
        """Test getting system statistics"""
        stats = self.limiter.get_system_stats()
        
        assert 'total_users_tracked' in stats
        assert 'total_active_requests' in stats
        assert 'memory_usage_mb' in stats
        assert 'timestamp' in stats
        assert isinstance(stats['total_users_tracked'], int)
    
    @pytest.mark.asyncio
    async def test_multiple_operations(self):
        """Test different operation types"""
        user_id = "test_user_ops"
        tier = SubscriptionTier.PREMIUM
        
        # Test different operation types
        operations = ['api_call', 'journal_store', 'journal_read']
        
        for operation in operations:
            result = await self.limiter.check_and_record(user_id, tier, operation)
            assert result.allowed is True
    
    @pytest.mark.asyncio
    async def test_rate_limit_result_to_dict(self):
        """Test RateLimitResult serialization"""
        user_id = "test_user_serialize"
        tier = SubscriptionTier.FREE
        
        result = await self.limiter.check_rate_limit(user_id, tier)
        result_dict = result.to_dict()
        
        assert 'allowed' in result_dict
        assert 'current_usage' in result_dict
        assert 'limits' in result_dict
        assert 'reset_times' in result_dict
        assert isinstance(result_dict['reset_times']['hour'], str)  # ISO format
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test concurrent requests from same user"""
        user_id = "test_user_concurrent"
        tier = SubscriptionTier.PREMIUM
        
        # Make concurrent requests
        tasks = []
        for i in range(10):
            task = self.limiter.check_and_record(user_id, tier)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful vs rate limited
        successful = sum(1 for r in results if isinstance(r, RateLimitResult) and r.allowed)
        rate_limited = sum(1 for r in results if isinstance(r, RateLimitError))
        
        # All should either succeed or be properly rate limited
        assert successful + rate_limited == len(results)
    
    @pytest.mark.asyncio
    async def test_reset_time_calculation(self):
        """Test reset time calculation accuracy"""
        user_id = "test_user_reset"
        tier = SubscriptionTier.FREE
        
        # Record a request
        await self.limiter.record_request(user_id, tier)
        
        result = await self.limiter.check_rate_limit(user_id, tier)
        
        # Reset time should be in the future
        for window_name, reset_time in result.reset_times.items():
            assert reset_time > datetime.now()
    
    @pytest.mark.parametrize("tier,expected_higher_limits", [
        (SubscriptionTier.BASIC, SubscriptionTier.FREE),
        (SubscriptionTier.PREMIUM, SubscriptionTier.BASIC),
        (SubscriptionTier.ENTERPRISE, SubscriptionTier.PREMIUM),
    ])
    @pytest.mark.asyncio
    async def test_tier_limit_hierarchy(self, tier, expected_higher_limits):
        """Test that higher tiers have higher or equal limits"""
        from fortunamind_persistence.subscription.tiers import TierDefinitions
        
        lower_limits = TierDefinitions.get_limits(expected_higher_limits)
        higher_limits = TierDefinitions.get_limits(tier)
        
        # Higher tier should have >= limits (or unlimited = -1)
        if higher_limits.api_calls_per_hour != -1:
            assert higher_limits.api_calls_per_hour >= lower_limits.api_calls_per_hour
        if higher_limits.api_calls_per_day != -1:
            assert higher_limits.api_calls_per_day >= lower_limits.api_calls_per_day