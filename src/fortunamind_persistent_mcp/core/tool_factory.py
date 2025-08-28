"""
Tool Factory - Enhanced extensibility for tool creation

Provides a centralized factory for creating tools with proper fallback
behavior and extension patterns. Addresses the extensibility concerns
identified in the senior engineer review.
"""

import logging
from typing import Dict, Type, Optional, Any, List
from abc import ABC, abstractmethod
from enum import Enum

# Clean, absolute imports using proper package name
from fortunamind_persistent_mcp.core.base import ReadOnlyTool, WriteEnabledTool
from fortunamind_persistent_mcp.persistent_mcp.storage.interface import StorageInterface
from fortunamind_persistent_mcp.config import Settings

logger = logging.getLogger(__name__)


class ToolType(str, Enum):
    """Tool types for factory creation"""
    PORTFOLIO = "portfolio"
    PRICES = "prices"
    MARKET_RESEARCH = "market_research"
    TRADING_JOURNAL = "trading_journal"
    TECHNICAL_INDICATORS = "technical_indicators"


class ToolImplementation(str, Enum):
    """Implementation types"""
    FRAMEWORK = "framework"       # Use framework tool
    PERSISTENT = "persistent"     # Framework + persistence layer
    MOCK = "mock"                # Mock/fallback implementation
    HYBRID = "hybrid"            # Best available combination


class ToolCreationError(Exception):
    """Raised when tool creation fails"""
    pass


class ToolFactoryInterface(ABC):
    """Interface for tool factories"""
    
    @abstractmethod
    def can_create(self, tool_type: ToolType, implementation: ToolImplementation) -> bool:
        """Check if this factory can create the specified tool"""
        pass
    
    @abstractmethod
    def create(self, tool_type: ToolType, **kwargs) -> Any:
        """Create a tool instance"""
        pass
    
    @abstractmethod
    def get_fallback_implementation(self, tool_type: ToolType) -> ToolImplementation:
        """Get the best fallback implementation for a tool type"""
        pass


class FrameworkToolFactory(ToolFactoryInterface):
    """Factory for framework-based tools"""
    
    def __init__(self):
        self.framework_available = self._check_framework_availability()
    
    def _check_framework_availability(self) -> bool:
        """Check if framework submodule is available"""
        try:
            from fortunamind_persistent_mcp.core.mock import FRAMEWORK_AVAILABLE
            return FRAMEWORK_AVAILABLE
        except ImportError:
            return False
    
    def can_create(self, tool_type: ToolType, implementation: ToolImplementation) -> bool:
        """Check if we can create framework tools"""
        if not self.framework_available:
            return False
            
        framework_tools = {
            ToolType.PORTFOLIO: "UnifiedPortfolioTool",
            ToolType.PRICES: "UnifiedPricesTool", 
            ToolType.MARKET_RESEARCH: "UnifiedMarketResearchTool",
        }
        
        return tool_type in framework_tools
    
    def create(self, tool_type: ToolType, **kwargs) -> Any:
        """Create framework tool instance"""
        if not self.can_create(tool_type, ToolImplementation.FRAMEWORK):
            raise ToolCreationError(f"Cannot create framework tool: {tool_type}")
        
        try:
            from fortunamind_persistent_mcp.core.mock import (
                UnifiedPortfolioTool,
                UnifiedPricesTool, 
                UnifiedMarketResearchTool
            )
            
            tool_class_map = {
                ToolType.PORTFOLIO: UnifiedPortfolioTool,
                ToolType.PRICES: UnifiedPricesTool,
                ToolType.MARKET_RESEARCH: UnifiedMarketResearchTool,
            }
            
            tool_class = tool_class_map[tool_type]
            return tool_class()
            
        except Exception as e:
            raise ToolCreationError(f"Failed to create framework tool {tool_type}: {e}")
    
    def get_fallback_implementation(self, tool_type: ToolType) -> ToolImplementation:
        """Framework tools fall back to mock"""
        return ToolImplementation.MOCK


