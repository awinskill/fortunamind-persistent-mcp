"""
Core Base Classes

Provides comprehensive base classes for tools, services, and components
to reduce code duplication and ensure consistent patterns across the application.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Type
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

try:
    from framework.src.core.interfaces import AuthContext, ToolResult, ToolSchema
    from framework.src.core.base import ReadOnlyTool as FrameworkReadOnlyTool, WriteEnabledTool as FrameworkWriteEnabledTool
    FRAMEWORK_AVAILABLE = True
except ImportError:
    from .mock import AuthContext, ToolResult, ToolSchema, ReadOnlyTool as FrameworkReadOnlyTool, WriteEnabledTool as FrameworkWriteEnabledTool
    FRAMEWORK_AVAILABLE = False

from config import Settings
from core.security import SecurityScanner, SecurityThreat, ThreatLevel

logger = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    """Tool categories for organization"""
    PORTFOLIO_MANAGEMENT = "portfolio_management"
    MARKET_ANALYSIS = "market_analysis" 
    TECHNICAL_ANALYSIS = "technical_analysis"
    RISK_MANAGEMENT = "risk_management"
    EDUCATIONAL = "educational"
    DIAGNOSTIC = "diagnostic"


class Permission(str, Enum):
    """Tool permissions"""
    READ_ONLY = "read_only"
    WRITE = "write"
    ADMIN = "admin"


@dataclass
class ValidationError:
    """Parameter validation error"""
    field: str
    message: str
    code: str


@dataclass
class ToolExecutionContext:
    """Enhanced execution context with metrics and validation"""
    auth_context: Optional[AuthContext]
    parameters: Dict[str, Any]
    start_time: datetime
    execution_id: str
    user_id_hash: Optional[str] = None
    
    def get_execution_time(self) -> float:
        """Get execution time in seconds"""
        return (datetime.now() - self.start_time).total_seconds()


class BaseTool(ABC):
    """
    Enhanced base tool class with comprehensive functionality
    
    Features:
    - Automatic parameter validation
    - Security scanning for sensitive data
    - Consistent error handling and logging
    - Execution metrics and timing
    - Educational content helpers
    - Storage backend integration
    """
    
    def __init__(self, settings: Optional[Settings] = None, storage=None):
        """
        Initialize base tool
        
        Args:
            settings: Application settings
            storage: Optional storage backend
        """
        self.settings = settings
        self.storage = storage
        self._security_scanner = None
        self._execution_metrics = {}
        
        # Initialize security scanner if settings available
        if settings and hasattr(settings, 'security_profile'):
            sensitivity = settings.security_profile.value.upper() if hasattr(settings.security_profile, 'value') else 'HIGH'
            self._security_scanner = SecurityScanner(sensitivity_level=sensitivity)
        
        logger.debug(f"Initialized {self.__class__.__name__}")
    
    @property
    @abstractmethod
    def schema(self) -> ToolSchema:
        """Tool schema definition - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def _execute_impl(self, context: ToolExecutionContext) -> Any:
        """
        Tool implementation - must be implemented by subclasses
        
        Args:
            context: Execution context with auth, parameters, and metrics
            
        Returns:
            Tool execution result
        """
        pass
    
    async def execute(self, auth_context: Optional[AuthContext], **parameters) -> ToolResult:
        """
        Execute tool with comprehensive error handling and validation
        
        Args:
            auth_context: Authentication context
            **parameters: Tool parameters
            
        Returns:
            Tool execution result
        """
        execution_id = f"{self.schema.name}_{int(time.time() * 1000)}"
        start_time = datetime.now()
        
        try:
            # Create execution context
            context = ToolExecutionContext(
                auth_context=auth_context,
                parameters=parameters,
                start_time=start_time,
                execution_id=execution_id,
                user_id_hash=auth_context.user_id_hash if auth_context else None
            )
            
            # Validate parameters
            validation_errors = await self._validate_parameters(parameters)
            if validation_errors:
                return ToolResult(
                    success=False,
                    error_message=f"Parameter validation failed: {'; '.join(error.message for error in validation_errors)}",
                    metadata={
                        "validation_errors": [
                            {"field": error.field, "message": error.message, "code": error.code}
                            for error in validation_errors
                        ],
                        "execution_id": execution_id
                    }
                )
            
            # Security scan for sensitive data
            security_issues = await self._scan_for_security_threats(parameters)
            if security_issues:
                logger.warning(f"Security threats detected in {self.schema.name}: {len(security_issues)} issues")
                return ToolResult(
                    success=False,
                    error_message="Security scan detected sensitive information in input parameters",
                    metadata={
                        "security_threats": [
                            {
                                "type": threat.threat_type,
                                "level": threat.level.value,
                                "description": threat.description,
                                "confidence": threat.confidence
                            }
                            for threat in security_issues
                        ],
                        "execution_id": execution_id
                    }
                )
            
            # Execute tool implementation
            result = await self._execute_impl(context)
            
            # Record successful execution metrics
            execution_time = context.get_execution_time()
            self._record_execution_metrics(execution_id, execution_time, True)
            
            logger.info(f"Tool {self.schema.name} executed successfully in {execution_time:.3f}s")
            
            return ToolResult(
                success=True,
                data=result,
                execution_time=execution_time,
                metadata={
                    "execution_id": execution_id,
                    "tool_category": self.schema.category if hasattr(self.schema, 'category') else None
                }
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_execution_metrics(execution_id, execution_time, False)
            
            logger.error(f"Tool {self.schema.name} execution failed: {str(e)}")
            
            return ToolResult(
                success=False,
                error_message=str(e),
                execution_time=execution_time,
                metadata={"execution_id": execution_id}
            )
    
    async def _validate_parameters(self, parameters: Dict[str, Any]) -> List[ValidationError]:
        """
        Validate tool parameters against schema
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        schema_params = self.schema.parameters
        
        if not isinstance(schema_params, dict) or "properties" not in schema_params:
            return errors
        
        required_fields = schema_params.get("required", [])
        properties = schema_params.get("properties", {})
        
        # Check required fields
        for field in required_fields:
            if field not in parameters or parameters[field] is None:
                errors.append(ValidationError(
                    field=field,
                    message=f"Required field '{field}' is missing",
                    code="MISSING_REQUIRED_FIELD"
                ))
        
        # Validate field types and constraints
        for field, value in parameters.items():
            if field not in properties:
                continue
                
            field_spec = properties[field]
            field_type = field_spec.get("type")
            
            if value is None:
                continue
            
            # Type validation
            if field_type == "string" and not isinstance(value, str):
                errors.append(ValidationError(
                    field=field,
                    message=f"Field '{field}' must be a string",
                    code="INVALID_TYPE"
                ))
            elif field_type == "integer" and not isinstance(value, int):
                errors.append(ValidationError(
                    field=field,
                    message=f"Field '{field}' must be an integer",
                    code="INVALID_TYPE"
                ))
            elif field_type == "number" and not isinstance(value, (int, float)):
                errors.append(ValidationError(
                    field=field,
                    message=f"Field '{field}' must be a number",
                    code="INVALID_TYPE"
                ))
            elif field_type == "boolean" and not isinstance(value, bool):
                errors.append(ValidationError(
                    field=field,
                    message=f"Field '{field}' must be a boolean",
                    code="INVALID_TYPE"
                ))
            
            # Enum validation
            enum_values = field_spec.get("enum")
            if enum_values and value not in enum_values:
                errors.append(ValidationError(
                    field=field,
                    message=f"Field '{field}' must be one of: {', '.join(map(str, enum_values))}",
                    code="INVALID_ENUM_VALUE"
                ))
            
            # String length validation
            if field_type == "string" and isinstance(value, str):
                min_length = field_spec.get("minLength")
                max_length = field_spec.get("maxLength")
                
                if min_length and len(value) < min_length:
                    errors.append(ValidationError(
                        field=field,
                        message=f"Field '{field}' must be at least {min_length} characters",
                        code="STRING_TOO_SHORT"
                    ))
                
                if max_length and len(value) > max_length:
                    errors.append(ValidationError(
                        field=field,
                        message=f"Field '{field}' must be at most {max_length} characters",
                        code="STRING_TOO_LONG"
                    ))
            
            # Number range validation
            if field_type in ["number", "integer"] and isinstance(value, (int, float)):
                minimum = field_spec.get("minimum")
                maximum = field_spec.get("maximum")
                
                if minimum is not None and value < minimum:
                    errors.append(ValidationError(
                        field=field,
                        message=f"Field '{field}' must be at least {minimum}",
                        code="NUMBER_TOO_SMALL"
                    ))
                
                if maximum is not None and value > maximum:
                    errors.append(ValidationError(
                        field=field,
                        message=f"Field '{field}' must be at most {maximum}",
                        code="NUMBER_TOO_LARGE"
                    ))
        
        return errors
    
    async def _scan_for_security_threats(self, parameters: Dict[str, Any]) -> List[SecurityThreat]:
        """
        Scan parameters for security threats
        
        Args:
            parameters: Parameters to scan
            
        Returns:
            List of detected security threats
        """
        if not self._security_scanner:
            return []
        
        threats = []
        
        # Scan string parameters for threats
        for key, value in parameters.items():
            if isinstance(value, str) and value.strip():
                # Skip API credentials parameters - they're expected to contain sensitive data
                if key.lower() in ['api_key', 'api_secret', 'private_key', 'secret', 'token']:
                    continue
                
                detected_threats = self._security_scanner.scan_content(value, context=f"parameter:{key}")
                
                # Filter out low-confidence threats for parameter validation
                high_confidence_threats = [
                    threat for threat in detected_threats
                    if threat.confidence > 0.7 and threat.level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]
                ]
                
                threats.extend(high_confidence_threats)
        
        return threats
    
    def _record_execution_metrics(self, execution_id: str, execution_time: float, success: bool) -> None:
        """Record execution metrics for monitoring"""
        self._execution_metrics[execution_id] = {
            "tool_name": self.schema.name,
            "execution_time": execution_time,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        # Keep only last 100 executions to prevent memory growth
        if len(self._execution_metrics) > 100:
            oldest_key = min(self._execution_metrics.keys())
            del self._execution_metrics[oldest_key]
    
    def get_execution_metrics(self) -> Dict[str, Any]:
        """Get execution metrics for this tool"""
        if not self._execution_metrics:
            return {"total_executions": 0}
        
        total = len(self._execution_metrics)
        successful = sum(1 for m in self._execution_metrics.values() if m["success"])
        avg_time = sum(m["execution_time"] for m in self._execution_metrics.values()) / total
        
        return {
            "total_executions": total,
            "successful_executions": successful,
            "success_rate": successful / total,
            "average_execution_time": round(avg_time, 3),
            "last_execution": max(m["timestamp"] for m in self._execution_metrics.values())
        }
    
    # === Helper Methods for Common Patterns ===
    
    def _require_auth(self, auth_context: Optional[AuthContext]) -> AuthContext:
        """
        Require authentication and return auth context
        
        Args:
            auth_context: Optional auth context
            
        Returns:
            Auth context if valid
            
        Raises:
            ValueError: If authentication is required but not provided
        """
        if not auth_context:
            raise ValueError("Authentication is required for this operation")
        
        if not auth_context.user_id_hash:
            raise ValueError("Valid user authentication is required")
        
        return auth_context
    
    def _extract_api_credentials(
        self, 
        parameters: Dict[str, Any], 
        auth_context: Optional[AuthContext]
    ) -> tuple[str, str]:
        """
        Extract API credentials from parameters or auth context
        
        Args:
            parameters: Tool parameters
            auth_context: Authentication context
            
        Returns:
            Tuple of (api_key, api_secret)
            
        Raises:
            ValueError: If credentials are not available
        """
        api_key = parameters.get("api_key")
        api_secret = parameters.get("api_secret")
        
        # Fall back to auth context
        if not api_key and auth_context:
            api_key = getattr(auth_context, "api_key", None)
        
        if not api_secret and auth_context:
            api_secret = getattr(auth_context, "api_secret", None)
        
        # Fall back to environment/settings
        if not api_key and self.settings:
            api_key = getattr(self.settings, "coinbase_api_key", None)
        
        if not api_secret and self.settings:
            api_secret = getattr(self.settings, "coinbase_api_secret", None)
        
        if not api_key or not api_secret:
            raise ValueError(
                "API credentials are required. Provide api_key and api_secret parameters, "
                "or configure them in your environment variables."
            )
        
        return api_key, api_secret
    
    def _generate_educational_content(
        self,
        content_type: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, str]:
        """
        Generate educational content for beginners
        
        Args:
            content_type: Type of educational content to generate
            context: Additional context for personalization
            
        Returns:
            Dictionary of educational content
        """
        context = context or {}
        
        # Base educational content library
        content_library = {
            "crypto_basics": {
                "title": "Understanding Cryptocurrency",
                "content": """
Cryptocurrency is digital money secured by cryptography. Unlike traditional currency, 
it's decentralized - meaning no single authority (like a bank) controls it.

Key concepts:
• **Blockchain**: The technology that records all transactions
• **Volatility**: Crypto prices can change dramatically
• **Market Cap**: The total value of a cryptocurrency
• **Liquidity**: How easily you can buy/sell without affecting price
                """.strip()
            },
            
            "portfolio_management": {
                "title": "Smart Portfolio Management", 
                "content": """
A crypto portfolio is your collection of different cryptocurrencies. Smart management principles:

• **Diversification**: Don't put all money in one crypto
• **Position Sizing**: Only invest what you can afford to lose
• **Risk Management**: Set limits on losses
• **Regular Review**: Check performance and rebalance if needed
• **Long-term Thinking**: Avoid emotional day-trading
                """.strip()
            },
            
            "technical_analysis": {
                "title": "Technical Analysis Basics",
                "content": """
Technical analysis uses price charts and patterns to predict future movements. 

Important principles:
• **No Crystal Ball**: Indicators show possibilities, not certainties
• **Multiple Confirmation**: Use several indicators together
• **Market Context**: Consider overall market conditions
• **Risk Management**: Always have exit strategies
• **Practice**: Start with small amounts while learning
                """.strip()
            },
            
            "risk_management": {
                "title": "Managing Investment Risk",
                "content": """
Risk management is protecting your investment capital. Key strategies:

• **Stop Losses**: Set prices where you'll sell to limit losses
• **Position Sizing**: Never risk more than 1-5% on a single trade
• **Diversification**: Spread risk across different assets
• **Emotional Control**: Don't panic buy/sell
• **Emergency Fund**: Keep some cash available for opportunities
                """.strip()
            }
        }
        
        # Return requested content or default guidance
        return content_library.get(content_type, {
            "title": "Investment Guidance",
            "content": "Remember: Do your own research, never invest more than you can afford to lose, and consider your risk tolerance."
        })
    
    async def _store_execution_history(
        self,
        context: ToolExecutionContext,
        result: Any,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Store execution history for analysis and improvement
        
        Args:
            context: Execution context
            result: Tool execution result
            metadata: Additional metadata
        """
        if not self.storage or not context.auth_context:
            return
        
        try:
            history_data = {
                "tool_name": self.schema.name,
                "parameters": context.parameters,
                "execution_time": context.get_execution_time(),
                "success": True,
                "result_summary": self._summarize_result(result),
                "metadata": metadata or {}
            }
            
            # Store using generic record storage
            from persistent_mcp.storage.interface import StorageRecord, DataType
            
            record = StorageRecord(
                user_id_hash=context.auth_context.user_id_hash,
                data_type=DataType.USER_PREFERENCE,  # Using as generic activity tracking
                data=history_data,
                timestamp=context.start_time,
                tags=["tool_execution", self.schema.name],
                metadata={"category": "execution_history"}
            )
            
            await self.storage.store_record(record)
            
        except Exception as e:
            logger.warning(f"Failed to store execution history: {e}")
    
    def _summarize_result(self, result: Any) -> Dict[str, Any]:
        """Create a summary of execution result for history storage"""
        if isinstance(result, dict):
            return {
                "type": "dict",
                "keys": list(result.keys())[:10],  # Limit to prevent large storage
                "size": len(result)
            }
        elif isinstance(result, list):
            return {
                "type": "list",
                "length": len(result),
                "sample": result[:3] if result else []
            }
        else:
            return {
                "type": type(result).__name__,
                "summary": str(result)[:200]  # Truncate long strings
            }


class ReadOnlyTool(BaseTool, FrameworkReadOnlyTool):
    """
    Enhanced read-only tool base class
    
    Inherits all BaseTool functionality and ensures read-only permissions
    """
    
    def __init__(self, settings: Optional[Settings] = None, storage=None):
        super().__init__(settings, storage)
    
    @property
    def permissions(self) -> List[Permission]:
        """Read-only tools have only read permission"""
        return [Permission.READ_ONLY]


class WriteEnabledTool(BaseTool, FrameworkWriteEnabledTool):
    """
    Enhanced write-enabled tool base class
    
    Inherits all BaseTool functionality and allows write operations
    with additional validation and security checks
    """
    
    def __init__(self, settings: Optional[Settings] = None, storage=None):
        super().__init__(settings, storage)
    
    @property
    def permissions(self) -> List[Permission]:
        """Write-enabled tools have read and write permissions"""
        return [Permission.READ_ONLY, Permission.WRITE]
    
    async def _validate_write_permission(self, context: ToolExecutionContext) -> None:
        """
        Validate that the user has write permissions
        
        Args:
            context: Execution context
            
        Raises:
            ValueError: If write permission is not available
        """
        if not context.auth_context:
            raise ValueError("Authentication required for write operations")
        
        # Additional write permission validation could be added here
        # For example, checking user subscription level, rate limits, etc.
        
        logger.debug(f"Write permission validated for user {context.auth_context.user_id_hash[:8]}...")


class ServiceBase(ABC):
    """
    Base class for services with dependency injection and lifecycle management
    """
    
    def __init__(self, settings: Settings, **dependencies):
        """
        Initialize service with settings and dependencies
        
        Args:
            settings: Application settings
            **dependencies: Injected dependencies
        """
        self.settings = settings
        self.dependencies = dependencies
        self._initialized = False
        self._logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    async def initialize(self) -> None:
        """Initialize service - override in subclasses for custom initialization"""
        self._initialized = True
        self._logger.info(f"{self.__class__.__name__} initialized")
    
    async def cleanup(self) -> None:
        """Cleanup service resources - override in subclasses"""
        self._initialized = False
        self._logger.info(f"{self.__class__.__name__} cleaned up")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check service health
        
        Returns:
            Health status information
        """
        return {
            "service": self.__class__.__name__,
            "initialized": self._initialized,
            "status": "healthy" if self._initialized else "not_initialized"
        }
    
    def require_dependency(self, name: str, expected_type: Type = None):
        """
        Get required dependency with type validation
        
        Args:
            name: Dependency name
            expected_type: Expected dependency type
            
        Returns:
            The dependency instance
            
        Raises:
            ValueError: If dependency is missing or wrong type
        """
        if name not in self.dependencies:
            raise ValueError(f"Required dependency '{name}' not provided to {self.__class__.__name__}")
        
        dependency = self.dependencies[name]
        
        if expected_type and not isinstance(dependency, expected_type):
            raise ValueError(f"Dependency '{name}' must be of type {expected_type.__name__}")
        
        return dependency


class ConfigurableService(ServiceBase):
    """
    Service base class with configuration validation and management
    """
    
    @property
    @abstractmethod
    def required_config_keys(self) -> List[str]:
        """List of required configuration keys"""
        pass
    
    async def initialize(self) -> None:
        """Initialize with configuration validation"""
        await self._validate_configuration()
        await super().initialize()
    
    async def _validate_configuration(self) -> None:
        """
        Validate that all required configuration is present
        
        Raises:
            ValueError: If required configuration is missing
        """
        missing_keys = []
        
        for key in self.required_config_keys:
            if not hasattr(self.settings, key) or getattr(self.settings, key) is None:
                missing_keys.append(key)
        
        if missing_keys:
            raise ValueError(f"Missing required configuration keys: {', '.join(missing_keys)}")