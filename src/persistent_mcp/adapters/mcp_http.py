"""
HTTP MCP Adapter

HTTP server implementation of the MCP protocol for web applications and API integrations.
Uses FastAPI for robust HTTP handling with JSON-RPC over REST endpoints.
"""

import logging
import json
import time
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import JSONResponse
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    FastAPI = None

try:
    from framework.core.registry import ToolRegistry
    from framework.core.interfaces import AuthContext, ToolResult, ToolSchema
    FRAMEWORK_AVAILABLE = True
except ImportError:
    from ...core.mock import ToolRegistry, AuthContext, ToolResult, ToolSchema
    FRAMEWORK_AVAILABLE = False

from ..storage import StorageBackend
from ..auth import SubscriberAuth
from config import Settings

logger = logging.getLogger(__name__)


class HTTPEndpointHandlers:
    """HTTP endpoint handlers for MCP protocol over REST"""
    
    def __init__(self, registry: ToolRegistry, storage: StorageBackend, auth: SubscriberAuth, settings: Settings):
        """
        Initialize HTTP endpoint handlers
        
        Args:
            registry: Tool registry containing available tools
            storage: Storage backend for persistence
            auth: Authentication system
            settings: Application settings
        """
        self.registry = registry
        self.storage = storage
        self.auth = auth
        self.settings = settings
        
        logger.info("HTTP endpoint handlers initialized")
    
    async def health_check(self):
        """Health check endpoint with server information"""
        try:
            # Get server health status
            health_status = {
                "status": "healthy",
                "service": self.settings.mcp_server_name,
                "version": "1.0.0",
                "timestamp": int(time.time()),
                "environment": self.settings.environment,
                "port": self.settings.server_port,
                "framework": "persistent_mcp_server",
                "protocol": "http",
                "features": {
                    "technical_indicators": self.settings.enable_technical_indicators,
                    "trading_journal": self.settings.enable_trading_journal,
                    "portfolio_integration": self.settings.enable_portfolio_integration,
                    "persistent_storage": True,
                    "subscription_auth": True
                }
            }
            
            # Check component health
            components = {}
            
            # Storage health
            if self.storage:
                try:
                    storage_health = await self.storage.health_check()
                    components["storage"] = storage_health.get("status", "unknown")
                except Exception as e:
                    components["storage"] = f"unhealthy: {e}"
            
            # Auth health
            if self.auth:
                try:
                    auth_health = await self.auth.health_check()
                    components["auth"] = auth_health.get("status", "unknown")
                except Exception as e:
                    components["auth"] = f"unhealthy: {e}"
            
            # Tools count
            tools = self.registry.get_tools()
            components["tools"] = f"{len(tools)} tools registered"
            
            health_status["components"] = components
            
            # Overall status
            unhealthy_components = [k for k, v in components.items() if "unhealthy" in str(v)]
            if unhealthy_components:
                health_status["status"] = "degraded"
                health_status["issues"] = unhealthy_components
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": int(time.time())
            }
    
    async def mcp_endpoint(self, request: Request):
        """
        MCP protocol endpoint handling JSON-RPC over HTTP
        
        Supports the standard MCP protocol methods:
        - initialize: Server initialization
        - tools/list: List available tools  
        - tools/call: Execute tool calls
        - ping: Server health check
        """
        req_uuid = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        try:
            # Parse JSON-RPC request
            body = await request.json()
            method = body.get("method")
            request_id = body.get("id")
            params = body.get("params", {})
            
            logger.info(
                f"🔄 HTTP MCP Request [{req_uuid}]",
                method=method,
                request_id=request_id,
                client_ip=request.client.host if request.client else "unknown"
            )
            
            # Route to appropriate handler
            if method == "initialize":
                response_content = await self._handle_initialize(request_id, params)
            elif method == "tools/list":
                response_content = await self._handle_tools_list(request_id, params)
            elif method == "tools/call":
                response_content = await self._handle_tools_call(request_id, params, request)
            elif method == "ping":
                response_content = await self._handle_ping(request_id, params)
            else:
                response_content = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            # Validate response structure
            response_content = self._validate_response(response_content, request_id, method)
            
            # Log successful response
            response_time = time.time() - start_time
            logger.info(
                f"✅ HTTP MCP Response [{req_uuid}]",
                method=method,
                response_time_ms=int(response_time * 1000),
                status="success" if "result" in response_content else "error"
            )
            
            return JSONResponse(content=response_content)
            
        except json.JSONDecodeError:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error: Invalid JSON"
                    }
                },
                status_code=400
            )
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(
                f"❌ HTTP MCP Error [{req_uuid}]",
                error=str(e),
                response_time_ms=int(response_time * 1000)
            )
            
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": body.get("id") if "body" in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
            )
    
    async def _handle_initialize(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request"""
        client_info = params.get("clientInfo", {})
        client_name = client_info.get("name", "unknown")
        client_version = client_info.get("version", "unknown")
        
        logger.info(f"MCP client initializing: {client_name} v{client_version}")
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "listChanged": False
                    },
                    "logging": {}
                },
                "serverInfo": {
                    "name": self.settings.mcp_server_name,
                    "version": "1.0.0",
                    "description": "Educational crypto tools with persistent storage for crypto-curious professionals"
                }
            }
        }
    
    async def _handle_tools_list(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tools/list request"""
        try:
            tools = self.registry.get_tools()
            
            mcp_tools = []
            for tool in tools:
                mcp_tool = {
                    "name": tool.schema.name,
                    "description": tool.schema.description,
                    "inputSchema": tool.schema.parameters
                }
                mcp_tools.append(mcp_tool)
            
            logger.info(f"Returning {len(mcp_tools)} tools for HTTP client")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": mcp_tools
                }
            }
            
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Failed to list tools: {e}"
                }
            }
    
    async def _handle_tools_call(self, request_id: str, params: Dict[str, Any], request: Request) -> Dict[str, Any]:
        """Handle MCP tools/call request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": "Missing tool name"
                }
            }
        
        logger.info(f"Executing HTTP tool call: {tool_name}")
        
        try:
            # Extract authentication context
            auth_context = await self._extract_auth_context(arguments, request)
            
            # Verify subscription if auth context provided
            if auth_context and self.auth:
                subscription_valid = await self.auth.verify_subscription(auth_context)
                if not subscription_valid:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": "Valid subscription required"
                        }
                    }
            
            # Execute tool
            result = await self._execute_tool(tool_name, auth_context, arguments)
            
            if result.success:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result.data, indent=2, default=str) if result.data else "Success"
                            }
                        ],
                        "isError": False
                    }
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error: {result.error_message}"
                            }
                        ],
                        "isError": True
                    }
                }
                
        except Exception as e:
            logger.error(f"HTTP tool call error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
    
    async def _handle_ping(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping request"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "server": self.settings.mcp_server_name
            }
        }
    
    async def _extract_auth_context(self, arguments: Dict[str, Any], request: Request) -> Optional[AuthContext]:
        """Extract authentication context from arguments or headers"""
        # Try arguments first
        api_key = arguments.get("api_key")
        api_secret = arguments.get("api_secret")
        
        if api_key and api_secret:
            return self._create_auth_context(api_key, api_secret, "arguments")
        
        # Try HTTP headers
        headers = request.headers
        header_api_key = headers.get("X-Coinbase-API-Key") or headers.get("x-coinbase-api-key")
        header_api_secret = headers.get("X-Coinbase-API-Secret") or headers.get("x-coinbase-api-secret")
        
        if header_api_key and header_api_secret:
            return self._create_auth_context(header_api_key, header_api_secret, "headers")
        
        # Try environment variables
        import os
        env_api_key = os.getenv("COINBASE_API_KEY")
        env_api_secret = os.getenv("COINBASE_API_SECRET")
        
        if env_api_key and env_api_secret:
            return self._create_auth_context(env_api_key, env_api_secret, "environment")
        
        return None
    
    def _create_auth_context(self, api_key: str, api_secret: str, source: str) -> AuthContext:
        """Create authentication context from credentials"""
        import hashlib
        
        user_id_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        
        return AuthContext(
            api_key=api_key,
            api_secret=api_secret,
            user_id_hash=user_id_hash,
            timestamp=datetime.now().isoformat(),
            source=source
        )
    
    async def _execute_tool(self, tool_name: str, auth_context: Optional[AuthContext], arguments: Dict[str, Any]) -> ToolResult:
        """Execute a tool with the given arguments"""
        try:
            # Get tool from registry
            tool = self.registry.get_tool(tool_name)
            if not tool:
                return ToolResult(
                    success=False,
                    error_message=f"Tool '{tool_name}' not found"
                )
            
            # Remove auth parameters from tool arguments
            clean_args = {k: v for k, v in arguments.items() 
                         if k not in ["api_key", "api_secret"]}
            
            # Execute tool
            result = await tool.execute(auth_context, **clean_args)
            
            logger.info(f"HTTP tool '{tool_name}' executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"HTTP tool execution error: {e}")
            return ToolResult(
                success=False,
                error_message=str(e)
            )
    
    def _validate_response(self, response: Dict[str, Any], request_id: str, method: str) -> Dict[str, Any]:
        """Validate and fix JSON-RPC response structure"""
        try:
            # Ensure JSON-RPC field
            if "jsonrpc" not in response:
                response["jsonrpc"] = "2.0"
            
            # Ensure ID is never null
            if request_id is not None:
                if "id" not in response or response.get("id") is None:
                    response["id"] = request_id
            
            # Ensure response has either result or error
            if request_id is not None and "result" not in response and "error" not in response:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": "Server returned malformed response"
                    }
                }
            
            # Validate error structure
            if "error" in response:
                error = response["error"]
                if not isinstance(error, dict):
                    response["error"] = {"code": -32603, "message": str(error)}
                elif "code" not in error:
                    error["code"] = -32603
                elif "message" not in error:
                    error["message"] = "Unknown error"
            
            return response
            
        except Exception as e:
            logger.error(f"Response validation failed: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": "Response validation failed"
                }
            }


class MCPHttpAdapter:
    """
    HTTP MCP Protocol Adapter
    
    Provides MCP protocol over HTTP using FastAPI for web applications
    and REST API integrations.
    """
    
    def __init__(
        self,
        registry: ToolRegistry,
        storage: StorageBackend,
        auth: SubscriberAuth,
        settings: Settings,
        host: str = "0.0.0.0",
        port: Optional[int] = None
    ):
        """
        Initialize HTTP MCP adapter
        
        Args:
            registry: Tool registry containing available tools
            storage: Storage backend for persistence
            auth: Authentication system
            settings: Application settings
            host: Server host address
            port: Server port (uses settings.server_port if None)
        """
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI not available. Install with: pip install fastapi uvicorn")
        
        self.registry = registry
        self.storage = storage
        self.auth = auth
        self.settings = settings
        self.host = host
        self.port = port or settings.server_port
        
        # Create FastAPI app
        self.app = FastAPI(
            title=settings.mcp_server_name,
            description="Educational crypto tools with persistent storage",
            version="1.0.0",
            docs_url="/docs" if settings.is_development() else None,
            redoc_url="/redoc" if settings.is_development() else None
        )
        
        # Initialize endpoint handlers
        self.handlers = HTTPEndpointHandlers(registry, storage, auth, settings)
        
        # Setup routes
        self._setup_routes()
        
        # Server state
        self._running = False
        
        logger.info(f"HTTP MCP adapter initialized on {host}:{self.port}")
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return await self.handlers.health_check()
        
        @self.app.post("/mcp")
        async def mcp_endpoint(request: Request):
            """MCP protocol endpoint"""
            return await self.handlers.mcp_endpoint(request)
        
        @self.app.get("/")
        async def root():
            """Root endpoint with server information"""
            return {
                "service": self.settings.mcp_server_name,
                "version": "1.0.0",
                "description": "Educational crypto tools with persistent storage",
                "protocol": "MCP over HTTP",
                "endpoints": {
                    "health": "/health",
                    "mcp": "/mcp (POST)",
                    "docs": "/docs" if self.settings.is_development() else "disabled"
                }
            }
        
        # Development endpoints
        if self.settings.is_development():
            @self.app.get("/debug/tools")
            async def debug_tools():
                """Debug endpoint to list all tools"""
                tools = self.registry.get_tools()
                return {
                    "total_tools": len(tools),
                    "tools": [
                        {
                            "name": tool.schema.name,
                            "description": tool.schema.description,
                            "category": tool.schema.category
                        }
                        for tool in tools
                    ]
                }
    
    async def initialize(self):
        """Initialize the HTTP adapter"""
        logger.info("Initializing HTTP MCP adapter...")
        logger.info("✅ HTTP MCP adapter ready")
    
    async def start(self):
        """Start the HTTP server"""
        if self._running:
            logger.warning("HTTP server already running")
            return
        
        self._running = True
        logger.info(f"🚀 Starting HTTP MCP server on {self.host}:{self.port}")
        
        try:
            # Configure uvicorn
            config = uvicorn.Config(
                self.app,
                host=self.host,
                port=self.port,
                log_level=self.settings.log_level.lower(),
                access_log=self.settings.is_development(),
                reload=self.settings.is_development()
            )
            
            # Create and run server
            server = uvicorn.Server(config)
            await server.serve()
            
        except Exception as e:
            logger.error(f"HTTP server failed: {e}")
            raise
        finally:
            self._running = False
    
    async def stop(self):
        """Stop the HTTP server"""
        if not self._running:
            logger.warning("HTTP server not running")
            return
        
        logger.info("🛑 Stopping HTTP MCP server...")
        self._running = False
    
    async def cleanup(self):
        """Cleanup HTTP adapter resources"""
        logger.info("Cleaning up HTTP MCP adapter...")
        await self.stop()
        logger.info("✅ HTTP MCP adapter cleanup complete")
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get HTTP server information"""
        return {
            "host": self.host,
            "port": self.port,
            "running": self._running,
            "protocol": "HTTP",
            "framework": "FastAPI",
            "endpoints": {
                "health": f"http://{self.host}:{self.port}/health",
                "mcp": f"http://{self.host}:{self.port}/mcp",
                "docs": f"http://{self.host}:{self.port}/docs" if self.settings.is_development() else None
            }
        }