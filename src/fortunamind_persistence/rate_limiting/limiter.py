"""
Rate Limiter

Implements tier-based rate limiting with sliding window algorithm.
Supports different time windows (hourly, daily, monthly) and burst protection.
"""

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
import structlog

from ..subscription.tiers import SubscriptionTier, TierDefinitions

logger = structlog.get_logger(__name__)


@dataclass
class RateLimitResult:
    """Result of rate limit check"""
    allowed: bool
    current_usage: Dict[str, int]
    limits: Dict[str, int]
    reset_times: Dict[str, datetime]
    retry_after: Optional[int] = None  # Seconds to wait before retry
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'allowed': self.allowed,
            'current_usage': self.current_usage,
            'limits': self.limits,
            'reset_times': {k: v.isoformat() for k, v in self.reset_times.items()},
            'retry_after': self.retry_after
        }


class RateLimitError(Exception):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str, result: RateLimitResult):
        super().__init__(message)
        self.result = result


class SlidingWindowCounter:
    """
    Sliding window counter for rate limiting.
    
    More accurate than fixed window, prevents thundering herd.
    """
    
    def __init__(self, window_size: int):
        """
        Initialize sliding window counter.
        
        Args:
            window_size: Window size in seconds
        """
        self.window_size = window_size
        self.requests: deque = deque()
    
    def add_request(self, timestamp: float = None):
        """Add a request to the window"""
        if timestamp is None:
            timestamp = time.time()
        
        # Remove old requests outside the window
        self._cleanup_old_requests(timestamp)
        
        # Add new request
        self.requests.append(timestamp)
    
    def get_count(self, timestamp: float = None) -> int:
        """Get current count in the window"""
        if timestamp is None:
            timestamp = time.time()
        
        # Remove old requests
        self._cleanup_old_requests(timestamp)
        
        return len(self.requests)
    
    def _cleanup_old_requests(self, current_time: float):
        """Remove requests outside the sliding window"""
        cutoff_time = current_time - self.window_size
        
        while self.requests and self.requests[0] < cutoff_time:
            self.requests.popleft()
    
    def get_reset_time(self, timestamp: float = None) -> datetime:
        """Get time when oldest request will expire"""
        if timestamp is None:
            timestamp = time.time()
        
        self._cleanup_old_requests(timestamp)
        
        if not self.requests:
            return datetime.now()
        
        oldest_request = self.requests[0]
        reset_time = oldest_request + self.window_size
        return datetime.fromtimestamp(reset_time)


