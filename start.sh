#!/bin/bash
# FortunaMind Persistent MCP Server - Render Startup Script
# This script ensures we use the correct server and environment

echo "🚀 FortunaMind Persistent MCP Server Startup"
echo "============================================="
echo "PWD: $(pwd)"
echo "Python: $(python --version)"
echo "PYTHONPATH: $PYTHONPATH"
echo "PORT: ${PORT:-8000}"

# Set up environment
export PYTHONPATH="/opt/render/project/src:$PYTHONPATH"
echo "Updated PYTHONPATH: $PYTHONPATH"

# Check if our server file exists
if [ -f "server.py" ]; then
    echo "✅ Found server.py - using standalone FastAPI server"
    echo "🚀 Starting standalone FastAPI server..."
    exec python server.py
else
    echo "❌ server.py not found!"
    echo "Files in current directory:"
    ls -la
    exit 1
fi