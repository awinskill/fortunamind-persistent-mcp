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

# Import from new persistence library
from fortunamind_persistence.storage.mock_backend import MockStorage
from fortunamind_persistence.subscription.validator import SubscriptionValidator
from fortunamind_persistence.identity.email_identity import EmailIdentity
from fortunamind_persistence.rate_limiting.limiter import RateLimiter
from fortunamind_persistence.adapters.framework_adapter import FrameworkPersistenceAdapter


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_env_vars():
    """Set up test environment variables"""
    test_vars = {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_ANON_KEY': 'test-anon-key',
        'DATABASE_URL': 'postgresql://test:test@test:5432/test'
    }
    
    # Set test environment variables
    for key, value in test_vars.items():
        os.environ[key] = value
    
    yield test_vars
    
    # Cleanup
    for key in test_vars:
        os.environ.pop(key, None)


@pytest.fixture
async def mock_storage(test_env_vars) -> AsyncGenerator[MockStorage, None]:
    """Create a mock storage backend for testing"""
    storage = MockStorage()
    await storage.initialize()
    
    yield storage
    
    # Cleanup if needed
    if hasattr(storage, 'cleanup'):
        await storage.cleanup()


@pytest.fixture
async def subscription_validator(test_env_vars) -> AsyncGenerator[SubscriptionValidator, None]:
    """Create a subscription validator for testing"""
    validator = SubscriptionValidator()
    await validator.initialize()
    
    yield validator
    
    await validator.cleanup()


@pytest.fixture
def email_identity() -> EmailIdentity:
    """Create an email identity handler for testing"""
    return EmailIdentity()


@pytest.fixture
def rate_limiter() -> RateLimiter:
    """Create a rate limiter for testing"""
    return RateLimiter()


@pytest.fixture
async def framework_adapter(mock_storage, subscription_validator, rate_limiter) -> FrameworkPersistenceAdapter:
    """Create a complete framework adapter for testing"""
    return FrameworkPersistenceAdapter(
        subscription_validator=subscription_validator,
        storage_backend=mock_storage,
        rate_limiter=rate_limiter
    )


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