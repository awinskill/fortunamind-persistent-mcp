# CLAUDE.md - FortunaMind Persistent MCP Server

This file provides **mandatory guidance** to Claude Code (claude.ai/code) when working with this FortunaMind Persistent MCP Server repository.

## ⚠️ **PROJECT OVERVIEW**

### Project Identity
**FortunaMind Persistent MCP Server** - Extended functionality MCP server leveraging the FortunaMind Tool Framework for persistent operations, enhanced analytics, and extended trading capabilities.

### 🎯 **ARCHITECTURE FOUNDATION**

This project is built upon the **FortunaMind Tool Framework** and **Unified MCP Server Architecture** from the main coinbase-mcp repository. Understanding these foundational components is **mandatory** for effective development.

## 🚨 **CRITICAL: FRAMEWORK SUBMODULE PROTECTION RULES**

### **ABSOLUTE PROHIBITION - NO FRAMEWORK MODIFICATIONS**

The `framework/` directory (once added as a git submodule) contains the FortunaMind Tool Framework from the parent `fortunamind-mcp` repository. This code is used by beta testers and MUST remain completely untouched.

#### **MANDATORY RULES - NO EXCEPTIONS**

1. **NEVER modify ANY file** within the `framework/` directory or submodule
2. **NEVER use Edit, Write, or MultiEdit tools** on any path starting with `framework/`
3. **NEVER commit changes** to files in the framework submodule
4. **NEVER run format, lint, or refactor commands** that affect framework files
5. **NEVER attempt to fix bugs or improve code** within the framework directory
6. **READ-ONLY access only** - you may use Read, Grep, Glob, and LS tools to understand the framework

#### **WHY THIS MATTERS**

- The framework code is shared with production beta testers via `fortunamind-mcp`
- Any modifications would break the beta testing experience
- The submodule ensures we use the exact same code without duplication
- This is a hard architectural boundary that MUST be respected

#### **WHAT YOU CAN DO**

✅ **READ** framework code to understand interfaces and contracts
✅ **IMPORT** from framework modules in your own code
✅ **EXTEND** framework classes in the `src/fortunamind_persistent_mcp/` directory
✅ **MOCK** framework functionality when it's not available
✅ **DOCUMENT** how to use framework components

#### **WHAT YOU CANNOT DO**

❌ **EDIT** any file in `framework/` directory
❌ **CREATE** new files in the framework directory
❌ **DELETE** framework files
❌ **REFACTOR** framework code, even if you see issues
❌ **FIX** bugs in framework code (report them instead)

#### **ENFORCEMENT**

If asked to modify framework code, you MUST:
1. **REFUSE** the request politely
2. **EXPLAIN** that framework modifications are prohibited
3. **SUGGEST** creating an extension or override in the project's own code
4. **OFFER** to report the issue for fixing in the parent repository

### **Example Response When Asked to Modify Framework**

> "I cannot modify files in the framework/ directory as it's a read-only submodule containing the shared FortunaMind Tool Framework. This code is used by beta testers and must remain unchanged. 
> 
> Instead, I can:
> - Create an extended version in our project that inherits from the framework class
> - Add a wrapper that modifies the behavior
> - Implement a mock version for our specific needs
> 
> Which approach would you prefer?"

---

## 🏗️ **FORTUNAMIND TOOL FRAMEWORK ARCHITECTURE**

### **Core Philosophy**
The FortunaMind Tool Framework implements a **unified, composable architecture** that provides consistent tool behavior across all server types while maximizing code reuse and maintainability.

### **Framework Components**

#### **1. Unified Tool Layer (`src/unified_tools/`)**
**Location**: `../coinbase-mcp/src/unified_tools/`

**Purpose**: Provides unified implementations that replace fragmented tool implementations across different server types.