class PersistentToolFactory(ToolFactoryInterface):
    """Factory for persistent-enhanced tools"""
    
    def __init__(self, storage: StorageInterface, settings: Settings):
        self.storage = storage
        self.settings = settings
        self.framework_factory = FrameworkToolFactory()
    
    def can_create(self, tool_type: ToolType, implementation: ToolImplementation) -> bool:
        """Check if we can create persistent tools"""
        persistent_tools = {
            ToolType.PORTFOLIO,
            ToolType.TRADING_JOURNAL, 
            ToolType.TECHNICAL_INDICATORS,
        }
        return tool_type in persistent_tools
    
    def create(self, tool_type: ToolType, **kwargs) -> Any:
        """Create persistent tool instance"""
        if not self.can_create(tool_type, ToolImplementation.PERSISTENT):
            raise ToolCreationError(f"Cannot create persistent tool: {tool_type}")
        
        try:
            if tool_type == ToolType.PORTFOLIO:
                from fortunamind_persistent_mcp.persistent_mcp.tools.persistent_portfolio import PersistentPortfolioTool
                return PersistentPortfolioTool(storage=self.storage)
                
            elif tool_type == ToolType.TRADING_JOURNAL:
                from fortunamind_persistent_mcp.persistent_mcp.tools.trading_journal import TradingJournalTool
                return TradingJournalTool(storage=self.storage, settings=self.settings)
                
            elif tool_type == ToolType.TECHNICAL_INDICATORS:
                from fortunamind_persistent_mcp.persistent_mcp.tools.technical_indicators import TechnicalIndicatorsTool
                return TechnicalIndicatorsTool(storage=self.storage, settings=self.settings)
                
            else:
                raise ToolCreationError(f"Unknown persistent tool type: {tool_type}")
                
        except Exception as e:
            raise ToolCreationError(f"Failed to create persistent tool {tool_type}: {e}")
    
    def get_fallback_implementation(self, tool_type: ToolType) -> ToolImplementation:
        """Persistent tools can fall back to framework or mock"""
        if self.framework_factory.can_create(tool_type, ToolImplementation.FRAMEWORK):
            return ToolImplementation.FRAMEWORK
        return ToolImplementation.MOCK


class MockToolFactory(ToolFactoryInterface):
    """Factory for mock/fallback tools"""
    
    def can_create(self, tool_type: ToolType, implementation: ToolImplementation) -> bool:
        """Mock factory can create any tool as fallback"""
        return implementation == ToolImplementation.MOCK
    
    def create(self, tool_type: ToolType, **kwargs) -> Any:
        """Create mock tool instance"""
        try:
            # Import mock tools from our proxy system
            from fortunamind_persistent_mcp.core.mock import (
                UnifiedPricesTool,
                UnifiedPortfolioTool,
                UnifiedMarketResearchTool
            )
            
            # Create appropriate mock based on tool type
            tool_map = {
                ToolType.PRICES: UnifiedPricesTool,
                ToolType.PORTFOLIO: UnifiedPortfolioTool,
                ToolType.MARKET_RESEARCH: UnifiedMarketResearchTool,
            }
            
            if tool_type in tool_map:
                tool_class = tool_map[tool_type]
                return tool_class() if callable(tool_class) else tool_class
            
            # For persistent tools, create minimal mock implementations
            return self._create_minimal_mock(tool_type, **kwargs)
            
        except Exception as e:
            # Fallback to minimal mock if import fails
            return self._create_minimal_mock(tool_type, **kwargs)
    
    def _create_minimal_mock(self, tool_type: ToolType, **kwargs) -> Any:
        """Create minimal mock implementations for persistent tools"""
        from fortunamind_persistent_mcp.core.base import ToolSchema, ToolCategory, Permission
        
        class MinimalMockTool(ReadOnlyTool):
            def __init__(self, tool_name: str):
                super().__init__()
                self.tool_name = tool_name
            
            @property
            def schema(self):
                return ToolSchema(
                    name=f"mock_{self.tool_name}",
                    description=f"Mock implementation of {self.tool_name} tool",
                    category=ToolCategory.DIAGNOSTIC,
                    permissions=[Permission.READ_ONLY],
                    parameters={"type": "object", "properties": {}, "required": []},
                    returns={"type": "object"}
                )
            
            async def _execute_impl(self, context) -> Any:
                return {
                    "status": "mock",
                    "message": f"This is a mock {self.tool_name} tool. Real implementation unavailable.",
                    "tool_type": self.tool_name
                }
        
        return MinimalMockTool(tool_type.value)
    
    def get_fallback_implementation(self, tool_type: ToolType) -> ToolImplementation:
        """Mock is the final fallback"""
        return ToolImplementation.MOCK


