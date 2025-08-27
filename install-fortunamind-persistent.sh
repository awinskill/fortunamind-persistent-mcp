#!/bin/bash
#
# FortunaMind Persistent MCP Client - One-Command Installer
# ========================================================
#
# Installs FortunaMind Persistent MCP client for Claude Desktop without requiring
# full repository checkout. Handles package installation, credential setup,
# and Claude Desktop configuration automatically.
#
# Supports DUAL credential types:
# - Subscription credentials (email + subscription key)
# - Coinbase API credentials (API key + API secret)
#
# Usage:
#   curl -fsSL https://fortunamind-persistent-mcp.onrender.com/install | bash
#
# Or with credentials:
#   FORTUNAMIND_USER_EMAIL="user@domain.com" \
#   FORTUNAMIND_SUBSCRIPTION_KEY="fm_sub_xxx" \
#   COINBASE_API_KEY="organizations/xxx/apiKeys/xxx" \
#   COINBASE_API_SECRET="-----BEGIN EC PRIVATE KEY-----..." \
#   curl -fsSL https://fortunamind-persistent-mcp.onrender.com/install | bash
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Header
echo -e "${BLUE}"
echo "🚀 FortunaMind Persistent MCP Client Installer v1.0"
echo "======================================================"
echo "📅 Install Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo -e "${NC}"

# Check prerequisites
check_prerequisites() {
    info "Checking prerequisites..."

    # Check Python 3.8+
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed. Please install Python 3.8+ and try again."
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        error "Python 3.8+ is required. Found Python $PYTHON_VERSION"
    fi

    # Check pip
    if ! command -v pip3 &> /dev/null; then
        error "pip3 is required but not installed. Please install pip3 and try again."
    fi

    success "Python $PYTHON_VERSION and pip3 found"
}

# Detect platform for Claude Desktop config path
get_claude_config_path() {
    case "$OSTYPE" in
        darwin*)
            echo "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
            ;;
        linux-gnu*)
            echo "$HOME/.config/Claude/claude_desktop_config.json"
            ;;
        msys*|cygwin*)
            echo "$HOME/AppData/Roaming/Claude/claude_desktop_config.json"
            ;;
        *)
            warning "Unknown platform: $OSTYPE. Using Linux path."
            echo "$HOME/.config/Claude/claude_desktop_config.json"
            ;;
    esac
}

# Setup virtual environment
setup_virtual_environment() {
    info "Setting up Python virtual environment..."

    # Create FortunaMind Persistent directory
    FORTUNAMIND_DIR="$HOME/.fortunamind-persistent"
    mkdir -p "$FORTUNAMIND_DIR"

    # Create virtual environment
    VENV_DIR="$FORTUNAMIND_DIR/venv"
    if [ -d "$VENV_DIR" ]; then
        warning "Virtual environment already exists, removing old one..."
        rm -rf "$VENV_DIR"
    fi

    python3 -m venv "$VENV_DIR"
    success "Virtual environment created: $VENV_DIR"

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    success "Virtual environment activated"

    # Upgrade pip in virtual environment
    pip install --upgrade pip
    success "Pip upgraded in virtual environment"
}

# Install HTTP bridge and dependencies
install_bridge() {
    info "Installing FortunaMind Persistent MCP HTTP Bridge..."

    # Download the HTTP bridge (single file, ~10KB)
    BRIDGE_PATH="$HOME/.fortunamind-persistent/fortunamind_persistent_bridge.py"

    if command -v curl &> /dev/null; then
        curl -fsSL "https://fortunamind-persistent-mcp.onrender.com/static/mcp_http_bridge.py" -o "$BRIDGE_PATH"
    elif command -v wget &> /dev/null; then
        wget -q "https://fortunamind-persistent-mcp.onrender.com/static/mcp_http_bridge.py" -O "$BRIDGE_PATH"
    else
        error "Neither curl nor wget found. Please install one of them and try again."
    fi

    # Make executable
    chmod +x "$BRIDGE_PATH"
    success "HTTP bridge downloaded: $BRIDGE_PATH (~10KB)"

    # Install dependencies in virtual environment
    info "Installing dependencies (aiohttp)..."
    source "$HOME/.fortunamind-persistent/venv/bin/activate"
    pip install aiohttp
    success "Dependencies installed in virtual environment"
}

