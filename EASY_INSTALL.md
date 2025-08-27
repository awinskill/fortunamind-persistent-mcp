# 🚀 Easy Install - FortunaMind Persistent MCP

**Get started with FortunaMind Persistent MCP in less than 5 minutes!**

The persistent MCP server provides journal storage, portfolio analytics, and extended trading capabilities through Claude Desktop with dual credential support.

---

## 📋 **What You Need**

**Prerequisites:**
- Claude Desktop (latest version)
- Python 3.8+ installed on your system
- Internet connection for setup

**Required Credentials:**
1. **Subscription Credentials** (from FortunaMind team):
   - Your email address
   - Subscription key (format: `fm_sub_xxxxx`)

2. **Coinbase API Credentials** (from your Coinbase account):
   - API Key (format: `organizations/xxx/apiKeys/xxx`)  
   - API Secret (PEM private key format)

---

## 🎯 **One-Command Install**

### **Automatic Setup (Recommended)**

Run this single command in your terminal:

```bash
curl -fsSL https://fortunamind-persistent-mcp.onrender.com/install | bash
```

The installer will:
- ✅ Check system requirements
- ✅ Create isolated Python environment  
- ✅ Download HTTP bridge (~10KB)
- ✅ Collect your credentials securely
- ✅ Configure Claude Desktop automatically
- ✅ Verify everything works

### **Pre-configured Install**

If you have your credentials ready, you can pre-configure them:

```bash
FORTUNAMIND_USER_EMAIL="your-email@domain.com" \
FORTUNAMIND_SUBSCRIPTION_KEY="fm_sub_your_key_here" \
COINBASE_API_KEY="organizations/xxx/apiKeys/xxx" \
COINBASE_API_SECRET="-----BEGIN EC PRIVATE KEY-----
your-private-key-content-here
-----END EC PRIVATE KEY-----" \
curl -fsSL https://fortunamind-persistent-mcp.onrender.com/install | bash
```

---

## 🛠️ **Manual Setup (Alternative)**

If you prefer manual setup:

### **1. Download Components**

```bash
# Create directory
mkdir -p ~/.fortunamind-persistent
cd ~/.fortunamind-persistent

# Download bridge
curl -fsSL https://fortunamind-persistent-mcp.onrender.com/static/mcp_http_bridge.py -o mcp_bridge.py

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install aiohttp
```

### **2. Configure Claude Desktop**

Add this to your Claude Desktop config file:

**Config file locations:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

**Configuration:**
```json
{
  "mcpServers": {
    "fortunamind-persistent": {
      "command": "python3",
      "args": ["/Users/yourusername/.fortunamind-persistent/mcp_bridge.py"],
      "env": {
        "FORTUNAMIND_USER_EMAIL": "your-email@domain.com",
        "FORTUNAMIND_SUBSCRIPTION_KEY": "fm_sub_your_key_here",
        "COINBASE_API_KEY": "organizations/xxx/apiKeys/xxx",
        "COINBASE_API_SECRET": "-----BEGIN EC PRIVATE KEY-----\nyour-private-key-here\n-----END EC PRIVATE KEY-----",
        "MCP_SERVER_URL": "https://fortunamind-persistent-mcp.onrender.com/mcp"
      }
    }
  }
}
```

**⚠️ Important**: Update the path in `args` to match your actual installation directory.

---

## 🔐 **Getting Your Credentials**

### **Subscription Credentials**

Contact your FortunaMind administrator or check if you have access:

```bash
# If you have the repository, you can check existing testers
python3 scripts/add_tester.py --list
```

### **Coinbase API Credentials**

1. Visit [Coinbase Developer Portal](https://portal.cdp.coinbase.com/access/api)
2. Create a new API key with **"View"** permissions only
3. Copy the API Key and Private Key (PEM format)

**⚠️ Security**: Only use "View" permissions. Never grant "Trade" permissions.

---

## 🎉 **Test Your Setup**

### **1. Restart Claude Desktop**

Completely quit and restart Claude Desktop to load the new configuration.

### **2. Test Basic Functionality**

Try these commands in Claude Desktop:

```
Store a journal entry: "Analyzed BTC price action today - seeing strong support at $43k"
```

```
Show me my portfolio summary and recent journal entries
```

```
What are my usage stats?
```

### **Expected Results**

✅ Journal entries save and can be retrieved  
✅ Portfolio data loads from Coinbase  
✅ Usage statistics show your activity  
✅ No authentication errors in responses

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **"Missing required environment variables"**
- Check your Claude Desktop config file
- Ensure all 4 credential variables are set
- Restart Claude Desktop after config changes

#### **"HTTP error 400: Missing required headers"** 
- Subscription key format should start with `fm_sub_`
- API key should start with `organizations/`
- Check for typos in credential values

#### **"Invalid subscription key format"**
- Contact your FortunaMind administrator
- Verify your subscription key is active

#### **Bridge fails to start**
- Check Python 3.8+ is installed: `python3 --version`
- Verify virtual environment: `source ~/.fortunamind-persistent/venv/bin/activate`
- Test aiohttp import: `python -c "import aiohttp; print('OK')"`

### **Manual Testing**

Test the bridge directly:
```bash
source ~/.fortunamind-persistent/venv/bin/activate
python ~/.fortunamind-persistent/mcp_bridge.py
```

Check server health:
```bash
curl https://fortunamind-persistent-mcp.onrender.com/health
```

Validate Claude config:
```bash
python3 -m json.tool ~/.config/Claude/claude_desktop_config.json
```

---

## 📊 **What You Get**

### **Persistent Features**
- **Journal Entries**: Store and retrieve your trading thoughts
- **Usage Tracking**: Monitor your API usage and activity
- **Subscription Management**: Tier-based access control
- **Data Privacy**: Email-based identity with hash storage

### **Portfolio Analytics**
- **Real-time Portfolio**: Live portfolio values and positions
- **Performance Metrics**: Returns, volatility, and risk analysis
- **Market Research**: Comprehensive asset research and analysis
- **Price Data**: Real-time and historical price information

### **Dual Integration**
- **Subscription System**: Persistent storage with your account
- **Coinbase Integration**: Direct API access to your portfolio
- **Seamless Experience**: One interface, full functionality

---

## 📞 **Support**

### **Getting Help**
- **Server Status**: https://fortunamind-persistent-mcp.onrender.com/health
- **Documentation**: Complete setup guides available
- **Logs**: Check Claude Desktop logs for connection details

### **File Locations**
- **Installation**: `~/.fortunamind-persistent/`
- **Bridge File**: `~/.fortunamind-persistent/mcp_bridge.py`
- **Virtual Environment**: `~/.fortunamind-persistent/venv/`
- **Claude Config**: Platform-specific (see above)

---

## 🎯 **Next Steps**

Once installed, try these advanced features:

```
"Analyze my portfolio risk and suggest improvements"
```

```
"Show me a comprehensive analysis of my recent trading activity"
```

```
"Store a detailed journal entry about my investment thesis for SOL"
```

```
"What patterns do you see in my journal entries over the past month?"
```

---

**🎉 You're all set!** Enjoy the enhanced Claude Desktop experience with persistent storage and comprehensive portfolio analytics.

---

*Last updated: August 27, 2025*