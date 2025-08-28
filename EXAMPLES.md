# 🎯 FortunaMind Persistent MCP Server - Usage Examples

This guide shows you how to use the FortunaMind Persistent MCP Server tools through various MCP clients.

## 📊 Available Tools Overview

### 1. Portfolio Tool
- **Purpose**: Enhanced portfolio analysis with historical tracking
- **Features**: Current holdings, performance metrics, historical snapshots
- **Persistence**: Stores portfolio snapshots for trend analysis

### 2. Technical Indicators Tool  
- **Purpose**: Educational technical analysis for crypto professionals
- **Features**: RSI, MACD, Bollinger Bands, Moving Averages
- **Persistence**: Tracks indicator history for pattern recognition

### 3. Trading Journal Tool
- **Purpose**: Learning-focused journaling with emotional analysis
- **Features**: Entry creation, emotional pattern detection, decision quality scoring
- **Persistence**: Long-term journal storage and trend analysis

### 4. Market Research Tool
- **Purpose**: Market data and research capabilities
- **Features**: Market analysis, trend identification
- **Persistence**: Research history and bookmark functionality

### 5. Prices Tool
- **Purpose**: Real-time and historical price data
- **Features**: Current prices, candlestick data, symbol lookup
- **Persistence**: Price history caching for performance

## 🖥️ Claude Desktop Examples

### Technical Indicators Usage

```
User: "Analyze BTC technical indicators for the past week"

Claude: I'll analyze Bitcoin's technical indicators using the FortunaMind Persistent MCP server.

[Technical Indicators Tool executes]

The analysis shows:

📈 **RSI (14-day)**: 67.3 (BULLISH signal)
- Currently in the upper range but not overbought
- Previous value: 62.1 (+5.2 increase)
- Educational note: RSI above 70 typically indicates overbought conditions

📊 **MACD**: 
- MACD Line: 2,147.23
- Signal Line: 1,892.45  
- Divergence: +254.78 (BULLISH crossover)
- Educational note: Positive divergence suggests upward momentum

🎯 **Bollinger Bands**:
- Upper Band: $67,892
- Current Price: $66,234 (near upper band)
- Lower Band: $63,445
- Educational note: Price near upper band suggests strong momentum

🔄 **Moving Averages**:
- 20-day SMA: $65,123 (price above)
- 50-day SMA: $63,890 (price above)  
- 200-day SMA: $58,234 (price above)
- Educational note: Price above all MAs indicates strong uptrend

**For crypto professionals aged 35-65**: These indicators suggest BTC is in a healthy uptrend with good momentum. However, the RSI approaching 70 warrants caution for new positions.
```

### Trading Journal Usage

```
User: "Add a trading journal entry about my recent ETH trade"

Claude: I'll help you create a trading journal entry for your ETH trade.

[Trading Journal Tool executes]

Journal entry created successfully! Here's what was analyzed:

📝 **Entry Summary**: "Bought 2 ETH at $3,245 based on breakout above resistance"

🧠 **Emotional Analysis**:
- Detected state: CONFIDENT
- Confidence level: HIGH
- Decision indicators: "breakout", "resistance" suggest technical analysis

⭐ **Decision Quality Score**: GOOD
- Reasoning: Technical analysis mentioned, clear entry criteria
- Improvement suggestion: Consider adding stop-loss and target levels

📊 **Educational Insights**:
- Your recent entries show improving pattern recognition
- Trend: More disciplined entries over past month
- Suggestion: Consider adding position sizing rationale

Entry ID: 7d8e9f10-abc1-2345-def6-789012345678
```

### Portfolio Analysis

