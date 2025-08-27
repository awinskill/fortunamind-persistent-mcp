"""
Subscription Validator

Validates FortunaMind subscriptions with intelligent caching and database integration.
Provides the core subscription validation logic used across all FortunaMind services.
"""

import time
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
import structlog
import asyncio

from .tiers import SubscriptionTier, TierDefinitions
from .models import (
    SubscriptionData, 
    SubscriptionStatus, 
    SubscriptionValidationResult,
    SubscriptionKey
)

logger = structlog.get_logger(__name__)


class SubscriptionCache:
    """
    Intelligent caching system for subscription validation.
    
    Implements multi-level caching with TTL and automatic cleanup.
    """
    
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_cleanup = time.time()
        self._cleanup_interval = 600  # 10 minutes
    
    def _cleanup_expired(self):
        """Remove expired cache entries"""
        now = time.time()
        
        # Only cleanup every 10 minutes
        if now - self._last_cleanup < self._cleanup_interval:
            return
        
        expired_keys = []
        for key, entry in self._cache.items():
            if now - entry['timestamp'] > self.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        self._last_cleanup = now
        
        if expired_keys:
            logger.debug("Cache cleanup", removed_entries=len(expired_keys))
    
    def get(self, cache_key: str) -> Optional[SubscriptionValidationResult]:
        """Get from cache if valid"""
        self._cleanup_expired()
        
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if time.time() - entry['timestamp'] < self.ttl:
                result = entry['result']
                result.cache_hit = True
                return result
        
        return None
    
    def set(self, cache_key: str, result: SubscriptionValidationResult):
        """Update cache"""
        self._cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }
    
    def invalidate(self, email: str):
        """Invalidate all cache entries for an email"""
        keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{email}:")]
        for key in keys_to_remove:
            del self._cache[key]
        
        logger.debug("Cache invalidated", email_hash=email[:8])
    
    def clear(self):
        """Clear entire cache"""
        self._cache.clear()
        logger.debug("Cache cleared")


