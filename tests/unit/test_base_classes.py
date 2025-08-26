"""
Unit Tests for Base Classes

Tests the core base classes for tools, services, and storage components.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from core.base import (
    BaseTool, ReadOnlyTool, WriteEnabledTool, 
    ServiceBase, ConfigurableService, 
    ToolExecutionContext, ValidationError,
    ToolCategory, Permission
)
from core.storage_template import InMemoryStorageTemplate
from persistent_mcp.storage.interface import StorageRecord, DataType, QueryFilter
from config import Settings


class MockTool(ReadOnlyTool):
    """Mock tool for testing base class functionality"""
    
    @property
    def schema(self):
        from core.base import ToolSchema
        return ToolSchema(
            name="mock_tool",
            description="Mock tool for testing",
            category=ToolCategory.DIAGNOSTIC.value,
            permissions=[Permission.READ_ONLY.value],
            parameters={
                "type": "object",
                "properties": {
                    "test_param": {
                        "type": "string",
                        "description": "Test parameter"
                    },
                    "required_param": {
                        "type": "string",
                        "description": "Required test parameter"
                    }
                },
                "required": ["required_param"]
            },
            returns={"type": "object"}
        )
    
    async def _execute_impl(self, context: ToolExecutionContext) -> dict:
        """Mock implementation"""
        return {
            "message": "Mock tool executed successfully",
            "parameters": context.parameters,
            "execution_id": context.execution_id
        }


class MockWriteTool(WriteEnabledTool):
    """Mock write tool for testing write permissions"""
    
    @property
    def schema(self):
        from core.base import ToolSchema
        return ToolSchema(
            name="mock_write_tool",
            description="Mock write tool for testing",
            category=ToolCategory.PORTFOLIO_MANAGEMENT.value,
            permissions=[Permission.READ_ONLY.value, Permission.WRITE.value],
            parameters={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Data to write"
                    }
                },
                "required": ["data"]
            },
            returns={"type": "object"}
        )
    
    async def _execute_impl(self, context: ToolExecutionContext) -> dict:
        """Mock write implementation"""
        await self._validate_write_permission(context)
        
        return {
            "message": "Mock write tool executed successfully",
            "data_written": context.parameters.get("data")
        }


class MockService(ServiceBase):
    """Mock service for testing service base functionality"""
    
    async def initialize(self) -> None:
        await super().initialize()
        # Mock initialization logic
        self.mock_initialized = True
    
    async def cleanup(self) -> None:
        await super().cleanup()
        # Mock cleanup logic
        self.mock_initialized = False


class MockConfigurableService(ConfigurableService):
    """Mock configurable service for testing configuration validation"""
    
    @property
    def required_config_keys(self) -> list:
        return ["database_url", "api_key"]
    
    async def initialize(self) -> None:
        await super().initialize()
        self.service_ready = True


class TestBaseTool:
    """Test suite for BaseTool functionality"""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing"""
        settings = Mock()
        settings.security_profile = Mock()
        settings.security_profile.value = "HIGH"
        return settings
    
    @pytest.fixture
    def mock_tool(self, mock_settings):
        """Create mock tool instance"""
        return MockTool(settings=mock_settings)
    
    @pytest.fixture
    def mock_auth_context(self):
        """Create mock auth context"""
        from core.base import AuthContext
        return AuthContext(
            api_key="test-api-key",
            api_secret="test-api-secret",
            user_id_hash="test-user-123",
            timestamp="2023-12-01T10:00:00Z"
        )
    
    async def test_tool_initialization(self, mock_tool):
        """Test tool initialization"""
        assert mock_tool.settings is not None
        assert mock_tool._security_scanner is not None
        assert isinstance(mock_tool._execution_metrics, dict)
    
    async def test_successful_execution(self, mock_tool, mock_auth_context):
        """Test successful tool execution"""
        result = await mock_tool.execute(
            mock_auth_context,
            required_param="test_value",
            test_param="optional_value"
        )
        
        assert result.success is True
        assert result.data is not None
        assert result.execution_time is not None
        assert "mock tool executed successfully" in result.data["message"].lower()
        assert result.data["parameters"]["required_param"] == "test_value"
    
    async def test_parameter_validation_failure(self, mock_tool, mock_auth_context):
        """Test parameter validation failure"""
        result = await mock_tool.execute(
            mock_auth_context,
            test_param="optional_value"  # Missing required_param
        )
        
        assert result.success is False
        assert "parameter validation failed" in result.error_message.lower()
        assert result.metadata["validation_errors"]
        
        validation_error = result.metadata["validation_errors"][0]
        assert validation_error["field"] == "required_param"
        assert validation_error["code"] == "MISSING_REQUIRED_FIELD"
    
    async def test_security_scanning(self, mock_tool, mock_auth_context):
        """Test security scanning functionality"""
        result = await mock_tool.execute(
            mock_auth_context,
            required_param="organizations/abc-123/apiKeys/def-456",  # Contains API key pattern
            test_param="normal_value"
        )
        
        # Should detect the API key pattern and fail
        assert result.success is False
        assert "security scan detected sensitive information" in result.error_message.lower()
        assert "security_threats" in result.metadata
    
    async def test_execution_metrics(self, mock_tool, mock_auth_context):
        """Test execution metrics collection"""
        # Execute tool multiple times
        for i in range(3):
            await mock_tool.execute(
                mock_auth_context,
                required_param=f"test_value_{i}"
            )
        
        metrics = mock_tool.get_execution_metrics()
        
        assert metrics["total_executions"] == 3
        assert metrics["successful_executions"] == 3
        assert metrics["success_rate"] == 1.0
        assert metrics["average_execution_time"] > 0
        assert "last_execution" in metrics
    
    async def test_auth_requirement_helper(self, mock_tool):
        """Test authentication requirement helper"""
        # Should raise ValueError when no auth provided
        with pytest.raises(ValueError, match="Authentication is required"):
            mock_tool._require_auth(None)
        
        # Should raise ValueError when no user_id_hash
        from core.base import AuthContext
        invalid_auth = AuthContext(
            api_key="test", api_secret="test", user_id_hash="", timestamp="test"
        )
        
        with pytest.raises(ValueError, match="Valid user authentication is required"):
            mock_tool._require_auth(invalid_auth)
    
    async def test_api_credentials_extraction(self, mock_tool, mock_settings):
        """Test API credentials extraction"""
        from core.base import AuthContext
        
        # Test extraction from parameters
        auth_context = AuthContext(
            api_key="", api_secret="", user_id_hash="test", timestamp="test"
        )
        
        parameters = {
            "api_key": "param-key",
            "api_secret": "param-secret"
        }
        
        api_key, api_secret = mock_tool._extract_api_credentials(parameters, auth_context)
        assert api_key == "param-key"
        assert api_secret == "param-secret"
        
        # Test missing credentials
        with pytest.raises(ValueError, match="API credentials are required"):
            mock_tool._extract_api_credentials({}, None)
    
    async def test_educational_content_generation(self, mock_tool):
        """Test educational content generation"""
        content = mock_tool._generate_educational_content("crypto_basics")
        
        assert "title" in content
        assert "content" in content
        assert "cryptocurrency" in content["content"].lower()
        
        # Test default content
        default_content = mock_tool._generate_educational_content("unknown_type")
        assert "investment guidance" in default_content["title"].lower()


