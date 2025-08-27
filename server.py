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

# Add src to Python path to ensure imports work
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
    
print(f"Added to Python path: {src_path}")
print(f"Current Python path: {sys.path[:3]}...")  # Show first 3 entries

# FastAPI and MCP imports
from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.responses import JSONResponse
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

# Initialize FastAPI app
app = FastAPI(
    title="FortunaMind Persistent MCP Server",
    description="Privacy-first persistent MCP server with email-based identity and subscription management",
    version="1.0.0",
    docs_url="/docs" if config['environment'] != 'production' else None,
    redoc_url="/redoc" if config['environment'] != 'production' else None
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


@app.on_event("startup")
async def startup_event():
    """Initialize the persistence adapter on startup"""
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