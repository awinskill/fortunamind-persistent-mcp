# FortunaMind Persistent MCP HTTP Server Guide

## 🌐 Overview

The FortunaMind Persistent MCP HTTP Server provides MCP (Model Context Protocol) over HTTP for web applications and API integrations. This allows AI agents and applications to access educational crypto tools through standard REST endpoints.

## 🚀 Quick Start

### Option 1: Direct Python Execution

```bash
# Set environment variables
export SERVER_MODE=http
export DATABASE_URL="postgresql://user:pass@host:port/db"
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-key"
export SUPABASE_SERVICE_ROLE_KEY="your-service-key"
export JWT_SECRET_KEY="your-32-character-secret-key"

# Install dependencies
pip install -r requirements.txt

# Start HTTP server
python src/http_server.py
```

### Option 2: Docker Deployment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env

# Build and run with Docker Compose
docker-compose -f docker-compose.http.yml up -d
```

## 📡 API Endpoints

### Health Check
```
GET http://localhost:8080/health
```

### MCP Protocol Endpoint
```
POST http://localhost:8080/mcp
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/list",
  "params": {}
}
```

### Interactive Documentation
```
GET http://localhost:8080/docs (Development mode only)
```

## 🛠️ MCP Protocol Usage

### 1. Initialize Connection
```json
POST /mcp
{
  "jsonrpc": "2.0",
  "id": "init-1",
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "My App",
      "version": "1.0.0"
    }
  }
}
```

### 2. List Available Tools
```json
POST /mcp
{
  "jsonrpc": "2.0",
  "id": "tools-1",
  "method": "tools/list",
  "params": {}
}
```

### 3. Execute Technical Indicators Tool
```json
POST /mcp
{
  "jsonrpc": "2.0",
  "id": "tool-1",
  "method": "tools/call",
  "params": {
    "name": "technical_indicators",
    "arguments": {
      "symbol": "BTC",
      "timeframe": "7d",
      "include_education": true,
      "api_key": "organizations/your-org/apiKeys/your-key",
      "api_secret": "your-coinbase-api-secret"
    }
  }
}
```

### 4. Execute Trading Journal Tool
```json
POST /mcp
{
  "jsonrpc": "2.0",
  "id": "tool-2", 
  "method": "tools/call",
  "params": {
    "name": "trading_journal",
    "arguments": {
      "action": "add_entry",
      "entry_type": "trade",
      "content": "I bought some BTC today because I think the market is oversold. RSI is at 25 and I've been watching for a good entry point.",
      "symbol": "BTC",
      "trade_action": "buy",
      "confidence_level": 7,
      "api_key": "organizations/your-org/apiKeys/your-key",
      "api_secret": "your-coinbase-api-secret"
    }
  }
}
```

## 🔐 Authentication

The HTTP server supports multiple authentication methods:

### 1. Request Parameters (Recommended)
Include API credentials in the tool call arguments:
```json
{
  "arguments": {
    "api_key": "organizations/your-org/apiKeys/your-key",
    "api_secret": "your-coinbase-api-secret",
    // ... other parameters
  }
}
```

### 2. HTTP Headers
```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "X-Coinbase-API-Key: organizations/your-org/apiKeys/your-key" \
  -H "X-Coinbase-API-Secret: your-coinbase-api-secret" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/list","params":{}}'
```

### 3. Environment Variables
Set system environment variables:
```bash
export COINBASE_API_KEY="organizations/your-org/apiKeys/your-key"
export COINBASE_API_SECRET="your-coinbase-api-secret"
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SERVER_MODE` | Server mode ("http" or "stdio") | No | "stdio" |
| `SERVER_HOST` | HTTP server bind host | No | "0.0.0.0" |
| `SERVER_PORT` | HTTP server port | No | 8080 |
| `DATABASE_URL` | PostgreSQL connection URL | Yes | - |
| `SUPABASE_URL` | Supabase project URL | Yes | - |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | Yes | - |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | Yes | - |
| `JWT_SECRET_KEY` | JWT signing secret (32+ chars) | Yes | - |
| `SUBSCRIPTION_API_KEY` | FortunaMind subscription API key | No | - |
| `ENVIRONMENT` | Runtime environment | No | "development" |

### Server Modes

- **STDIO Mode** (`SERVER_MODE=stdio`): For Claude Desktop integration
- **HTTP Mode** (`SERVER_MODE=http`): For web applications and API integrations

## 🏗️ Architecture

The HTTP MCP Server follows the unified framework HTTP bridge pattern:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   HTTP Client   │────│  FastAPI Server  │────│   MCP Adapter   │
│  (Web App/API)  │    │   (HTTP Bridge)  │    │    (Protocol)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  Tool Registry   │────│  Storage Layer  │
                       │   (Unified)      │    │   (Supabase)    │
                       └──────────────────┘    └─────────────────┘
```

