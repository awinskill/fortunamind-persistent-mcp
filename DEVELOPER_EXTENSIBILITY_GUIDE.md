# Developer Extensibility Guide

## Overview

This guide explains how to extend the FortunaMind Persistent MCP Server after the architectural improvements made to address extensibility concerns.

## 🏗️ Architecture Summary

The system now features:
- **Tool Factory Pattern** for extensible tool creation
- **Framework Proxy** for safe access to parent framework
- **Simplified Storage** utilities without over-engineering
- **Resilient Imports** that work in all execution contexts
- **Package Structure** with proper setup.py

## 🔧 Adding New Tools

### 1. Using the Tool Factory

The `UnifiedToolFactory` supports multiple implementation strategies:

```python
from core.tool_factory import UnifiedToolFactory, ToolType, ToolImplementation

# Create factory with storage and settings
factory = UnifiedToolFactory(storage=storage, settings=settings)

# Create tools with automatic fallback
portfolio_tool = factory.create_tool(ToolType.PORTFOLIO)  # Best available
mock_tool = factory.create_tool(ToolType.PRICES, ToolImplementation.MOCK)  # Force mock
```

### 2. Adding a New Tool Type

To add a completely new tool:

1. **Add to ToolType enum**:
```python
# In src/core/tool_factory.py
class ToolType(str, Enum):
    PORTFOLIO = "portfolio"
    PRICES = "prices"
    # ... existing types
    NEW_ANALYSIS = "new_analysis"  # Add this
```

2. **Create the tool class**:
```python
# In src/persistent_mcp/tools/new_analysis.py
from core.base import ReadOnlyTool, ToolExecutionContext

class NewAnalysisTool(ReadOnlyTool):
    def __init__(self, storage=None, settings=None):
        super().__init__()
        self.storage = storage
        self.settings = settings
    
    @property
    def schema(self):
        return ToolSchema(
            name="new_analysis",
            description="Your new analysis tool",
            category=ToolCategory.MARKET_ANALYSIS,
            permissions=[Permission.READ_ONLY],
            parameters={"type": "object", "properties": {}, "required": []},
            returns={"type": "object"}
        )
    
    async def _execute_impl(self, context: ToolExecutionContext) -> Any:
        # Your implementation here
        return {"result": "analysis complete"}
```

3. **Register with factory**:
```python
# In src/core/tool_factory.py PersistentToolFactory.create()
elif tool_type == ToolType.NEW_ANALYSIS:
    from src.persistent_mcp.tools.new_analysis import NewAnalysisTool
    return NewAnalysisTool(storage=self.storage, settings=self.settings)
```

### 3. Extending Framework Tools

To create persistent versions of framework tools:

```python
class PersistentMarketAnalysisTool(ReadOnlyTool):
    def __init__(self, storage: StorageInterface):
        super().__init__()
        self.storage = storage
        
        # Try to load framework tool
        try:
            from framework_proxy import unified_tools
            tools = unified_tools()
            if hasattr(tools, 'UnifiedMarketResearchTool'):
                self.framework_tool = tools.UnifiedMarketResearchTool()
            else:
                self.framework_tool = None
        except Exception:
            self.framework_tool = None
    
    async def _execute_impl(self, context: ToolExecutionContext) -> Any:
        # Get data from framework tool
        if self.framework_tool:
            result = await self.framework_tool._execute_impl(context.auth_context, **context.parameters)
        else:
            result = {"mock": "data"}
        
        # Add persistence
        await self._store_analysis_result(context.auth_context.user_id_hash, result)
        
        # Add historical comparison
        result["historical_trends"] = await self._get_historical_trends(context.auth_context.user_id_hash)
        
        return result
```

## 📦 Storage Extensions

### 1. Simple Utilities

Use the simplified storage utilities:

```python
from core.storage import StorageMetrics, generate_record_id, validate_user_id_hash, sanitize_data

# Track metrics
metrics = StorageMetrics()
start_time = time.time()
# ... do operation
metrics.update(time.time() - start_time, success=True)

# Generate IDs
record_id = generate_record_id()

# Validate inputs
validate_user_id_hash(user_id)
clean_data = sanitize_data(user_input)
```

### 2. Custom Storage Backend

Create custom storage by implementing `StorageInterface`:

```python
from persistent_mcp.storage.interface import StorageInterface, StorageRecord, QueryFilter

class CustomStorageBackend(StorageInterface):
    def __init__(self, settings):
        self.settings = settings
        self.metrics = StorageMetrics()
    
    async def initialize(self) -> None:
        # Setup your storage
        pass
    
    async def store_record(self, record: StorageRecord) -> str:
        start_time = time.time()
        try:
            # Your storage logic
            record_id = generate_record_id()
            # ... store the record
            self.metrics.update(time.time() - start_time, True)
            return record_id
        except Exception as e:
            self.metrics.update(time.time() - start_time, False)
            raise
    
    # Implement other required methods...
```

## 🔌 Plugin System

### 1. Dynamic Tool Loading

Load tools dynamically:

```python
def load_plugin_tools(plugin_dir: str, factory: UnifiedToolFactory):
    """Load tools from plugin directory"""
    import importlib.util
    
    for plugin_file in Path(plugin_dir).glob("*_tool.py"):
        spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)
        plugin = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plugin)
        
        # Look for tool classes
        for attr_name in dir(plugin):
            attr = getattr(plugin, attr_name)
            if isinstance(attr, type) and issubclass(attr, BaseTool):
                # Register with factory or server
                tool_instance = attr()
                server.registry.register(tool_instance)
```