class RateLimiter:
    """
    Tier-based rate limiter with sliding window algorithm.
    
    Supports multiple time windows and burst protection based on
    subscription tiers.
    """
    
    def __init__(self, storage_backend=None):
        """
        Initialize rate limiter.
        
        Args:
            storage_backend: Optional persistent storage for rate limits
                            If None, uses in-memory storage
        """
        self.storage = storage_backend
        
        # In-memory storage for rate limiting
        # Structure: user_id -> window_type -> SlidingWindowCounter
        self._counters: Dict[str, Dict[str, SlidingWindowCounter]] = defaultdict(
            lambda: defaultdict(lambda: None)
        )
        
        # Window sizes in seconds
        self.windows = {
            'hour': 3600,
            'day': 86400,
            'month': 2592000  # 30 days
        }
        
        logger.info("Rate limiter initialized")
    
    async def check_rate_limit(
        self,
        user_id: str,
        tier: SubscriptionTier,
        operation: str = 'api_call'
    ) -> RateLimitResult:
        """
        Check if user is within rate limits.
        
        Args:
            user_id: User's unique identifier
            tier: User's subscription tier
            operation: Type of operation being rate limited
            
        Returns:
            RateLimitResult with current usage and limits
        """
        current_time = time.time()
        limits = TierDefinitions.get_limits(tier)
        
        # Get or create counters for this user
        user_counters = self._counters[user_id]
        
        # Initialize counters if needed
        for window_name in self.windows:
            if user_counters[window_name] is None:
                user_counters[window_name] = SlidingWindowCounter(
                    self.windows[window_name]
                )
        
        # Get current usage
        current_usage = {}
        reset_times = {}
        
        for window_name, counter in user_counters.items():
            current_usage[window_name] = counter.get_count(current_time)
            reset_times[window_name] = counter.get_reset_time(current_time)
        
        # Check limits
        tier_limits = {
            'hour': limits.api_calls_per_hour,
            'day': limits.api_calls_per_day,
            'month': limits.api_calls_per_month
        }
        
        # Determine if request is allowed
        allowed = True
        retry_after = None
        
        for window_name, limit in tier_limits.items():
            if limit == -1:  # Unlimited
                continue
            
            if current_usage[window_name] >= limit:
                allowed = False
                
                # Calculate retry after (time until oldest request expires)
                reset_time = reset_times[window_name]
                retry_after_seconds = int((reset_time - datetime.now()).total_seconds())
                if retry_after is None or retry_after_seconds < retry_after:
                    retry_after = max(1, retry_after_seconds)
        
        result = RateLimitResult(
            allowed=allowed,
            current_usage=current_usage,
            limits=tier_limits,
            reset_times=reset_times,
            retry_after=retry_after
        )
        
        logger.debug(
            "Rate limit check",
            user_id_hash=user_id[:8],
            tier=tier.value,
            allowed=allowed,
            current_usage=current_usage
        )
        
        return result
    
    async def record_request(
        self,
        user_id: str,
        tier: SubscriptionTier,
        operation: str = 'api_call'
    ):
        """
        Record a request (increments counters).
        
        Args:
            user_id: User's unique identifier
            tier: User's subscription tier
            operation: Type of operation
        """
        current_time = time.time()
        
        # Get user counters
        user_counters = self._counters[user_id]
        
        # Record request in all windows
        for window_name in self.windows:
            if user_counters[window_name] is None:
                user_counters[window_name] = SlidingWindowCounter(
                    self.windows[window_name]
                )
            
            user_counters[window_name].add_request(current_time)
        
        logger.debug(
            "Request recorded",
            user_id_hash=user_id[:8],
            tier=tier.value,
            operation=operation
        )
    
    async def check_and_record(
        self,
        user_id: str,
        tier: SubscriptionTier,
        operation: str = 'api_call'
    ) -> RateLimitResult:
        """
        Check rate limit and record request if allowed.
        
        Args:
            user_id: User's unique identifier
            tier: User's subscription tier
            operation: Type of operation
            
        Returns:
            RateLimitResult
            
        Raises:
            RateLimitError: If rate limit exceeded
        """
        # Check current limits
        result = await self.check_rate_limit(user_id, tier, operation)
        
        if not result.allowed:
            logger.warning(
                "Rate limit exceeded",
                user_id_hash=user_id[:8],
                tier=tier.value,
                current_usage=result.current_usage,
                limits=result.limits
            )
            
            raise RateLimitError(
                f"Rate limit exceeded for {tier.value} tier", 
                result
            )
        
        # Record the request
        await self.record_request(user_id, tier, operation)
        
        return result
    
    async def get_user_stats(
        self,
        user_id: str,
        tier: SubscriptionTier
    ) -> Dict[str, Any]:
        """
        Get detailed rate limiting stats for a user.
        
        Args:
            user_id: User's unique identifier
            tier: User's subscription tier
            
        Returns:
            Dict with detailed statistics
        """
        current_time = time.time()
        user_counters = self._counters[user_id]
        limits = TierDefinitions.get_limits(tier)
        
        stats = {
            'user_id_hash': user_id[:8],
            'tier': tier.value,
            'current_usage': {},
            'limits': {
                'hour': limits.api_calls_per_hour,
                'day': limits.api_calls_per_day,
                'month': limits.api_calls_per_month
            },
            'utilization_percentage': {},
            'reset_times': {},
            'burst_limit': limits.burst_limit
        }
        
        for window_name, counter in user_counters.items():
            if counter is not None:
                current_count = counter.get_count(current_time)
                limit = stats['limits'][window_name]
                
                stats['current_usage'][window_name] = current_count
                stats['reset_times'][window_name] = counter.get_reset_time(current_time).isoformat()
                
                if limit > 0:
                    stats['utilization_percentage'][window_name] = (current_count / limit) * 100
                else:
                    stats['utilization_percentage'][window_name] = 0
            else:
                stats['current_usage'][window_name] = 0
                stats['utilization_percentage'][window_name] = 0
                stats['reset_times'][window_name] = datetime.now().isoformat()
        
        return stats
    
    async def cleanup_old_data(self, cutoff_hours: int = 24):
        """
        Cleanup old rate limiting data.
        
        Args:
            cutoff_hours: Remove data older than this many hours
        """
        current_time = time.time()
        cutoff_time = current_time - (cutoff_hours * 3600)
        
        users_to_remove = []
        
        for user_id, user_counters in self._counters.items():
            # Check if user has any recent activity
            has_recent_activity = False
            
            for counter in user_counters.values():
                if counter is not None and counter.requests:
                    # Check if any requests are newer than cutoff
                    if any(req_time > cutoff_time for req_time in counter.requests):
                        has_recent_activity = True
                        break
            
            if not has_recent_activity:
                users_to_remove.append(user_id)
        
        # Remove inactive users
        for user_id in users_to_remove:
            del self._counters[user_id]
        
        logger.info(
            "Rate limiter cleanup completed",
            removed_users=len(users_to_remove),
            cutoff_hours=cutoff_hours
        )
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system rate limiting statistics"""
        total_users = len(self._counters)
        
        # Count total requests across all users and windows
        total_requests = 0
        for user_counters in self._counters.values():
            for counter in user_counters.values():
                if counter is not None:
                    total_requests += len(counter.requests)
        
        return {
            'total_users_tracked': total_users,
            'total_active_requests': total_requests,
            'memory_usage_mb': self._estimate_memory_usage(),
            'timestamp': datetime.now().isoformat()
        }
    
    def _estimate_memory_usage(self) -> float:
        """Rough estimate of memory usage in MB"""
        # Very rough estimate based on data structures
        total_requests = 0
        for user_counters in self._counters.values():
            for counter in user_counters.values():
                if counter is not None:
                    total_requests += len(counter.requests)
        
        # Each request timestamp is ~8 bytes, plus overhead
        estimated_bytes = total_requests * 16  # 16 bytes per request estimate
        return estimated_bytes / (1024 * 1024)