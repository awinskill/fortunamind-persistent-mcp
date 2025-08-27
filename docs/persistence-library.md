# FortunaMind Persistence Library

A comprehensive, privacy-first persistence library for FortunaMind projects that provides user identity management, subscription validation, rate limiting, and secure data storage.

## 🎯 Overview

The FortunaMind Persistence Library (`fortunamind_persistence`) is designed to provide:

- **Privacy-First Identity**: Email-based user identification without storing sensitive account data
- **Subscription Management**: Validation and tier-based access control with caching
- **Rate Limiting**: Sliding window rate limiting with tier-based quotas
- **Secure Storage**: Supabase integration with Row Level Security (RLS)
- **Framework Integration**: Seamless integration with FortunaMind Tool Framework

## 🏗️ Architecture

```
fortunamind_persistence/
├── identity/           # User identity management
├── subscription/       # Subscription validation and tiers
├── storage/           # Storage backends (Supabase, Mock)
├── rate_limiting/     # Rate limiting with sliding windows
└── adapters/          # Framework integration adapters
```

## 📚 Core Components

### EmailIdentity

Handles email-based user identification with privacy-preserving hashing.

```python
from fortunamind_persistence.identity import EmailIdentity

identity = EmailIdentity()

# Generate consistent user ID from email
user_id = identity.generate_user_id("user@example.com")
# Returns: SHA-256 hash (64 hex characters)

# Gmail normalization (removes dots and plus addressing)
normalized = identity.normalize_email("test.user+label@gmail.com")
# Returns: "testuser@gmail.com"
```

**Key Features:**
- SHA-256 hashing for privacy
- Gmail normalization (dots and plus addressing)
- Case-insensitive email handling
- Consistent ID generation across sessions

### SubscriptionValidator

Validates subscription keys with caching for performance.

```python
from fortunamind_persistence.subscription import (
    SubscriptionValidator,
    SubscriptionTier
)

validator = SubscriptionValidator()
await validator.initialize()

# Validate subscription
result = await validator.validate("user@example.com", "fm_sub_abc123")

if result.is_valid:
    print(f"User tier: {result.tier}")  # SubscriptionTier.PREMIUM
    print(f"Expires: {result.subscription_data.expires_at}")
```

**Subscription Key Format:**
- Pattern: `fm_sub_<identifier>`
- Example: `fm_sub_abc123def456`
- Similar to API key format for consistency

**Tiers:**
- `FREE`: Basic access with limited quotas
- `BASIC`: Enhanced access with moderate quotas
- `PREMIUM`: Advanced access with high quotas
- `ENTERPRISE`: Full access with unlimited quotas

### RateLimiter

Sliding window rate limiting with tier-based quotas.

```python
from fortunamind_persistence.rate_limiting import RateLimiter
from fortunamind_persistence.subscription import SubscriptionTier

limiter = RateLimiter()

# Check rate limit
result = await limiter.check_and_record("user_id", SubscriptionTier.PREMIUM)

if result.allowed:
    print("Request allowed")
else:
    print(f"Rate limited. Retry after: {result.retry_after}")
```

**Time Windows:**
- `hour`: Hourly quotas
- `day`: Daily quotas  
- `month`: Monthly quotas

**Tier Limits (examples):**
```python
# FREE tier
api_calls_per_hour: 100
api_calls_per_day: 1000
api_calls_per_month: 10000

# PREMIUM tier
api_calls_per_hour: 1000
api_calls_per_day: 10000
api_calls_per_month: 100000

# ENTERPRISE tier
api_calls_per_hour: -1  # Unlimited
```

### Storage Backends

#### SupabaseStorage

Production-ready storage with PostgreSQL and Row Level Security.

```python
from fortunamind_persistence.storage import SupabaseStorage

# Initialize (reads from environment variables)
storage = SupabaseStorage()
await storage.initialize()

# Store journal entry
entry_id = await storage.store_journal_entry(
    user_id_hash="user123...",
    entry="Trading journal entry",
    metadata={"timestamp": "2023-12-01T10:00:00Z"}
)

# Retrieve entries
entries = await storage.get_journal_entries(
    user_id_hash="user123...",
    limit=10
)
```

**Environment Variables:**
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
DATABASE_URL=postgresql://postgres:password@host:5432/postgres?sslmode=require
```

#### MockStorage

Development and testing storage backend.

```python
from fortunamind_persistence.storage import MockStorage

storage = MockStorage()
await storage.initialize()