class UnifiedToolFactory:
    """
    Main tool factory that orchestrates all tool creation
    
    Provides intelligent tool creation with automatic fallback
    handling and extension support.
    """
    
    def __init__(self, storage: Optional[StorageInterface] = None, settings: Optional[Settings] = None):
        self.storage = storage
        self.settings = settings
        
        # Initialize sub-factories
        self.factories: List[ToolFactoryInterface] = [
            PersistentToolFactory(storage, settings) if storage and settings else None,
            FrameworkToolFactory(),
            MockToolFactory(),
        ]
        # Remove None factories
        self.factories = [f for f in self.factories if f is not None]
    
    def create_tool(
        self, 
        tool_type: ToolType, 
        preferred_implementation: ToolImplementation = ToolImplementation.HYBRID,
        **kwargs
    ) -> Any:
        """
        Create a tool with intelligent fallback handling
        
        Args:
            tool_type: Type of tool to create
            preferred_implementation: Preferred implementation type
            **kwargs: Additional arguments for tool creation
            
        Returns:
            Tool instance
            
        Raises:
            ToolCreationError: If no factory can create the tool
        """
        logger.debug(f"Creating tool: {tool_type}, preferred: {preferred_implementation}")
        
        # For hybrid, determine best available implementation
        if preferred_implementation == ToolImplementation.HYBRID:
            preferred_implementation = self._get_best_implementation(tool_type)
        
        # Try to create with preferred implementation
        for factory in self.factories:
            if factory.can_create(tool_type, preferred_implementation):
                try:
                    tool = factory.create(tool_type, **kwargs)
                    logger.info(f"✅ Created {tool_type} tool using {preferred_implementation} implementation")
                    return tool
                except ToolCreationError as e:
                    logger.warning(f"Factory failed to create {tool_type}: {e}")
                    continue
        
        # Try fallback implementations
        for factory in self.factories:
            fallback = factory.get_fallback_implementation(tool_type)
            if factory.can_create(tool_type, fallback):
                try:
                    tool = factory.create(tool_type, **kwargs)
                    logger.warning(f"⚠️ Created {tool_type} tool using fallback {fallback} implementation")
                    return tool
                except ToolCreationError as e:
                    logger.warning(f"Fallback factory failed to create {tool_type}: {e}")
                    continue
        
        raise ToolCreationError(f"No factory could create tool: {tool_type}")
    
    def _get_best_implementation(self, tool_type: ToolType) -> ToolImplementation:
        """Determine the best available implementation for a tool type"""
        
        # Persistent tools get persistence when available
        if tool_type in [ToolType.PORTFOLIO, ToolType.TRADING_JOURNAL, ToolType.TECHNICAL_INDICATORS]:
            if self.storage and self.settings:
                return ToolImplementation.PERSISTENT
        
        # Framework tools get framework when available
        for factory in self.factories:
            if isinstance(factory, FrameworkToolFactory) and factory.framework_available:
                if tool_type in [ToolType.PORTFOLIO, ToolType.PRICES, ToolType.MARKET_RESEARCH]:
                    return ToolImplementation.FRAMEWORK
        
        # Fall back to mock
        return ToolImplementation.MOCK
    
    def get_available_tools(self) -> Dict[ToolType, List[ToolImplementation]]:
        """Get all available tool types and their implementations"""
        available = {}
        
        for tool_type in ToolType:
            implementations = []
            for factory in self.factories:
                for implementation in ToolImplementation:
                    if factory.can_create(tool_type, implementation):
                        implementations.append(implementation)
            
            if implementations:
                available[tool_type] = implementations
        
        return available


# Convenience functions for common patterns
def create_portfolio_tool(storage: Optional[StorageInterface] = None, **kwargs) -> Any:
    """Create the best available portfolio tool"""
    factory = UnifiedToolFactory(storage=storage)
    return factory.create_tool(ToolType.PORTFOLIO, **kwargs)


def create_trading_journal_tool(storage: StorageInterface, settings: Settings, **kwargs) -> Any:
    """Create trading journal tool (requires persistence)"""
    factory = UnifiedToolFactory(storage=storage, settings=settings)
    return factory.create_tool(ToolType.TRADING_JOURNAL, **kwargs)


def create_all_available_tools(storage: Optional[StorageInterface] = None, settings: Optional[Settings] = None) -> Dict[str, Any]:
    """Create all available tools for registration"""
    factory = UnifiedToolFactory(storage=storage, settings=settings)
    tools = {}
    
    for tool_type in ToolType:
        try:
            tool = factory.create_tool(tool_type)
            tools[tool_type.value] = tool
        except ToolCreationError as e:
            logger.warning(f"Could not create {tool_type}: {e}")
    
    return tools