**Key Components**:
```python
# Portfolio Tools
from .portfolio import (
    UnifiedPortfolioTool,          # Comprehensive portfolio overview
    UnifiedDetailedHoldingsTool,   # Granular holdings breakdown  
    UnifiedPortfolioPerformanceTool # Advanced performance analytics
)

# Market Data Tools
from .market import (
    UnifiedPricesTool,    # Real-time price data with symbol parsing fixes
    UnifiedCandleTool     # OHLCV historical data
)

# Transaction Tools
from .transactions import (
    UnifiedTransactionTool,  # Transaction history and analysis
    UnifiedOrdersTool,       # Order management and tracking
    UnifiedFillsTool         # Trade execution details
)

# Analytics Tools
from .analytics import (
    UnifiedPerformanceTool,  # Advanced performance metrics
    UnifiedBatchTool         # Batch operations and analysis
)

# Research Tools  
from .research import (
    UnifiedMarketResearchTool  # Market analysis and insights
)

# Diagnostic Tools
from .diagnostics import (
    UnifiedDiagnosticTool,      # System diagnostics
    UnifiedConnectionTestTool,  # Connection validation
    UnifiedConfigurationTool    # Configuration management
)

# Composed Tools (Phase 1 Enhancement)
from .composed import (
    UnifiedSmartPortfolioTool,    # Intelligent portfolio insights
    UnifiedTradingActivityTool    # Comprehensive trading analysis
)
```

#### **2. Core Interface System (`src/core/interfaces.py`)**
**Location**: `../coinbase-mcp/src/core/interfaces.py`

**Defines the contracts that all tools, executors, and adapters must follow:**

```python
# Core Authentication
@dataclass
class AuthContext:
    """Standardized authentication context"""
    api_key: str
    api_secret: str  
    user_id_hash: str
    timestamp: str
    signature: Optional[str] = None
    source: str = "unknown"

# Tool Definition
@dataclass 
class ToolSchema:
    """Standardized tool schema"""
    name: str
    description: str
    category: ToolCategory
    permissions: List[Permission]
    parameters: Dict[str, Any]
    returns: Dict[str, Any]

# Execution Result
@dataclass
class ToolResult:
    """Standardized execution result"""
    success: bool
    data: Any = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

# Base Tool Interface
class ToolInterface(ABC):
    @property
    @abstractmethod
    def schema(self) -> ToolSchema: pass
    
    @abstractmethod
    async def execute(self, auth_context: Optional[AuthContext], **parameters) -> ToolResult: pass
```

#### **3. Base Tool Classes (`src/core/base.py`)**
**Location**: `../coinbase-mcp/src/core/base.py`

**Provides abstract base classes with common functionality:**

```python
class BaseTool(ToolInterface):
    """Base class for all FortunaMind tools"""
    # Provides: parameter validation, error handling, execution timing, metrics

class ReadOnlyTool(BaseTool):
    """Base for read-only tools (safe for all environments)"""
    # Default permissions: [Permission.READ_ONLY]

class WriteEnabledTool(BaseTool):  
    """Base for tools that modify data"""
    # Default permissions: [Permission.READ_ONLY, Permission.WRITE]
    # Enhanced permission checks for write operations
```

#### **4. Permission and Category System**

```python
class Permission(Enum):
    READ_ONLY = "read_only"    # Safe operations (portfolio viewing)
    WRITE = "write"            # Data modification (order placement)
    ADMIN = "admin"            # System administration

class ToolCategory(Enum):
    PORTFOLIO = "portfolio"      # Portfolio management tools
    MARKET = "market"           # Market data and pricing
    TRANSACTIONS = "transactions" # Transaction and order tools
    ANALYTICS = "analytics"      # Performance and risk analytics  
    RESEARCH = "research"        # Market research and insights
    DIAGNOSTIC = "diagnostic"    # System diagnostics and health
```

### **Framework Benefits**

#### **🔧 Unified Implementation Pattern**
All tools follow the same implementation pattern:

```python
class UnifiedExampleTool(ReadOnlyTool):
    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="example_tool",
            description="""Tool description with semantic field definitions:
            • field1: Description of what this field represents
            • field2: Description of this field's meaning""",
            category=ToolCategory.PORTFOLIO,
            permissions=[Permission.READ_ONLY],
            parameters={
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "Parameter description"},
                    "api_key": {"type": "string", "description": "Coinbase API key (optional if set in environment)"},
                    "api_secret": {"type": "string", "description": "Coinbase API secret (optional if set in environment)"}
                },
                "required": []
            },
            returns={"type": "object"}
        )

    async def _execute_impl(self, auth_context: Optional[AuthContext], **parameters) -> Any:
        """Implementation logic here"""
        # 1. Create legacy auth context for backward compatibility
        # 2. Use existing tool implementations  
        # 3. Apply response formatting
        # 4. Return results
```

