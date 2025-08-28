# 🚀 FortunaMind Persistent MCP Server - Quick Start Guide

## 📋 Prerequisites

- Python 3.9 or higher
- Access to a Supabase project (for persistent storage)
- Optional: Coinbase API credentials (for real market data testing)

## 🛠️ Installation

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone https://github.com/awinskill/fortunamind-persistent-mcp.git
cd fortunamind-persistent-mcp

# Install the package in development mode
pip install -e .

# Install additional dependencies
pip install -r requirements.txt
```

### 2. Set Up Environment Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your settings (see configuration section below)
nano .env
```

## 🗄️ Database Setup

### Option A: Supabase (Recommended for Production)

1. **Create a Supabase Project**
   ```bash
   # Go to https://supabase.com and create a new project
   # Note down your project URL and anon key
   ```

2. **Configure Environment Variables**
   ```bash
   # In your .env file, set:
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_ANON_KEY=your-anon-key-here
   ```

3. **Run Database Migrations**
   ```bash
   # Create the database schema
   alembic upgrade head
   ```

4. **Set Up Row Level Security**
   ```bash
   # Apply RLS policies (requires service role key)
   psql -d "postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres" \
        -f scripts/setup_rls_policies.sql
   ```

### Option B: Mock Storage (Development)

```bash
# In your .env file, set:
STORAGE_BACKEND=mock
USE_MOCK_STORAGE=true
```

## 🎯 Quick Test

### 1. Verify Installation

```bash
# Test the server initialization
python -c "
from src.fortunamind_persistent_mcp.persistent_mcp.server import PersistentMCPServer
from src.fortunamind_persistent_mcp.config import Settings

settings = Settings()
server = PersistentMCPServer(settings=settings)
print('✅ Server created successfully!')
"
```

### 2. Test Tool Creation

```bash
# Verify all tools can be created
python -c "
from src.fortunamind_persistent_mcp.core.tool_factory import UnifiedToolFactory, ToolType

factory = UnifiedToolFactory()
tools = {}
for tool_type in ToolType:
    try:
        tool = factory.create_tool(tool_type)
        tools[tool_type.name] = tool
        print(f'✅ Created {tool_type.name}')
    except Exception as e:
        print(f'❌ Failed {tool_type.name}: {e}')

print(f'Successfully created {len(tools)}/5 tools')
"
```

## 🔧 Configuration Reference

### Core Settings (.env)

```bash
# Application
ENVIRONMENT=development
MCP_SERVER_NAME=FortunaMind-Persistent-MCP-Dev
LOG_LEVEL=INFO

# Database (choose one)
# Option 1: Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# Option 2: Mock storage
STORAGE_BACKEND=mock
USE_MOCK_STORAGE=true

# Features
ENABLE_PORTFOLIO_INTEGRATION=true
ENABLE_TECHNICAL_INDICATORS=true
ENABLE_TRADING_JOURNAL=true
ENABLE_MARKET_RESEARCH=true

# Security
SECURITY_PROFILE=MODERATE
RATE_LIMIT_PER_MINUTE=60
```

## 📊 Available Tools

The server provides these five main tools:

1. **Portfolio Tool** - Enhanced portfolio analysis with historical tracking
2. **Technical Indicators Tool** - RSI, MACD, Bollinger Bands, Moving Averages
3. **Trading Journal Tool** - Persistent journaling with emotional analysis
4. **Market Research Tool** - Market data and research capabilities
5. **Prices Tool** - Real-time and historical price data

## 🐳 Docker Deployment (Optional)

```bash
# Build the Docker image
docker build -t fortunamind-persistent-mcp .

# Run with environment file
docker run -d \
  --env-file .env \
  -p 8080:8080 \
  --name persistent-mcp \
  fortunamind-persistent-mcp
```

## 📡 Claude Desktop Integration

1. **Update Claude Desktop Config**
   ```json
   {
     "mcpServers": {
       "fortunamind-persistent": {
         "command": "python",
         "args": ["-m", "src.fortunamind_persistent_mcp.main"],
         "cwd": "/path/to/fortunamind-persistent-mcp",
         "env": {
           "SUPABASE_URL": "your-supabase-url",
           "SUPABASE_ANON_KEY": "your-anon-key"
         }
       }
     }
   }
   ```

2. **Restart Claude Desktop**
   - The persistent tools will be available in Claude Desktop

## 🧪 Testing

### Unit Tests
```bash
# Run unit tests
python -m pytest tests/unit/ -v
```

### Integration Tests
```bash
# Run integration tests (requires real credentials)
python -m pytest tests/integration/ -v
```

### End-to-End Test
```bash
# Test complete pipeline
python tests/test_e2e_pipeline.py
```

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure package is installed in development mode
   pip install -e .
   ```

2. **Framework Tools Not Available**
   ```bash
   # This is expected - the system falls back to mock tools
   # Framework warnings can be safely ignored during development
   ```

3. **Database Connection Issues**
   ```bash
   # Test Supabase connection
   python scripts/test_connection.py
   
   # Check your .env configuration
   # Verify Supabase project is running
   ```

4. **Tool Creation Failures**
   ```bash
   # Enable debug logging
   LOG_LEVEL=DEBUG
   
   # Check storage backend configuration
   ```

### Error Messages

- **"Framework not available"** → Normal, uses mock implementations
- **"Storage initialization failed"** → Check Supabase credentials
- **"Tool creation failed"** → Check storage backend configuration

## 📚 Next Steps

1. **Development**: Start with mock storage for rapid development
2. **Testing**: Set up Supabase project for persistence testing
3. **Production**: Deploy with proper Supabase configuration and RLS
4. **Integration**: Connect to Claude Desktop or other MCP clients

## 🔒 Security Notes

- **API Keys**: Never commit API keys to version control
- **Database**: Use Row Level Security policies in production
- **Environment**: Use secure environment variables for production
- **Network**: Enable HTTPS and proper firewall rules for production deployment

## 📞 Support

- Check the troubleshooting section above
- Review logs for specific error messages
- Verify environment configuration matches requirements
- Test with mock storage first to isolate database issues