```
User: "Show my portfolio performance with historical comparison"

Claude: I'll analyze your portfolio performance with historical data from the persistent storage.

[Persistent Portfolio Tool executes]

📊 **Current Portfolio** (as of 2025-08-28 15:30 UTC):

**Holdings**:
- BTC: 0.5234 ($34,678.90)
- ETH: 3.2145 ($10,234.56)  
- SOL: 45.67 ($8,901.23)
- Total Value: $53,814.69

📈 **Performance Metrics**:
- 24h Change: +2.34% (+$1,234.56)
- 7d Change: +8.91% (+$4,567.89)
- 30d Change: +15.67% (+$7,234.12)

🔄 **Historical Comparison**:
Based on stored snapshots from the past 90 days:

- Best performing period: Week of Aug 15-22 (+12.3%)
- Portfolio diversity improved: Previously 80% BTC, now 64%
- Risk-adjusted return: Sharpe ratio of 1.47 (excellent)

📊 **Trend Analysis**:
- Your portfolio allocation shows increased diversification
- SOL position added 3 weeks ago is outperforming (+23.4%)
- Overall risk has decreased while returns improved

**For experienced traders**: Your risk management has improved significantly. The diversification strategy is working well.
```

## 🌐 HTTP Integration Examples

### Direct HTTP API Calls

```bash
# Get technical indicators via HTTP
curl -X POST http://localhost:8080/tools/technical_indicators \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC-USD",
    "indicators": ["rsi", "macd", "bollinger"],
    "period": "7d",
    "user_id": "user123"
  }'
```

```json
{
  "success": true,
  "data": {
    "symbol": "BTC-USD",
    "indicators": {
      "rsi": {
        "value": 67.3,
        "signal": "BULLISH",
        "explanation": "RSI is in the upper range but not overbought",
        "educational_note": "Values above 70 typically indicate overbought conditions"
      },
      "macd": {
        "macd_line": 2147.23,
        "signal_line": 1892.45,
        "divergence": 254.78,
        "signal": "BULLISH",
        "explanation": "Positive divergence suggests upward momentum"
      }
    },
    "timestamp": "2025-08-28T15:30:00Z",
    "educational_context": "For crypto professionals aged 35-65: These indicators suggest strong momentum"
  }
}
```

### Trading Journal via HTTP

```bash
# Create journal entry
curl -X POST http://localhost:8080/tools/trading_journal \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create_entry",
    "entry": "Sold 0.1 BTC at $66,500 for profit taking",
    "metadata": {
      "trade_type": "sell",
      "symbol": "BTC-USD",
      "quantity": 0.1,
      "price": 66500
    },
    "user_id": "user123"
  }'
```

```json
{
  "success": true,
  "data": {
    "entry_id": "7d8e9f10-abc1-2345-def6-789012345678",
    "emotional_analysis": {
      "detected_state": "CONFIDENT",
      "confidence_level": "HIGH",
      "decision_quality": "EXCELLENT"
    },
    "insights": {
      "pattern": "Disciplined profit-taking",
      "suggestion": "Good timing based on recent patterns"
    },
    "educational_note": "Profit-taking at resistance levels is a sound risk management strategy"
  }
}
```

## 🔧 Development Integration

### Python Client Example

```python
import asyncio
from fortunamind_persistent_mcp.client import PersistentMCPClient

async def analyze_portfolio():
    """Example: Analyze portfolio with persistent tracking"""
    
    client = PersistentMCPClient()
    await client.connect()
    
    # Get current portfolio
    portfolio = await client.call_tool(
        "persistent_portfolio_summary",
        user_id="user123",
        include_history=True
    )
    
    # Analyze technical indicators
    btc_indicators = await client.call_tool(
        "technical_indicators",
        symbol="BTC-USD",
        indicators=["rsi", "macd", "bollinger"],
        user_id="user123"
    )
    
    # Create comprehensive report
    report = {
        "portfolio": portfolio,
        "btc_analysis": btc_indicators,
        "timestamp": datetime.utcnow()
    }
    
    # Store analysis in journal
    await client.call_tool(
        "trading_journal",
        action="create_entry", 
        entry=f"Portfolio analysis: {report['summary']}",
        metadata=report,
        user_id="user123"
    )
    
    await client.disconnect()
    return report

# Run analysis
result = asyncio.run(analyze_portfolio())
```

