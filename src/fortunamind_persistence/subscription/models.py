"""
Subscription Data Models

Data structures for subscription management and billing integration.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from .tiers import SubscriptionTier


class SubscriptionStatus(Enum):
    """Subscription status values"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    PENDING = "pending"


@dataclass
class SubscriptionData:
    """
    Complete subscription information for a user.
    
    This is the primary data structure returned by subscription
    validation and used throughout the system.
    """
    email: str
    subscription_key: str
    tier: SubscriptionTier
    status: SubscriptionStatus
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
    
    # Billing information
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    
    # Usage tracking
    current_usage: Optional[Dict[str, int]] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None
    
    def is_active(self) -> bool:
        """Check if subscription is currently active"""
        return (
            self.status == SubscriptionStatus.ACTIVE and
            self.expires_at > datetime.utcnow()
        )
    
    def is_trial(self) -> bool:
        """Check if subscription is in trial period"""
        return self.status == SubscriptionStatus.TRIAL
    
    def days_until_expiry(self) -> int:
        """Get number of days until expiry (negative if expired)"""
        delta = self.expires_at - datetime.utcnow()
        return delta.days
    
    def is_expiring_soon(self, days: int = 7) -> bool:
        """Check if subscription is expiring within specified days"""
        return 0 <= self.days_until_expiry() <= days


@dataclass
class SubscriptionValidationResult:
    """
    Result of subscription validation operation.
    
    Contains both the validation result and detailed subscription
    information for use by the calling system.
    """
    is_valid: bool
    subscription_data: Optional[SubscriptionData] = None
    error_message: Optional[str] = None
    
    # Validation metadata
    validation_time: datetime = None
    cache_hit: bool = False
    
    def __post_init__(self):
        if self.validation_time is None:
            self.validation_time = datetime.utcnow()
    
    @property
    def tier(self) -> Optional[SubscriptionTier]:
        """Get subscription tier if valid"""
        return self.subscription_data.tier if self.subscription_data else None
    
    @property
    def is_premium(self) -> bool:
        """Check if this is a premium subscription"""
        if not self.is_valid or not self.subscription_data:
            return False
        return self.subscription_data.tier in [
            SubscriptionTier.PREMIUM, 
            SubscriptionTier.ENTERPRISE
        ]


@dataclass
class UsageRecord:
    """
    Records API usage for billing and rate limiting.
    """
    user_id: str
    endpoint: str
    timestamp: datetime
    tier: SubscriptionTier
    cost_credits: int = 1  # Cost in credits/tokens
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class BillingEvent:
    """
    Represents a billing-related event from Stripe or other providers.
    """
    event_id: str
    event_type: str  # e.g., 'subscription.created', 'payment.succeeded'
    customer_email: str
    subscription_id: Optional[str] = None
    amount: Optional[int] = None  # In cents
    currency: str = "usd"
    timestamp: datetime = None
    processed: bool = False
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass 
class SubscriptionKey:
    """
    Represents a subscription key with metadata.
    """
    key: str
    email: str
    tier: SubscriptionTier
    created_at: datetime
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    is_active: bool = True
    
    # Security
    created_from_ip: Optional[str] = None
    last_used_from_ip: Optional[str] = None
    
    def __post_init__(self):
        if not self.key.startswith("fm_sub_"):
            raise ValueError("Subscription key must start with 'fm_sub_'")
        if len(self.key) < 20:
            raise ValueError("Subscription key must be at least 20 characters")
    
    def mark_used(self, ip_address: Optional[str] = None):
        """Mark key as used with optional IP tracking"""
        self.last_used_at = datetime.utcnow()
        self.usage_count += 1
        if ip_address:
            self.last_used_from_ip = ip_address