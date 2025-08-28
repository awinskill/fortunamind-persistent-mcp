"""
Framework Proxy with Mock Fallback

Tries to import from the copied framework first, falls back to mock implementations
if the framework is not available. This provides safe isolation while leveraging
the real framework tools when possible.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

# Framework proxy - try to import real framework tools first
FRAMEWORK_AVAILABLE = False
_framework_tools = {}

def _try_import_framework():
    """Attempt to import framework tools from the copied framework directory"""
    global FRAMEWORK_AVAILABLE, _framework_tools
    
    try:
        # Import from the copied framework at framework/src/
        import sys
        import os
        
        # Add framework to path
        framework_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../framework/src"))
        if framework_path not in sys.path:
            sys.path.insert(0, framework_path)
        
        # Try importing core framework first
        import core.interfaces as framework_interfaces
        import core.base as framework_base
        import core.registry as framework_registry
        
        # Try importing unified tools
        import unified_tools
        
        # Extract the classes we need
        AuthContext = framework_interfaces.AuthContext
        ToolResult = framework_interfaces.ToolResult  
        ToolSchema = framework_interfaces.ToolSchema
        ReadOnlyTool = framework_base.ReadOnlyTool
        WriteEnabledTool = framework_base.WriteEnabledTool
        ToolRegistry = framework_registry.ToolRegistry
        
        UnifiedPortfolioTool = unified_tools.UnifiedPortfolioTool
        UnifiedPricesTool = unified_tools.UnifiedPricesTool
        UnifiedMarketResearchTool = unified_tools.UnifiedMarketResearchTool
        UnifiedPerformanceTool = unified_tools.UnifiedPerformanceTool
        UnifiedTransactionTool = unified_tools.UnifiedTransactionTool
        UnifiedOrdersTool = unified_tools.UnifiedOrdersTool
        
        _framework_tools.update({
            'UnifiedPortfolioTool': UnifiedPortfolioTool,
            'UnifiedPricesTool': UnifiedPricesTool,
            'UnifiedMarketResearchTool': UnifiedMarketResearchTool,
            'UnifiedPerformanceTool': UnifiedPerformanceTool,
            'UnifiedTransactionTool': UnifiedTransactionTool,
            'UnifiedOrdersTool': UnifiedOrdersTool,
            'AuthContext': AuthContext,
            'ToolResult': ToolResult,
            'ToolSchema': ToolSchema,
            'ReadOnlyTool': ReadOnlyTool,
            'WriteEnabledTool': WriteEnabledTool,
            'ToolRegistry': ToolRegistry,
        })
        
        FRAMEWORK_AVAILABLE = True
        logger.info("✅ Framework tools loaded from copied framework directory")
        return True
        
    except ImportError as e:
        logger.warning(f"⚠️ Framework not available: {e}")
        logger.info("Falling back to mock implementations")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error loading framework: {e}")
        return False

# Try to import framework tools on module load
_try_import_framework()

def get_framework_tool(name: str):
    """Get a framework tool if available, otherwise return None"""
    return _framework_tools.get(name)


@dataclass
class AuthContext:
    """Mock authentication context"""
    api_key: str
    api_secret: str
    user_id_hash: str
    timestamp: str
    signature: Optional[str] = None
    source: str = "mock"


@dataclass
class ToolResult:
    """Mock tool execution result"""
    success: bool
    data: Any = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ToolSchema:
    """Mock tool schema"""
    name: str
    description: str
    category: str
    permissions: List[str]
    parameters: Dict[str, Any]
    returns: Dict[str, Any]


class ToolRegistry:
    """Mock tool registry"""
    
    def __init__(self):
        self.tools: Dict[str, Any] = {}
        logger.warning("Using mock ToolRegistry - framework not available")
    
    def register(self, tool):
        """Register a tool"""
        if hasattr(tool, 'schema') and hasattr(tool.schema, 'name'):
            self.tools[tool.schema.name] = tool
            logger.debug(f"Registered mock tool: {tool.schema.name}")
    
    def get_tools(self) -> List[Any]:
        """Get all registered tools"""
        return list(self.tools.values())
    
    def get_tool(self, name: str) -> Optional[Any]:
        """Get a specific tool by name"""
        return self.tools.get(name)


class ReadOnlyTool(ABC):
    """Mock read-only tool base class"""
    
    @property
    @abstractmethod
    def schema(self) -> ToolSchema:
        """Tool schema"""
        pass
    
    @abstractmethod
    async def _execute_impl(self, auth_context: Optional[AuthContext], **parameters) -> Any:
        """Execute tool implementation"""
        pass
    
    async def execute(self, auth_context: Optional[AuthContext], **parameters) -> ToolResult:
        """Execute tool with error handling"""
        try:
            start_time = datetime.now()
            result = await self._execute_impl(auth_context, **parameters)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ToolResult(
                success=True,
                data=result,
                execution_time=execution_time
            )
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return ToolResult(
                success=False,
                error_message=str(e)
            )


class WriteEnabledTool(ReadOnlyTool):
    """Mock write-enabled tool base class"""
    pass


# Export the right classes - framework if available, mock if not

# Core classes
if FRAMEWORK_AVAILABLE:
    # Use real framework classes
    AuthContext = _framework_tools['AuthContext']
    ToolResult = _framework_tools['ToolResult'] 
    ToolSchema = _framework_tools['ToolSchema']
    ReadOnlyTool = _framework_tools['ReadOnlyTool']
    WriteEnabledTool = _framework_tools['WriteEnabledTool']
    ToolRegistry = _framework_tools['ToolRegistry']
    
    # Tool classes
    UnifiedPortfolioTool = _framework_tools['UnifiedPortfolioTool']
    UnifiedPricesTool = _framework_tools['UnifiedPricesTool']
    UnifiedMarketResearchTool = _framework_tools['UnifiedMarketResearchTool']
    UnifiedPerformanceTool = _framework_tools['UnifiedPerformanceTool']
    UnifiedTransactionTool = _framework_tools['UnifiedTransactionTool']
    UnifiedOrdersTool = _framework_tools['UnifiedOrdersTool']
    
else:
    # Use mock implementations when framework not available
    
    class MockUnifiedPricesTool:
        """Mock prices tool for development"""
        
        @property
        def schema(self) -> ToolSchema:
            return ToolSchema(
                name="unified_prices",
                description="Mock prices tool",
                category="market_data",
                permissions=["read_only"],
                parameters={},
                returns={}
            )
        
        async def _execute_impl(self, auth_context: Optional[AuthContext], **parameters) -> Any:
            """Mock price data implementation"""
            logger.warning("Using mock price data - framework not available")
            
            symbol = parameters.get("symbol", "BTC-USD")
            granularity = parameters.get("granularity", "ONE_HOUR")
            start = parameters.get("start", 7)
            
            # Generate mock candlestick data
            import random
            from datetime import timedelta
            
            base_price = 45000 if "BTC" in symbol else 3000
            candles = []
            
            for i in range(24 * start):  # Hourly data for specified days
                price = base_price * (1 + random.uniform(-0.05, 0.05))
                high = price * random.uniform(1.01, 1.03)
                low = price * random.uniform(0.97, 0.99)
                volume = random.uniform(1000, 10000)
                
                candles.append({
                    "start": (datetime.now() - timedelta(hours=24*start-i)).isoformat(),
                    "low": str(low),
                    "high": str(high),
                    "open": str(price),
                    "close": str(price),
                    "volume": str(volume)
                })
            
            return {
                "symbol": symbol,
                "granularity": granularity,
                "candles": candles
            }
        
        async def execute(self, auth_context: Optional[AuthContext], **parameters) -> ToolResult:
            """Execute with mock data"""
            try:
                result = await self._execute_impl(auth_context, **parameters)
                return ToolResult(success=True, data=result)
            except Exception as e:
                return ToolResult(success=False, error_message=str(e))
    
    # Mock tool classes
    UnifiedPricesTool = MockUnifiedPricesTool
    
    class MockBaseTool(ReadOnlyTool):
        """Generic mock tool"""
        def __init__(self, name: str):
            self.name = name
            
        @property  
        def schema(self) -> ToolSchema:
            return ToolSchema(
                name=self.name,
                description=f"Mock {self.name} tool",
                category="mock",
                permissions=["read_only"],
                parameters={},
                returns={}
            )
        
        async def _execute_impl(self, auth_context: Optional[AuthContext], **parameters) -> Any:
            return {"status": "mock", "message": f"Mock {self.name} response"}
    
    # Create mock versions of other tools
    class MockUnifiedPortfolioTool(MockBaseTool):
        def __init__(self):
            super().__init__("portfolio")
    
    class MockUnifiedMarketResearchTool(MockBaseTool):
        def __init__(self):
            super().__init__("market_research")
    
    class MockUnifiedPerformanceTool(MockBaseTool):
        def __init__(self):
            super().__init__("performance")
            
    class MockUnifiedTransactionTool(MockBaseTool):
        def __init__(self):
            super().__init__("transactions")
            
    class MockUnifiedOrdersTool(MockBaseTool):
        def __init__(self):
            super().__init__("orders")
    
    UnifiedPortfolioTool = MockUnifiedPortfolioTool
    UnifiedMarketResearchTool = MockUnifiedMarketResearchTool
    UnifiedPerformanceTool = MockUnifiedPerformanceTool
    UnifiedTransactionTool = MockUnifiedTransactionTool
    UnifiedOrdersTool = MockUnifiedOrdersTool