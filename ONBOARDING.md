# 🚀 FortunaMind Persistent MCP - User Onboarding Guide

Welcome to **FortunaMind Persistent MCP Server** - your privacy-first, persistent trading journal and analytics platform!

## 🎯 What is FortunaMind Persistent MCP?

FortunaMind Persistent MCP Server extends the standard MCP (Model Context Protocol) with persistent storage capabilities, enabling:

- **📝 Persistent Trading Journal** - Your entries survive across sessions
- **🔒 Privacy-First Design** - Email-based identity, zero account data storage
- **📊 Tier-Based Access** - Flexible subscription tiers for different needs
- **🌐 Multi-Platform Support** - HTTP API, Claude Desktop, and custom integrations
- **⚡ Production-Ready** - Deployed on Render with Supabase PostgreSQL backend

## 🏁 Quick Start (5 Minutes)

### Step 1: Get Your Credentials

You'll need:
1. **Email Address** - Your identity for the system
2. **Subscription Key** - Generated key in format `fm_sub_xxxxx`

Contact your administrator or use the subscription management system to get your key.

### Step 2: Choose Your Integration

Pick the integration method that works best for you:

#### Option A: Claude Desktop Integration (Recommended)

1. **Install the MCP server:**
   ```bash
   git clone https://github.com/awinskill/fortunamind-persistent-mcp.git
   cd fortunamind-persistent-mcp
   pip install -r requirements.txt
   ```

2. **Configure Claude Desktop:**
   Add to your Claude Desktop MCP configuration:
   ```json
   {
     "mcpServers": {
       "fortunamind-persistent": {
         "command": "python",
         "args": ["/path/to/fortunamind-persistent-mcp/examples/claude_desktop_integration.py"],
         "env": {
           "FORTUNAMIND_USER_EMAIL": "your-email@domain.com",
           "FORTUNAMIND_SUBSCRIPTION_KEY": "fm_sub_your_key_here"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop** and start using the tools!

#### Option B: HTTP API Integration

Use the REST API directly:
```python
import httpx

# Store a journal entry
response = httpx.post(
    "https://fortunamind-persistent-mcp.onrender.com/store_journal_entry",
    headers={
        "X-User-Email": "your-email@domain.com",
        "X-Subscription-Key": "fm_sub_your_key_here",
        "Content-Type": "application/json"
    },
    json={
        "entry": "Analyzed BTC - strong support at $42k",
        "metadata": {"symbol": "BTC-USD", "type": "analysis"}
    }
)
```

#### Option C: Python Client Library

Use our comprehensive Python client:
```python
from examples.client_integration import FortunaMindPersistentClient

async with FortunaMindPersistentClient() as client:
    # Store journal entry
    result = await client.store_journal_entry(
        entry="Great trading day - up 2.5%",
        entry_type="reflection",
        tags=["performance", "daily_recap"]
    )
    
    # Get recent entries
    entries = await client.get_journal_entries(limit=10)