#### **🔄 Legacy Compatibility Bridge**
The framework maintains compatibility with existing tools through legacy auth context conversion:

```python
def _create_legacy_auth_context(
    self, auth_context: Optional[AuthContext], parameters: Dict[str, Any]
) -> AuthenticationContext:
    """Convert unified auth context to legacy format"""
    if not auth_context:
        raise ToolExecutionError("Authentication required")

    # Extract credentials from parameters or auth context
    api_key = parameters.get("api_key") or getattr(auth_context, "api_key", None)
    api_secret = parameters.get("api_secret") or getattr(auth_context, "api_secret", None)

    if not api_key or not api_secret:
        raise ToolExecutionError("Missing API credentials")

    # Create legacy authentication context
    return AuthenticationContext(
        api_key=api_key,
        api_secret=api_secret,
        user_id_hash=getattr(auth_context, "user_id_hash", "unified"),
        timestamp=getattr(auth_context, "timestamp", None),
        signature=getattr(auth_context, "signature", None),
    )
```

## 🚀 **UNIFIED MCP SERVER ARCHITECTURE**

### **Core Concept**
The Unified MCP Server Architecture eliminates the need for multiple fragmented MCP server implementations by providing a **single, configurable server** that can adapt to different deployment scenarios.

### **Server Types Unified**

#### **1. Standard MCP Server (STDIO)**
- **Usage**: Direct MCP protocol communication via STDIO
- **Clients**: Claude Desktop, Perplexity, other MCP clients
- **Configuration**: Uses unified tool registry with MCP protocol adapter

#### **2. HTTP MCP Server**  
- **Usage**: HTTP endpoints with MCP protocol over REST
- **Clients**: Web applications, custom integrations
- **Configuration**: Same tool registry with HTTP adapter

#### **3. Persistent MCP Server (This Project)**
- **Usage**: Enhanced functionality with persistent storage and extended operations
- **Clients**: Applications requiring stateful operations
- **Configuration**: Unified tool registry + persistence layer + extended capabilities

### **Unified Server Configuration**

All servers share the same core configuration:

```python
# Server initialization (same for all types)
from src.core.registry import ToolRegistry
from src.unified_tools import (
    UnifiedPortfolioTool,
    UnifiedPricesTool, 
    UnifiedMarketResearchTool,
    # ... all unified tools
)

# Universal tool registration
registry = ToolRegistry()
registry.register(UnifiedPortfolioTool())
registry.register(UnifiedPricesTool())
registry.register(UnifiedMarketResearchTool())
# ... register all tools

# Server-specific adapter
if server_type == "stdio":
    adapter = StdioMCPAdapter(registry)
elif server_type == "http":
    adapter = HttpMCPAdapter(registry)  
elif server_type == "persistent":
    adapter = PersistentMCPAdapter(registry)  # This project
```

### **Protocol Adapters**

Each server type uses a specific adapter that implements the `ServerAdapterInterface`:

```python
class ServerAdapterInterface(ABC):
    @abstractmethod
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming request and return response"""

    @abstractmethod  
    def format_tool_list(self, tools: List[ToolSchema]) -> Dict[str, Any]:
        """Format tool list for the specific server protocol"""

    @abstractmethod
    def format_tool_result(self, result: ToolResult, request_id: str) -> Dict[str, Any]:
        """Format tool result for the specific server protocol"""

    @abstractmethod
    def extract_auth_context(self, request: Dict[str, Any]) -> Optional[AuthContext]:
        """Extract authentication context from request"""
```

## 📚 **LEVERAGING THE FRAMEWORK IN THIS PROJECT**

### **Step 1: Import the Framework**