class SubscriptionValidator:
    """
    Validates FortunaMind subscriptions with caching and database integration.
    
    This is the primary subscription validation service used across all
    FortunaMind applications.
    """
    
    def __init__(
        self, 
        cache_ttl: int = 300,
        database_connection: Optional[Any] = None
    ):
        """
        Initialize the subscription validator.
        
        Args:
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
            database_connection: Database connection for subscription lookup
        """
        self.cache = SubscriptionCache(cache_ttl)
        self.db = database_connection
        self._key_generation_lock = asyncio.Lock()
        
        logger.info(
            "Subscription validator initialized",
            cache_ttl=cache_ttl,
            has_database=self.db is not None
        )
    
    async def validate(
        self, 
        email: str, 
        subscription_key: str
    ) -> SubscriptionValidationResult:
        """
        Validate subscription and return detailed result.
        
        Args:
            email: User's email address
            subscription_key: Subscription key starting with 'fm_sub_'
            
        Returns:
            SubscriptionValidationResult with validation details
        """
        if not email or not subscription_key:
            return SubscriptionValidationResult(
                is_valid=False,
                error_message="Email and subscription key are required"
            )
        
        # Normalize email
        email = email.lower().strip()
        
        # Validate key format
        if not self._is_valid_key_format(subscription_key):
            return SubscriptionValidationResult(
                is_valid=False,
                error_message="Invalid subscription key format"
            )
        
        # Check cache first
        cache_key = f"{email}:{subscription_key}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.debug("Cache hit", email_hash=email[:8])
            return cached_result
        
        # Validate against database
        try:
            result = await self._validate_in_database(email, subscription_key)
            
            # Cache the result
            self.cache.set(cache_key, result)
            
            logger.debug(
                "Subscription validated",
                email_hash=email[:8],
                is_valid=result.is_valid,
                tier=result.tier.value if result.tier else None
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Subscription validation error",
                error=str(e),
                email_hash=email[:8]
            )
            return SubscriptionValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )
    
    async def validate_simple(self, email: str, subscription_key: str) -> bool:
        """
        Simple boolean validation for backward compatibility.
        
        Args:
            email: User's email address
            subscription_key: Subscription key
            
        Returns:
            True if subscription is valid, False otherwise
        """
        result = await self.validate(email, subscription_key)
        return result.is_valid
    
    async def get_subscription_data(self, email: str) -> Optional[SubscriptionData]:
        """
        Get complete subscription data for a user.
        
        Args:
            email: User's email address
            
        Returns:
            SubscriptionData if found, None otherwise
        """
        try:
            return await self._get_subscription_from_database(email)
        except Exception as e:
            logger.error("Error getting subscription data", error=str(e))
            return None
    
    async def generate_subscription_key(
        self,
        email: str,
        tier: SubscriptionTier
    ) -> str:
        """
        Generate a new subscription key for a user.
        
        Args:
            email: User's email address
            tier: Subscription tier
            
        Returns:
            New subscription key
        """
        async with self._key_generation_lock:
            # Generate cryptographically secure key
            random_part = secrets.token_urlsafe(32)
            key = f"fm_sub_{random_part}"
            
            # Store in database
            subscription_key = SubscriptionKey(
                key=key,
                email=email.lower().strip(),
                tier=tier,
                created_at=datetime.utcnow()
            )
            
            await self._store_subscription_key(subscription_key)
            
            logger.info(
                "Subscription key generated", 
                email_hash=email[:8],
                tier=tier.value
            )
            
            return key
    
    def invalidate_cache(self, email: str):
        """
        Invalidate cached subscription data for a user.
        
        Args:
            email: User's email address
        """
        self.cache.invalidate(email.lower().strip())
    
    def _is_valid_key_format(self, key: str) -> bool:
        """Validate subscription key format"""
        return (
            isinstance(key, str) and
            key.startswith("fm_sub_") and
            len(key) >= 20
        )
    
    async def _validate_in_database(
        self,
        email: str,
        subscription_key: str
    ) -> SubscriptionValidationResult:
        """
        Validate subscription against database.
        
        This is the core validation logic that checks the subscription
        status in the database.
        """
        if not self.db:
            # Fall back to mock validation for development
            return await self._mock_validation(email, subscription_key)
        
        try:
            # Query subscription from database
            subscription = await self._get_subscription_from_database_by_key(
                email, subscription_key
            )
            
            if not subscription:
                return SubscriptionValidationResult(
                    is_valid=False,
                    error_message="Subscription not found"
                )
            
            # Check if subscription is active
            if not subscription.is_active():
                return SubscriptionValidationResult(
                    is_valid=False,
                    subscription_data=subscription,
                    error_message=f"Subscription {subscription.status.value}"
                )
            
            return SubscriptionValidationResult(
                is_valid=True,
                subscription_data=subscription
            )
            
        except Exception as e:
            logger.error("Database validation error", error=str(e))
            raise
    
    async def _mock_validation(
        self,
        email: str,
        subscription_key: str
    ) -> SubscriptionValidationResult:
        """
        Mock validation for development/testing.
        
        Accepts any key starting with 'fm_sub_' as valid premium subscription.
        """
        if not subscription_key.startswith("fm_sub_"):
            return SubscriptionValidationResult(
                is_valid=False,
                error_message="Invalid key format"
            )
        
        # Create mock subscription data
        mock_subscription = SubscriptionData(
            email=email,
            subscription_key=subscription_key,
            tier=SubscriptionTier.PREMIUM,
            status=SubscriptionStatus.ACTIVE,
            expires_at=datetime.utcnow() + timedelta(days=30),
            created_at=datetime.utcnow() - timedelta(days=5),
            updated_at=datetime.utcnow(),
            metadata={"mock": True}
        )
        
        logger.debug("Mock validation", email_hash=email[:8])
        
        return SubscriptionValidationResult(
            is_valid=True,
            subscription_data=mock_subscription
        )
    
    async def _get_subscription_from_database(self, email: str) -> Optional[SubscriptionData]:
        """Get subscription data from database by email"""
        # TODO: Implement actual database query
        # This will be implemented when we add the database connection
        return None
    
    async def _get_subscription_from_database_by_key(
        self,
        email: str,
        subscription_key: str
    ) -> Optional[SubscriptionData]:
        """Get subscription data from database by email and key"""
        # TODO: Implement actual database query
        # This will be implemented when we add the database connection
        return None
    
    async def _store_subscription_key(self, subscription_key: SubscriptionKey):
        """Store subscription key in database"""
        # TODO: Implement actual database storage
        # This will be implemented when we add the database connection
        pass


# Convenience functions for backward compatibility
_default_validator = None

async def validate_subscription(email: str, subscription_key: str) -> bool:
    """Global convenience function for subscription validation"""
    global _default_validator
    
    if _default_validator is None:
        _default_validator = SubscriptionValidator()
    
    return await _default_validator.validate_simple(email, subscription_key)