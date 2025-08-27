#!/usr/bin/env python3
"""
FortunaMind Persistent MCP - Add Tester Tool

Simple command-line tool for adding testers to the system.
Works in local mode (generates keys locally) or production mode (syncs to Supabase).
"""

import os
import sys
import json
import argparse
import asyncio
import secrets
from datetime import datetime, timedelta
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fortunamind_persistence.identity import EmailIdentity
from fortunamind_persistence.subscription import SubscriptionTier


def generate_subscription_key() -> str:
    """Generate a new subscription key locally"""
    random_part = secrets.token_urlsafe(32)
    return f"fm_sub_{random_part}"


def save_tester_locally(email: str, subscription_key: str, tier: str, duration_days: int):
    """Save tester information to local JSON file"""
    testers_file = Path(__file__).parent / "testers.json"
    
    # Load existing testers or create new list
    if testers_file.exists():
        with open(testers_file, 'r') as f:
            testers = json.load(f)
    else:
        testers = []
    
    # Generate user ID
    identity = EmailIdentity()
    user_id = identity.generate_user_id(email)
    
    # Create tester record
    tester_record = {
        "email": email,
        "user_id": user_id,
        "subscription_key": subscription_key,
        "tier": tier,
        "duration_days": duration_days,
        "expires_at": (datetime.utcnow() + timedelta(days=duration_days)).isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "source": "add_tester_cli"
    }
    
    # Check if tester already exists
    for i, existing in enumerate(testers):
        if existing.get("email") == email:
            print(f"⚠️  Tester {email} already exists. Updating...")
            testers[i] = tester_record
            break
    else:
        testers.append(tester_record)
    
    # Save back to file
    with open(testers_file, 'w') as f:
        json.dump(testers, f, indent=2)
    
    print(f"💾 Saved tester to {testers_file}")
    return tester_record


async def sync_to_production(email: str, subscription_key: str, tier: str, duration_days: int):
    """Sync tester to production Supabase (optional)"""
    try:
        from fortunamind_persistence.storage import SupabaseStorage
        from fortunamind_persistence.subscription import SubscriptionValidator
        
        storage = SupabaseStorage()
        await storage.initialize()
        
        validator = SubscriptionValidator()
        tier_enum = SubscriptionTier(tier.upper())
        
        # Try to create subscription in production
        result = await validator.generate_subscription_key(email, tier_enum)
        
        print(f"✅ Synced to production Supabase")
        return True
        
    except ImportError:
        print("⚠️  Production sync not available (missing dependencies)")
        return False
    except Exception as e:
        print(f"⚠️  Production sync failed: {e}")
        return False


def display_tester_info(tester_record: dict):
    """Display formatted tester information"""
    print("\n" + "="*60)
    print("🎉 TESTER ADDED SUCCESSFULLY")
    print("="*60)
    print(f"📧 Email: {tester_record['email']}")
    print(f"🎫 Subscription Key: {tester_record['subscription_key']}")
    print(f"🏷️  Tier: {tester_record['tier'].upper()}")
    print(f"⏰ Expires: {tester_record['expires_at'][:10]}")
    print(f"👤 User ID: {tester_record['user_id'][:16]}...")
    print("\n📋 CONFIGURATION FOR TESTER:")
    print("-" * 40)
    print("Set these environment variables:")
    print(f"export FORTUNAMIND_USER_EMAIL='{tester_record['email']}'")
    print(f"export FORTUNAMIND_SUBSCRIPTION_KEY='{tester_record['subscription_key']}'")
    print("\nOr use in Claude Desktop config:")
    print(f'  "FORTUNAMIND_USER_EMAIL": "{tester_record["email"]}",')
    print(f'  "FORTUNAMIND_SUBSCRIPTION_KEY": "{tester_record["subscription_key"]}"')
    print("="*60)


def list_testers():
    """List all existing testers"""
    testers_file = Path(__file__).parent / "testers.json"
    
    if not testers_file.exists():
        print("📝 No testers found. Create some with: python add_tester.py email@domain.com")
        return
    
    with open(testers_file, 'r') as f:
        testers = json.load(f)
    
    if not testers:
        print("📝 No testers found.")
        return
    
    print(f"\n📋 TESTERS LIST ({len(testers)} total)")
    print("="*80)
    
    for i, tester in enumerate(testers, 1):
        expires = datetime.fromisoformat(tester['expires_at'].replace('Z', ''))
        is_expired = expires < datetime.utcnow()
        status = "❌ EXPIRED" if is_expired else "✅ ACTIVE"
        
        print(f"{i}. {tester['email']}")
        print(f"   Key: {tester['subscription_key']}")
        print(f"   Tier: {tester['tier'].upper()} | Status: {status}")
        print(f"   Expires: {expires.strftime('%Y-%m-%d')}")
        print()


