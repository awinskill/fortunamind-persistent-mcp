"""
Subscriber Authentication

Handles FortunaMind subscriber authentication and subscription verification.
"""

import logging
import asyncio
import hashlib
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    from framework.core.interfaces import AuthContext
    FRAMEWORK_AVAILABLE = True
except ImportError:
    from core.mock import AuthContext
    FRAMEWORK_AVAILABLE = False

from config import Settings

logger = logging.getLogger(__name__)


class SubscriptionStatus(str, Enum):
    """Subscription status values"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    TRIAL = "trial"
    GRACE_PERIOD = "grace_period"
    UNKNOWN = "unknown"


class SubscriptionTier(str, Enum):
    """Subscription tier levels"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


@dataclass
class SubscriptionInfo:
    """Subscription information"""
    user_id_hash: str
    status: SubscriptionStatus
    tier: SubscriptionTier
    expires_at: Optional[datetime]
    features: Dict[str, bool]
    limits: Dict[str, int]
    metadata: Optional[Dict[str, Any]] = None


class SubscriberAuth:
    """
    FortunaMind Subscriber Authentication System
    
    Handles subscriber verification, subscription status checking,
    and feature access control based on subscription tiers.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize subscriber authentication
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self._cache: Dict[str, SubscriptionInfo] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        
        # HTTP session for API calls
        self._session: Optional[aiohttp.ClientSession] = None
        
        logger.info("Subscriber authentication system initialized")
    
    async def initialize(self):
        """Initialize authentication system"""
        if not AIOHTTP_AVAILABLE:
            logger.warning("aiohttp not available - subscription verification disabled")
            return
        
        # Create HTTP session for subscription API calls
        timeout = aiohttp.ClientTimeout(total=self.settings.http_timeout_seconds)
        self._session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                "User-Agent": f"{self.settings.mcp_server_name}/1.0.0",
                "Content-Type": "application/json"
            }
        )
        
        logger.info("✅ Authentication system initialized")
    
    async def cleanup(self):
        """Cleanup authentication resources"""
        if self._session:
            await self._session.close()
            self._session = None
        
        logger.info("✅ Authentication cleanup complete")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check authentication system health"""
        status = {
            "status": "healthy",
            "cache_entries": len(self._cache),
            "api_available": bool(self._session and AIOHTTP_AVAILABLE)
        }
        
        # Test subscription API connectivity if available
        if self.settings.subscription_api_key and self._session:
            try:
                async with self._session.get(
                    f"{self.settings.subscription_api_url}/health",
                    headers={"Authorization": f"Bearer {self.settings.subscription_api_key}"}
                ) as response:
                    if response.status == 200:
                        status["subscription_api"] = "healthy"
                    else:
                        status["subscription_api"] = f"unhealthy: HTTP {response.status}"
            except Exception as e:
                status["subscription_api"] = f"unhealthy: {e}"
        else:
            status["subscription_api"] = "not_configured"
        
        return status
    
    async def verify_subscription(self, auth_context: AuthContext) -> bool:
        """
        Verify user subscription status
        
        Args:
            auth_context: User authentication context
            
        Returns:
            True if subscription is valid, False otherwise
        """
        if not auth_context or not auth_context.user_id_hash:
            logger.warning("No authentication context provided")
            return False
        
        # Check if mocking is enabled
        if self.settings.mock_subscription_check:
            logger.debug("Using mock subscription verification (development mode)")
            return True
        
        try:
            # Get subscription info
            subscription = await self.get_subscription_info(auth_context.user_id_hash)
            
            if not subscription:
                logger.warning(f"No subscription found for user {auth_context.user_id_hash[:8]}...")
                return False
            
            # Check subscription status
            valid_statuses = [
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIAL,
                SubscriptionStatus.GRACE_PERIOD
            ]
            
            is_valid = subscription.status in valid_statuses
            
            # Additional expiry check
            if subscription.expires_at and datetime.now() > subscription.expires_at:
                # Check grace period
                grace_end = subscription.expires_at + timedelta(
                    days=self.settings.subscription_grace_period_days
                )
                if datetime.now() > grace_end:
                    is_valid = False
                    logger.warning(f"Subscription expired for user {auth_context.user_id_hash[:8]}...")
            
            logger.debug(f"Subscription verification for {auth_context.user_id_hash[:8]}...: {'valid' if is_valid else 'invalid'}")
            return is_valid
            
        except Exception as e:
            logger.error(f"Subscription verification error: {e}")
            return False
    
    async def get_subscription_info(self, user_id_hash: str) -> Optional[SubscriptionInfo]:
        """
        Get detailed subscription information for a user
        
        Args:
            user_id_hash: User identifier hash
            
        Returns:
            Subscription information if found, None otherwise
        """
        # Check cache first
        if self._is_cache_valid(user_id_hash):
            logger.debug(f"Using cached subscription for {user_id_hash[:8]}...")
            return self._cache[user_id_hash]
        
        # Development mode fallback
        if self.settings.mock_subscription_check or not self.settings.subscription_api_key:
            return self._create_mock_subscription(user_id_hash)
        
        # Fetch from subscription API
        subscription = await self._fetch_subscription_from_api(user_id_hash)
        
        # Cache the result
        if subscription:
            self._cache[user_id_hash] = subscription
            self._cache_timestamps[user_id_hash] = datetime.now()
        
        return subscription
    
    def _is_cache_valid(self, user_id_hash: str) -> bool:
        """Check if cached subscription info is still valid"""
        if user_id_hash not in self._cache:
            return False
        
        cache_time = self._cache_timestamps.get(user_id_hash)
        if not cache_time:
            return False
        
        # Check if cache has expired
        cache_ttl = timedelta(minutes=self.settings.subscription_cache_ttl_minutes)
        return datetime.now() - cache_time < cache_ttl
    
    def _create_mock_subscription(self, user_id_hash: str) -> SubscriptionInfo:
        """Create mock subscription for development/testing"""
        logger.debug(f"Creating mock subscription for {user_id_hash[:8]}...")
        
        return SubscriptionInfo(
            user_id_hash=user_id_hash,
            status=SubscriptionStatus.ACTIVE,
            tier=SubscriptionTier.PREMIUM,
            expires_at=datetime.now() + timedelta(days=30),
            features={
                "technical_indicators": True,
                "trading_journal": True,
                "portfolio_integration": True,
                "advanced_analytics": True,
                "api_access": True
            },
            limits={
                "journal_entries_per_month": 1000,
                "api_calls_per_hour": 500,
                "storage_mb": 100
            },
            metadata={"mock": True}
        )
    
    async def _fetch_subscription_from_api(self, user_id_hash: str) -> Optional[SubscriptionInfo]:
        """Fetch subscription information from FortunaMind API"""
        if not self._session or not self.settings.subscription_api_key:
            logger.warning("Subscription API not configured")
            return None
        
        try:
            # Prepare API request
            url = f"{self.settings.subscription_api_url}/verify"
            headers = {
                "Authorization": f"Bearer {self.settings.subscription_api_key}"
            }
            payload = {
                "user_id_hash": user_id_hash,
                "service": "persistent-mcp"
            }
            
            logger.debug(f"Fetching subscription for {user_id_hash[:8]}... from API")
            
            # Make API call with retry
            for attempt in range(self.settings.http_retry_attempts):
                try:
                    async with self._session.post(url, json=payload, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            return self._parse_subscription_response(data)
                        elif response.status == 404:
                            logger.warning(f"User {user_id_hash[:8]}... not found in subscription system")
                            return None
                        elif response.status == 401:
                            logger.error("Subscription API authentication failed")
                            return None
                        else:
                            logger.warning(f"Subscription API returned {response.status}")
                            if attempt == self.settings.http_retry_attempts - 1:
                                return None
                            
                except asyncio.TimeoutError:
                    logger.warning(f"Subscription API timeout (attempt {attempt + 1})")
                    if attempt == self.settings.http_retry_attempts - 1:
                        return None
                
                # Backoff before retry
                if attempt < self.settings.http_retry_attempts - 1:
                    backoff = self.settings.http_retry_backoff_factor ** attempt
                    await asyncio.sleep(backoff)
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching subscription from API: {e}")
            return None
    
    def _parse_subscription_response(self, data: Dict[str, Any]) -> Optional[SubscriptionInfo]:
        """Parse subscription API response"""
        try:
            # Parse response data
            user_id_hash = data.get("user_id_hash")
            status_str = data.get("status", "unknown")
            tier_str = data.get("tier", "free")
            expires_str = data.get("expires_at")
            
            # Parse status
            try:
                status = SubscriptionStatus(status_str)
            except ValueError:
                status = SubscriptionStatus.UNKNOWN
            
            # Parse tier
            try:
                tier = SubscriptionTier(tier_str)
            except ValueError:
                tier = SubscriptionTier.FREE
            
            # Parse expiration date
            expires_at = None
            if expires_str:
                try:
                    expires_at = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
                except ValueError:
                    logger.warning(f"Invalid expiration date: {expires_str}")
            
            # Parse features and limits
            features = data.get("features", {})
            limits = data.get("limits", {})
            metadata = data.get("metadata", {})
            
            return SubscriptionInfo(
                user_id_hash=user_id_hash,
                status=status,
                tier=tier,
                expires_at=expires_at,
                features=features,
                limits=limits,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error parsing subscription response: {e}")
            return None
    
    async def check_feature_access(
        self, 
        user_id_hash: str, 
        feature: str
    ) -> bool:
        """
        Check if user has access to a specific feature
        
        Args:
            user_id_hash: User identifier hash
            feature: Feature name to check
            
        Returns:
            True if user has access, False otherwise
        """
        subscription = await self.get_subscription_info(user_id_hash)
        
        if not subscription:
            return False
        
        # Check if subscription is valid
        if subscription.status not in [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIAL,
            SubscriptionStatus.GRACE_PERIOD
        ]:
            return False
        
        # Check feature access
        return subscription.features.get(feature, False)
    
    async def check_usage_limit(
        self,
        user_id_hash: str,
        limit_type: str,
        current_usage: int
    ) -> bool:
        """
        Check if user is within usage limits
        
        Args:
            user_id_hash: User identifier hash
            limit_type: Type of limit to check
            current_usage: Current usage count
            
        Returns:
            True if within limits, False otherwise
        """
        subscription = await self.get_subscription_info(user_id_hash)
        
        if not subscription:
            return False
        
        # Get limit for this type
        limit = subscription.limits.get(limit_type, 0)
        
        # Check if usage is within limit
        return current_usage < limit
    
    def invalidate_cache(self, user_id_hash: str) -> None:
        """Invalidate cached subscription data for a user"""
        if user_id_hash in self._cache:
            del self._cache[user_id_hash]
            del self._cache_timestamps[user_id_hash]
            logger.debug(f"Invalidated subscription cache for {user_id_hash[:8]}...")
    
    def clear_cache(self) -> None:
        """Clear all cached subscription data"""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Cleared all subscription cache data")