# Get subscription credentials from user if not in environment
get_subscription_credentials() {
    if [ -n "$FORTUNAMIND_USER_EMAIL" ] && [ -n "$FORTUNAMIND_SUBSCRIPTION_KEY" ]; then
        success "Using subscription credentials from environment variables"
        return
    fi

    info "FortunaMind Persistent MCP requires subscription credentials"
    info "📖 Contact your FortunaMind administrator for subscription access"
    echo

    # Get email
    while [ -z "$FORTUNAMIND_USER_EMAIL" ]; do
        echo -n "Enter your email address: "
        read -r FORTUNAMIND_USER_EMAIL
        if [ -z "$FORTUNAMIND_USER_EMAIL" ]; then
            warning "Email address cannot be empty"
        elif [[ ! "$FORTUNAMIND_USER_EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            warning "Please enter a valid email address"
            FORTUNAMIND_USER_EMAIL=""
        fi
    done

    # Get subscription key
    while [ -z "$FORTUNAMIND_SUBSCRIPTION_KEY" ]; do
        echo -n "Enter your subscription key (starts with fm_sub_): "
        read -r FORTUNAMIND_SUBSCRIPTION_KEY
        if [ -z "$FORTUNAMIND_SUBSCRIPTION_KEY" ]; then
            warning "Subscription key cannot be empty"
        elif [[ ! "$FORTUNAMIND_SUBSCRIPTION_KEY" =~ ^fm_sub_ ]]; then
            warning "Subscription key should start with 'fm_sub_'"
            FORTUNAMIND_SUBSCRIPTION_KEY=""
        fi
    done

    success "Subscription credentials collected"
}

# Get Coinbase credentials from user if not in environment
get_coinbase_credentials() {
    if [ -n "$COINBASE_API_KEY" ] && [ -n "$COINBASE_API_SECRET" ]; then
        success "Using Coinbase credentials from environment variables"
        return
    fi

    info "FortunaMind Persistent MCP also requires Coinbase Advanced Trading API credentials"
    info "📖 Get your credentials at: https://portal.cdp.coinbase.com/access/api"
    echo

    # Get API key
    while [ -z "$COINBASE_API_KEY" ]; do
        echo -n "Enter your Coinbase API Key: "
        read -r COINBASE_API_KEY
        if [ -z "$COINBASE_API_KEY" ]; then
            warning "API Key cannot be empty"
        fi
    done

    # Get API secret
    echo "Enter your Coinbase API Secret (PEM private key):"
    echo "Paste the entire private key including -----BEGIN EC PRIVATE KEY----- headers"
    echo "Press Enter on an empty line when finished:"

    COINBASE_API_SECRET=""
    while IFS= read -r line; do
        [ -z "$line" ] && break
        COINBASE_API_SECRET="${COINBASE_API_SECRET}${line}\n"
    done

    # Remove trailing newline and escape for JSON
    COINBASE_API_SECRET=$(echo -e "$COINBASE_API_SECRET" | sed 's/$//')

    if [[ ! "$COINBASE_API_SECRET" =~ "BEGIN EC PRIVATE KEY" ]]; then
        error "Invalid API Secret format. Must be a PEM private key"
    fi

    success "Coinbase credentials collected"
}

# Configure Claude Desktop
configure_claude_desktop() {
    info "Configuring Claude Desktop..."

    CLAUDE_CONFIG_PATH=$(get_claude_config_path)
    CLAUDE_CONFIG_DIR=$(dirname "$CLAUDE_CONFIG_PATH")

    # Create config directory
    mkdir -p "$CLAUDE_CONFIG_DIR"

    # Backup existing config
    if [ -f "$CLAUDE_CONFIG_PATH" ]; then
        BACKUP_PATH="${CLAUDE_CONFIG_PATH}.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$CLAUDE_CONFIG_PATH" "$BACKUP_PATH"
        success "Existing configuration backed up to: $BACKUP_PATH"
    fi

    # Load existing config or create new
    if [ -f "$CLAUDE_CONFIG_PATH" ]; then
        EXISTING_CONFIG=$(cat "$CLAUDE_CONFIG_PATH")
    else
        EXISTING_CONFIG='{"mcpServers": {}}'
    fi

    # Use virtual environment Python and HTTP bridge
    VENV_PYTHON="$HOME/.fortunamind-persistent/venv/bin/python"
    BRIDGE_PATH="$HOME/.fortunamind-persistent/fortunamind_persistent_bridge.py"

    # Verify files exist
    if [ ! -f "$VENV_PYTHON" ]; then
        error "Virtual environment Python not found: $VENV_PYTHON"
    fi

    if [ ! -f "$BRIDGE_PATH" ]; then
        error "HTTP bridge not found: $BRIDGE_PATH"
    fi

    # Escape API secret for JSON (handle newlines properly)
    ESCAPED_SECRET=$(echo "$COINBASE_API_SECRET" | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')

    # Create new configuration with HTTP bridge
    python3 - << EOF
import json
import sys

try:
    config = json.loads('''$EXISTING_CONFIG''')
except:
    config = {"mcpServers": {}}

if "mcpServers" not in config:
    config["mcpServers"] = {}

config["mcpServers"]["fortunamind-persistent"] = {
    "command": "$VENV_PYTHON",
    "args": ["$BRIDGE_PATH"],
    "env": {
        "FORTUNAMIND_USER_EMAIL": "$FORTUNAMIND_USER_EMAIL",
        "FORTUNAMIND_SUBSCRIPTION_KEY": "$FORTUNAMIND_SUBSCRIPTION_KEY",
        "COINBASE_API_KEY": "$COINBASE_API_KEY",
        "COINBASE_API_SECRET": "$ESCAPED_SECRET",
        "MCP_SERVER_URL": "https://fortunamind-persistent-mcp.onrender.com/mcp"
    }
}

with open("$CLAUDE_CONFIG_PATH", "w") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("Configuration written successfully")
EOF

    # Set secure permissions
    chmod 600 "$CLAUDE_CONFIG_PATH"

    success "Claude Desktop configured: $CLAUDE_CONFIG_PATH"
    success "Secure file permissions set (600)"
}

# Verify installation
verify_installation() {
    info "Verifying installation..."

    # Check virtual environment
    VENV_PYTHON="$HOME/.fortunamind-persistent/venv/bin/python"
    if [ -f "$VENV_PYTHON" ]; then
        success "Virtual environment Python found: $VENV_PYTHON"
    else
        error "Virtual environment Python not found: $VENV_PYTHON"
    fi

    # Check HTTP bridge
    BRIDGE_PATH="$HOME/.fortunamind-persistent/fortunamind_persistent_bridge.py"
    if [ -f "$BRIDGE_PATH" ]; then
        success "HTTP bridge found: $BRIDGE_PATH"
    else
        error "HTTP bridge not found: $BRIDGE_PATH"
    fi

    # Check required Python packages in virtual environment
    source "$HOME/.fortunamind-persistent/venv/bin/activate"
    if python -c "import aiohttp; print('aiohttp:', aiohttp.__version__)" 2>/dev/null; then
        success "Required dependencies installed in virtual environment"
    else
        error "Dependencies not installed in virtual environment"
    fi
    deactivate

    # Check Claude Desktop config
    CLAUDE_CONFIG_PATH=$(get_claude_config_path)
    if [ -f "$CLAUDE_CONFIG_PATH" ]; then
        if python3 -c "
import json
with open('$CLAUDE_CONFIG_PATH') as f:
    config = json.load(f)
assert 'mcpServers' in config
assert 'fortunamind-persistent' in config['mcpServers']
assert 'FORTUNAMIND_USER_EMAIL' in config['mcpServers']['fortunamind-persistent']['env']
assert 'COINBASE_API_KEY' in config['mcpServers']['fortunamind-persistent']['env']
print('Claude Desktop config: OK')
        " 2>/dev/null; then
            success "Claude Desktop configuration verified"
        else
            error "Claude Desktop configuration is invalid"
        fi
    else
        error "Claude Desktop configuration file not found"
    fi

    success "Installation verification complete"
}

# Test connection to server
test_connection() {
    info "Testing connection to FortunaMind Persistent MCP server..."

    if command -v curl &> /dev/null; then
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://fortunamind-persistent-mcp.onrender.com/health")
        if [ "$HTTP_STATUS" = "200" ]; then
            success "FortunaMind Persistent MCP server is reachable"
        else
            warning "Server returned HTTP $HTTP_STATUS (may be starting up)"
        fi
    else
        info "curl not available, skipping server connectivity test"
    fi
}

# Main installation flow
main() {
    # Create install log
    INSTALL_LOG="$HOME/.fortunamind-persistent/install.log"
    mkdir -p "$HOME/.fortunamind-persistent"
    
    echo "$(date): Starting FortunaMind Persistent MCP installation" > "$INSTALL_LOG"
    
    check_prerequisites
    setup_virtual_environment
    install_bridge
    get_subscription_credentials
    get_coinbase_credentials
    configure_claude_desktop
    verify_installation
    test_connection
    
    echo "$(date): Installation completed successfully" >> "$INSTALL_LOG"

    echo
    echo -e "${GREEN}🎉 Installation Complete!${NC}"
    echo "========================"
    success "FortunaMind Persistent MCP client installed successfully"
    success "Virtual environment configured: $HOME/.fortunamind-persistent/venv/"
    success "HTTP bridge downloaded: $HOME/.fortunamind-persistent/fortunamind_persistent_bridge.py"
    success "Claude Desktop configured with secure dual credential handling"
    echo
    info "📋 Next Steps:"
    echo "1. Restart Claude Desktop"
    echo "2. FortunaMind Persistent tools will be available in your conversations"
    echo "3. Test with: 'Store a journal entry about my trading thoughts today'"
    echo "4. Try: 'Show me my portfolio and recent journal entries'"
    echo
    info "📁 Installation Details:"
    echo "- Virtual Environment: $HOME/.fortunamind-persistent/venv/"
    echo "- HTTP Bridge: $HOME/.fortunamind-persistent/fortunamind_persistent_bridge.py (~10KB)"
    echo "- Claude Config: $(get_claude_config_path)"
    echo "- Install Log: $HOME/.fortunamind-persistent/install.log"
    echo
    info "🔧 Troubleshooting:"
    echo "- Server status: https://fortunamind-persistent-mcp.onrender.com/health"
    echo "- Documentation: GitHub repository"
    echo "- Check logs in Claude Desktop for connection issues"
    echo
    info "🛠️  Manual Testing:"
    echo "- Test bridge: source $HOME/.fortunamind-persistent/venv/bin/activate && python $HOME/.fortunamind-persistent/fortunamind_persistent_bridge.py"
    echo "- Validate config: python3 -m json.tool $(get_claude_config_path)"
    echo
    info "🔐 Features Available:"
    echo "- Persistent journal entries with your trading thoughts"
    echo "- Portfolio analytics powered by Coinbase Advanced Trading"
    echo "- Subscription-based access with tier management"
    echo "- Privacy-first design with email-based identity"
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n${RED}Installation cancelled by user${NC}"; exit 1' INT

# Run main installation
main "$@"