```python
# Import unified tools
from ..coinbase-mcp.src.unified_tools import (
    UnifiedPortfolioTool,
    UnifiedPricesTool,
    UnifiedMarketResearchTool,
    UnifiedPerformanceTool,
    # ... all tools you need
)

# Import core framework
from ..coinbase-mcp.src.core.interfaces import (
    ToolInterface, 
    AuthContext,
    ToolResult,
    ToolSchema
)

from ..coinbase-mcp.src.core.base import (
    BaseTool,
    ReadOnlyTool, 
    WriteEnabledTool
)
```

### **Step 2: Create Persistent-Specific Extensions**

```python
class PersistentPortfolioTool(UnifiedPortfolioTool):
    """Extended portfolio tool with persistence capabilities"""
    
    async def _execute_impl(self, auth_context: Optional[AuthContext], **parameters) -> Any:
        # Call parent implementation
        result = await super()._execute_impl(auth_context, **parameters)
        
        # Add persistent storage
        await self._store_portfolio_snapshot(auth_context.user_id_hash, result)
        
        # Add persistent-specific enhancements
        result = await self._add_historical_comparisons(result)
        
        return result
    
    async def _store_portfolio_snapshot(self, user_id: str, data: Any) -> None:
        """Store portfolio data for historical analysis"""
        # Implement persistence logic
        pass
        
    async def _add_historical_comparisons(self, data: Any) -> Any:
        """Add historical trend analysis"""
        # Implement historical comparison logic
        pass
```

### **Step 3: Register Enhanced Tools**

```python
# Create registry with enhanced tools
registry = ToolRegistry()

# Register base unified tools
registry.register(UnifiedPricesTool())         # Market data (no persistence needed)
registry.register(UnifiedMarketResearchTool()) # Research (no persistence needed)

# Register persistent-enhanced tools  
registry.register(PersistentPortfolioTool())   # Enhanced portfolio with history
registry.register(PersistentPerformanceTool()) # Enhanced performance tracking
registry.register(PersistentAnalyticsTool())   # Advanced analytics with persistence
```

### **Step 4: Implement Persistent MCP Adapter**

```python
class PersistentMCPAdapter(ServerAdapterInterface):
    """MCP adapter with persistence and extended capabilities"""
    
    def __init__(self, registry: ToolRegistry, storage_backend: StorageInterface):
        self.registry = registry
        self.storage = storage_backend
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP requests with persistence context"""
        # Standard MCP protocol handling
        # + Persistence context injection
        # + Extended capability routing
```

## 🛠️ **DEVELOPMENT PATTERNS**

### **Pattern 1: Tool Extension**

When you need to extend an existing unified tool:

```python
class ExtendedUnifiedTool(UnifiedBaseTool):
    """Extend existing tool with additional capabilities"""
    
    async def _execute_impl(self, auth_context: Optional[AuthContext], **parameters) -> Any:
        # Get base result
        base_result = await super()._execute_impl(auth_context, **parameters)
        
        # Add enhancements
        enhanced_result = await self._add_enhancements(base_result, auth_context, parameters)
        
        return enhanced_result
```

### **Pattern 2: Composed Operations**

Create tools that combine multiple unified tools:

```python
class ComposedAnalyticsTool(ReadOnlyTool):
    """Combine portfolio + performance + market data for comprehensive analysis"""
    
    def __init__(self):
        super().__init__()
        self.portfolio_tool = UnifiedPortfolioTool()
        self.performance_tool = UnifiedPerformanceTool()
        self.market_tool = UnifiedMarketResearchTool()
        
    async def _execute_impl(self, auth_context: Optional[AuthContext], **parameters) -> Any:
        # Execute multiple tools
        portfolio_data = await self.portfolio_tool._execute_impl(auth_context, **parameters)
        performance_data = await self.performance_tool._execute_impl(auth_context, **parameters)
        market_data = await self.market_tool._execute_impl(auth_context, **parameters)
        
        # Combine and analyze
        return self._create_comprehensive_analysis(portfolio_data, performance_data, market_data)
```

### **Pattern 3: Persistent State Management**

