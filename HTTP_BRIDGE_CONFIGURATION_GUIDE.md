# HTTP Bridge & Claude Desktop Configuration Guide

**FortunaMind Persistent MCP Server - Complete Configuration Reference**

This guide provides comprehensive documentation for connecting Claude Desktop to your FortunaMind Persistent MCP server using the HTTP bridge with both subscription and Coinbase API credentials.

---

## 📋 **Table of Contents**

1. [HTTP Bridge Overview](#http-bridge-overview)
2. [Quick Start](#quick-start)
3. [Configuration Options](#configuration-options)
4. [Credential Management](#credential-management)
5. [Troubleshooting](#troubleshooting)
6. [Advanced Configuration](#advanced-configuration)

---

## 🌉 **HTTP Bridge Overview**

### **What is the HTTP Bridge?**

The **HTTP Bridge** (`mcp_http_bridge.py`) is a smart proxy server that enables Claude Desktop to connect to your remote FortunaMind Persistent MCP server while automatically handling both subscription and Coinbase API credentials.

### **Architecture Flow**

```
Claude Desktop (stdio) ↔ HTTP Bridge (local) ↔ Render Server (HTTPS)
```

**Step-by-Step Process:**
1. **Claude Desktop** sends MCP requests via stdio protocol to local bridge
2. **HTTP Bridge** receives stdio requests and converts to HTTP JSON-RPC
3. **HTTP Bridge** automatically injects BOTH credential types:
   - Subscription credentials (X-User-Email, X-Subscription-Key)
   - Coinbase API credentials (X-Coinbase-Api-Key, X-Coinbase-Api-Secret)
4. **HTTP Bridge** forwards requests to `https://fortunamind-persistent-mcp.onrender.com/mcp`
5. **Render Server** validates subscription AND processes Coinbase API calls
6. **HTTP Bridge** receives responses and converts back to stdio format
7. **Claude Desktop** receives responses as if from local MCP server

### **Key Benefits**

✅ **Always Updated**: Uses your Render deployment with latest features  
✅ **Dual Credential Handling**: Automatic injection of both subscription and Coinbase credentials  
✅ **SSL Security**: All remote communication encrypted  
✅ **Zero Maintenance**: No local server management required  
✅ **Stateless Design**: Server doesn't store your credentials  
✅ **Enterprise Ready**: Production-grade architecture  
✅ **Full Functionality**: Both journal persistence AND Coinbase portfolio access

---

## 🚀 **Quick Start**

### **Step 1: Get Your Credentials**

You need FOUR types of credentials:

**Subscription Credentials** (from FortunaMind team):
- Your email address
- Subscription key (format: `fm_sub_xxxxx`)

**Coinbase Credentials** (from your Coinbase account):
- Coinbase API Key (format: `organizations/xxx/apiKeys/xxx`)
- Coinbase API Secret (PEM private key)

### **Step 2: Configure Claude Desktop**

Add this to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "fortunamind-persistent": {
      "command": "python3",
      "args": [
        "/path/to/fortunamind-persistent-mcp/mcp_http_bridge.py"
      ],
      "env": {
        "FORTUNAMIND_USER_EMAIL": "your-email@domain.com",
        "FORTUNAMIND_SUBSCRIPTION_KEY": "fm_sub_your_key_here",
        "COINBASE_API_KEY": "organizations/your-org/apiKeys/your-key",
        "COINBASE_API_SECRET": "-----BEGIN EC PRIVATE KEY-----\nYOUR_PEM_KEY_HERE\n-----END EC PRIVATE KEY-----",
        "MCP_SERVER_URL": "https://fortunamind-persistent-mcp.onrender.com"
      }
    }
  }
}
```

### **Step 3: Restart Claude Desktop**

Restart Claude Desktop and you should see the FortunaMind tools available!

---

## ⚙️ **Configuration Options**

### **Environment Variables**

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `FORTUNAMIND_USER_EMAIL` | ✅ Yes | Your email address | `trader@example.com` |
| `FORTUNAMIND_SUBSCRIPTION_KEY` | ✅ Yes | Your subscription key | `fm_sub_abc123...` |
| `COINBASE_API_KEY` | ✅ Yes | Coinbase API key | `organizations/xxx/apiKeys/xxx` |
| `COINBASE_API_SECRET` | ✅ Yes | Coinbase API secret (PEM) | `-----BEGIN EC PRIVATE KEY-----\n...` |
| `MCP_SERVER_URL` | ⚠️ Optional | Server URL | `https://fortunamind-persistent-mcp.onrender.com` |

### **Claude Desktop Configuration File Locations**

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```
~/.config/claude/claude_desktop_config.json
```

---

## 🔑 **Credential Management**

### **Getting Subscription Credentials**

Contact your FortunaMind administrator or use the subscription management tools:

```bash
# Check if you have existing subscription
python3 scripts/add_tester.py --validate your-email@domain.com

# Or list all testers
python3 scripts/add_tester.py --list
```

### **Getting Coinbase API Credentials**

1. Go to [Coinbase Advanced Trade](https://www.coinbase.com/advanced-trade)
2. Navigate to Settings → API
3. Create a new API key with "View" permissions
4. Copy the API Key and API Secret (PEM format)

⚠️ **Security Note**: Only "View" permissions are needed. Never grant "Trade" permissions.

### **Credential Validation**

Test your credentials:

```bash
# Test the HTTP bridge
python3 mcp_http_bridge.py
```

If successful, you should see:
```
🌉 Starting FortunaMind Persistent MCP HTTP Bridge
🔗 Target server: https://fortunamind-persistent-mcp.onrender.com/mcp
📧 User email: your-email@domain.com
🎫 Subscription key: fm_sub_abc123...
🔑 Coinbase API key: organizations/xxx/apiKeys/xxx...
🔐 Coinbase API secret: ************
```

---

## 🛠️ **Available Tools**

Once configured, you'll have access to these tools in Claude Desktop:

### **Journal Management**
- `store_journal_entry` - Save trading thoughts and analysis
- `get_journal_entries` - Retrieve your stored entries
- `get_user_stats` - View usage statistics
- `validate_subscription` - Check subscription status

### **Coinbase Integration**
The bridge also handles Coinbase API credentials, so any Coinbase-specific tools from the framework will work seamlessly.

### **Example Usage in Claude Desktop**

```
You: "Store a journal entry about today's BTC analysis"
Claude: "I'll store that journal entry for you..."
[Uses store_journal_entry tool with your credentials]

You: "Show me my recent journal entries"  
Claude: "Here are your recent entries..."
[Uses get_journal_entries tool]
```

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### ❌ "Missing required environment variables"

```
❌ Missing required environment variables:
  - FORTUNAMIND_USER_EMAIL
  - COINBASE_API_KEY
```

**Solution**: Check your Claude Desktop configuration file and ensure all variables are set.

#### ❌ "HTTP error 400: Missing required headers"

**Solution**: The bridge couldn't inject credentials. Check that all environment variables are present and properly formatted.

#### ❌ "Invalid subscription: Invalid subscription key format"

**Solution**: Subscription key should start with `fm_sub_`. Contact your administrator for a valid key.

#### ❌ "Request timeout"

**Solution**: Server might be slow or unreachable. Check your internet connection and server status.

### **Debug Mode**

Run the bridge manually to see debug output:

```bash
export FORTUNAMIND_USER_EMAIL="your-email@domain.com"
export FORTUNAMIND_SUBSCRIPTION_KEY="fm_sub_your_key"
export COINBASE_API_KEY="organizations/xxx/apiKeys/xxx"
export COINBASE_API_SECRET="-----BEGIN EC PRIVATE KEY-----..."

python3 mcp_http_bridge.py
```

### **Server Health Check**

Check if the server is healthy:

```bash
curl https://fortunamind-persistent-mcp.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-27T12:00:00.000000",
  "server": "FortunaMind-Persistent-MCP-Production"
}
```

---

## 🔬 **Advanced Configuration**

### **Custom Server URL**

To use a different server (e.g., local development):

```json
"env": {
  "MCP_SERVER_URL": "http://localhost:8000",
  ...
}
```

### **Multiple Configurations**

You can have multiple configurations for different environments:

```json
{
  "mcpServers": {
    "fortunamind-production": {
      "command": "python3",
      "args": ["/path/to/mcp_http_bridge.py"],
      "env": {
        "FORTUNAMIND_USER_EMAIL": "prod@example.com",
        "MCP_SERVER_URL": "https://fortunamind-persistent-mcp.onrender.com",
        ...
      }
    },
    "fortunamind-staging": {
      "command": "python3", 
      "args": ["/path/to/mcp_http_bridge.py"],
      "env": {
        "FORTUNAMIND_USER_EMAIL": "staging@example.com",
        "MCP_SERVER_URL": "https://staging.fortunamind.com",
        ...
      }
    }
  }
}
```

### **Logging Configuration**

For more detailed logging, modify the bridge:

```python
# In mcp_http_bridge.py, change logging level:
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    format="%(asctime)s - %(levelname)s - %(message)s", 
    stream=sys.stderr
)
```

### **Request Timeout Configuration**

Adjust timeout for slow connections:

```python
# In mcp_http_bridge.py, find this line and modify:
timeout=aiohttp.ClientTimeout(total=60),  # Changed from 30
```

---

## 🔐 **Security Best Practices**

### **Credential Storage**

1. ✅ **Use environment variables** (as shown in this guide)
2. ❌ **Never hardcode credentials** in configuration files
3. ✅ **Use minimal permissions** for Coinbase API (View only)
4. ✅ **Regularly rotate credentials**
5. ✅ **Keep subscription keys private**

### **Network Security**

1. ✅ All communication uses HTTPS/TLS encryption
2. ✅ No credentials are logged by default
3. ✅ Server uses stateless authentication
4. ✅ Rate limiting prevents abuse

### **File Permissions**

Secure your configuration file:

```bash
chmod 600 ~/.claude/claude_desktop_config.json
```

---

## 📞 **Support & Resources**

### **Getting Help**

1. **Server Status**: Check https://fortunamind-persistent-mcp.onrender.com/health
2. **Documentation**: This guide covers most common use cases
3. **Debug Logs**: Run the bridge manually to see detailed output
4. **Community**: GitHub Issues for bugs and feature requests

### **Useful Commands**

```bash
# Test subscription
python3 scripts/add_tester.py --validate your@email.com

# List available testers
python3 scripts/add_tester.py --list

# Test bridge connection
python3 mcp_http_bridge.py

# Check server health
curl https://fortunamind-persistent-mcp.onrender.com/health
```

---

## 🎉 **You're All Set!**

Once configured, you'll have full access to both:
- **Persistent journal functionality** (subscription-based)
- **Coinbase portfolio access** (API-based)

All through a single, seamless Claude Desktop integration!

**Happy Trading!** 📈💰

---

*Questions? Issues? Feature requests? Open an issue on GitHub or contact your FortunaMind administrator.*