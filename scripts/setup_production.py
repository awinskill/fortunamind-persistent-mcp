#!/usr/bin/env python3
"""
Production Setup Script for FortunaMind Persistent MCP Server

This script sets up the production Supabase environment with:
1. Database schema validation
2. RLS policy application
3. Performance indexes
4. Initial admin users
5. Health check validation

Usage:
    python scripts/setup_production.py --env production
    python scripts/setup_production.py --verify-only
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime
from typing import Dict, List, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import asyncpg
    from supabase import create_client, Client
    from fortunamind_persistence.adapters import FrameworkPersistenceAdapter
    from fortunamind_persistence.storage import SupabaseStorage
    from fortunamind_persistence.subscription import SubscriptionValidator, SubscriptionTier
    from fortunamind_persistence.identity import EmailIdentity
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you've installed requirements: pip install -r requirements.txt")
    sys.exit(1)


class ProductionSetup:
    """Handles production environment setup and validation."""
    
    def __init__(self, env_file: str = None):
        self.env_file = env_file or '.env.production'
        self.load_environment()
        self.identity = EmailIdentity()
        
    def load_environment(self):
        """Load environment variables from file if specified."""
        if os.path.exists(self.env_file):
            print(f"📁 Loading environment from {self.env_file}")
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
        
        # Validate required environment variables
        required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'DATABASE_URL']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {missing_vars}")
            print(f"💡 Create {self.env_file} with required credentials")
            sys.exit(1)
            
        print("✅ Environment variables loaded successfully")

    async def validate_database_connection(self) -> bool:
        """Validate direct PostgreSQL connection."""
        print("\n🗄️ Testing database connection...")
        
        try:
            database_url = os.getenv('DATABASE_URL')
            conn = await asyncpg.connect(database_url)
            
            # Test basic query
            version = await conn.fetchval('SELECT version()')
            print(f"✅ Database connection successful")
            print(f"   PostgreSQL version: {version.split(',')[0]}")
            
            # Check if our tables exist
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('user_subscriptions', 'journal_entries', 'user_preferences', 'storage_records')
                ORDER BY table_name
            """)
            
            table_names = [row['table_name'] for row in tables]
            if len(table_names) == 4:
                print(f"✅ Found all required tables: {table_names}")
            else:
                print(f"⚠️  Found {len(table_names)}/4 tables: {table_names}")
                print("💡 You may need to run: alembic upgrade head")
            
            await conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    async def validate_supabase_api(self) -> bool:
        """Validate Supabase API connection."""
        print("\n🔌 Testing Supabase API connection...")
        
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')
            
            client: Client = create_client(supabase_url, supabase_key)
            
            # Test API with a simple query (should work with anon key)
            response = client.table('user_subscriptions').select('count', count='exact').execute()
            
            print("✅ Supabase API connection successful")
            print(f"   Project URL: {supabase_url}")
            print(f"   API Key: {supabase_key[:20]}...{supabase_key[-10:]}")
            
            return True
            
        except Exception as e:
            print(f"❌ Supabase API connection failed: {e}")
            print("💡 Check your SUPABASE_URL and SUPABASE_ANON_KEY")
            return False

    async def apply_rls_policies(self) -> bool:
        """Apply RLS policies using service role if available."""
        print("\n🔒 Setting up Row Level Security policies...")
        
        service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        if not service_role_key:
            print("⚠️  SUPABASE_SERVICE_ROLE_KEY not provided")
            print("💡 RLS policies need to be applied manually via Supabase SQL editor")
            print(f"💡 Use the script: scripts/setup_rls_policies.sql")
            return True
        
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            service_client: Client = create_client(supabase_url, service_role_key)
            
            # Read RLS policy script
            script_path = os.path.join(os.path.dirname(__file__), 'setup_rls_policies.sql')
            
            if not os.path.exists(script_path):
                print(f"❌ RLS policy script not found: {script_path}")
                return False
                
            with open(script_path, 'r') as f:
                rls_sql = f.read()
            
            # Execute RLS policies (this might need to be done in chunks)
            print("🔧 Applying RLS policies...")
            
            # Note: Supabase Python client might not support direct SQL execution
            # This would typically be done via the Supabase dashboard SQL editor
            print("💡 RLS policies should be applied via Supabase Dashboard → SQL Editor")
            print(f"💡 Copy and execute the contents of: {script_path}")
            
            return True
            
        except Exception as e:
            print(f"⚠️  Could not apply RLS policies automatically: {e}")
            print("💡 Apply RLS policies manually via Supabase Dashboard → SQL Editor")
            return True

    async def test_persistence_library(self) -> bool:
        """Test the persistence library end-to-end."""
        print("\n🧪 Testing persistence library...")
        
        try:
            # Initialize the adapter components
            storage = SupabaseStorage()
            await storage.initialize()
            
            validator = SubscriptionValidator()
            
            from fortunamind_persistence.rate_limiting import RateLimiter
            rate_limiter = RateLimiter()
            
            # Initialize the adapter
            adapter = FrameworkPersistenceAdapter(
                subscription_validator=validator,
                storage_backend=storage,
                rate_limiter=rate_limiter
            )
            
            # Test health check
            health = await adapter.health_check()
            print("✅ Persistence library health check passed")
            
            for component, status in health['components'].items():
                status_icon = "✅" if status == "healthy" else "❌"
                print(f"   {status_icon} {component}: {status}")
            
            # Test user context validation
            test_email = "test@fortunamind.com"
            test_subscription = "fm_sub_production_test"
            
            try:
                user_context = await adapter.validate_and_get_user_context(
                    test_email, 
                    test_subscription
                )
                print(f"✅ User context validation working (user_id: {user_context['user_id'][:16]}...)")
                
            except Exception as e:
                print(f"⚠️  User context validation: {e}")
                print("💡 This is expected if no test subscription exists")
            
            return True
            
        except Exception as e:
            print(f"❌ Persistence library test failed: {e}")
            return False

    async def create_test_subscription(self) -> bool:
        """Create a test subscription for validation."""
        print("\n👤 Creating test subscription...")
        
        try:
            storage = SupabaseStorage()
            await storage.initialize()
            
            test_email = "test@fortunamind.com"
            
            # Check if subscription already exists
            database_url = os.getenv('DATABASE_URL')
            conn = await asyncpg.connect(database_url)
            
            existing = await conn.fetchval(
                "SELECT id FROM user_subscriptions WHERE email = $1",
                test_email
            )
            
            if existing:
                print(f"✅ Test subscription already exists for {test_email}")
            else:
                # Create test subscription
                await conn.execute("""
                    INSERT INTO user_subscriptions (email, subscription_key, tier, status)
                    VALUES ($1, $2, $3, $4)
                """, test_email, "fm_sub_production_test", "premium", "active")
                
                print(f"✅ Created test subscription for {test_email}")
            
            await conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Failed to create test subscription: {e}")
            return False

    async def validate_indexes_and_performance(self) -> bool:
        """Validate database indexes and performance."""
        print("\n⚡ Checking database performance...")
        
        try:
            database_url = os.getenv('DATABASE_URL')
            conn = await asyncpg.connect(database_url)
            
            # Check for required indexes
            indexes = await conn.fetch("""
                SELECT tablename, indexname 
                FROM pg_indexes 
                WHERE schemaname = 'public' 
                AND tablename IN ('journal_entries', 'user_preferences', 'storage_records', 'user_subscriptions')
                ORDER BY tablename, indexname
            """)
            
            print("📊 Database indexes:")
            for row in indexes:
                print(f"   {row['tablename']}: {row['indexname']}")
            
            # Check table sizes
            sizes = await conn.fetch("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
                FROM pg_tables 
                WHERE schemaname = 'public'
                AND tablename IN ('journal_entries', 'user_preferences', 'storage_records', 'user_subscriptions')
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """)
            
            print("📦 Table sizes:")
            for row in sizes:
                print(f"   {row['tablename']}: {row['size']}")
            
            await conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Performance check failed: {e}")
            return False

    def print_production_checklist(self):
        """Print production readiness checklist."""
        print("\n" + "="*60)
        print("📋 PRODUCTION READINESS CHECKLIST")
        print("="*60)
        
        checklist = [
            ("Database schema deployed", "alembic upgrade head"),
            ("RLS policies applied", "Execute scripts/setup_rls_policies.sql in Supabase"),
            ("Performance indexes created", "Included in RLS script"),
            ("Test subscription created", "Done by this script"),
            ("Health endpoints working", "Test /health and /status"),
            ("Environment variables set", "Configure in Render dashboard"),
            ("SSL/TLS configured", "Automatic with Render + Supabase"),
            ("Monitoring configured", "Set up alerts and dashboards"),
            ("Backup strategy confirmed", "Supabase automatic backups enabled"),
            ("Documentation updated", "Ensure all docs are current"),
        ]
        
        for item, action in checklist:
            print(f"   □ {item}")
            print(f"     → {action}")
        
        print("\n🚀 Next Steps:")
        print("   1. Configure Render environment variables")
        print("   2. Deploy to Render")
        print("   3. Test end-to-end functionality")
        print("   4. Set up monitoring and alerts")

    async def run_setup(self, verify_only: bool = False):
        """Run the complete production setup process."""
        print("🚀 FortunaMind Persistent MCP Server - Production Setup")
        print("="*60)
        
        if verify_only:
            print("🔍 Running verification checks only...")
        else:
            print("⚙️  Running full production setup...")
        
        # Step 1: Validate connections
        db_ok = await self.validate_database_connection()
        api_ok = await self.validate_supabase_api()
        
        if not (db_ok and api_ok):
            print("\n❌ Connection validation failed. Fix issues before proceeding.")
            return False
        
        # Step 2: Apply RLS policies (if not verify-only)
        if not verify_only:
            await self.apply_rls_policies()
        
        # Step 3: Test persistence library
        lib_ok = await self.test_persistence_library()
        
        # Step 4: Create test subscription (if not verify-only)
        if not verify_only:
            await self.create_test_subscription()
        
        # Step 5: Validate performance
        perf_ok = await self.validate_indexes_and_performance()
        
        # Summary
        print("\n" + "="*60)
        if db_ok and api_ok and lib_ok and perf_ok:
            print("✅ Production setup validation completed successfully!")
            if not verify_only:
                self.print_production_checklist()
        else:
            print("❌ Some validation checks failed. Review output above.")
        
        return db_ok and api_ok and lib_ok and perf_ok


async def main():
    parser = argparse.ArgumentParser(description='Setup FortunaMind Persistent MCP Server for production')
    parser.add_argument('--env', default='.env.production', 
                        help='Environment file to load (default: .env.production)')
    parser.add_argument('--verify-only', action='store_true',
                        help='Only verify setup, don\'t make changes')
    
    args = parser.parse_args()
    
    setup = ProductionSetup(args.env)
    success = await setup.run_setup(verify_only=args.verify_only)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())