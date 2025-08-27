#!/usr/bin/env python3
"""
FortunaMind Persistent MCP Server

A privacy-first, persistent MCP server with email-based identity,
subscription management, and tier-based access control.

Features:
- Email-based user identification (privacy-preserving)
- Subscription tier management with rate limiting
- Persistent storage with Supabase/PostgreSQL
- Row Level Security (RLS) for data isolation
- Comprehensive health monitoring
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

# Add src to Python path to ensure imports work
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
    
print(f"Added to Python path: {src_path}")
print(f"Current Python path: {sys.path[:3]}...")  # Show first 3 entries

# FastAPI and MCP imports
from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# FortunaMind Persistence Library
try:
    from fortunamind_persistence.adapters import FrameworkPersistenceAdapter
    from fortunamind_persistence.storage import SupabaseStorage
    from fortunamind_persistence.subscription import SubscriptionValidator, SubscriptionTier
    from fortunamind_persistence.rate_limiting import RateLimiter, RateLimitError
    from fortunamind_persistence.identity import EmailIdentity
    from fortunamind_persistence.exceptions import ValidationError, StorageError
except ImportError as e:
    print(f"❌ Failed to import persistence library: {e}")
    print("💡 Make sure you've installed requirements: pip install -r requirements.txt")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Global configuration
config = {
    'environment': os.getenv('ENVIRONMENT', 'development'),
    'log_level': os.getenv('LOG_LEVEL', 'INFO'),
    'port': int(os.getenv('PORT', 8000)),
    'host': os.getenv('SERVER_HOST', '0.0.0.0'),
    'server_name': os.getenv('MCP_SERVER_NAME', 'FortunaMind Persistent MCP Server'),
}

# Set log level
logging.getLogger().setLevel(getattr(logging, config['log_level'].upper()))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    global adapter
    
    try:
        logger.info("🚀 Starting FortunaMind Persistent MCP Server...")
        logger.info(f"Environment: {config['environment']}")
        logger.info(f"Log Level: {config['log_level']}")
        
        # Check required environment variables
        required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'DATABASE_URL']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {missing_vars}")
            logger.error("💡 Make sure to set them in Render dashboard")
            raise RuntimeError(f"Missing environment variables: {missing_vars}")
        
        # Initialize adapter components
        logger.info("📦 Initializing persistence components...")
        
        storage = SupabaseStorage()
        await storage.initialize()
        logger.info("✅ Storage backend initialized")
        
        validator = SubscriptionValidator()
        logger.info("✅ Subscription validator initialized")
        
        rate_limiter = RateLimiter()
        logger.info("✅ Rate limiter initialized")
        
        # Create the adapter
        adapter = FrameworkPersistenceAdapter(
            subscription_validator=validator,
            storage_backend=storage,
            rate_limiter=rate_limiter
        )
        logger.info("✅ Framework persistence adapter initialized")
        
        # Test the adapter
        health = await adapter.health_check()
        logger.info(f"🏥 Health check: {health['overall']}")
        
        logger.info("🎉 Server startup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        raise
    
    yield
    
    # Shutdown (if needed)
    logger.info("🛑 Server shutdown")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="FortunaMind Persistent MCP Server",
    description="Privacy-first persistent MCP server with email-based identity and subscription management",
    version="1.0.0",
    docs_url="/docs" if config['environment'] != 'production' else None,
    redoc_url="/redoc" if config['environment'] != 'production' else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global adapter instance
adapter: Optional[FrameworkPersistenceAdapter] = None
startup_time = datetime.utcnow()


async def get_adapter() -> FrameworkPersistenceAdapter:
    """Get the global adapter instance"""
    global adapter
    if adapter is None:
        raise HTTPException(status_code=503, detail="Server not initialized")
    return adapter


def extract_user_credentials(
    request: Request,
    x_user_email: Optional[str] = Header(None),
    x_subscription_key: Optional[str] = Header(None),
    x_coinbase_api_key: Optional[str] = Header(None),
    x_coinbase_api_secret: Optional[str] = Header(None)
) -> Dict[str, Optional[str]]:
    """Extract user credentials from request headers"""
    return {
        'email': x_user_email,
        'subscription_key': x_subscription_key,
        'coinbase_api_key': x_coinbase_api_key,
        'coinbase_api_secret': x_coinbase_api_secret
    }



@app.get("/")
async def root():
    """Root endpoint with server information"""
    return {
        "server": "FortunaMind Persistent MCP Server",
        "version": "1.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "status": "/status", 
            "mcp": "/mcp",
            "install": "/install",
            "bridge": "/static/mcp_http_bridge.py"
        },
        "documentation": "https://github.com/awinskill/fortunamind-persistent-mcp",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": (datetime.utcnow() - startup_time).total_seconds(),
        "server": config['server_name']
    }


@app.get("/status")
async def detailed_status(adapter: FrameworkPersistenceAdapter = Depends(get_adapter)):
    """Detailed system status endpoint"""
    try:
        health = await adapter.health_check()
        return {
            "overall": health.get('overall', 'unknown'),
            "timestamp": datetime.utcnow().isoformat(),
            "components": health.get('components', {}),
            "server": config['server_name'],
            "environment": config['environment'],
            "uptime_seconds": (datetime.utcnow() - startup_time).total_seconds()
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@app.get("/static/mcp_http_bridge.py")
async def serve_http_bridge():
    """Serve the HTTP bridge Python file for one-command installation"""
    try:
        bridge_path = os.path.join(os.path.dirname(__file__), 'static', 'mcp_http_bridge.py')
        
        if not os.path.exists(bridge_path):
            raise HTTPException(status_code=404, detail="HTTP bridge file not found")
        
        with open(bridge_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return Response(
            content=content,
            media_type="text/x-python",
            headers={
                "Content-Disposition": "attachment; filename=mcp_http_bridge.py",
                "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to serve HTTP bridge: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve bridge file")


@app.get("/install")
async def serve_install_script():
    """Serve the one-command installer script"""
    try:
        install_path = os.path.join(os.path.dirname(__file__), 'install-fortunamind-persistent.sh')
        
        if not os.path.exists(install_path):
            raise HTTPException(status_code=404, detail="Install script not found")
        
        with open(install_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return Response(
            content=content,
            media_type="application/x-sh",
            headers={
                "Content-Type": "text/x-shellscript",
                "Cache-Control": "public, max-age=1800"  # Cache for 30 minutes
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to serve install script: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve install script")


@app.post("/store_journal_entry")
async def store_journal_entry(
    request: Request,
    entry_data: Dict[str, Any],
    credentials: Dict[str, Optional[str]] = Depends(extract_user_credentials),
    adapter: FrameworkPersistenceAdapter = Depends(get_adapter)
):
    """Store a trading journal entry"""
    try:
        # Validate required credentials
        if not credentials['email'] or not credentials['subscription_key']:
            raise HTTPException(
                status_code=400, 
                detail="Missing required headers: X-User-Email and X-Subscription-Key"
            )
        
        # Extract entry data
        entry = entry_data.get('entry', '')
        metadata = entry_data.get('metadata', {})
        
        if not entry:
            raise HTTPException(status_code=400, detail="Entry content is required")
        
        # Store with validation
        result = await adapter.store_journal_entry_with_validation(
            email=credentials['email'],
            subscription_key=credentials['subscription_key'],
            entry=entry,
            metadata=metadata
        )
        
        if result['success']:
            return {
                "success": True,
                "entry_id": result['entry_id'],
                "message": "Journal entry stored successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Storage failed'))
            
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=f"Rate limit exceeded: {e}")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")
    except Exception as e:
        logger.error(f"Store journal entry failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/get_journal_entries")
async def get_journal_entries(
    request: Request,
    limit: int = 10,
    offset: int = 0,
    entry_type: Optional[str] = None,
    credentials: Dict[str, Optional[str]] = Depends(extract_user_credentials),
    adapter: FrameworkPersistenceAdapter = Depends(get_adapter)
):
    """Retrieve trading journal entries"""
    try:
        # Validate required credentials
        if not credentials['email'] or not credentials['subscription_key']:
            raise HTTPException(
                status_code=400,
                detail="Missing required headers: X-User-Email and X-Subscription-Key"
            )
        
        # Get entries with validation
        result = await adapter.get_journal_entries_with_validation(
            email=credentials['email'],
            subscription_key=credentials['subscription_key'],
            limit=limit,
            offset=offset,
            entry_type=entry_type
        )
        
        if result['success']:
            return {
                "success": True,
                "entries": result['entries'],
                "count": result['count'],
                "total": result.get('total', result['count'])
            }
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Retrieval failed'))
            
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=f"Rate limit exceeded: {e}")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")
    except Exception as e:
        logger.error(f"Get journal entries failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/user_stats")
async def get_user_stats(
    request: Request,
    credentials: Dict[str, Optional[str]] = Depends(extract_user_credentials),
    adapter: FrameworkPersistenceAdapter = Depends(get_adapter)
):
    """Get user statistics and usage information"""
    try:
        # Validate required credentials
        if not credentials['email'] or not credentials['subscription_key']:
            raise HTTPException(
                status_code=400,
                detail="Missing required headers: X-User-Email and X-Subscription-Key"
            )
        
        # Get stats
        result = await adapter.get_user_stats(
            email=credentials['email'],
            subscription_key=credentials['subscription_key']
        )
        
        if result['success']:
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Stats retrieval failed'))
            
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")
    except Exception as e:
        logger.error(f"Get user stats failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/validate_subscription")
async def validate_subscription(
    request: Request,
    credentials: Dict[str, Optional[str]] = Depends(extract_user_credentials),
    adapter: FrameworkPersistenceAdapter = Depends(get_adapter)
):
    """Validate user subscription and return user context"""
    try:
        # Validate required credentials
        if not credentials['email'] or not credentials['subscription_key']:
            raise HTTPException(
                status_code=400,
                detail="Missing required headers: X-User-Email and X-Subscription-Key"
            )
        
        # Validate subscription
        user_context = await adapter.validate_and_get_user_context(
            email=credentials['email'],
            subscription_key=credentials['subscription_key']
        )
        
        return {
            "success": True,
            "valid": user_context['is_valid'],
            "tier": user_context['tier'],
            "user_id": user_context['user_id'][:16] + "..."  # Partial for privacy
        }
        
    except ValidationError as e:
        return {
            "success": False,
            "valid": False,
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Subscription validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/mcp")
async def mcp_endpoint(
    request: Request,
    credentials: Dict[str, Optional[str]] = Depends(extract_user_credentials),
    adapter: FrameworkPersistenceAdapter = Depends(get_adapter)
):
    """
    MCP protocol endpoint for HTTP bridge integration.
    
    This endpoint accepts JSON-RPC MCP requests and routes them to the appropriate
    functionality based on the method name.
    """
    try:
        # Parse JSON-RPC request
        body = await request.json()
        
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")
        
        logger.info(f"MCP request: {method}")
        
        # Route based on MCP method
        if method == "tools/list":
            # Return list of available tools
            tools = [
                {
                    "name": "store_journal_entry",
                    "description": "Store a trading journal entry with persistent storage",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "entry": {"type": "string", "description": "Journal entry content"},
                            "entry_type": {"type": "string", "description": "Type of entry (trade, analysis, reflection, etc.)"},
                            "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for categorization"},
                            "metadata": {"type": "object", "description": "Additional metadata"}
                        },
                        "required": ["entry"]
                    }
                },
                {
                    "name": "get_journal_entries", 
                    "description": "Retrieve stored journal entries with filtering",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "description": "Maximum entries to return"},
                            "offset": {"type": "integer", "description": "Number of entries to skip"},
                            "entry_type": {"type": "string", "description": "Filter by entry type"}
                        }
                    }
                },
                {
                    "name": "get_user_stats",
                    "description": "Get user statistics and subscription information",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "validate_subscription",
                    "description": "Validate user subscription status", 
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools}
            }
            
        elif method == "tools/call":
            # Execute a tool
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "store_journal_entry":
                result = await adapter.store_journal_entry_with_validation(
                    email=credentials['email'],
                    subscription_key=credentials['subscription_key'],
                    entry=arguments.get('entry', ''),
                    metadata=arguments.get('metadata', {})
                )
                
                return {
                    "jsonrpc": "2.0", 
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"✅ Journal entry stored successfully!\nEntry ID: {result.get('entry_id', 'unknown')}" if result.get('success') else f"❌ Failed to store entry: {result.get('error', 'Unknown error')}"
                            }
                        ]
                    }
                }
                
            elif tool_name == "get_journal_entries":
                result = await adapter.get_journal_entries_with_validation(
                    email=credentials['email'],
                    subscription_key=credentials['subscription_key'],
                    limit=arguments.get('limit', 10),
                    offset=arguments.get('offset', 0),
                    entry_type=arguments.get('entry_type')
                )
                
                if result.get('success'):
                    entries_text = "📝 Journal Entries:\n\n"
                    for i, entry in enumerate(result.get('entries', []), 1):
                        entries_text += f"{i}. {entry.get('entry', '')[:100]}...\n"
                        entries_text += f"   Created: {entry.get('created_at', 'unknown')}\n\n"
                else:
                    entries_text = f"❌ Failed to retrieve entries: {result.get('error', 'Unknown error')}"
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id, 
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": entries_text
                            }
                        ]
                    }
                }
                
            elif tool_name == "get_user_stats":
                result = await adapter.get_user_stats(
                    email=credentials['email'],
                    subscription_key=credentials['subscription_key']
                )
                
                if result.get('success'):
                    stats_text = f"📊 User Statistics:\n"
                    stats_text += f"• Total Entries: {result.get('total_entries', 'unknown')}\n"
                    stats_text += f"• Tier: {result.get('tier', 'unknown')}\n"
                else:
                    stats_text = f"❌ Failed to get stats: {result.get('error', 'Unknown error')}"
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text", 
                                "text": stats_text
                            }
                        ]
                    }
                }
                
            elif tool_name == "validate_subscription":
                try:
                    user_context = await adapter.validate_and_get_user_context(
                        email=credentials['email'],
                        subscription_key=credentials['subscription_key']
                    )
                    
                    status_text = f"🎫 Subscription Status:\n"
                    status_text += f"• Valid: {'✅ Yes' if user_context['is_valid'] else '❌ No'}\n"
                    status_text += f"• Tier: {user_context['tier']}\n"
                    status_text += f"• User ID: {user_context['user_id'][:16]}...\n"
                    
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": status_text
                                }
                            ]
                        }
                    }
                    
                except Exception as e:
                    return {
                        "jsonrpc": "2.0", 
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"❌ Subscription validation failed: {str(e)}"
                                }
                            ]
                        }
                    }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }
                
        elif method == "initialize":
            # MCP initialization
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "FortunaMind Persistent MCP Server",
                        "version": "1.0.0"
                    }
                }
            }
            
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id, 
                "error": {
                    "code": -32601,
                    "message": f"Unknown method: {method}"
                }
            }
        
    except Exception as e:
        logger.error(f"MCP endpoint error: {e}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "id": body.get("id") if 'body' in locals() else None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    logger.info(f"🚀 Starting server on {config['host']}:{config['port']}")
    uvicorn.run(
        "server:app",
        host=config['host'],
        port=config['port'],
        reload=config['environment'] == 'development',
        log_level=config['log_level'].lower()
    )