```python
class StatefulTool(ReadOnlyTool):
    """Tool with persistent state management"""
    
    def __init__(self, storage: StorageInterface):
        super().__init__()
        self.storage = storage
        
    async def _execute_impl(self, auth_context: Optional[AuthContext], **parameters) -> Any:
        # Load previous state
        previous_state = await self.storage.load_state(auth_context.user_id_hash, self.schema.name)
        
        # Execute with state context
        result = await self._execute_with_state(auth_context, previous_state, **parameters)
        
        # Save new state
        await self.storage.save_state(auth_context.user_id_hash, self.schema.name, result)
        
        return result
```

## 🔧 **CONFIGURATION REQUIREMENTS**

### **Environment Variables**
```bash
# Coinbase API (same as parent project)
COINBASE_API_KEY=organizations/your-org/apiKeys/your-key
COINBASE_API_SECRET=your-pem-private-key

# Persistent-specific configuration
STORAGE_BACKEND=postgresql  # postgresql, redis, file
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port/db
STORAGE_PATH=/path/to/storage  # for file backend

# Server configuration  
SERVER_TYPE=persistent
MCP_SERVER_NAME=FortunaMind Persistent MCP Server
LOG_LEVEL=INFO
```

### **Dependencies**
```python
# requirements.txt additions to parent project
psycopg2-binary>=2.9.0    # PostgreSQL adapter
redis>=4.0.0              # Redis adapter  
aiofiles>=0.8.0           # File I/O
sqlalchemy>=2.0.0         # ORM
alembic>=1.8.0           # Database migrations
```

## 🎯 **PROJECT GOALS AND USE CASES**

### **Enhanced Capabilities**

1. **Historical Analysis**
   - Portfolio evolution tracking
   - Performance trend analysis  
   - Risk metric evolution
   - Comparative benchmarking over time

2. **Persistent User Context**
   - User preferences and settings
   - Custom dashboard configurations
   - Alert thresholds and notifications
   - Personalized insights

3. **Advanced Analytics**
   - Multi-timeframe correlation analysis
   - Risk scenario modeling
   - Portfolio optimization suggestions
   - Predictive analytics

4. **Workflow Automation**
   - Scheduled analysis runs
   - Automated report generation
   - Alert triggering and notifications
   - Batch processing capabilities

### **Target Use Cases**

1. **Professional Portfolio Management**
   - Institutional investors requiring detailed historical analysis
   - Financial advisors managing multiple client portfolios
   - Quantitative analysts requiring extensive data persistence

2. **Research and Development**
   - Academic research requiring long-term data collection
   - Strategy backtesting with persistent results
   - Algorithm development with historical performance tracking

3. **Enterprise Integration**
   - Integration with existing trading platforms
   - Custom dashboard development
   - Multi-user environments with shared analytics

## ⚠️ **MANDATORY DEVELOPMENT GUIDELINES**

### **🔒 Framework Submodule Protection**

1. **Framework is READ-ONLY** - Never modify `framework/` directory contents
2. **Use Extension Pattern** - Extend framework classes, don't modify them
3. **Report Don't Fix** - Report framework issues, don't fix them locally
4. **Submodule Updates** - Only update submodule commit hash when explicitly requested

### **🚨 Code Reuse Requirements**

1. **NEVER reimplement existing unified tools** - Always extend or compose
2. **ALWAYS use the framework interfaces** - Ensures compatibility and maintainability  
3. **ALWAYS implement proper authentication** - Use the unified auth context system
4. **ALWAYS follow the permission model** - Respect READ_ONLY vs WRITE vs ADMIN permissions

### **🔒 Security Requirements**

1. **Stateless API Credentials** - Never store API keys permanently
2. **User Data Isolation** - Ensure proper user_id_hash-based data separation
3. **Audit Logging** - Log all operations with user context
4. **Secure Storage** - Encrypt sensitive data at rest

### **📊 Performance Requirements**

1. **Connection Pooling** - Use connection pools for database operations
2. **Caching Strategy** - Implement intelligent caching for frequently accessed data
3. **Background Processing** - Use async operations for heavy computations
4. **Resource Limits** - Implement proper timeouts and resource constraints

## 🚀 **GETTING STARTED**

### **1. Setup Development Environment**
```bash
# Clone this repository
cd /Users/andywinskill/Documents/Programming/AIAgents/MCP/fortunamind-persistent-mcp

# Link to parent framework
ln -s ../coinbase-mcp/src ./framework

# Install dependencies
pip install -r requirements.txt
pip install -r ../coinbase-mcp/requirements.txt

# Setup database
alembic upgrade head
```

