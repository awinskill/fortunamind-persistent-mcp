# FortunaMind Persistent MCP Client Integration Examples

This directory contains comprehensive examples for integrating with the FortunaMind Persistent MCP Server.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install httpx asyncio
```

### 2. Set Environment Variables

```bash
export FORTUNAMIND_USER_EMAIL="your-email@domain.com"
export FORTUNAMIND_SUBSCRIPTION_KEY="fm_sub_your_key_here"
```

### 3. Run Examples

```bash
python examples/client_integration.py
```

## 📚 Integration Examples

### Basic Client Usage

```python
from examples.client_integration import FortunaMindPersistentClient

async def basic_example():
    async with FortunaMindPersistentClient() as client:
        # Validate subscription
        validation = await client.validate_subscription()
        
        # Store journal entry
        result = await client.store_journal_entry(
            entry="Market analysis for BTC",
            entry_type="analysis",
            tags=["BTC", "analysis"]
        )
        
        # Get entries
        entries = await client.get_journal_entries(limit=10)
```

### Trading Journal Manager

```python
from examples.client_integration import FortunaMindPersistentClient, TradingJournalManager

async def journal_example():
    async with FortunaMindPersistentClient() as client:
        journal = TradingJournalManager(client)
        
        # Log a trade
        await journal.log_trade_entry(
            symbol="BTC-USD",
            action="buy", 
            quantity=0.1,
            price=42500.00,
            reasoning="Strong technical setup"
        )
        
        # Log analysis
        await journal.log_analysis_entry(
            symbol="ETH-USD",
            analysis="Bullish momentum building",
            outlook="bullish",
            confidence=8
        )
```

## 🔧 Available Clients

### FortunaMindPersistentClient

Core client for server communication:

- `validate_subscription()` - Verify user credentials
- `store_journal_entry()` - Store journal entries
- `get_journal_entries()` - Retrieve entries with filtering
- `get_user_stats()` - Get usage statistics
- `health_check()` - Check server health

### TradingJournalManager

High-level trading journal operations:

- `log_trade_entry()` - Log trades with structured metadata
- `log_analysis_entry()` - Log market analysis
- `log_reflection()` - Log learning and reflections
- `get_trades_for_symbol()` - Get symbol-specific trades

## 🏗️ Integration Patterns

### 1. Portfolio Tracking Integration

```python
async def portfolio_sync(client, positions):
    """Sync portfolio positions to journal"""
    portfolio_entry = "Portfolio Update:\\n"
    for pos in positions:
        portfolio_entry += f"- {pos['symbol']}: {pos['quantity']} @ ${pos['price']}\\n"
    
    await client.store_journal_entry(
        entry=portfolio_entry,
        entry_type="portfolio_snapshot",
        metadata={"positions": positions}
    )
```

### 2. Trading Bot Integration

```python
class TradingBot:
    def __init__(self):
        self.client = FortunaMindPersistentClient()
        self.journal = TradingJournalManager(self.client)
    
    async def execute_trade(self, symbol, action, quantity, price):
        # Execute trade logic here...
        
        # Log to persistent journal
        await self.journal.log_trade_entry(
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            reasoning="Automated signal trigger",
            strategy="momentum_bot"
        )
```

### 3. Research Workflow

```python
async def research_workflow(client, symbol):
    """Complete research and analysis workflow"""
    
    # Store research notes
    await client.store_journal_entry(
        entry=f"Starting research on {symbol}",
        entry_type="research",
        tags=[symbol, "research_start"]
    )
    
    # Perform analysis...
    
    # Store conclusions
    await client.store_journal_entry(
        entry=f"Research complete: {symbol} shows strong fundamentals",
        entry_type="research_conclusion",
        tags=[symbol, "research_complete"],
        metadata={"recommendation": "buy", "target_price": 50000}
    )
```

### 4. Risk Management Integration

```python
async def risk_check(client, portfolio_value, max_risk_per_trade):
    """Log risk management decisions"""
    
    risk_entry = f"Portfolio value: ${portfolio_value:,.2f}\\n"
    risk_entry += f"Max risk per trade: ${max_risk_per_trade:,.2f}"
    
    await client.store_journal_entry(
        entry=risk_entry,
        entry_type="risk_management",
        metadata={
            "portfolio_value": portfolio_value,
            "max_risk": max_risk_per_trade,
            "risk_percentage": (max_risk_per_trade / portfolio_value) * 100
        }
    )
