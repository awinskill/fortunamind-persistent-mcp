"""
Pytest Configuration and Fixtures

Provides common test fixtures and configuration for the FortunaMind
Persistent MCP Server test suite.
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import Settings, Environment, SecurityProfile, LogLevel
from core.container import DIContainer
from core.security import SecurityScanner
from persistent_mcp.storage import MockStorageBackend
from persistent_mcp.auth import SubscriberAuth


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with safe defaults"""
    return Settings(
        # Database settings (mock)
        database_url="postgresql://test:test@test:5432/test",
        supabase_url="https://test.supabase.co",
        supabase_anon_key="test-anon-key",
        supabase_service_role_key="test-service-role-key",
        
        # Server settings
        mcp_server_name="Test-MCP-Server",
        server_host="127.0.0.1",
        server_port=8888,
        server_mode="http",
        environment=Environment.DEVELOPMENT,
        
        # Security settings
        jwt_secret_key="test-secret-key-must-be-at-least-32-characters-long-for-validation",
        jwt_algorithm="HS256",
        security_profile=SecurityProfile.MODERATE,
        
        # Logging
        log_level=LogLevel.DEBUG,
        log_format="text",
        log_file_path=None,
        
        # Feature flags
        enable_trading_journal=True,
        enable_technical_indicators=True,
        enable_portfolio_integration=True,
        enable_pre_trade_analysis=True,
        enable_advanced_analytics=False,
        enable_predictive_insights=False,
        
        # Rate limiting
        api_rate_limit_per_minute=1000,
        max_journal_entry_length=10000,
        
        # Mock settings
        mock_subscription_check=True,
        mock_technical_data=True,
        
        # Performance
        db_pool_size=5,
        db_max_overflow=10,
        db_pool_timeout=10,
        http_timeout_seconds=10,
        http_retry_attempts=2,
        cache_default_ttl_seconds=60
    )


@pytest.fixture
async def test_container(test_settings: Settings) -> AsyncGenerator[DIContainer, None]:
    """Create and initialize a test DI container"""
    container = DIContainer(test_settings)
    await container.initialize()
    
    yield container
    
    # Cleanup
    await container.shutdown()


@pytest.fixture
async def mock_storage(test_settings: Settings) -> AsyncGenerator[MockStorageBackend, None]:
    """Create a mock storage backend for testing"""
    storage = MockStorageBackend(test_settings)
    await storage.initialize()
    
    yield storage
    
    # Cleanup if needed
    if hasattr(storage, 'cleanup'):
        await storage.cleanup()


@pytest.fixture
def mock_auth(test_settings: Settings) -> SubscriberAuth:
    """Create a mock authentication system"""
    auth = SubscriberAuth(test_settings)
    
    # Mock the verification methods for testing
    auth.verify_subscription = AsyncMock(return_value=True)
    auth.get_user_id_hash = Mock(return_value="test-user-hash-123")
    auth.health_check = AsyncMock(return_value={"status": "healthy"})
    
    return auth


@pytest.fixture
def security_scanner() -> SecurityScanner:
    """Create a security scanner for testing"""
    return SecurityScanner(sensitivity_level="HIGH")


@pytest.fixture
def sample_journal_entry() -> dict:
    """Sample trading journal entry for testing"""
    return {
        "symbol": "BTC",
        "action": "BUY",
        "amount": 0.1,
        "price": 45000.0,
        "timestamp": "2023-12-01T10:30:00Z",
        "reasoning": "Strong technical breakout above resistance",
        "emotional_state": "confident",
        "decision_quality": "good",
        "notes": "Waited for confirmation, good entry point",
        "tags": ["technical-analysis", "breakout"]
    }


@pytest.fixture
def sample_technical_indicator() -> dict:
    """Sample technical indicator data for testing"""
    return {
        "symbol": "BTC",
        "indicator_type": "RSI",
        "timeframe": "1d",
        "value": 65.5,
        "signal": "neutral",
        "confidence": "medium",
        "timestamp": "2023-12-01T10:00:00Z",
        "metadata": {
            "period": 14,
            "data_points": 100
        }
    }


@pytest.fixture
def sample_portfolio_data() -> dict:
    """Sample portfolio data for testing"""
    return {
        "total_value": 10000.0,
        "cash_balance": 5000.0,
        "holdings": [
            {
                "symbol": "BTC",
                "quantity": 0.1,
                "current_price": 45000.0,
                "market_value": 4500.0,
                "cost_basis": 40000.0,
                "unrealized_pnl": 500.0
            },
            {
                "symbol": "ETH", 
                "quantity": 2.0,
                "current_price": 2500.0,
                "market_value": 5000.0,
                "cost_basis": 2000.0,
                "unrealized_pnl": 1000.0
            }
        ],
        "performance": {
            "total_return": 1500.0,
            "total_return_pct": 17.65,
            "daily_pnl": 250.0,
            "daily_pnl_pct": 2.56
        }
    }


@pytest.fixture
def mock_api_response() -> dict:
    """Mock API response for external service calls"""
    return {
        "status": "success",
        "data": {
            "symbol": "BTC-USD",
            "price": "45000.00",
            "volume": "1000000",
            "timestamp": "2023-12-01T10:00:00Z"
        },
        "metadata": {
            "source": "test",
            "latency_ms": 50
        }
    }


# Test markers for different test categories
pytest_markers = [
    "unit: Unit tests",
    "integration: Integration tests", 
    "e2e: End-to-end tests",
    "security: Security-related tests",
    "performance: Performance tests",
    "slow: Tests that take more than 5 seconds"
]


# Mock external dependencies
class MockExternalAPI:
    """Mock external API for testing"""
    
    def __init__(self):
        self.call_count = 0
        
    async def get_price(self, symbol: str) -> dict:
        self.call_count += 1
        return {
            "symbol": symbol,
            "price": 45000.0 if "BTC" in symbol else 2500.0,
            "timestamp": "2023-12-01T10:00:00Z"
        }
    
    async def get_portfolio(self, api_key: str) -> dict:
        self.call_count += 1 
        return {
            "total_value": 10000.0,
            "holdings": []
        }


@pytest.fixture
def mock_external_api() -> MockExternalAPI:
    """Mock external API client"""
    return MockExternalAPI()


# Error simulation fixtures
@pytest.fixture
def failing_storage(test_settings: Settings) -> MockStorageBackend:
    """Storage backend that simulates failures"""
    storage = MockStorageBackend(test_settings)
    
    # Override methods to simulate failures
    original_store = storage.store_journal_entry
    
    async def failing_store(*args, **kwargs):
        raise ConnectionError("Simulated storage failure")
    
    storage.store_journal_entry = failing_store
    return storage


# Async test utilities
class AsyncContextManagerMock:
    """Mock async context manager for testing"""
    
    def __init__(self, return_value=None):
        self.return_value = return_value
        
    async def __aenter__(self):
        return self.return_value
        
    async def __aexit__(self, *args):
        pass


@pytest.fixture
def async_context_mock():
    """Factory for creating async context manager mocks"""
    return AsyncContextManagerMock


# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Automatically clean up test data after each test"""
    yield
    
    # Clean up any temporary files, reset global state, etc.
    # This runs after each test
    
    # Clear any environment variables set during tests
    test_env_vars = [key for key in os.environ.keys() if key.startswith("TEST_")]
    for var in test_env_vars:
        del os.environ[var]