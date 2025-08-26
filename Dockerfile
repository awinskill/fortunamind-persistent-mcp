# FortunaMind Persistent MCP Server - Render Optimized Dockerfile
# Single-stage build optimized for Render.com deployment
FROM python:3.11-slim

# Set environment variables for Python (PORT will be set by Render)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    MCP_SERVER_NAME="FortunaMind-Persistent-MCP-Production"

# Create non-root user for security
RUN groupadd --gid 1000 mcpuser && \
    useradd --uid 1000 --gid mcpuser --shell /bin/bash --create-home mcpuser

# Install system dependencies including git for version generation
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies first (for better caching)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ ./src/

# Copy configuration files
COPY pyproject.toml setup.py ./

# Install the package itself for proper imports
RUN pip install -e .

# Create logs directory and set proper permissions
RUN mkdir -p /app/logs && \
    chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Comprehensive health check using PORT environment variable support
HEALTHCHECK --interval=30s --timeout=15s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Expose default port (Render will set PORT dynamically)
EXPOSE 8080

# Production command optimized for Render
# Use the direct HTTP server startup script
CMD python -m fortunamind_persistent_mcp.http_server