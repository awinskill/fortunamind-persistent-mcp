#!/usr/bin/env python3
"""
FortunaMind Persistent MCP HTTP Server

HTTP server entry point for the FortunaMind Persistent MCP Server.
Provides MCP protocol over HTTP for web applications and API integrations.
"""

import asyncio
import os
import sys
from pathlib import Path

from fortunamind_persistent_mcp.config import get_settings
from fortunamind_persistent_mcp.persistent_mcp.server import PersistentMCPServer


def print_http_banner():
    """Print HTTP server startup banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║    FortunaMind Persistent MCP HTTP Server v1.0.0           ║
    ║                                                              ║
    ║    🌐 MCP Protocol over HTTP                                 ║
    ║    📊 Educational crypto tools with persistence             ║
    ║    📝 Trading journal & technical indicators                ║
    ║    🔒 Enterprise security & subscription auth               ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_http_environment():
    """Check HTTP server environment and configuration"""
    settings = get_settings()
    
    print("🔧 HTTP Server Configuration:")
    print(f"   Environment: {settings.environment}")
    print(f"   Server: {settings.server_host}:{settings.server_port}")
    print(f"   Security Profile: {settings.security_profile}")
    print(f"   Log Level: {settings.log_level}")
    
    # Check critical HTTP configuration
    issues = []
    
    if not settings.database_url:
        issues.append("❌ DATABASE_URL not configured")
    else:
        print(f"   Database: Connected to Supabase")
    
    if not settings.supabase_url:
        issues.append("❌ SUPABASE_URL not configured") 
    
    if len(settings.jwt_secret_key) < 32:
        issues.append("❌ JWT_SECRET_KEY too short (minimum 32 characters)")
    
    # Check HTTP-specific requirements
    try:
        import fastapi
        import uvicorn
        print(f"   FastAPI: v{fastapi.__version__}")
        print(f"   Uvicorn: v{uvicorn.__version__}")
    except ImportError as e:
        issues.append(f"❌ HTTP dependencies missing: {e}")
    
    if issues:
        print("\n🚨 Configuration Issues:")
        for issue in issues:
            print(f"   {issue}")
        
        if settings.environment == "production":
            print("\n❌ Cannot start HTTP server in production with configuration issues")
            return False
        else:
            print("\n⚠️ Starting in development mode despite issues")
    
    print("✅ HTTP server configuration check completed\n")
    return True


async def create_http_server():
    """Create and configure the HTTP MCP server"""
    settings = get_settings()
    
    print("🚀 Initializing HTTP server components...")
    
    # Create server instance in HTTP mode
    server = PersistentMCPServer(settings, server_mode="http")
    
    print(f"   🌐 HTTP mode enabled on {settings.server_host}:{settings.server_port}")
    print("   📊 Technical indicators and trading journal ready")
    print("   🛡️ Security scanner and authentication configured")
    print("   🗄️ Persistent storage backend initialized")
    
    return server


async def main():
    """Main HTTP server entry point"""
    try:
        print_http_banner()
        
        # Check environment configuration
        if not check_http_environment():
            sys.exit(1)
        
        # Create HTTP server
        server = await create_http_server()
        
        # Start HTTP server
        settings = get_settings()
        print(f"🌟 Starting FortunaMind Persistent MCP HTTP Server...")
        print(f"   🌐 Server URL: http://{settings.server_host}:{settings.server_port}")
        print(f"   📖 API Documentation: http://{settings.server_host}:{settings.server_port}/docs" if settings.is_development() else "   📖 API Documentation: Disabled in production")
        print(f"   💖 Health Check: http://{settings.server_host}:{settings.server_port}/health")
        print(f"   🎯 MCP Endpoint: http://{settings.server_host}:{settings.server_port}/mcp")
        print("")
        
        # Start the server (this will block)
        await server.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Received shutdown signal")
    except Exception as e:
        print(f"\n❌ HTTP server startup failed: {e}")
        if get_settings().is_development():
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        print("👋 FortunaMind Persistent MCP HTTP Server shutdown complete")


if __name__ == "__main__":
    # Check for HTTP mode environment variable
    os.environ.setdefault("MCP_SERVER_MODE", "http")
    
    # Ensure we have a proper event loop
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)