### **2. Basic Server Implementation**
```python
# main.py
from framework.core.registry import ToolRegistry
from framework.unified_tools import *
from adapters.persistent_mcp_adapter import PersistentMCPAdapter
from storage.database_backend import DatabaseStorage

# Initialize storage
storage = DatabaseStorage(database_url=os.getenv("DATABASE_URL"))

# Create registry and register tools
registry = ToolRegistry()
registry.register(UnifiedPortfolioTool())
registry.register(PersistentPortfolioTool(storage))
# ... register all needed tools

# Create server
adapter = PersistentMCPAdapter(registry, storage)
server = PersistentMCPServer(adapter)

# Start server
server.run()
```

### **3. Testing Your Implementation**
```python
# test_persistent_server.py
import asyncio
from main import create_server

async def test_portfolio_persistence():
    server = create_server()
    
    # Test portfolio snapshot storage
    auth_context = AuthContext(
        api_key="test-key",
        api_secret="test-secret", 
        user_id_hash="test-user",
        timestamp="2023-01-01T00:00:00Z"
    )
    
    result = await server.execute_tool(
        "persistent_portfolio_summary",
        auth_context,
        {"include_history": True}
    )
    
    assert result.success
    assert "historical_comparison" in result.data

if __name__ == "__main__":
    asyncio.run(test_portfolio_persistence())
```

## 📚 **ADDITIONAL RESOURCES**

### **Parent Project Documentation**
- **Main Repository**: `/Users/andywinskill/Documents/Programming/AIAgents/MCP/coinbase-mcp/`
- **Architecture Documentation**: `../coinbase-mcp/documentation/`
- **Tool Framework**: `../coinbase-mcp/src/unified_tools/`
- **Core Interfaces**: `../coinbase-mcp/src/core/`

### **Key Reference Files**
- **Unified Tools**: `../coinbase-mcp/src/unified_tools/__init__.py`
- **Core Interfaces**: `../coinbase-mcp/src/core/interfaces.py`
- **Base Classes**: `../coinbase-mcp/src/core/base.py`
- **Portfolio Example**: `../coinbase-mcp/src/unified_tools/portfolio.py`

## 🔧 **DEVELOPMENT NOTES (Updated 2025-08-26)**

### **Resolved Import Issues**

The project has been refactored to eliminate the problematic "triple-try import pattern" that was causing import failures and fragility. Key improvements:

1. **Clean Package Structure**: All code now uses absolute imports with proper package naming:
   ```python
   # OLD (problematic):
   try:
       from core.base import ReadOnlyTool
   except ImportError:
       try:
           from ..core.base import ReadOnlyTool
       except ImportError:
           from src.core.base import ReadOnlyTool

   # NEW (clean):
   from fortunamind_persistent_mcp.core.base import ReadOnlyTool
   ```

2. **Proper Package Installation**: The package can now be properly installed and imported:
   ```bash
   pip install -e .
   python -c "from fortunamind_persistent_mcp.core.tool_factory import UnifiedToolFactory"
   ```

3. **Package Structure**:
   ```
   src/
     fortunamind_persistent_mcp/
       __init__.py
       config.py
       core/
         base.py
         tool_factory.py
       persistent_mcp/
         server.py
         tools/
         storage/
   ```

4. **Entry Points**: Both setup.py and pyproject.toml are properly configured with correct module paths.

### **Installation and Testing**

The package installs successfully with all dependencies resolved. Framework warnings are expected during development:

```
⚠️ Framework not available: Framework module unified_tools has missing dependencies: No module named 'fortunamind_framework'
This is expected during initial development setup.
```

This warning is harmless and indicates the framework proxy is working correctly, falling back to mock implementations when the parent framework isn't available.

---

**Ready to build the next generation of persistent MCP capabilities!** 🚀📊

**Remember**: This project leverages the proven FortunaMind Tool Framework - focus on enhancing and extending rather than rebuilding. Maximum code reuse leads to maximum reliability and maintainability.