### JavaScript/TypeScript Integration

```javascript
import { PersistentMCPClient } from 'fortunamind-persistent-mcp-js';

class TradingDashboard {
  constructor() {
    this.client = new PersistentMCPClient({
      url: 'ws://localhost:8080/mcp',
      userId: 'user123'
    });
  }

  async initializeDashboard() {
    await this.client.connect();
    
    // Load persistent data
    const [portfolio, journal, indicators] = await Promise.all([
      this.loadPortfolio(),
      this.loadJournalEntries(), 
      this.loadTechnicalIndicators()
    ]);
    
    this.renderDashboard({ portfolio, journal, indicators });
  }

  async loadPortfolio() {
    return await this.client.callTool('persistent_portfolio_summary', {
      include_history: true,
      period: '30d'
    });
  }

  async loadJournalEntries() {
    return await this.client.callTool('trading_journal', {
      action: 'get_entries',
      limit: 10,
      include_analysis: true
    });
  }

  async loadTechnicalIndicators() {
    const symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD'];
    const indicators = await Promise.all(
      symbols.map(symbol => 
        this.client.callTool('technical_indicators', {
          symbol,
          indicators: ['rsi', 'macd'],
          period: '7d'
        })
      )
    );
    
    return indicators;
  }
}

// Initialize dashboard
const dashboard = new TradingDashboard();
dashboard.initializeDashboard();
```

## 📱 Real-World Use Cases

### 1. Daily Market Analysis Routine

```
Morning routine for crypto professionals:

1. Check portfolio performance vs yesterday
   → "Show my portfolio performance with yesterday's comparison"

2. Analyze key holdings' technical indicators  
   → "Analyze BTC, ETH, and SOL technical indicators"

3. Review recent journal entries for patterns
   → "Show my last 5 journal entries with emotional analysis"

4. Document market observations
   → "Add journal entry about today's market conditions"
```

### 2. Trade Decision Support

```
Before making a trade:

1. Analyze technical indicators
   → "Analyze [SYMBOL] technical indicators for entry signals"

2. Check historical performance at similar levels
   → "Show [SYMBOL] performance when RSI was at current level"

3. Document trade rationale  
   → "Add journal entry: Planning to [buy/sell] [SYMBOL] because..."

4. Set up tracking
   → "Store this trade plan for future performance analysis"
```

### 3. Weekly Performance Review

```
Weekly review process:

1. Portfolio performance summary
   → "Show weekly portfolio performance with historical context"

2. Journal entry analysis
   → "Analyze my trading decisions from this week" 

3. Technical pattern review
   → "Show technical indicator accuracy for my trades this week"

4. Learning documentation
   → "Add journal entry with lessons learned this week"
```

## 🎯 Educational Features

### Beginner-Friendly Explanations

Every tool response includes educational context:

- **Plain English explanations** of technical terms
- **Warning alerts** for risky decisions  
- **Best practice suggestions** for crypto professionals
- **Historical context** for pattern recognition

### Progressive Learning

The journal tool tracks your development:

- **Decision quality trends** over time
- **Emotional pattern recognition** 
- **Learning milestone identification**
- **Personalized improvement suggestions**

## 🔍 Advanced Features

### Cross-Tool Integration

The persistent storage enables powerful cross-tool analysis:

- Portfolio changes correlated with journal entries
- Technical indicator accuracy tracked against actual trades
- Emotional state patterns linked to performance outcomes
- Market research insights connected to trading decisions

### Data Export

```python
# Export your complete trading history
export_data = await client.call_tool(
    "data_export",
    user_id="user123",
    include_portfolio=True,
    include_journal=True, 
    include_indicators=True,
    format="json"
)

# Save for external analysis
with open('my_trading_history.json', 'w') as f:
    json.dump(export_data, f, indent=2)
```

This comprehensive persistence makes the FortunaMind MCP Server ideal for serious crypto professionals who want to track their learning journey and improve their decision-making over time.