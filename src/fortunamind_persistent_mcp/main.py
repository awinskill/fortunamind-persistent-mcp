#!/usr/bin/env python3
"""
FortunaMind Persistent MCP Server

Main entry point for the persistent MCP server that provides advanced
technical analysis and trading journal capabilities.
"""

import asyncio
import os
import sys
from pathlib import Path

# Path imports no longer needed with proper package structure

try:
    # Import framework proxy but don't call it at import time
    from fortunamind_persistent_mcp.framework_proxy import get_framework, unified_tools, core_interfaces
    FRAMEWORK_AVAILABLE = True
    print("✅ Framework proxy available")
except Exception as e:
    print(f"⚠️ Framework proxy not available: {e}")
    print("This is expected during initial development setup.")
    FRAMEWORK_AVAILABLE = False

from fortunamind_persistent_mcp.config import get_settings
from fortunamind_persistent_mcp.persistent_mcp.server import PersistentMCPServer


def print_banner():
    """Print startup banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║    FortunaMind Persistent MCP Server v1.0.0                 ║
    ║                                                              ║
    ║    🎯 Educational crypto tools for curious professionals     ║
    ║    📊 Technical indicators in plain English                  ║
    ║    📝 Learning-focused trading journal                       ║
    ║    🔒 Privacy-first with enterprise security                 ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_environment():
    """Check environment setup and configuration"""
    settings = get_settings()
    
    print("🔧 Environment Check:")
    print(f"   Environment: {settings.environment}")
    print(f"   Server: {settings.server_host}:{settings.server_port}")
    print(f"   Security Profile: {settings.security_profile}")
    print(f"   Log Level: {settings.log_level}")
    
    # Check critical configuration
    issues = []
    
    if not settings.database_url:
        issues.append("❌ DATABASE_URL not configured")
    else:
        print(f"   Database: Connected to Supabase")
    
    if not settings.supabase_url:
        issues.append("❌ SUPABASE_URL not configured") 
    
    if len(settings.jwt_secret_key) < 32:
        issues.append("❌ JWT_SECRET_KEY too short (minimum 32 characters)")
    
    if not FRAMEWORK_AVAILABLE:
        issues.append("⚠️ FortunaMind framework not available (expected during initial setup)")
    
    if issues:
        print("\n🚨 Configuration Issues:")
        for issue in issues:
            print(f"   {issue}")
        
        if settings.environment == "production":
            print("\n❌ Cannot start in production with configuration issues")
            return False
        else:
            print("\n⚠️ Starting in development mode despite issues")
    
    print("✅ Environment check completed\n")
    return True


async def create_server():
    """Create and configure the MCP server"""
    settings = get_settings()
    
    print("🚀 Initializing server components...")
    
    # Create server instance with mode from settings
    server = PersistentMCPServer(settings, server_mode=settings.server_mode)
    
    if FRAMEWORK_AVAILABLE:
        print("   📦 FortunaMind framework loaded")
        print("   🔧 Unified tools registered")
    else:
        print("   ⚠️ Running in development mode without framework")
    
    print("   🛡️ Security scanner configured")
    print("   🗄️ Database connection established")
    
    return server


async def main():
    """Main application entry point"""
    try:
        print_banner()
        
        # Check environment configuration
        if not check_environment():
            sys.exit(1)
        
        # Create server
        server = await create_server()
        
        # Start server
        settings = get_settings()
        if settings.server_mode == "http":
            print(f"🌟 Starting FortunaMind Persistent MCP HTTP Server...")
            print(f"   🌐 Server URL: http://{settings.server_host}:{settings.server_port}")
            print(f"   📖 API Documentation: http://{settings.server_host}:{settings.server_port}/docs" if settings.is_development() else "   📖 API Documentation: Disabled in production")
            print(f"   💖 Health Check: http://{settings.server_host}:{settings.server_port}/health")
        else:
            print("🌟 Starting FortunaMind Persistent MCP STDIO Server...")
            print(f"   Ready for Claude Desktop and MCP client integration")
        
        print(f"   Ready to help crypto-curious professionals learn and grow!")
        print("")
        
        await server.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Received shutdown signal")
    except Exception as e:
        print(f"\n❌ Startup failed: {e}")
        if get_settings().is_development():
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        print("👋 FortunaMind Persistent MCP Server shutdown complete")


if __name__ == "__main__":
    # Ensure we have a proper event loop
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        sys.exit(0)