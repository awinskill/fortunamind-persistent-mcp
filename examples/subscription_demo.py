#!/usr/bin/env python3
"""
FortunaMind Subscription Management Demo

This demo shows how the subscription management system works
without requiring production database credentials.
"""

import os
import sys
import json
import hashlib
from datetime import datetime, timedelta

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fortunamind_persistence.identity import EmailIdentity
from fortunamind_persistence.subscription import SubscriptionTier


def demo_user_identity():
    """Demonstrate email-based identity generation"""
    print("🔐 Email-Based Identity System Demo")
    print("=" * 50)
    
    identity = EmailIdentity()
    
    test_emails = [
        "user@example.com",
        "john.doe@gmail.com", 
        "jane.smith+trading@hotmail.com",
        "test.user@fortunamind.com"
    ]
    
    print("Testing email normalization and ID generation:\n")
    
    for email in test_emails:
        user_id = identity.generate_user_id(email)
        normalized = identity.normalize_email(email)
        
        print(f"Original: {email}")
        print(f"Normalized: {normalized}")
        print(f"User ID: {user_id}")
        print(f"Valid Email: {EmailIdentity.validate_email(email)}")
        print("-" * 40)


def demo_subscription_key_format():
    """Demonstrate subscription key generation format"""
    print("\n🔑 Subscription Key Format Demo")
    print("=" * 50)
    
    import secrets
    
    print("FortunaMind subscription keys follow the format: fm_sub_<secure_token>")
    print("\nExample keys:")
    
    for i in range(3):
        random_part = secrets.token_urlsafe(32)
        key = f"fm_sub_{random_part}"
        print(f"  {key}")
    
    print(f"\nKey components:")
    print(f"  • Prefix: 'fm_sub_' (identifies FortunaMind subscriptions)")
    print(f"  • Token: 32-byte cryptographically secure random token")
    print(f"  • Encoding: URL-safe base64 (no special characters)")


def demo_subscription_tiers():
    """Demonstrate subscription tier system"""
    print("\n📊 Subscription Tier System Demo")
    print("=" * 50)
    
    tiers = [
        (SubscriptionTier.FREE, "Portfolio view, price checks, basic analysis (no persistence)"),
        (SubscriptionTier.STARTER, "100 journal entries, historical analysis"),
        (SubscriptionTier.PREMIUM, "Unlimited entries, advanced analytics, custom alerts"), 
        (SubscriptionTier.ENTERPRISE, "All features, API access, unlimited usage")
    ]
    
    print("Available subscription tiers:\n")
    
    for tier, description in tiers:
        print(f"🏷️  {tier.value.upper()}")
        print(f"   {description}")
        print(f"   Enum value: {tier}")
        print()


def demo_user_context():
    """Demonstrate user context generation"""
    print("👤 User Context Demo")
    print("=" * 50)
    
    identity = EmailIdentity()
    
    # Simulate user context creation
    test_user = {
        "email": "demo@fortunamind.com",
        "tier": SubscriptionTier.PREMIUM,
        "subscription_key": "fm_sub_demo_key_12345"
    }
    
    user_id = identity.generate_user_id(test_user["email"])
    
    user_context = {
        "user_id": user_id,
        "tier": test_user["tier"],
        "is_valid": True,
        "subscription_key": test_user["subscription_key"],
        "created_at": datetime.utcnow().isoformat()
    }
    
    print("Example user context structure:")
    print(json.dumps({
        "user_id": user_id[:16] + "..." + user_id[-8:],  # Partial for demo
        "email_normalized": identity.normalize_email(test_user["email"]),
        "tier": user_context["tier"].value,
        "is_valid": user_context["is_valid"],
        "subscription_key": test_user["subscription_key"][:20] + "...",
        "created_at": user_context["created_at"]
    }, indent=2))


def demo_privacy_features():
    """Demonstrate privacy-preserving features"""
    print("\n🛡️  Privacy and Security Features")
    print("=" * 50)
    
    identity = EmailIdentity()
    
    print("Privacy-preserving design principles:")
    print("\n1. Email Hashing:")
    print("   • Raw emails are NEVER stored in database")
    print("   • SHA-256 hashed with namespace for security")
    print("   • Gmail-specific normalization (dots, plus addressing)")
    
    email = "john.doe+trading@gmail.com"
    normalized = identity.normalize_email(email)
    user_id = identity.generate_user_id(email)
    
    print(f"\n   Example transformation:")
    print(f"   Raw: {email}")
    print(f"   Normalized: {normalized}")
    print(f"   User ID: {user_id}")
    
    print("\n2. User ID Generation:")
    print("   • Deterministic but secure user identification")
    print("   • Same email always generates same ID (survives API key rotation)")
    print("   • Includes version namespace for future migration support")
    
    print("\n3. Row Level Security (RLS):")
    print("   • Database-enforced user isolation")
    print("   • Users can ONLY access their own data")
    print("   • No application-level security dependencies")
    
    print("\n4. Zero Account Data Storage:")
    print("   • No Coinbase account IDs stored")
    print("   • No API keys persisted")
    print("   • Only journal entries and user preferences")


def demo_database_schema():
    """Demonstrate database schema structure"""
    print("\n🗄️  Database Schema Overview")
    print("=" * 50)
    
    schema = {
        "user_subscriptions": {
            "description": "User subscription management",
            "columns": [
                "user_id_hash (PK) - SHA-256 hash of normalized email",
                "email_hash - Additional email verification hash",
                "subscription_key - Encrypted subscription key",
                "tier - Subscription tier (free/premium/pro)",
                "status - active/inactive/suspended",
                "created_at, updated_at, expires_at - Timestamps"
            ]
        },
        "journal_entries": {
            "description": "Trading journal storage with RLS",
            "columns": [
                "id (PK) - UUID entry identifier",
                "user_id_hash (FK) - Links to user_subscriptions",
                "entry - Journal entry text content",
                "metadata - JSON metadata (tags, prices, etc.)",
                "entry_type - Type categorization",
                "created_at - Entry timestamp"
            ]
        },
        "user_preferences": {
            "description": "User settings and preferences",
            "columns": [
                "user_id_hash (PK) - User identifier",
                "preferences - JSON preferences object",
                "updated_at - Last update timestamp"
            ]
        }
    }
    
    for table_name, table_info in schema.items():
        print(f"📋 Table: {table_name}")
        print(f"   {table_info['description']}")
        print("   Columns:")
        for column in table_info['columns']:
            print(f"     • {column}")
        print()


def main():
    """Run all demos"""
    print("🚀 FortunaMind Persistent MCP Subscription System Demo")
    print("🔒 Privacy-First • 📊 Tier-Based • 🌐 Production-Ready")
    print("=" * 60)
    
    demo_user_identity()
    demo_subscription_key_format()
    demo_subscription_tiers()
    demo_user_context()
    demo_privacy_features()
    demo_database_schema()
    
    print("\n✅ Demo Complete!")
    print("\nNext Steps:")
    print("1. Set up your Supabase credentials in environment variables")
    print("2. Use scripts/subscription_manager.py to create real subscriptions") 
    print("3. Test with examples/client_integration.py")
    print("4. Integrate with Claude Desktop using examples/claude_desktop_integration.py")


if __name__ == "__main__":
    main()