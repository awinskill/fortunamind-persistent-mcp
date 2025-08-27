"""
Subscription Tiers and Limits

Defines subscription tiers, their limits, and feature access for FortunaMind services.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Set


class SubscriptionTier(Enum):
    """Subscription tier levels"""
    FREE = "free"
    STARTER = "starter"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True)
class TierLimits:
    """Limits for a specific subscription tier"""
    # API usage limits
    api_calls_per_hour: int
    api_calls_per_day: int
    api_calls_per_month: int
    
    # Storage limits
    journal_entries: int  # -1 for unlimited
    storage_mb: int       # -1 for unlimited
    
    # Feature access
    features: Set[str]
    
    # Support level
    support_level: str
    
    # Rate limiting
    burst_limit: int  # Max calls in a short burst
    
    def __post_init__(self):
        """Validate limits after creation"""
        if self.api_calls_per_hour < 0 and self.api_calls_per_hour != -1:
            raise ValueError("api_calls_per_hour must be positive or -1 for unlimited")


class TierDefinitions:
    """
    Central definition of all subscription tiers and their limits.
    
    This class provides the authoritative source for what each tier includes.
    """
    
    # Available features
    FEATURES = {
        # Free features
        "portfolio_view",
        "price_check", 
        "basic_analysis",
        
        # Premium features
        "journal_persistence",
        "historical_analysis", 
        "performance_metrics",
        "risk_analysis",
        "advanced_charts",
        "export_data",
        "custom_alerts",
        
        # Enterprise features
        "api_access",
        "bulk_operations",
        "priority_support",
        "custom_integrations",
        "dedicated_account_manager"
    }
    
    # Tier definitions
    TIERS: Dict[SubscriptionTier, TierLimits] = {
        SubscriptionTier.FREE: TierLimits(
            api_calls_per_hour=60,
            api_calls_per_day=1000,
            api_calls_per_month=20000,
            journal_entries=0,  # No persistence
            storage_mb=0,
            features={
                "portfolio_view",
                "price_check", 
                "basic_analysis"
            },
            support_level="community",
            burst_limit=10
        ),
        
        SubscriptionTier.STARTER: TierLimits(
            api_calls_per_hour=300,
            api_calls_per_day=5000,
            api_calls_per_month=100000,
            journal_entries=100,
            storage_mb=50,
            features={
                "portfolio_view",
                "price_check",
                "basic_analysis", 
                "journal_persistence",
                "historical_analysis"
            },
            support_level="email",
            burst_limit=50
        ),
        
        SubscriptionTier.PREMIUM: TierLimits(
            api_calls_per_hour=1000,
            api_calls_per_day=20000,
            api_calls_per_month=500000,
            journal_entries=-1,  # Unlimited
            storage_mb=1000,
            features={
                "portfolio_view",
                "price_check",
                "basic_analysis",
                "journal_persistence", 
                "historical_analysis",
                "performance_metrics",
                "risk_analysis",
                "advanced_charts",
                "export_data",
                "custom_alerts"
            },
            support_level="priority_email",
            burst_limit=100
        ),
        
        SubscriptionTier.ENTERPRISE: TierLimits(
            api_calls_per_hour=-1,  # Unlimited
            api_calls_per_day=-1,   # Unlimited
            api_calls_per_month=-1, # Unlimited
            journal_entries=-1,     # Unlimited
            storage_mb=-1,          # Unlimited
            features=FEATURES,      # All features
            support_level="phone_and_email",
            burst_limit=-1          # Unlimited
        )
    }
    
    @classmethod
    def get_limits(cls, tier: SubscriptionTier) -> TierLimits:
        """Get limits for a specific tier"""
        return cls.TIERS[tier]
    
    @classmethod
    def get_tier_from_string(cls, tier_str: str) -> Optional[SubscriptionTier]:
        """Convert string to SubscriptionTier enum"""
        try:
            return SubscriptionTier(tier_str.lower())
        except ValueError:
            return None
    
    @classmethod
    def has_feature(cls, tier: SubscriptionTier, feature: str) -> bool:
        """Check if a tier has access to a specific feature"""
        limits = cls.get_limits(tier)
        return feature in limits.features
    
    @classmethod
    def can_make_api_call(cls, tier: SubscriptionTier, current_usage: Dict[str, int]) -> bool:
        """
        Check if user can make an API call based on current usage.
        
        Args:
            tier: User's subscription tier
            current_usage: Dict with 'hour', 'day', 'month' usage counts
            
        Returns:
            True if user can make the call, False otherwise
        """
        limits = cls.get_limits(tier)
        
        # Check hourly limit
        if limits.api_calls_per_hour != -1:
            if current_usage.get('hour', 0) >= limits.api_calls_per_hour:
                return False
        
        # Check daily limit
        if limits.api_calls_per_day != -1:
            if current_usage.get('day', 0) >= limits.api_calls_per_day:
                return False
        
        # Check monthly limit
        if limits.api_calls_per_month != -1:
            if current_usage.get('month', 0) >= limits.api_calls_per_month:
                return False
        
        return True
    
    @classmethod
    def can_store_journal_entry(cls, tier: SubscriptionTier, current_entries: int) -> bool:
        """Check if user can store another journal entry"""
        limits = cls.get_limits(tier)
        
        # Unlimited storage
        if limits.journal_entries == -1:
            return True
        
        # No storage allowed
        if limits.journal_entries == 0:
            return False
        
        # Check against limit
        return current_entries < limits.journal_entries
    
    @classmethod
    def get_upgrade_recommendation(cls, current_tier: SubscriptionTier, needed_feature: str) -> Optional[SubscriptionTier]:
        """
        Recommend tier upgrade for a needed feature.
        
        Args:
            current_tier: User's current tier
            needed_feature: Feature they need
            
        Returns:
            Recommended tier upgrade, None if feature not available
        """
        # Check all tiers in order
        tier_order = [SubscriptionTier.STARTER, SubscriptionTier.PREMIUM, SubscriptionTier.ENTERPRISE]
        
        for tier in tier_order:
            if tier.value > current_tier.value:  # Only consider upgrades
                if cls.has_feature(tier, needed_feature):
                    return tier
        
        return None


# Convenience functions
def get_tier_limits(tier: SubscriptionTier) -> TierLimits:
    """Get limits for a subscription tier"""
    return TierDefinitions.get_limits(tier)

def has_feature(tier: SubscriptionTier, feature: str) -> bool:
    """Check if tier has access to feature"""
    return TierDefinitions.has_feature(tier, feature)