def validate_tester(email: str = None, key: str = None):
    """Validate a tester's credentials"""
    testers_file = Path(__file__).parent / "testers.json"
    
    if not testers_file.exists():
        print("❌ No testers file found.")
        return False
    
    with open(testers_file, 'r') as f:
        testers = json.load(f)
    
    # Find tester
    tester = None
    if email and key:
        tester = next((t for t in testers if t['email'] == email and t['subscription_key'] == key), None)
    elif email:
        tester = next((t for t in testers if t['email'] == email), None)
    elif key:
        tester = next((t for t in testers if t['subscription_key'] == key), None)
    
    if not tester:
        print("❌ Tester not found.")
        return False
    
    # Check expiration
    expires = datetime.fromisoformat(tester['expires_at'].replace('Z', ''))
    is_expired = expires < datetime.utcnow()
    
    print(f"✅ Tester found: {tester['email']}")
    print(f"📧 Email: {tester['email']}")
    print(f"🎫 Key: {tester['subscription_key']}")
    print(f"🏷️  Tier: {tester['tier'].upper()}")
    print(f"⏰ Status: {'❌ EXPIRED' if is_expired else '✅ ACTIVE'}")
    print(f"📅 Expires: {expires.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return not is_expired


async def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Add testers to FortunaMind Persistent MCP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a premium tester
  python add_tester.py alice@example.com --tier premium
  
  # Add a free tier tester for 30 days
  python add_tester.py bob@test.com --tier free --days 30
  
  # List all testers
  python add_tester.py --list
  
  # Validate a tester
  python add_tester.py --validate alice@example.com
  
  # Sync existing tester to production
  python add_tester.py alice@example.com --sync-only
        """
    )
    
    parser.add_argument('email', nargs='?', help='Tester email address')
    parser.add_argument('--tier', choices=['free', 'starter', 'premium', 'enterprise'], 
                       default='premium', help='Subscription tier (default: premium)')
    parser.add_argument('--days', type=int, default=90, 
                       help='Subscription duration in days (default: 90)')
    parser.add_argument('--sync', action='store_true', 
                       help='Also sync to production Supabase (requires credentials)')
    parser.add_argument('--sync-only', action='store_true',
                       help='Only sync to production (tester must exist locally)')
    parser.add_argument('--list', action='store_true', 
                       help='List all existing testers')
    parser.add_argument('--validate', action='store_true',
                       help='Validate tester credentials')
    
    args = parser.parse_args()
    
    # Handle list command
    if args.list:
        list_testers()
        return
    
    # Handle validate command  
    if args.validate:
        if not args.email:
            print("❌ Email required for validation")
            parser.print_help()
            return
        validate_tester(email=args.email)
        return
    
    # Require email for other commands
    if not args.email:
        print("❌ Email address required")
        parser.print_help()
        return
    
    # Validate email format
    if '@' not in args.email or '.' not in args.email:
        print("❌ Invalid email format")
        return
    
    print(f"🚀 Adding tester: {args.email}")
    print(f"🏷️  Tier: {args.tier}")
    print(f"⏰ Duration: {args.days} days")
    
    if args.sync_only:
        # Load existing tester and sync to production
        testers_file = Path(__file__).parent / "testers.json"
        if not testers_file.exists():
            print("❌ No testers file found")
            return
            
        with open(testers_file, 'r') as f:
            testers = json.load(f)
        
        tester = next((t for t in testers if t['email'] == args.email), None)
        if not tester:
            print(f"❌ Tester {args.email} not found locally")
            return
        
        print("🔄 Syncing existing tester to production...")
        await sync_to_production(
            tester['email'], 
            tester['subscription_key'], 
            tester['tier'], 
            tester['duration_days']
        )
        return
    
    # Generate subscription key
    subscription_key = generate_subscription_key()
    
    # Save locally
    tester_record = save_tester_locally(args.email, subscription_key, args.tier, args.days)
    
    # Sync to production if requested
    if args.sync:
        print("🔄 Syncing to production...")
        await sync_to_production(args.email, subscription_key, args.tier, args.days)
    
    # Display tester info
    display_tester_info(tester_record)
    
    print(f"\n💡 NEXT STEPS:")
    print("1. Share the subscription key with the tester")
    print("2. Help them set up environment variables or Claude Desktop config")
    print("3. Test the connection with: python examples/subscription_demo.py")


if __name__ == "__main__":
    asyncio.run(main())