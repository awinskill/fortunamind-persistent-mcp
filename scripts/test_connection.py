#!/usr/bin/env python3
"""
Test database connection for FortunaMind Persistent MCP Server

This script tests both the direct PostgreSQL connection and Supabase API connection
to ensure everything is configured correctly before running migrations or the server.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def load_env():
    """Load environment variables from .env file"""
    try:
        from dotenv import load_dotenv
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ Loaded environment from {env_path}")
        else:
            print(f"⚠️ No .env file found at {env_path}")
            print("Environment variables must be set manually")
    except ImportError:
        print("💡 Install python-dotenv for .env support: pip install python-dotenv")

async def test_postgresql_connection():
    """Test direct PostgreSQL connection"""
    print("\n🔍 Testing PostgreSQL connection...")
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set")
        return False
    
    if '[YOUR-PASSWORD]' in database_url:
        print("❌ DATABASE_URL contains placeholder - please set your actual password")
        return False
    
    try:
        from sqlalchemy import create_engine, text
        
        # Ensure SSL for Supabase
        if "sslmode" not in database_url:
            database_url += "?sslmode=require"
        
        engine = create_engine(database_url, echo=False)
        
        with engine.connect() as conn:
            # Test basic connection
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL: {version[:50]}...")
            
            # Test database info
            result = conn.execute(text("SELECT current_database(), current_user"))
            db_name, user = result.fetchone()
            print(f"✅ Database: {db_name}, User: {user}")
            
            # Test if our tables exist (after migration)
            try:
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('user_subscriptions', 'trading_journal', 'user_preferences', 'storage_records')
                    ORDER BY table_name
                """))
                tables = [row[0] for row in result]
                if tables:
                    print(f"✅ Found tables: {', '.join(tables)}")
                else:
                    print("⚠️ No FortunaMind tables found - run 'alembic upgrade head' to create them")
            except Exception as e:
                print(f"⚠️ Could not check tables: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

async def test_supabase_connection():
    """Test Supabase API connection"""
    print("\n🔍 Testing Supabase API connection...")
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url:
        print("❌ SUPABASE_URL not set")
        return False
    
    if not supabase_key:
        print("❌ SUPABASE_ANON_KEY not set")
        return False
    
    if '[YOUR-ANON-KEY]' in supabase_key:
        print("❌ SUPABASE_ANON_KEY contains placeholder - please set your actual key")
        return False
    
    try:
        from supabase import create_client
        
        client = create_client(supabase_url, supabase_key)
        print(f"✅ Supabase client created for {supabase_url}")
        
        # Test basic API call
        try:
            response = client.table('user_subscriptions').select('count').limit(1).execute()
            print("✅ Supabase API connection successful")
        except Exception as e:
            if "relation" in str(e).lower() or "table" in str(e).lower():
                print("⚠️ Supabase API works, but tables don't exist yet - run migration")
            else:
                print(f"❌ Supabase API error: {e}")
                return False
        
        return True
        
    except ImportError:
        print("❌ Supabase library not installed: pip install supabase")
        return False
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

async def test_persistence_library():
    """Test our persistence library initialization"""
    print("\n🔍 Testing FortunaMind persistence library...")
    
    try:
        from fortunamind_persistence.storage.supabase_backend import SupabaseStorage
        
        # Test initialization (should read from env vars)
        storage = SupabaseStorage()
        print("✅ SupabaseStorage initialized from environment")
        
        # Test connection
        success = await storage.initialize()
        if success:
            print("✅ SupabaseStorage connected successfully")
            
            # Test health check
            health = await storage.health_check()
            print(f"✅ Storage health: {health.get('status', 'unknown')}")
            
        else:
            print("❌ SupabaseStorage initialization failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Persistence library error: {e}")
        return False

async def main():
    """Run all connection tests"""
    print("🚀 FortunaMind Persistent MCP - Connection Test")
    print("=" * 50)
    
    # Load environment
    load_env()
    
    # Run tests
    tests = [
        ("PostgreSQL", test_postgresql_connection()),
        ("Supabase API", test_supabase_connection()),
        ("Persistence Library", test_persistence_library())
    ]
    
    results = []
    for name, test_coro in tests:
        try:
            result = await test_coro
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 30)
    
    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if result:
            passed += 1
    
    print(f"\n{passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Your configuration is working correctly.")
        print("\nNext steps:")
        print("1. Run migrations: alembic upgrade head")
        print("2. Start server: python -m src.main")
    else:
        print("\n⚠️ Some tests failed. Please check your configuration:")
        print("1. Verify .env file has correct credentials")
        print("2. Check network connectivity to Supabase")
        print("3. Ensure Supabase project is active")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))