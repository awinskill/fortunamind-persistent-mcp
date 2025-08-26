"""
Mock Framework Classes

Mock implementations of FortunaMind framework classes for development
when the actual framework is not available via symlink.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


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


class UnifiedPricesTool:
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