class TestWriteEnabledTool:
    """Test suite for WriteEnabledTool functionality"""
    
    @pytest.fixture
    def mock_write_tool(self):
        """Create mock write tool instance"""
        return MockWriteTool()
    
    @pytest.fixture
    def mock_auth_context(self):
        """Create mock auth context"""
        from core.base import AuthContext
        return AuthContext(
            api_key="test-api-key",
            api_secret="test-api-secret", 
            user_id_hash="test-user-123",
            timestamp="2023-12-01T10:00:00Z"
        )
    
    async def test_write_permission_validation(self, mock_write_tool, mock_auth_context):
        """Test write permission validation"""
        result = await mock_write_tool.execute(
            mock_auth_context,
            data="test data to write"
        )
        
        assert result.success is True
        assert result.data["data_written"] == "test data to write"
    
    async def test_write_permission_failure_no_auth(self, mock_write_tool):
        """Test write permission failure without auth"""
        result = await mock_write_tool.execute(
            None,
            data="test data"
        )
        
        assert result.success is False
        assert "authentication required" in result.error_message.lower()
    
    async def test_permissions_property(self, mock_write_tool):
        """Test permissions property"""
        permissions = mock_write_tool.permissions
        assert Permission.READ_ONLY in permissions
        assert Permission.WRITE in permissions


