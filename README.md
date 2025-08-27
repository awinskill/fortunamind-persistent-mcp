# FortunaMind Persistent MCP Server

A premium MCP server for FortunaMind subscribers that provides advanced technical analysis tools and personal trading journal capabilities. Designed for crypto-curious professionals aged 35-65 who want to learn and improve their investment decisions systematically.

## 🎯 **What This Is**

An educational companion that transforms complete crypto beginners into informed, confident investors through:

- **Professional technical indicators** explained in plain English
- **Personal trading journal** for reflection and learning
- **Historical analysis** and pattern recognition
- **Privacy-first design** with complete user control

## 🚀 **Key Features**

### Technical Analysis Made Simple
- RSI, SMA, EMA, MACD, Bollinger Bands, Volume Analysis
- Beginner-friendly explanations with real-world analogies
- Automatic integration with portfolio viewing
- Pre-trade analysis and overbought/oversold warnings

### Learning-Focused Trading Journal
- Conversational entry: "I bought Bitcoin because..."
- Automatic context capture (market conditions, technical indicators)
- Emotional pattern recognition and learning insights
- Privacy-first: dollar amounts optional, complete data control

### Enterprise-Grade Security
- Comprehensive API key detection and blocking
- Prompt injection protection
- Row-level security with Supabase
- No credentials ever stored

## 🏗️ **Architecture**

Built on the proven FortunaMind Tool Framework:
- **Base:** FortunaMind Common Library with Unified Server
- **Protocol:** MCP (Model Context Protocol) 
- **Storage:** PostgreSQL on Supabase with Row Level Security
- **Security:** Integrated common security scanner

## 🚀 **Easy Install (5 Minutes)**

### For End Users - One Command Setup

Get started immediately with our automated installer:

```bash
curl -fsSL https://fortunamind-persistent-mcp.onrender.com/install | bash
```

**What you need:**
- Python 3.8+ installed
- FortunaMind subscription credentials (email + key)
- Coinbase Advanced Trading API credentials

**What it does:**
- ✅ Creates isolated Python environment
- ✅ Downloads HTTP bridge (~10KB)
- ✅ Configures Claude Desktop automatically
- ✅ Handles both subscription and Coinbase credentials
- ✅ Verifies everything works

📖 **[Complete Install Guide →](EASY_INSTALL.md)**

---

## 📋 **Development Setup**

### Prerequisites
- Active FortunaMind subscription
- Python 3.11+
- Access to Supabase database
- Coinbase Advanced Trading API credentials (provided per session)

### Development Environment
```bash
# Clone repository
git clone https://github.com/awinskill/fortunamind-persistent-mcp.git
cd fortunamind-persistent-mcp

# Set up framework symlink
ln -s ../coinbase-mcp/src src/framework

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Supabase credentials

# Run migrations
alembic upgrade head

# Start development server
python -m src.main
```

## 🛡️ **Security First**

This project prioritizes user security:
- **Never stores API credentials** - users provide per session
- **Scans all inputs** for sensitive information
- **Blocks prompt injection** attempts automatically  
- **Encrypts all user data** at rest
- **Implements zero-trust** architecture

## 📚 **Documentation**

- [Product Requirements Document](PRD.md)
- [EPICs, Features & User Stories](EPICS_FEATURES_USER_STORIES.md)
- [API Documentation](docs/api/README.md)
- [Architecture Overview](docs/architecture/README.md)
- [Deployment Guide](docs/deployment/README.md)

## 🎓 **Educational Philosophy**

Designed for **learning, not just tracking:**

- Every interaction is an educational opportunity
- Focus on **decision quality** over just outcomes
- **Progressive disclosure** - simple first, details on request
- **Pattern recognition** helps users identify what works
- **Risk education** with every recommendation

## 👥 **Target Users**

**The Established Professional Explorer:**
- Age: 35-65
- Professional with disposable income
- 0-2 years crypto experience (including complete beginners)
- Values education and systematic learning
- Already trusts FortunaMind through subscription

## 🚦 **Project Status**

- **Phase 1:** Foundation & Infrastructure ⚠️ *In Progress*
- **Phase 2:** Technical Indicators & Journal *Planned*
- **Phase 3:** Testing & Polish *Planned*
- **Phase 4:** Beta Launch *Planned*

## 🤝 **Contributing**

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## 📄 **License**

This project is proprietary to FortunaMind. See [LICENSE](LICENSE) for details.

## 🔗 **Related Projects**

- [FortunaMind MCP Server](https://github.com/awinskill/fortunamind-mcp) - Base functionality
- [FortunaMind Common Library](https://github.com/awinskill/fortunamind-core) - Shared components

---

**Ready to transform crypto-curious professionals into confident investors through AI-powered education!** 🚀📊