```

## 🛡️ Privacy & Security

### Why Email-Based Identity?

Unlike other systems that store account information, we use a **privacy-first approach**:

- ✅ **Your email generates a stable user ID** that survives API key rotations
- ✅ **Raw emails are never stored** - only SHA-256 hashes with namespaces
- ✅ **Zero account data storage** - no Coinbase account IDs, no API keys persisted
- ✅ **Row Level Security (RLS)** - database enforces user isolation
- ✅ **Works across exchanges** - same identity for Coinbase, Binance, etc.

### Gmail Users - Special Handling

We automatically normalize Gmail addresses:
- `john.doe+trading@gmail.com` → same as `johndoe@gmail.com`
- `john.doe@gmail.com` → same as `johndoe@gmail.com`
- This ensures consistent identity even with Gmail's aliasing

## 📊 Subscription Tiers

Choose the tier that fits your needs:

### 🆓 FREE Tier
- **Cost:** Free forever
- **Features:** Portfolio view, price checks, basic analysis
- **Limits:** No persistence, 1,000 API calls/day
- **Support:** Community forums

### 🚀 STARTER Tier  
- **Cost:** $9/month
- **Features:** 100 journal entries, historical analysis
- **Limits:** 5,000 API calls/day, 50MB storage
- **Support:** Email support

### ⭐ PREMIUM Tier
- **Cost:** $29/month  
- **Features:** Unlimited entries, advanced analytics, custom alerts
- **Limits:** 20,000 API calls/day, 1GB storage
- **Support:** Priority email support

### 🏢 ENTERPRISE Tier
- **Cost:** Custom pricing
- **Features:** All features, API access, unlimited usage
- **Limits:** No limits
- **Support:** Phone & email, dedicated account manager

## 🛠️ Available Tools & Features

### Core Journal Tools

#### `store_journal_entry`
Store any trading-related thought, analysis, or reflection:
```python
await client.store_journal_entry(
    entry="BTC showing strong momentum after breaking $45k resistance",
    entry_type="analysis",
    tags=["BTC", "breakout", "momentum"],
    metadata={
        "symbol": "BTC-USD",
        "price": 45200,
        "confidence": 8
    }
)
```

#### `get_journal_entries`  
Retrieve your stored entries with filtering:
```python
# Get recent analyses
entries = await client.get_journal_entries(
    limit=20,
    entry_type="analysis"
)

# Get all entries (paginated)
entries = await client.get_journal_entries(limit=50, offset=0)
```

### Specialized Trading Tools

#### `log_trade_entry`
Log actual trades with structured data:
```python
await journal.log_trade_entry(
    symbol="ETH-USD",
    action="buy",
    quantity=2.0,
    price=2850.00,
    reasoning="Strong DeFi adoption signals, oversold RSI",
    strategy="dip_buying"
)
```

#### `log_analysis_entry`
Store market analysis with outlook tracking:
```python
await journal.log_analysis_entry(
    symbol="MATIC-USD", 
    analysis="Polygon showing strong fundamentals with zkEVM launch",
    outlook="bullish",
    confidence=7
)
```

#### `search_entries_by_symbol`
Find all entries related to a specific asset:
```python
btc_entries = await client.search_entries_by_symbol("BTC")
```

### Administrative Tools

#### `get_user_stats`
Monitor your usage and subscription:
```python
stats = await client.get_user_stats()
# Returns: total_entries, entries_this_month, tier, status
```

#### `validate_subscription`
Check subscription status:
```python
validation = await client.validate_subscription()
# Returns: valid, tier, user_id (partial)
```

## 🎮 Common Usage Patterns

### Daily Trading Journal

```python
async def daily_journal_workflow():
    async with FortunaMindPersistentClient() as client:
        journal = TradingJournalManager(client)
        
        # Morning market outlook
        await journal.log_analysis_entry(
            symbol="MARKET",
            analysis="Strong overnight futures, expecting bullish open",
            outlook="bullish",
            confidence=6
        )
        
        # Log trades throughout the day
        await journal.log_trade_entry(
            symbol="BTC-USD",
            action="buy",
            quantity=0.1,
            price=43500,
            reasoning="Bounce off 50-day MA",
            strategy="technical_bounce"
        )
        
        # Evening reflection  
        await client.store_journal_entry(
            entry="Good trading day. Stayed disciplined with stop losses.",
            entry_type="reflection",
            tags=["discipline", "risk_management"]
        )
```

### Portfolio Tracking Integration

```python
async def sync_portfolio_to_journal(portfolio_data):
    async with FortunaMindPersistentClient() as client:
        
        # Create portfolio snapshot
        snapshot_text = "Portfolio Update:\n"
        total_value = 0
        
        for position in portfolio_data:
            value = position['quantity'] * position['current_price']
            total_value += value
            snapshot_text += f"• {position['symbol']}: {position['quantity']} @ ${position['current_price']:,.2f} = ${value:,.2f}\n"
        
        snapshot_text += f"\nTotal Portfolio Value: ${total_value:,.2f}"
        
        # Store with structured metadata
        await client.store_journal_entry(
            entry=snapshot_text,
            entry_type="portfolio_snapshot",
            metadata={
                "total_value": total_value,
                "positions": len(portfolio_data),
                "timestamp": datetime.now().isoformat()
            }
        )
