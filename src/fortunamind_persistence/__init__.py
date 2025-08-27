"""
FortunaMind Common Persistence Library

A reusable library for subscription management, user identity, and persistent storage
that can be used across FortunaMind projects.

Features:
- Email-based stable user identity
- Subscription validation with caching
- Supabase storage with Row Level Security
- Tier-based rate limiting
- Framework adapters for fortunamind-core integration

Example Usage:
    from fortunamind_persistence.identity import EmailIdentity
    from fortunamind_persistence.subscription import SubscriptionValidator
    from fortunamind_persistence.storage.supabase_backend import SupabaseStorage
    
    # Create identity
    identity = EmailIdentity()
    user_id = identity.generate_user_id("user@example.com")
    
    # Validate subscription
    validator = SubscriptionValidator()
    is_valid, tier = await validator.validate("user@example.com", "fm_sub_abc123")
    
    # Store data
    storage = SupabaseStorage()
    await storage.store_journal_entry(user_id, {"entry": "Bought BTC at $45k"})
"""

__version__ = "0.1.0"
__author__ = "FortunaMind Technologies"

# Core imports for easy access
from .identity import EmailIdentity
from .subscription import SubscriptionValidator, SubscriptionTier
from .exceptions import (
    FortunaMindPersistenceError,
    ValidationError,
    StorageError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    SubscriptionError,
    ConfigurationError,
    DatabaseError,
    CacheError,
    IdentityError
)

__all__ = [
    "EmailIdentity",
    "SubscriptionValidator", 
    "SubscriptionTier",
    # Exceptions
    "FortunaMindPersistenceError",
    "ValidationError",
    "StorageError", 
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
    "SubscriptionError",
    "ConfigurationError",
    "DatabaseError",
    "CacheError",
    "IdentityError",
    "__version__"
]