# Same API as SupabaseStorage
# Data stored in memory, reset on restart
```

### Framework Adapter

Integrates with FortunaMind Tool Framework.

```python
from fortunamind_persistence.adapters import FrameworkPersistenceAdapter
from fortunamind_persistence.subscription import SubscriptionValidator
from fortunamind_persistence.storage import SupabaseStorage
from fortunamind_persistence.rate_limiting import RateLimiter

# Initialize components
storage = SupabaseStorage()
validator = SubscriptionValidator()
rate_limiter = RateLimiter()

# Create adapter
adapter = FrameworkPersistenceAdapter(
    subscription_validator=validator,
    storage_backend=storage,
    rate_limiter=rate_limiter
)

# Create auth context from credentials
auth_context = await adapter.create_auth_context_from_credentials(
    email="user@example.com",
    subscription_key="fm_sub_abc123",
    coinbase_credentials={
        'api_key': 'organizations/org/apiKeys/key',
        'api_secret': 'pem-private-key'
    }
)

# Validate and store journal entry
result = await adapter.store_journal_entry_with_validation(
    email="user@example.com",
    subscription_key="fm_sub_abc123",
    entry="Trading journal entry",
    metadata={"timestamp": "2023-12-01T10:00:00Z"}
)
```

## 🚀 Quick Start

### 1. Installation

```python
# Add to your project's requirements.txt
supabase>=2.0.0
psycopg2-binary>=2.9.0
asyncpg>=0.28.0
pydantic>=2.0.0
```

### 2. Environment Setup

Create `.env` file:
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
DATABASE_URL=postgresql://postgres:password@host:5432/postgres?sslmode=require

# Optional: Redis for caching
REDIS_URL=redis://localhost:6379/0
```

### 3. Database Migration

```bash
# Run Alembic migrations
alembic upgrade head
```

### 4. Basic Usage

```python
import asyncio
import os
from fortunamind_persistence.adapters import FrameworkPersistenceAdapter

async def main():
    # Create adapter with default components
    adapter = FrameworkPersistenceAdapter()
    
    # Store journal entry
    result = await adapter.store_journal_entry_with_validation(
        email="trader@example.com",
        subscription_key="fm_sub_premium123",
        entry="Bought 0.1 BTC at $45,000. Strong technical breakout.",
        metadata={
            "symbol": "BTC",
            "action": "BUY",
            "amount": 0.1,
            "price": 45000.0
        }
    )
    
    if result['success']:
        print(f"Entry stored with ID: {result['entry_id']}")
    else:
        print(f"Error: {result['error']}")
    
    # Retrieve entries
    entries = await adapter.get_journal_entries_with_validation(
        email="trader@example.com",
        subscription_key="fm_sub_premium123",
        limit=10
    )
    
    print(f"Retrieved {entries['count']} entries")
    for entry in entries['entries']:
        print(f"- {entry['entry']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔒 Security Features

### Privacy-First Design

- **No Account Data Storage**: Never stores Coinbase account IDs or sensitive information
- **Email-Based Identity**: Uses normalized email addresses for user identification
- **Hashed User IDs**: SHA-256 hashing ensures privacy while maintaining consistency
- **API Key Rotation Resilience**: User identity survives API key changes

### Database Security

- **Row Level Security (RLS)**: Supabase RLS ensures user data isolation
- **Encrypted at Rest**: Supabase provides encryption for stored data
- **SSL/TLS**: All database connections use SSL encryption
- **Environment Variables**: Secrets stored securely, never in code

### Rate Limiting

- **Tier-Based Quotas**: Different limits based on subscription tier
- **Sliding Windows**: Prevents burst attacks while allowing normal usage
- **Graceful Degradation**: Informative error messages with retry times

## 📊 Data Models

### User Subscriptions

```sql
CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    subscription_key VARCHAR(255),
    tier VARCHAR(50) NOT NULL DEFAULT 'free',
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Journal Entries

```sql
CREATE TABLE journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id_hash VARCHAR(64) NOT NULL,
    entry TEXT NOT NULL,
    metadata JSONB,
    entry_type VARCHAR(50) DEFAULT 'general',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### User Preferences

```sql
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id_hash VARCHAR(64) NOT NULL,
    preference_key VARCHAR(255) NOT NULL,
    preference_value JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## 🧪 Testing

### Unit Tests

```bash
# Run unit tests
pytest tests/unit/ -v

# Test specific component
pytest tests/unit/test_email_identity.py -v
```

### Integration Tests

```bash
# Run integration tests
pytest tests/integration/ -v

# Test framework adapter
pytest tests/integration/test_framework_adapter.py -v
```

### Mock vs Production Testing