```

### Research Workflow

```python
async def research_workflow(symbol):
    async with FortunaMindPersistentClient() as client:
        journal = TradingJournalManager(client)
        
        # Start research
        await client.store_journal_entry(
            entry=f"Starting deep dive research on {symbol}",
            entry_type="research",
            tags=[symbol, "research_start"]
        )
        
        # ... do research ...
        
        # Store findings
        await journal.log_analysis_entry(
            symbol=symbol,
            analysis="Strong fundamentals, growing adoption, solid tokenomics",
            outlook="bullish",
            confidence=8
        )
        
        # Research conclusion
        await client.store_journal_entry(
            entry=f"Research complete: {symbol} added to watchlist with price target $500",
            entry_type="research_conclusion",
            tags=[symbol, "watchlist", "price_target"],
            metadata={"target_price": 500, "research_date": datetime.now().isoformat()}
        )
```

## 🔧 Troubleshooting

### Common Issues

#### ❌ "Invalid subscription" errors
```python
# Check your credentials
validation = await client.validate_subscription()
print(validation)

# Ensure environment variables are set correctly
import os
print(f"Email: {os.getenv('FORTUNAMIND_USER_EMAIL')}")
print(f"Key: {os.getenv('FORTUNAMIND_SUBSCRIPTION_KEY')[:20]}...")
```

#### ❌ "Rate limit exceeded" errors
```python
# Check your usage
stats = await client.get_user_stats()
print(f"Current tier: {stats['tier']}")
print(f"Usage this month: {stats['entries_this_month']}")

# Consider upgrading tier if needed
```

#### ❌ Connection timeouts
```python
# Use longer timeout for slower connections
client = FortunaMindPersistentClient(timeout=60)
```

### Health Checking

Always check server health when troubleshooting:
```python
health = await client.health_check()
print(f"Server status: {health.get('overall')}")

if health.get('overall') != 'healthy':
    print("Server issues detected:")
    for component, status in health.get('components', {}).items():
        print(f"  {component}: {status}")
```

### Debug Mode

Enable debug logging for detailed information:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now all HTTP requests and responses will be logged
```

## 📚 Advanced Usage

### Batch Operations

```python
async def batch_import_trades(trades_data):
    async with FortunaMindPersistentClient() as client:
        journal = TradingJournalManager(client)
        
        successful = 0
        
        for trade in trades_data:
            try:
                result = await journal.log_trade_entry(**trade)
                if result.get('success'):
                    successful += 1
                
                # Rate limiting - wait between requests
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Failed to import trade: {e}")
        
        print(f"Successfully imported {successful}/{len(trades_data)} trades")
```

### Custom Integrations

```python
class CustomTradingBot:
    def __init__(self):
        self.client = FortunaMindPersistentClient()
        self.journal = TradingJournalManager(self.client)
    
    async def on_trade_signal(self, signal):
        """Called when trading signal is generated"""
        
        # Log the signal
        await self.journal.log_analysis_entry(
            symbol=signal['symbol'],
            analysis=f"Bot signal: {signal['type']} - {signal['reason']}",
            outlook=signal['direction'],
            confidence=signal['confidence']
        )
        
        # Execute trade if confidence high enough
        if signal['confidence'] >= 7:
            await self.execute_trade(signal)
    
    async def execute_trade(self, signal):
        """Execute the trade and log it"""
        
        # ... execute trade logic ...
        
        # Log the trade
        await self.journal.log_trade_entry(
            symbol=signal['symbol'],
            action=signal['direction'], # 'buy' or 'sell'
            quantity=signal['quantity'],
            price=signal['price'],
            reasoning=signal['reason'],
            strategy="automated_signal"
        )
```

