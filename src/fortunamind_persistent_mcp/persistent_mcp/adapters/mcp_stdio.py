"""
MCP STDIO Adapter

Handles MCP protocol communication over STDIO for direct client integration
with Claude Desktop and other MCP clients.
"""

import asyncio
import json
import logging
import sys
from typing import Dict, List, Optional, Any, TextIO
from datetime import datetime

try:
    from framework.src.core.registry import ToolRegistry
    from framework.src.core.interfaces import AuthContext, ToolResult, ToolSchema
    FRAMEWORK_AVAILABLE = True
except ImportError:
    from ...core.mock import ToolRegistry, AuthContext, ToolResult, ToolSchema
    FRAMEWORK_AVAILABLE = False

# Import new persistence library
from fortunamind_persistence.adapters import FrameworkPersistenceAdapter
from fortunamind_persistence.identity import EmailIdentity
from fortunamind_persistence.subscription import SubscriptionValidator
from fortunamind_persistence.storage.interfaces import PersistentStorageInterface
from fortunamind_persistence.rate_limiting import RateLimiter

from fortunamind_persistent_mcp.config import Settings

logger = logging.getLogger(__name__)


class MCPStdioAdapter:
    """
    MCP STDIO Protocol Adapter
    
    Implements the MCP protocol over STDIO for direct communication
    with MCP clients like Claude Desktop.
    """
    
    def __init__(
        self, 
        registry: ToolRegistry,
        storage_backend: PersistentStorageInterface,
        settings: Settings,
        stdin: Optional[TextIO] = None,
        stdout: Optional[TextIO] = None
    ):
        """
        Initialize MCP STDIO adapter
        
        Args:
            registry: Tool registry containing available tools
            storage_backend: Persistent storage implementation
            settings: Application settings
            stdin: Input stream (defaults to sys.stdin)
            stdout: Output stream (defaults to sys.stdout)
        """
        self.registry = registry
        self.settings = settings
        
        # Initialize persistence components
        self.identity = EmailIdentity()
        self.subscription_validator = SubscriptionValidator()
        self.rate_limiter = RateLimiter()
        
        # Create framework adapter
        self.persistence_adapter = FrameworkPersistenceAdapter(
            subscription_validator=self.subscription_validator,
            storage_backend=storage_backend,
            rate_limiter=self.rate_limiter
        )
        
        # I/O streams
        self.stdin = stdin or sys.stdin
        self.stdout = stdout or sys.stdout
        
        # Protocol state
        self._running = False
        self._request_id_counter = 0
        
        # Session state
        self._session_id: Optional[str] = None
        self._auth_context: Optional[AuthContext] = None
        
        logger.info("MCP STDIO adapter initialized")
    
    async def initialize(self):
        """Initialize the adapter"""
        logger.info("Initializing MCP STDIO adapter...")
        
        # Initialize persistence components
        await self.subscription_validator.initialize()
        
        # Setup I/O handling
        self._setup_stdio()
        
        logger.info("✅ MCP STDIO adapter ready")
    
    def _setup_stdio(self):
        """Setup STDIO streams for MCP communication"""
        # Ensure stdout is line buffered for immediate response
        if hasattr(self.stdout, 'reconfigure'):
            try:
                self.stdout.reconfigure(line_buffering=True)
            except (AttributeError, OSError):
                pass  # Not all streams support reconfiguration
    
    async def start(self):
        """Start the MCP STDIO server"""
        if self._running:
            logger.warning("MCP STDIO adapter already running")
            return
        
        self._running = True
        logger.info("🚀 Starting MCP STDIO protocol handler")
        
        try:
            await self._handle_stdio_loop()
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"MCP STDIO handler error: {e}")
            raise
        finally:
            self._running = False
    
    async def _handle_stdio_loop(self):
        """Main STDIO handling loop"""
        # Use asyncio to handle blocking I/O
        loop = asyncio.get_event_loop()
        
        while self._running:
            try:
                # Read line from stdin (blocking)
                line = await loop.run_in_executor(None, self.stdin.readline)
                
                if not line:  # EOF
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Process MCP request
                await self._process_request_line(line)
                
            except EOFError:
                break
            except Exception as e:
                logger.error(f"Error processing STDIO request: {e}")
                # Send error response
                await self._send_error_response(None, "internal_error", str(e))
    
    async def _process_request_line(self, line: str):
        """Process a single MCP request line"""
        try:
            # Parse JSON request
            request = json.loads(line)
            
            # Validate basic MCP structure
            if not isinstance(request, dict):
                await self._send_error_response(None, "parse_error", "Request must be JSON object")
                return
            
            request_id = request.get("id")
            method = request.get("method")
            
            if not method:
                await self._send_error_response(request_id, "invalid_request", "Missing method")
                return
            
            # Route request to appropriate handler
            response = await self._route_request(request)
            
            # Send response
            await self._send_response(response)
            
        except json.JSONDecodeError as e:
            await self._send_error_response(None, "parse_error", f"Invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Request processing error: {e}")
            await self._send_error_response(request.get("id"), "internal_error", str(e))
    
    async def _route_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Route MCP request to appropriate handler"""
        method = request["method"]
        request_id = request.get("id")
        params = request.get("params", {})
        
        logger.debug(f"Processing MCP request: {method} (id: {request_id})")
        
        # Handle MCP protocol methods
        if method == "initialize":
            return await self._handle_initialize(request_id, params)
        elif method == "tools/list":
            return await self._handle_tools_list(request_id, params)
        elif method == "tools/call":
            return await self._handle_tool_call(request_id, params)
        elif method == "ping":
            return await self._handle_ping(request_id, params)
        else:
            return {
                "id": request_id,
                "error": {
                    "code": "method_not_found",
                    "message": f"Unknown method: {method}"
                }
            }
    
    async def _handle_initialize(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request"""
        logger.info("Handling MCP initialize request")
        
        # Extract client info
        client_info = params.get("clientInfo", {})
        client_name = client_info.get("name", "unknown")
        client_version = client_info.get("version", "unknown")
        
        logger.info(f"MCP client: {client_name} v{client_version}")
        
        # Create session
        self._session_id = f"session_{datetime.now().isoformat()}"
        
        # Initialize response
        server_info = {
            "name": self.settings.mcp_server_name,
            "version": "1.0.0",
            "protocolVersion": "1.0.0"
        }
        
        capabilities = {
            "tools": {
                "listChanged": False  # We don't support dynamic tool registration yet
            },
            "logging": {}  # Basic logging support
        }
        
        return {
            "id": request_id,
            "result": {
                "serverInfo": server_info,
                "capabilities": capabilities
            }
        }
    
    async def _handle_tools_list(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tools/list request"""
        logger.debug("Handling tools/list request")
        
        try:
            # Get available tools from registry
            tools = self.registry.get_tools()
            
            # Convert to MCP format
            mcp_tools = []
            for tool in tools:
                mcp_tool = {
                    "name": tool.schema.name,
                    "description": tool.schema.description,
                    "inputSchema": tool.schema.parameters
                }
                mcp_tools.append(mcp_tool)
            
            logger.info(f"Returning {len(mcp_tools)} tools")
            
            return {
                "id": request_id,
                "result": {
                    "tools": mcp_tools
                }
            }
            
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return {
                "id": request_id,
                "error": {
                    "code": "internal_error",
                    "message": f"Failed to list tools: {e}"
                }
            }
    
    async def _handle_tool_call(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tools/call request"""
        tool_name = params.get("name")
        tool_arguments = params.get("arguments", {})
        
        logger.info(f"Handling tool call: {tool_name}")
        
        try:
            # Extract authentication context
            auth_context = await self._extract_auth_context(tool_arguments)
            
            # For new email-based authentication, validation is done in _extract_auth_context
            # For legacy API key auth, we'll allow it but log a deprecation warning
            if auth_context and auth_context.source == "mcp_stdio_legacy":
                logger.warning("Using deprecated API key authentication. Please upgrade to email + subscription key authentication.")
            
            # Execute tool
            result = await self._execute_tool(tool_name, auth_context, tool_arguments)
            
            if result.success:
                # Format successful response
                return {
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result.data, indent=2) if result.data else "Success"
                            }
                        ],
                        "isError": False
                    }
                }
            else:
                # Format error response
                return {
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
            logger.error(f"Tool call error: {e}")
            return {
                "id": request_id,
                "error": {
                    "code": "internal_error",
                    "message": str(e)
                }
            }
    
    async def _handle_ping(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping request"""
        return {
            "id": request_id,
            "result": {
                "status": "ok",
                "timestamp": datetime.now().isoformat()
            }
        }
    
    async def _extract_auth_context(self, arguments: Dict[str, Any]) -> Optional[AuthContext]:
        """Extract authentication context from tool arguments"""
        # Check for new authentication format (email + subscription key)
        email = arguments.get("email")
        subscription_key = arguments.get("subscription_key")
        
        if email and subscription_key:
            try:
                # Use the framework adapter to create auth context
                coinbase_credentials = {
                    'api_key': arguments.get("api_key"),
                    'api_secret': arguments.get("api_secret")
                }
                auth_context = await self.persistence_adapter.create_auth_context_from_credentials(
                    email=email,
                    subscription_key=subscription_key,
                    coinbase_credentials=coinbase_credentials if coinbase_credentials['api_key'] else None
                )
                return auth_context
                
            except ValueError as e:
                logger.warning(f"Authentication failed: {e}")
                return None
        
        # Fallback to legacy API key authentication
        api_key = arguments.get("api_key")
        api_secret = arguments.get("api_secret")
        
        if not api_key or not api_secret:
            return None
        
        # Create legacy auth context (for backward compatibility)
        user_id = self.identity.generate_user_id_from_api_key(api_key)
        return AuthContext(
            api_key=api_key,
            api_secret=api_secret,
            user_id_hash=user_id,
            timestamp=datetime.now().isoformat(),
            source="mcp_stdio_legacy"
        )
    
    # Removed _generate_user_id_hash - now using EmailIdentity.generate_user_id_from_api_key
    
    async def _execute_tool(
        self, 
        tool_name: str, 
        auth_context: Optional[AuthContext], 
        arguments: Dict[str, Any]
    ) -> ToolResult:
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
            
            logger.info(f"Tool '{tool_name}' executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return ToolResult(
                success=False,
                error_message=str(e)
            )
    
    async def _send_response(self, response: Dict[str, Any]):
        """Send MCP response to stdout"""
        try:
            response_json = json.dumps(response, separators=(',', ':'))
            self.stdout.write(response_json + "\n")
            self.stdout.flush()
            
        except Exception as e:
            logger.error(f"Failed to send response: {e}")
    
    async def _send_error_response(self, request_id: Optional[str], code: str, message: str):
        """Send MCP error response"""
        response = {
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
        await self._send_response(response)
    
    async def cleanup(self):
        """Cleanup adapter resources"""
        logger.info("Cleaning up MCP STDIO adapter...")
        self._running = False
        
        # Cleanup persistence components
        await self.subscription_validator.cleanup()
        
        # Close streams if we own them
        if self.stdin != sys.stdin:
            try:
                self.stdin.close()
            except Exception:
                pass
                
        if self.stdout != sys.stdout:
            try:
                self.stdout.close()
            except Exception:
                pass
        
        logger.info("✅ MCP STDIO adapter cleanup complete")