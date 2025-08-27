"""
Framework Persistence Adapter

Bridges the fortunamind-common-persistence library with the fortunamind-core framework.
Provides seamless integration while maintaining clean separation of concerns.
"""

import time
from typing import Optional, Dict, Any
from datetime import datetime
import structlog

# Try to import framework components
try:
    from framework.src.core.interfaces import AuthContext
    from framework.src.auth import AuthenticationContext
    FRAMEWORK_AVAILABLE = True
except ImportError:
    # Create mock types for development without framework
    AuthContext = Any
    AuthenticationContext = Any
    FRAMEWORK_AVAILABLE = False

from ..identity import EmailIdentity
from ..subscription import SubscriptionValidator, SubscriptionTier
from ..storage.interfaces import PersistentStorageInterface
from ..rate_limiting import RateLimiter

logger = structlog.get_logger(__name__)


class FrameworkPersistenceAdapter:
    """
    Adapts fortunamind-common-persistence to work with fortunamind-core framework.
    
    This adapter provides a bridge between our persistence system and the
    existing framework, allowing seamless integration without modifying
    the core framework.
    """
    
    def __init__(
        self,
        subscription_validator: SubscriptionValidator,
        storage_backend: PersistentStorageInterface,
        rate_limiter: Optional[RateLimiter] = None
    ):
        """
        Initialize the framework adapter.
        
        Args:
            subscription_validator: Subscription validation service
            storage_backend: Persistent storage implementation
            rate_limiter: Optional rate limiter
        """
        self.validator = subscription_validator
        self.storage = storage_backend
        self.rate_limiter = rate_limiter
        self.identity = EmailIdentity()
        
        logger.info(
            "Framework persistence adapter initialized",
            has_framework=FRAMEWORK_AVAILABLE,
            has_rate_limiter=rate_limiter is not None
        )
    
    async def create_auth_context_from_credentials(
        self,
        email: str,
        subscription_key: str,
        coinbase_credentials: Optional[Dict[str, str]] = None
    ) -> AuthContext:
        """
        Create framework AuthContext from our persistence credentials.
        
        Args:
            email: User's email address
            subscription_key: Subscription key (fm_sub_xxx)
            coinbase_credentials: Optional Coinbase API credentials
            
        Returns:
            Framework AuthContext
            
        Raises:
            ValueError: If subscription is invalid or framework not available
        """
        if not FRAMEWORK_AVAILABLE:
            raise ImportError("Framework not available")
        
        # Validate subscription first
        validation_result = await self.validator.validate(email, subscription_key)
        if not validation_result.is_valid:
            raise ValueError(f"Invalid subscription: {validation_result.error_message}")
        
        # Generate user ID from email
        user_id = self.identity.generate_user_id(email)
        
        # Create framework AuthContext
        auth_context = AuthContext(
            api_key=coinbase_credentials.get('api_key') if coinbase_credentials else subscription_key,
            api_secret=coinbase_credentials.get('api_secret') if coinbase_credentials else '',
            user_id_hash=user_id,
            timestamp=str(int(time.time())),
            signature=email,  # Store email for later retrieval
            source="persistent_mcp"
        )
        
        logger.debug(
            "Framework auth context created",
            email_hash=email[:8],
            user_id_hash=user_id[:8],
            tier=validation_result.tier.value if validation_result.tier else None
        )
        
        return auth_context
    
    def extract_email_from_auth_context(self, auth_context: AuthContext) -> Optional[str]:
        """
        Extract email from framework auth context.
        
        Args:
            auth_context: Framework auth context
            
        Returns:
            Email address if found, None otherwise
        """
        return self.identity.extract_from_auth_context(auth_context)
    
    def extract_user_id_from_auth_context(self, auth_context: AuthContext) -> Optional[str]:
        """
        Extract user ID from framework auth context.
        
        Args:
            auth_context: Framework auth context
            
        Returns:
            User ID if found, None otherwise
        """
        if hasattr(auth_context, 'user_id_hash'):
            return auth_context.user_id_hash
        return None
    
    async def validate_and_get_user_context(
        self,
        email: str,
        subscription_key: str
    ) -> Dict[str, Any]:
        """
        Validate subscription and return complete user context.
        
        Args:
            email: User's email address
            subscription_key: Subscription key
            
        Returns:
            Dict with user context information
            
        Raises:
            ValueError: If subscription is invalid
        """
        # Validate subscription
        validation_result = await self.validator.validate(email, subscription_key)
        
        if not validation_result.is_valid:
            raise ValueError(f"Invalid subscription: {validation_result.error_message}")
        
        # Generate user ID
        user_id = self.identity.generate_user_id(email)
        
        # Get subscription data
        subscription_data = validation_result.subscription_data
        
        return {
            'user_id': user_id,
            'email': email,
            'tier': subscription_data.tier if subscription_data else SubscriptionTier.FREE,
            'is_valid': True,
            'subscription_data': subscription_data,
            'validation_result': validation_result
        }
    
    async def check_feature_access(
        self,
        user_context: Dict[str, Any],
        feature: str
    ) -> bool:
        """
        Check if user has access to a specific feature.
        
        Args:
            user_context: User context from validate_and_get_user_context
            feature: Feature name to check
            
        Returns:
            True if user has access, False otherwise
        """
        from ..subscription.tiers import TierDefinitions
        
        tier = user_context.get('tier', SubscriptionTier.FREE)
        return TierDefinitions.has_feature(tier, feature)
    
    async def check_rate_limit(
        self,
        user_context: Dict[str, Any],
        operation: str = 'api_call'
    ) -> bool:
        """
        Check and record rate limit for user.
        
        Args:
            user_context: User context from validate_and_get_user_context
            operation: Operation being rate limited
            
        Returns:
            True if within limits, False if exceeded
        """
        if not self.rate_limiter:
            return True  # No rate limiting if not configured
        
        user_id = user_context['user_id']
        tier = user_context['tier']
        
        try:
            await self.rate_limiter.check_and_record(user_id, tier, operation)
            return True
        except Exception as e:
            logger.warning(
                "Rate limit exceeded",
                user_id_hash=user_id[:8],
                tier=tier.value,
                operation=operation,
                error=str(e)
            )
            return False
    
    async def store_journal_entry_with_validation(
        self,
        email: str,
        subscription_key: str,
        entry: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store journal entry with full validation and rate limiting.
        
        Args:
            email: User's email address
            subscription_key: Subscription key
            entry: Journal entry text
            metadata: Optional metadata
            
        Returns:
            Dict with operation result
        """
        try:
            # Validate user and get context
            user_context = await self.validate_and_get_user_context(email, subscription_key)
            
            # Check feature access
            if not await self.check_feature_access(user_context, 'journal_persistence'):
                return {
                    'success': False,
                    'error': 'Journal persistence requires subscription upgrade',
                    'upgrade_url': 'https://fortunamind.com/subscribe'
                }
            
            # Check rate limits
            if not await self.check_rate_limit(user_context, 'journal_store'):
                return {
                    'success': False,
                    'error': 'Rate limit exceeded. Please try again later.',
                    'retry_after': 60  # seconds
                }
            
            # Store entry
            entry_id = await self.storage.store_journal_entry(
                user_context['user_id'],
                entry,
                metadata
            )
            
            logger.info(
                "Journal entry stored via adapter",
                user_id_hash=user_context['user_id'][:8],
                entry_id=entry_id,
                tier=user_context['tier'].value
            )
            
            return {
                'success': True,
                'entry_id': entry_id,
                'tier': user_context['tier'].value
            }
            
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(
                "Failed to store journal entry",
                error=str(e),
                email_hash=email[:8]
            )
            return {
                'success': False,
                'error': f'Storage error: {str(e)}'
            }
    
    async def get_journal_entries_with_validation(
        self,
        email: str,
        subscription_key: str,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get journal entries with validation.
        
        Args:
            email: User's email address
            subscription_key: Subscription key
            limit: Maximum entries to return
            offset: Number of entries to skip
            
        Returns:
            Dict with entries or error
        """
        try:
            # Validate user and get context
            user_context = await self.validate_and_get_user_context(email, subscription_key)
            
            # Check rate limits
            if not await self.check_rate_limit(user_context, 'journal_read'):
                return {
                    'success': False,
                    'error': 'Rate limit exceeded. Please try again later.',
                    'entries': []
                }
            
            # Get entries
            entries = await self.storage.get_journal_entries(
                user_context['user_id'],
                limit=limit,
                offset=offset
            )
            
            return {
                'success': True,
                'entries': entries,
                'count': len(entries),
                'tier': user_context['tier'].value
            }
            
        except ValueError as e:
            return {
                'success': False,
                'error': str(e),
                'entries': []
            }
        except Exception as e:
            logger.error(
                "Failed to get journal entries",
                error=str(e),
                email_hash=email[:8]
            )
            return {
                'success': False,
                'error': f'Retrieval error: {str(e)}',
                'entries': []
            }
    
    async def get_user_stats(
        self,
        email: str,
        subscription_key: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive user statistics.
        
        Args:
            email: User's email address
            subscription_key: Subscription key
            
        Returns:
            Dict with user statistics
        """
        try:
            # Validate user and get context
            user_context = await self.validate_and_get_user_context(email, subscription_key)
            
            # Get storage stats
            storage_stats = await self.storage.get_storage_stats(user_context['user_id'])
            
            # Get rate limit stats
            rate_limit_stats = {}
            if self.rate_limiter:
                rate_limit_stats = await self.rate_limiter.get_user_stats(
                    user_context['user_id'],
                    user_context['tier']
                )
            
            return {
                'success': True,
                'user_id_hash': user_context['user_id'][:8],
                'email_hash': email[:8],
                'tier': user_context['tier'].value,
                'storage': storage_stats,
                'rate_limits': rate_limit_stats,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(
                "Failed to get user stats",
                error=str(e),
                email_hash=email[:8]
            )
            return {
                'success': False,
                'error': f'Stats error: {str(e)}'
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check for all components.
        
        Returns:
            Dict with health status of all components
        """
        health_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall': 'healthy',
            'components': {}
        }
        
        # Check storage health
        try:
            storage_health = await self.storage.health_check()
            health_status['components']['storage'] = storage_health
        except Exception as e:
            health_status['components']['storage'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['overall'] = 'degraded'
        
        # Check subscription validator (basic check)
        try:
            # Try a mock validation
            result = await self.validator.validate('test@example.com', 'fm_sub_invalid')
            health_status['components']['subscription_validator'] = {
                'status': 'healthy',
                'cache_size': len(self.validator.cache._cache) if hasattr(self.validator, 'cache') else 0
            }
        except Exception as e:
            health_status['components']['subscription_validator'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['overall'] = 'degraded'
        
        # Check rate limiter
        if self.rate_limiter:
            try:
                rate_limiter_stats = self.rate_limiter.get_system_stats()
                health_status['components']['rate_limiter'] = {
                    'status': 'healthy',
                    'stats': rate_limiter_stats
                }
            except Exception as e:
                health_status['components']['rate_limiter'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health_status['overall'] = 'degraded'
        
        # Check framework availability
        health_status['components']['framework'] = {
            'status': 'available' if FRAMEWORK_AVAILABLE else 'unavailable',
            'available': FRAMEWORK_AVAILABLE
        }
        
        return health_status