```python
# Use MockStorage for fast unit tests
from fortunamind_persistence.storage import MockStorage

storage = MockStorage()
await storage.initialize()

# Use SupabaseStorage for integration tests
from fortunamind_persistence.storage import SupabaseStorage

storage = SupabaseStorage()  # Reads from environment
await storage.initialize()
```

## 🔧 Advanced Configuration

### Custom Tier Definitions

```python
from fortunamind_persistence.subscription.tiers import (
    TierDefinitions,
    TierLimits
)

# Define custom tier
custom_limits = TierLimits(
    api_calls_per_hour=500,
    api_calls_per_day=5000,
    api_calls_per_month=50000,
    storage_mb=100,
    features=["journal_persistence", "analytics"]
)

TierDefinitions.add_tier("CUSTOM", custom_limits)
```

### Custom Storage Backend

```python
from fortunamind_persistence.storage.base import StorageInterface

class CustomStorage(StorageInterface):
    """Custom storage implementation"""
    
    async def initialize(self) -> None:
        # Initialize your storage
        pass
    
    async def store_journal_entry(
        self, 
        user_id_hash: str, 
        entry: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        # Store entry, return ID
        pass
    
    # Implement other required methods...
```

### Caching Configuration

```python
from fortunamind_persistence.subscription.cache import SimpleCache

# Custom cache with different TTL
custom_cache = SimpleCache(default_ttl_minutes=10)

validator = SubscriptionValidator(cache=custom_cache)
```

## 📈 Performance Optimization

### Connection Pooling

```python
# SupabaseStorage automatically uses connection pooling
# Configure pool size via environment:
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

### Caching Strategy

- **Subscription Validation**: 5-minute cache TTL
- **Rate Limiting**: In-memory sliding window counters
- **User Preferences**: Consider Redis for high-traffic scenarios

### Batch Operations

```python
# Store multiple entries efficiently
entries = [
    {"entry": "Entry 1", "metadata": {"type": "trade"}},
    {"entry": "Entry 2", "metadata": {"type": "analysis"}},
]

entry_ids = await storage.batch_store_journal_entries(user_id_hash, entries)
```

## 🚨 Error Handling

### Common Error Types

```python
from fortunamind_persistence.exceptions import (
    ValidationError,
    StorageError,
    RateLimitError,
    AuthenticationError
)

try:
    result = await adapter.store_journal_entry_with_validation(
        email="user@example.com",
        subscription_key="invalid_key",
        entry="Test entry"
    )
except ValidationError as e:
    print(f"Validation failed: {e}")
except RateLimitError as e:
    print(f"Rate limited: {e.retry_after}")
except StorageError as e:
    print(f"Storage error: {e}")
```

### Error Response Format

```python
{
    "success": false,
    "error": "Invalid subscription key format",
    "error_type": "validation_error",
    "timestamp": "2023-12-01T10:00:00Z"
}
```

## 🔄 Migration Guide

### From API Key Auth to Email+Subscription Auth

**Before:**
```python
# Old authentication
auth_context = AuthContext(
    api_key="organizations/org/apiKeys/key",
    api_secret="pem-private-key",
    user_id_hash="generated-from-api-key"
)
```

**After:**
```python
# New authentication
auth_context = await adapter.create_auth_context_from_credentials(
    email="user@example.com",
    subscription_key="fm_sub_abc123",
    coinbase_credentials={
        'api_key': 'organizations/org/apiKeys/key',
        'api_secret': 'pem-private-key'
    }
)
```

**Benefits:**
- ✅ Survives API key rotation
- ✅ Privacy-preserving (email-based identity)
- ✅ Cross-exchange compatibility
- ✅ Subscription-based access control

## 🤝 Integration Examples

### With FortunaMind Tool Framework

```python
from fortunamind_persistence.adapters import FrameworkPersistenceAdapter

# Create enhanced portfolio tool with persistence
class PersistentPortfolioTool(UnifiedPortfolioTool):
    def __init__(self, persistence_adapter: FrameworkPersistenceAdapter):
        super().__init__()
        self.persistence = persistence_adapter
    
    async def _execute_impl(self, auth_context, **parameters):
        # Get portfolio data
        result = await super()._execute_impl(auth_context, **parameters)
        
        # Store snapshot for historical analysis
        email = self.persistence.extract_email_from_auth_context(auth_context)
        if email:
            await self.persistence.store_portfolio_snapshot(email, result)
        
        return result
```

### With FastAPI

```python
from fastapi import FastAPI, Depends, HTTPException
from fortunamind_persistence.adapters import FrameworkPersistenceAdapter

app = FastAPI()
adapter = FrameworkPersistenceAdapter()

