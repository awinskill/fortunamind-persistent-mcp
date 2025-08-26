"""
Persistent MCP Server

Main server class that orchestrates all persistent MCP functionality
including technical indicators, trading journal, and security scanning.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union

# Set up logging first
logger = logging.getLogger(__name__)

# Framework components will be loaded at runtime
# For now, always use mock classes and detect framework availability later
FRAMEWORK_AVAILABLE = False

try:
    # Try to access framework submodule to see if it works
    import framework.src.unified_tools
    # Check if the key tools are available
    if hasattr(framework.src.unified_tools, 'UnifiedPortfolioTool'):
        logger.info("Framework submodule detected and available")
        FRAMEWORK_AVAILABLE = True
    else:
        logger.warning("Framework submodule exists but tools not found")
except ImportError as e:
    logger.warning(f"Framework submodule not available: {e}")

# Clean imports using proper package structure
from fortunamind_persistent_mcp.core.mock import ToolRegistry, AuthContext, ToolResult
from fortunamind_persistent_mcp.config import Settings
from .adapters import MCPStdioAdapter, MCPHttpAdapter
from .storage.interface import StorageInterface
from .auth import SubscriberAuth
from .tools.technical_indicators import TechnicalIndicatorsTool
from .tools.trading_journal import TradingJournalTool
from .tools.persistent_portfolio import PersistentPortfolioTool


class PersistentMCPServer:
    """
    FortunaMind Persistent MCP Server
    
    Provides educational crypto tools with persistence for learning
    and improvement over time. Designed for crypto-curious professionals
    who want to make informed decisions.
    """
    
    def __init__(self, settings: Settings, server_mode: str = "stdio"):
        """
        Initialize the persistent MCP server
        
        Args:
            settings: Application configuration
            server_mode: Server mode - "stdio" or "http"
        """
        self.settings = settings
        self.server_mode = server_mode
        self.registry = ToolRegistry()
        self.storage: Optional[StorageInterface] = None
        self.auth: Optional[SubscriberAuth] = None
        self.adapter: Optional[Union[MCPStdioAdapter, MCPHttpAdapter]] = None
        
        # Server state
        self._running = False
        self._shutdown_event = asyncio.Event()
        
        logger.info(f"Initializing {settings.mcp_server_name} in {server_mode} mode")
    
    async def initialize(self):
        """Initialize all server components"""
        logger.info("Initializing server components...")
        
        # Initialize storage backend
        if self.storage is None:
            try:
                from .storage import SupabaseStorageBackend
                self.storage = SupabaseStorageBackend(self.settings)
                await self.storage.initialize()
                logger.info("✅ Storage backend initialized")
            except Exception as e:
                logger.warning(f"Supabase storage initialization failed: {e}")
                logger.info("🔄 Falling back to mock storage for demo mode")
                from .storage import MockStorageBackend
                self.storage = MockStorageBackend(self.settings)
                await self.storage.initialize()
                logger.info("✅ Mock storage backend initialized")
        
        # Initialize authentication
        if self.auth is None:
            self.auth = SubscriberAuth(self.settings)
            logger.info("✅ Authentication system initialized")
        
        # Register tools
        await self._register_tools()
        
        # Initialize MCP adapter based on server mode
        if self.adapter is None:
            if self.server_mode == "http":
                self.adapter = MCPHttpAdapter(
                    registry=self.registry,
                    storage=self.storage,
                    auth=self.auth,
                    settings=self.settings
                )
            else:  # Default to STDIO
                self.adapter = MCPStdioAdapter(
                    registry=self.registry,
                    storage=self.storage,
                    auth=self.auth,
                    settings=self.settings
                )
            
            await self.adapter.initialize()
            logger.info(f"✅ MCP {self.server_mode.upper()} adapter initialized")
        
        logger.info("🎯 Server initialization complete")
    
    async def _register_tools(self):
        """Register all available tools using the extensible factory pattern"""
        logger.info("Registering tools using unified factory...")
        
        # Import the tool factory
        from fortunamind_persistent_mcp.core.tool_factory import UnifiedToolFactory, ToolType, create_all_available_tools
        
        # Create factory with our storage and settings
        factory = UnifiedToolFactory(storage=self.storage, settings=self.settings)
        
        # Show available implementations
        available_tools = factory.get_available_tools()
        logger.info(f"Available tool implementations: {len(available_tools)} tool types")
        for tool_type, implementations in available_tools.items():
            logger.debug(f"  {tool_type}: {implementations}")
        
        # Register tools based on settings
        total_tools = 0
        
        # Core tools (always enabled)
        core_tools = [ToolType.PRICES, ToolType.MARKET_RESEARCH]
        for tool_type in core_tools:
            try:
                tool = factory.create_tool(tool_type)
                self.registry.register(tool)
                total_tools += 1
                logger.debug(f"Registered core tool: {tool_type}")
            except Exception as e:
                logger.warning(f"Failed to register core tool {tool_type}: {e}")
        
        # Conditional tools based on settings
        if self.settings.enable_portfolio_integration:
            try:
                portfolio_tool = factory.create_tool(ToolType.PORTFOLIO)
                self.registry.register(portfolio_tool)
                total_tools += 1
                logger.debug("Registered portfolio tool")
            except Exception as e:
                logger.warning(f"Failed to register portfolio tool: {e}")
        
        if self.settings.enable_technical_indicators:
            try:
                tech_tool = factory.create_tool(ToolType.TECHNICAL_INDICATORS)
                self.registry.register(tech_tool)
                total_tools += 1
                logger.debug("Registered technical indicators tool")
            except Exception as e:
                logger.warning(f"Failed to register technical indicators tool: {e}")
        
        if self.settings.enable_trading_journal:
            try:
                journal_tool = factory.create_tool(ToolType.TRADING_JOURNAL)
                self.registry.register(journal_tool)
                total_tools += 1
                logger.debug("Registered trading journal tool")
            except Exception as e:
                logger.warning(f"Failed to register trading journal tool: {e}")
        
        logger.info(f"✅ Registered {total_tools} tools successfully")
        
        if total_tools == 0:
            logger.error("❌ No tools registered! Server will not be functional.")
            # Register at least one mock tool so server can start
            try:
                mock_tool = factory.create_tool(ToolType.PRICES)  # Will create mock
                self.registry.register(mock_tool)
                logger.info("⚠️ Registered emergency mock tool to allow server startup")
            except Exception as e:
                logger.error(f"Cannot even create mock tools: {e}")
                raise RuntimeError("Server cannot start - no tools available")
    
    async def start(self):
        """Start the MCP server"""
        if self._running:
            logger.warning("Server is already running")
            return
        
        try:
            # Initialize if not already done
            await self.initialize()
            
            self._running = True
            logger.info(f"🚀 FortunaMind Persistent MCP Server started ({self.server_mode} mode)")
            logger.info(f"📊 Educational tools ready for crypto-curious professionals")
            
            # Start the MCP adapter (this will handle protocol communication)
            await self.adapter.start()
            
            # For HTTP mode, the server runs continuously
            # For STDIO mode, wait for shutdown signal
            if self.server_mode == "stdio":
                await self._shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"Server startup failed: {e}")
            raise
        finally:
            await self._cleanup()
    
    async def stop(self):
        """Stop the MCP server gracefully"""
        if not self._running:
            logger.warning("Server is not running")
            return
        
        logger.info("🛑 Stopping FortunaMind Persistent MCP Server...")
        self._running = False
        self._shutdown_event.set()
    
    async def _cleanup(self):
        """Clean up resources"""
        logger.info("🧹 Cleaning up server resources...")
        
        if self.adapter:
            await self.adapter.cleanup()
        
        if self.storage:
            await self.storage.cleanup()
        
        logger.info("✅ Server cleanup complete")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check and return status
        
        Returns:
            Dictionary with health status information
        """
        status = {
            "status": "healthy",
            "server": "FortunaMind Persistent MCP Server",
            "version": "1.0.0",
            "running": self._running,
            "components": {}
        }
        
        # Check storage
        if self.storage:
            try:
                await self.storage.health_check()
                status["components"]["storage"] = "healthy"
            except Exception as e:
                status["components"]["storage"] = f"unhealthy: {e}"
                status["status"] = "degraded"
        
        # Check auth
        if self.auth:
            try:
                await self.auth.health_check()
                status["components"]["auth"] = "healthy"
            except Exception as e:
                status["components"]["auth"] = f"unhealthy: {e}"
                status["status"] = "degraded"
        
        # Check tools
        try:
            tools = self.registry.get_tools()
            status["components"]["tools"] = f"{len(tools)} tools registered"
        except Exception as e:
            status["components"]["tools"] = f"error: {e}"
            status["status"] = "degraded"
        
        return status
    
    async def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get all available tool schemas for MCP tools/list
        
        Returns:
            List of tool schema dictionaries
        """
        try:
            tools = self.registry.get_tools()
            return [tool.schema.to_dict() for tool in tools]
        except Exception as e:
            logger.error(f"Failed to get tool schemas: {e}")
            return []
    
    async def execute_tool(
        self,
        tool_name: str,
        auth_context: Optional[AuthContext],
        parameters: Dict[str, Any]
    ) -> ToolResult:
        """
        Execute a specific tool
        
        Args:
            tool_name: Name of the tool to execute
            auth_context: User authentication context
            parameters: Tool parameters
            
        Returns:
            Tool execution result
        """
        try:
            # Get tool from registry
            tool = self.registry.get_tool(tool_name)
            if not tool:
                return ToolResult(
                    success=False,
                    error_message=f"Tool '{tool_name}' not found"
                )
            
            # Execute tool
            result = await tool.execute(auth_context, **parameters)
            
            logger.info(f"Tool '{tool_name}' executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return ToolResult(
                success=False,
                error_message=str(e)
            )
    
    def get_supported_features(self) -> Dict[str, bool]:
        """
        Get list of supported features based on configuration
        
        Returns:
            Dictionary of feature names and their enabled status
        """
        return {
            "trading_journal": self.settings.enable_trading_journal,
            "technical_indicators": self.settings.enable_technical_indicators,
            "portfolio_integration": self.settings.enable_portfolio_integration,
            "pre_trade_analysis": self.settings.enable_pre_trade_analysis,
            "advanced_analytics": self.settings.enable_advanced_analytics,
            "predictive_insights": self.settings.enable_predictive_insights,
            "framework_integration": FRAMEWORK_AVAILABLE,
            "security_scanning": True,  # Always enabled
            "educational_content": True,  # Always enabled
            "privacy_controls": True,  # Always enabled
        }