### 2. Configuration-Driven Extensions

Create tools based on configuration:

```python
# config.yml
custom_tools:
  - name: "custom_indicator"
    type: "technical"
    module: "plugins.custom_indicator"
    class: "CustomIndicatorTool"
    enabled: true

# Loading code
def load_configured_tools(config, factory):
    for tool_config in config.get('custom_tools', []):
        if not tool_config.get('enabled', True):
            continue
            
        module = importlib.import_module(tool_config['module'])
        tool_class = getattr(module, tool_config['class'])
        
        tool_instance = tool_class()
        factory.registry.register(tool_instance)
```

## 🧪 Testing Extensions

### 1. Test Framework Integration

```python
import pytest
from core.tool_factory import UnifiedToolFactory, ToolType

@pytest.fixture
async def factory():
    return UnifiedToolFactory()

async def test_tool_creation(factory):
    # Test tool creation
    tool = factory.create_tool(ToolType.PRICES)
    assert tool is not None
    
    # Test execution
    from core.mock import MockAuthContext
    context = ToolExecutionContext(
        auth_context=MockAuthContext(),
        parameters={},
        start_time=datetime.now(),
        execution_id="test"
    )
    
    result = await tool._execute_impl(context)
    assert result is not None
```

### 2. Mock Framework for Testing

```python
class MockFrameworkTool:
    def __init__(self):
        self.schema = ToolSchema(
            name="mock_framework_tool",
            description="Mock for testing",
            category=ToolCategory.DIAGNOSTIC,
            permissions=[Permission.READ_ONLY],
            parameters={},
            returns={}
        )
    
    async def _execute_impl(self, auth_context, **parameters):
        return {"mock": "result", "parameters": parameters}

# Use in tests
@pytest.fixture
def mock_framework_tools(monkeypatch):
    def mock_unified_tools():
        class MockModule:
            UnifiedPortfolioTool = MockFrameworkTool
        return MockModule()
    
    monkeypatch.setattr("framework_proxy.unified_tools", mock_unified_tools)
```

## ⚠️ Best Practices

### 1. Error Handling

Always use the factory pattern for robust error handling:

```python
try:
    tool = factory.create_tool(ToolType.PORTFOLIO)
except ToolCreationError as e:
    # Handle gracefully - factory will have tried fallbacks
    logger.warning(f"Could not create portfolio tool: {e}")
    tool = factory.create_tool(ToolType.PORTFOLIO, ToolImplementation.MOCK)
```

### 2. Import Resilience

Use the triple-try pattern for imports:

```python
try:
    from module import Class
except ImportError:
    try:
        from ..module import Class
    except ImportError:
        from src.module import Class
```

### 3. Graceful Degradation

Always provide fallback behavior:

```python
class RobustTool(ReadOnlyTool):
    async def _execute_impl(self, context: ToolExecutionContext) -> Any:
        try:
            # Try advanced feature
            return await self._advanced_analysis(context)
        except Exception as e:
            logger.warning(f"Advanced analysis failed: {e}")
            # Fall back to basic implementation
            return await self._basic_analysis(context)
```

## 📈 Performance Considerations

### 1. Lazy Loading

Load expensive resources only when needed:

```python
class OptimizedTool(ReadOnlyTool):
    def __init__(self):
        super().__init__()
        self._expensive_resource = None
    
    @property
    def expensive_resource(self):
        if self._expensive_resource is None:
            self._expensive_resource = load_expensive_resource()
        return self._expensive_resource
```

### 2. Caching

Use storage for caching expensive computations:

```python
async def _execute_impl(self, context: ToolExecutionContext) -> Any:
    cache_key = f"analysis_{hash(str(context.parameters))}"
    
    # Check cache
    cached_result = await self.storage.get_user_preference(
        context.auth_context.user_id_hash, 
        cache_key
    )
    
    if cached_result:
        return cached_result
    
    # Compute and cache
    result = await self._compute_analysis(context)
    await self.storage.store_user_preference(
        context.auth_context.user_id_hash,
        cache_key,
        result,
        category="cache"
    )
    
    return result
```

## 🚀 Deployment

The system now supports proper package installation:

```bash
# Install in development mode
pip install -e .

# Or install from git
pip install git+https://github.com/user/repo.git

# Run server
fortunamind-persistent-mcp
# or
fmcp-server
```

## 📋 Extension Checklist

When adding new functionality:

- [ ] Use the tool factory pattern
- [ ] Implement resilient imports (triple-try pattern)
- [ ] Provide graceful fallback behavior
- [ ] Add appropriate error handling
- [ ] Include tests with mocks
- [ ] Document the extension
- [ ] Consider performance implications
- [ ] Test in all execution contexts

## 🎯 Future Extensibility

The architecture supports:

- **Dynamic plugin loading** from directories
- **Configuration-driven tool creation**
- **Hot-swapping** of tool implementations
- **Multi-backend storage** with automatic failover
- **Framework version compatibility** through the proxy layer
- **Gradual migration** from mock to real implementations

This foundation enables rapid development while maintaining stability and backward compatibility.