@app.post("/journal/entries")
async def create_journal_entry(
    email: str,
    subscription_key: str,
    entry: str,
    metadata: dict = None
):
    try:
        result = await adapter.store_journal_entry_with_validation(
            email=email,
            subscription_key=subscription_key,
            entry=entry,
            metadata=metadata
        )
        
        if result['success']:
            return {"entry_id": result['entry_id']}
        else:
            raise HTTPException(status_code=400, detail=result['error'])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## 📋 API Reference

### FrameworkPersistenceAdapter

The main interface for all persistence operations.

#### Methods

##### `create_auth_context_from_credentials()`
```python
async def create_auth_context_from_credentials(
    self,
    email: str,
    subscription_key: str,
    coinbase_credentials: Optional[Dict[str, str]] = None
) -> AuthContext
```

Creates an authenticated context from user credentials.

**Parameters:**
- `email`: User email address
- `subscription_key`: FortunaMind subscription key (fm_sub_xxx)
- `coinbase_credentials`: Optional Coinbase API credentials

**Returns:** `AuthContext` object for use with tools

**Raises:** `ValidationError` if credentials are invalid

##### `validate_and_get_user_context()`
```python
async def validate_and_get_user_context(
    self,
    email: str,
    subscription_key: str
) -> Dict[str, Any]
```

Validates subscription and returns user context.

**Parameters:**
- `email`: User email address
- `subscription_key`: FortunaMind subscription key

**Returns:** Dictionary with user context including tier, user_id, subscription_data

##### `store_journal_entry_with_validation()`
```python
async def store_journal_entry_with_validation(
    self,
    email: str,
    subscription_key: str,
    entry: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

Stores a journal entry after validation and rate limiting.

**Parameters:**
- `email`: User email address
- `subscription_key`: FortunaMind subscription key
- `entry`: Journal entry text
- `metadata`: Optional metadata dictionary

**Returns:** Success status and entry_id or error details

##### `get_journal_entries_with_validation()`
```python
async def get_journal_entries_with_validation(
    self,
    email: str,
    subscription_key: str,
    limit: int = 10,
    offset: int = 0,
    entry_type: Optional[str] = None
) -> Dict[str, Any]
```

Retrieves journal entries after validation.

**Parameters:**
- `email`: User email address
- `subscription_key`: FortunaMind subscription key
- `limit`: Maximum entries to return (default: 10)
- `offset`: Number of entries to skip (default: 0)
- `entry_type`: Optional filter by entry type

**Returns:** Success status, entries list, and count

##### `get_user_stats()`
```python
async def get_user_stats(
    self,
    email: str,
    subscription_key: str
) -> Dict[str, Any]
```

Gets comprehensive user statistics.

**Returns:** Dictionary with user_id_hash, tier, storage usage, rate limits

##### `health_check()`
```python
async def health_check(self) -> Dict[str, Any]
```

Performs health check of all components.

**Returns:** Health status of storage, validator, rate limiter

## 🔍 Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```
ERROR: could not connect to server
```

**Solutions:**
- Check `DATABASE_URL` environment variable
- Verify Supabase project is running
- Ensure SSL mode is enabled (`?sslmode=require`)
- Check network connectivity

#### 2. Subscription Validation Failures
```
ValidationError: Invalid subscription key format
```

**Solutions:**
- Verify key starts with `fm_sub_`
- Check email format is valid
- Ensure subscription is active in Supabase

#### 3. Rate Limiting Issues
```
RateLimitError: Rate limit exceeded
```

**Solutions:**
- Check tier limits configuration
- Wait for reset time (included in error)
- Verify tier assignment is correct
- Consider upgrading subscription tier

#### 4. RLS Policy Errors
```
ERROR: new row violates row-level security policy
```

**Solutions:**
- Verify RLS policies are created
- Check user context is properly set
- Ensure Supabase anon key has correct permissions

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging
adapter = FrameworkPersistenceAdapter(debug=True)
```

### Health Check Script

```python
#!/usr/bin/env python3
"""Health check script for persistence library."""

import asyncio
from fortunamind_persistence.adapters import FrameworkPersistenceAdapter

async def health_check():
    adapter = FrameworkPersistenceAdapter()
    
    try:
        health = await adapter.health_check()
        print(f"Overall health: {health['overall']}")
        
        for component, status in health['components'].items():
            print(f"{component}: {status}")
            
    except Exception as e:
        print(f"Health check failed: {e}")

if __name__ == "__main__":
    asyncio.run(health_check())
```

---

## 📞 Support

For issues and questions:

1. Check troubleshooting section above
2. Review test cases in `tests/` directory  
3. Run health check script
4. Enable debug logging for detailed error information

The persistence library is designed to be robust and provide clear error messages to help diagnose issues quickly.