class TestServiceBase:
    """Test suite for ServiceBase functionality"""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings"""
        return Mock(spec=Settings)
    
    @pytest.fixture
    def mock_service(self, mock_settings):
        """Create mock service instance"""
        return MockService(mock_settings, dependency1="test_dep")
    
    async def test_service_initialization(self, mock_service):
        """Test service initialization"""
        assert not mock_service._initialized
        
        await mock_service.initialize()
        
        assert mock_service._initialized
        assert mock_service.mock_initialized
    
    async def test_service_cleanup(self, mock_service):
        """Test service cleanup"""
        await mock_service.initialize()
        assert mock_service._initialized
        
        await mock_service.cleanup()
        
        assert not mock_service._initialized
        assert not mock_service.mock_initialized
    
    async def test_health_check(self, mock_service):
        """Test service health check"""
        health = await mock_service.health_check()
        
        assert health["service"] == "MockService"
        assert health["initialized"] is False
        assert health["status"] == "not_initialized"
        
        await mock_service.initialize()
        health = await mock_service.health_check()
        
        assert health["initialized"] is True
        assert health["status"] == "healthy"
    
    async def test_require_dependency(self, mock_service):
        """Test dependency requirement"""
        # Test successful dependency retrieval
        dep = mock_service.require_dependency("dependency1")
        assert dep == "test_dep"
        
        # Test missing dependency
        with pytest.raises(ValueError, match="Required dependency 'missing' not provided"):
            mock_service.require_dependency("missing")
        
        # Test type validation
        with pytest.raises(ValueError, match="must be of type"):
            mock_service.require_dependency("dependency1", expected_type=int)


class TestConfigurableService:
    """Test suite for ConfigurableService functionality"""
    
    @pytest.fixture
    def mock_settings_valid(self):
        """Create valid mock settings"""
        settings = Mock(spec=Settings)
        settings.database_url = "postgresql://test:test@localhost/test"
        settings.api_key = "test-api-key"
        return settings
    
    @pytest.fixture
    def mock_settings_invalid(self):
        """Create invalid mock settings (missing required keys)"""
        settings = Mock(spec=Settings)
        settings.database_url = None
        # api_key is missing entirely
        return settings
    
    async def test_valid_configuration(self, mock_settings_valid):
        """Test service with valid configuration"""
        service = MockConfigurableService(mock_settings_valid)
        
        await service.initialize()
        
        assert service._initialized
        assert service.service_ready
    
    async def test_invalid_configuration(self, mock_settings_invalid):
        """Test service with invalid configuration"""
        service = MockConfigurableService(mock_settings_invalid)
        
        with pytest.raises(ValueError, match="Missing required configuration keys"):
            await service.initialize()


class TestInMemoryStorageTemplate:
    """Test suite for InMemoryStorageTemplate functionality"""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings"""
        return Mock(spec=Settings)
    
    @pytest.fixture
    def storage(self, mock_settings):
        """Create storage instance"""
        return InMemoryStorageTemplate(mock_settings)
    
    @pytest.fixture
    def sample_record(self):
        """Create sample storage record"""
        return StorageRecord(
            user_id_hash="test-user-123",
            data_type=DataType.JOURNAL_ENTRY,
            data={
                "entry_type": "trade",
                "symbol": "BTC",
                "action": "buy",
                "reasoning": "Technical breakout pattern"
            },
            timestamp=datetime.now(),
            tags=["journal", "trade", "btc"]
        )
    
    async def test_storage_initialization(self, storage):
        """Test storage initialization"""
        assert not storage._initialized
        
        await storage.initialize()
        
        assert storage._initialized
    
    async def test_health_check(self, storage):
        """Test storage health check"""
        await storage.initialize()
        
        health = await storage.health_check()
        
        assert health["backend"] == "InMemoryStorageTemplate"
        assert health["initialized"] is True
        assert health["status"] == "healthy"
        assert "connectivity" in health["checks"]
        assert "permissions" in health["checks"]
        assert "storage_space" in health["checks"]
    
    async def test_record_storage_and_retrieval(self, storage, sample_record):
        """Test record storage and retrieval"""
        await storage.initialize()
        
        # Store record
        record_id = await storage.store_record(sample_record)
        
        assert record_id is not None
        assert isinstance(record_id, str)
        
        # Retrieve record
        retrieved_record = await storage.get_record(
            sample_record.user_id_hash, 
            record_id
        )
        
        assert retrieved_record is not None
        assert retrieved_record.user_id_hash == sample_record.user_id_hash
        assert retrieved_record.data_type == sample_record.data_type
        assert retrieved_record.data["symbol"] == "BTC"
    
    async def test_record_querying(self, storage, sample_record):
        """Test record querying with filters"""
        await storage.initialize()
        
        # Store multiple records
        record_id_1 = await storage.store_record(sample_record)
        
        # Create second record with different data
        sample_record_2 = StorageRecord(
            user_id_hash=sample_record.user_id_hash,
            data_type=DataType.TECHNICAL_INDICATOR,
            data={"symbol": "ETH", "indicator": "RSI", "value": 65.5},
            timestamp=datetime.now(),
            tags=["technical", "rsi", "eth"]
        )
        record_id_2 = await storage.store_record(sample_record_2)
        
        # Query by data type
        filter_criteria = QueryFilter(data_type=DataType.JOURNAL_ENTRY)
        results = await storage.query_records(
            sample_record.user_id_hash, 
            filter_criteria
        )
        
        assert len(results) == 1
        assert results[0].data_type == DataType.JOURNAL_ENTRY
        
        # Query by tags
        filter_criteria = QueryFilter(tags=["technical"])
        results = await storage.query_records(
            sample_record.user_id_hash,
            filter_criteria
        )
        
        assert len(results) == 1
        assert results[0].data_type == DataType.TECHNICAL_INDICATOR
    
    async def test_specialized_operations(self, storage):
        """Test specialized storage operations"""
        await storage.initialize()
        
        user_id = "test-user-456"
        
        # Test journal entry storage
        entry_id = await storage.store_journal_entry(
            user_id,
            {
                "entry_type": "analysis",
                "content": "Market analysis for BTC",
                "symbol": "BTC"
            }
        )
        
        assert entry_id is not None
        
        # Test journal entry retrieval
        entries = await storage.get_journal_entries(user_id)
        
        assert len(entries) == 1
        assert entries[0]["entry_type"] == "analysis"
        
        # Test portfolio snapshot
        snapshot_id = await storage.store_portfolio_snapshot(
            user_id,
            {
                "total_value": 10000.0,
                "holdings": [{"symbol": "BTC", "amount": 0.5}]
            }
        )
        
        assert snapshot_id is not None
        
        latest_portfolio = await storage.get_latest_portfolio(user_id)
        assert latest_portfolio is not None
        assert latest_portfolio["total_value"] == 10000.0
    
    async def test_user_preferences(self, storage):
        """Test user preference storage and retrieval"""
        await storage.initialize()
        
        user_id = "test-user-789"
        
        # Store preferences
        await storage.store_user_preference(user_id, "theme", "dark", "ui")
        await storage.store_user_preference(user_id, "alerts_enabled", True, "notifications")
        
        # Get specific preference
        theme = await storage.get_user_preference(user_id, "theme")
        assert theme == "dark"
        
        # Get preference with default
        timeout = await storage.get_user_preference(user_id, "timeout", 300)
        assert timeout == 300
        
        # Get all preferences
        all_prefs = await storage.get_user_preferences(user_id)
        assert len(all_prefs) == 2
        assert all_prefs["theme"] == "dark"
        assert all_prefs["alerts_enabled"] is True
        
        # Get preferences by category
        ui_prefs = await storage.get_user_preferences(user_id, "ui")
        assert len(ui_prefs) == 1
        assert ui_prefs["theme"] == "dark"
    
    async def test_storage_stats(self, storage, sample_record):
        """Test storage statistics"""
        await storage.initialize()
        
        # Add some data
        await storage.store_record(sample_record)
        await storage.store_journal_entry("user-123", {"test": "data"})
        
        stats = await storage.get_storage_stats(sample_record.user_id_hash)
        
        assert stats["user_id_hash"] == sample_record.user_id_hash
        assert stats["total_records"] >= 2
        assert "by_data_type" in stats
        assert "backend_metrics" in stats