```

## 🔒 Security Best Practices

### 1. Credential Management

```python
# Use environment variables
client = FortunaMindPersistentClient(
    user_email=os.getenv('FORTUNAMIND_USER_EMAIL'),
    subscription_key=os.getenv('FORTUNAMIND_SUBSCRIPTION_KEY')
)

# Or use credential files (not in version control)
with open('.credentials.json') as f:
    creds = json.load(f)
    client = FortunaMindPersistentClient(**creds)
```

### 2. Error Handling

```python
async def safe_journal_operation(client):
    try:
        result = await client.store_journal_entry(
            entry="Safe operation",
            entry_type="test"
        )
        if not result.get("success"):
            logger.error(f"Operation failed: {result.get('error')}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
```

### 3. Rate Limiting Awareness

```python
import asyncio

async def batch_with_rate_limit(client, entries, delay=1.0):
    """Store entries with rate limiting"""
    results = []
    for entry_data in entries:
        result = await client.store_journal_entry(**entry_data)
        results.append(result)
        
        # Respect rate limits
        await asyncio.sleep(delay)
    
    return results
```

## 🧪 Testing

### Mock Server for Testing

```python
class MockPersistentClient(FortunaMindPersistentClient):
    """Mock client for testing"""
    
    def __init__(self):
        self.entries = []
        self.valid_subscription = True
    
    async def validate_subscription(self):
        return {"success": True, "valid": self.valid_subscription}
    
    async def store_journal_entry(self, entry, **kwargs):
        entry_id = f"mock_{len(self.entries)}"
        self.entries.append({"id": entry_id, "entry": entry, **kwargs})
        return {"success": True, "entry_id": entry_id}
```

### Unit Tests

```python
import pytest

@pytest.mark.asyncio
async def test_journal_entry_storage():
    client = MockPersistentClient()
    
    result = await client.store_journal_entry(
        entry="Test entry",
        entry_type="test"
    )
    
    assert result["success"] is True
    assert "entry_id" in result
```

## 🔄 Background Processing

### Async Task Queue Integration

```python
from celery import Celery

app = Celery('journal_processor')

@app.task
async def process_journal_entry(entry_data):
    """Background task for journal processing"""
    async with FortunaMindPersistentClient() as client:
        result = await client.store_journal_entry(**entry_data)
        return result

# Usage
process_journal_entry.delay({
    "entry": "Background processed entry",
    "entry_type": "automated"
})
```

## 📊 Analytics Integration

### Custom Analytics Pipeline

```python
async def analytics_pipeline(client):
    """Extract journal data for analytics"""
    
    # Get all entries
    all_entries = []
    offset = 0
    limit = 100
    
    while True:
        batch = await client.get_journal_entries(limit=limit, offset=offset)
        if not batch.get("entries"):
            break
        
        all_entries.extend(batch["entries"])
        offset += limit
    
    # Process for analytics
    trade_entries = [e for e in all_entries if e.get("entry_type") == "trade"]
    analysis_entries = [e for e in all_entries if e.get("entry_type") == "analysis"]
    
    return {
        "total_entries": len(all_entries),
        "trades": len(trade_entries),
        "analyses": len(analysis_entries)
    }
```

## 🚀 Production Deployment

### Production Configuration

```python
# production_config.py
FORTUNAMIND_CONFIG = {
    "server_url": "https://fortunamind-persistent-mcp.onrender.com",
    "timeout": 30,
    "retry_attempts": 3,
    "rate_limit_delay": 1.0
}

class ProductionClient(FortunaMindPersistentClient):
    def __init__(self, **kwargs):
        config = {**FORTUNAMIND_CONFIG, **kwargs}
        super().__init__(**config)
```

### Health Monitoring

```python
async def health_monitor():
    """Monitor server health"""
    async with FortunaMindPersistentClient() as client:
        health = await client.health_check()
        
        if health.get("overall") != "healthy":
            # Send alert
            logger.error(f"Server unhealthy: {health}")
            # Integration with monitoring system
```

---

## 📞 Support

For integration support:

1. Check server health: `GET /health`
2. Validate credentials: `POST /validate_subscription`
3. Review error logs in your application
4. Contact support with specific error messages

## 🔗 Related Documentation

- [Server API Documentation](../README.md)
- [Subscription Management](../docs/subscription_management.md)  
- [Privacy and Security](../docs/privacy_security.md)