### Analytics and Reporting

```python
async def generate_monthly_report():
    async with FortunaMindPersistentClient() as client:
        
        # Get all entries from this month
        entries = []
        offset = 0
        
        while True:
            batch = await client.get_journal_entries(limit=100, offset=offset)
            if not batch.get('entries'):
                break
            entries.extend(batch['entries'])
            offset += 100
        
        # Analyze entries
        trades = [e for e in entries if e.get('entry_type') == 'trade']
        analyses = [e for e in entries if e.get('entry_type') == 'analysis'] 
        reflections = [e for e in entries if e.get('entry_type') == 'reflection']
        
        report = f"""
        📊 Monthly Trading Report
        
        • Total Entries: {len(entries)}
        • Trades Logged: {len(trades)}
        • Analyses: {len(analyses)}  
        • Reflections: {len(reflections)}
        
        Most Analyzed Symbols:
        """
        
        # Find most analyzed symbols
        symbols = {}
        for entry in entries:
            metadata = entry.get('metadata', {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    continue
            
            symbol = metadata.get('symbol')
            if symbol:
                symbols[symbol] = symbols.get(symbol, 0) + 1
        
        for symbol, count in sorted(symbols.items(), key=lambda x: x[1], reverse=True)[:5]:
            report += f"        • {symbol}: {count} entries\n"
        
        # Store the report
        await client.store_journal_entry(
            entry=report,
            entry_type="monthly_report",
            tags=["report", "monthly", "analytics"]
        )
        
        return report
```

## 🔄 Migration & Backup

### Exporting Your Data

```python
async def export_all_data():
    """Export all your journal data"""
    async with FortunaMindPersistentClient() as client:
        
        # Get all entries
        all_entries = []
        offset = 0
        
        while True:
            batch = await client.get_journal_entries(limit=100, offset=offset)
            if not batch.get('entries'):
                break
            all_entries.extend(batch['entries'])
            offset += 100
        
        # Save to file
        with open('journal_backup.json', 'w') as f:
            json.dump(all_entries, f, indent=2)
        
        print(f"Exported {len(all_entries)} entries to journal_backup.json")
```

### Data Retention

- **FREE/STARTER:** Entries retained for 1 year
- **PREMIUM:** Entries retained for 3 years  
- **ENTERPRISE:** Indefinite retention

## 📞 Support & Resources

### Getting Help

1. **Documentation:** This guide covers most common use cases
2. **Examples:** Check `/examples` directory for code samples
3. **Health Check:** Always verify server status first
4. **Community:** GitHub Issues for bugs and feature requests

### Server Status

- **Production Server:** https://fortunamind-persistent-mcp.onrender.com
- **Health Endpoint:** https://fortunamind-persistent-mcp.onrender.com/health
- **Status Page:** Check GitHub for service announcements

### Rate Limits

Respect the rate limits for your tier:
- **FREE:** 60/hour, 1,000/day, 20,000/month
- **STARTER:** 300/hour, 5,000/day, 100,000/month  
- **PREMIUM:** 1,000/hour, 20,000/day, 500,000/month
- **ENTERPRISE:** Unlimited

### Best Practices

1. **Use async context managers** for automatic cleanup
2. **Implement retry logic** for production applications
3. **Monitor your usage** with `get_user_stats()`
4. **Tag your entries** for better organization
5. **Include metadata** for structured analysis
6. **Regular backups** if you have critical data

---

## 🎉 Welcome to FortunaMind!

You're all set to start building your persistent trading journal! The system is designed to grow with your needs - start with basic journaling and expand into advanced analytics as your trading evolves.

**Happy Trading!** 📈💰

---

*Questions? Issues? Feature requests? Open an issue on GitHub or contact support.*