## 📊 Available Tools

### Technical Indicators Tool
- **Name**: `technical_indicators`
- **Purpose**: Beginner-friendly crypto technical analysis
- **Features**: RSI, moving averages, MACD, Bollinger Bands
- **Educational Focus**: Plain English explanations

### Trading Journal Tool
- **Name**: `trading_journal`
- **Purpose**: Learning-focused investment decision tracking
- **Features**: Emotional analysis, decision quality scoring
- **Actions**: `add_entry`, `review_entries`, `get_insights`, `search_entries`

## 🔒 Security Features

- **API Key Detection**: Prevents accidental storage of credentials
- **Prompt Injection Protection**: Blocks malicious prompts
- **Row Level Security**: Database isolation by user
- **Subscription Verification**: FortunaMind subscriber authentication
- **Rate Limiting**: Configurable request limits
- **Input Validation**: Comprehensive parameter validation

## 🚀 Production Deployment

### Using Docker Compose

1. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

2. **Deploy with SSL**:
   ```bash
   # Enable nginx proxy for SSL
   docker-compose -f docker-compose.http.yml --profile production up -d
   ```

3. **Monitor Health**:
   ```bash
   curl http://localhost:8080/health
   ```

### Using Kubernetes

Create deployment manifests based on the Docker image:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fortunamind-mcp-http
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fortunamind-mcp-http
  template:
    metadata:
      labels:
        app: fortunamind-mcp-http
    spec:
      containers:
      - name: http-server
        image: fortunamind/persistent-mcp:latest
        ports:
        - containerPort: 8080
        env:
        - name: SERVER_MODE
          value: "http"
        # Add other environment variables
```

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**:
   ```bash
   # Change port in .env or environment
   export SERVER_PORT=8081
   ```

2. **Database Connection Failed**:
   ```bash
   # Check DATABASE_URL format
   export DATABASE_URL="postgresql://user:pass@host:port/dbname"
   ```

3. **Subscription Verification Failed**:
   ```bash
   # Enable mock mode for testing
   export MOCK_SUBSCRIPTION_CHECK=true
   ```

### Debug Mode

Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
export ENVIRONMENT=development
python src/http_server.py
```

### Health Check

Monitor server health:
```bash
curl -s http://localhost:8080/health | jq .
```

## 🤝 Client Integration Examples

### Python Client
```python
import httpx
import json

async def call_mcp_tool():
    async with httpx.AsyncClient() as client:
        response = await client.post("http://localhost:8080/mcp", json={
            "jsonrpc": "2.0",
            "id": "1",
            "method": "tools/call",
            "params": {
                "name": "technical_indicators",
                "arguments": {
                    "symbol": "BTC",
                    "api_key": "your-api-key",
                    "api_secret": "your-api-secret"
                }
            }
        })
        return response.json()
```

### JavaScript Client
```javascript
async function callMCPTool() {
    const response = await fetch('http://localhost:8080/mcp', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            jsonrpc: '2.0',
            id: '1',
            method: 'tools/call',
            params: {
                name: 'trading_journal',
                arguments: {
                    action: 'add_entry',
                    entry_type: 'trade',
                    content: 'Today I bought ETH because...',
                    api_key: 'your-api-key',
                    api_secret: 'your-api-secret'
                }
            }
        })
    });
    
    return await response.json();
}
```

## 📚 Additional Resources

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [FortunaMind Framework Documentation](../coinbase-mcp/documentation/)
- [Supabase Setup Guide](https://supabase.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review server logs in `logs/persistent-mcp-http.log`
3. Create an issue in the GitHub repository
4. Contact FortunaMind support for subscription issues