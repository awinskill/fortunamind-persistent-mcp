"""
FortunaMind Persistence Exceptions

Custom exception classes for the FortunaMind persistence library.
Provides specific error types for different failure scenarios.
"""

from typing import Optional, Dict, Any


class FortunaMindPersistenceError(Exception):
    """Base exception for all FortunaMind persistence errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(FortunaMindPersistenceError):
    """Raised when data validation fails"""
    pass


class StorageError(FortunaMindPersistenceError):
    """Raised when storage operations fail"""
    
    def __init__(self, message: str, storage_type: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.storage_type = storage_type


class AuthenticationError(FortunaMindPersistenceError):
    """Raised when authentication fails"""
    pass


class AuthorizationError(FortunaMindPersistenceError):
    """Raised when authorization/permission checks fail"""
    
    def __init__(self, message: str, required_permission: Optional[str] = None, user_tier: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.required_permission = required_permission
        self.user_tier = user_tier


class RateLimitError(FortunaMindPersistenceError):
    """Raised when rate limits are exceeded"""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, current_usage: Optional[Dict[str, int]] = None, limits: Optional[Dict[str, int]] = None):
        super().__init__(message, {
            'retry_after': retry_after,
            'current_usage': current_usage,
            'limits': limits
        })
        self.retry_after = retry_after
        self.current_usage = current_usage or {}
        self.limits = limits or {}


class SubscriptionError(FortunaMindPersistenceError):
    """Raised when subscription-related operations fail"""
    
    def __init__(self, message: str, subscription_key: Optional[str] = None, email: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.subscription_key = subscription_key
        self.email = email


class ConfigurationError(FortunaMindPersistenceError):
    """Raised when configuration is invalid or missing"""
    
    def __init__(self, message: str, missing_config: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.missing_config = missing_config


class DatabaseError(StorageError):
    """Raised when database operations fail"""
    
    def __init__(self, message: str, query: Optional[str] = None, table: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "database", details)
        self.query = query
        self.table = table


class CacheError(FortunaMindPersistenceError):
    """Raised when cache operations fail"""
    
    def __init__(self, message: str, cache_key: Optional[str] = None, operation: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.cache_key = cache_key
        self.operation = operation


class IdentityError(FortunaMindPersistenceError):
    """Raised when identity operations fail"""
    
    def __init__(self, message: str, email: Optional[str] = None, user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.email = email
        self.user_id = user_id


# Convenience functions for creating common errors

def validation_error(field: str, value: Any, reason: str) -> ValidationError:
    """Create a validation error for a specific field"""
    return ValidationError(
        f"Validation failed for field '{field}': {reason}",
        details={'field': field, 'value': str(value), 'reason': reason}
    )


def storage_connection_error(storage_type: str, connection_string: Optional[str] = None) -> StorageError:
    """Create a storage connection error"""
    message = f"Failed to connect to {storage_type} storage"
    if connection_string:
        # Don't include full connection string for security
        sanitized = connection_string.split('@')[-1] if '@' in connection_string else "***"
        message += f" at {sanitized}"
    
    return StorageError(message, storage_type, {'connection_attempted': True})


def rate_limit_exceeded_error(tier: str, window: str, current: int, limit: int, reset_time: Optional[int] = None) -> RateLimitError:
    """Create a rate limit exceeded error"""
    message = f"Rate limit exceeded for {tier} tier: {current}/{limit} requests in {window}"
    if reset_time:
        message += f". Resets in {reset_time} seconds"
    
    return RateLimitError(
        message,
        retry_after=reset_time,
        current_usage={window: current},
        limits={window: limit}
    )


def subscription_invalid_error(email: str, subscription_key: str, reason: str) -> SubscriptionError:
    """Create a subscription validation error"""
    return SubscriptionError(
        f"Invalid subscription for {email}: {reason}",
        subscription_key=subscription_key,
        email=email,
        details={'reason': reason}
    )


def missing_config_error(config_name: str, suggestion: Optional[str] = None) -> ConfigurationError:
    """Create a missing configuration error"""
    message = f"Missing required configuration: {config_name}"
    if suggestion:
        message += f". {suggestion}"
    
    return ConfigurationError(message, missing_config=config_name)