# FortunaMind Persistent MCP Server Docker Configuration
# Multi-stage build for production optimization
FROM python:3.11-slim AS base

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for security
RUN groupadd --gid 1000 mcpuser && \
    useradd --uid 1000 --gid mcpuser --shell /bin/bash --create-home mcpuser

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY .env.example ./
COPY *.md ./
COPY *.toml ./

# Create logs directory
RUN mkdir -p /app/logs && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose MCP server port
EXPOSE 8080

# Default command - can be overridden
CMD ["python", "src/http_server.py"]

# =============================================================================
# Production stage with additional optimizations
# =============================================================================
FROM base AS production

# Production environment variables
ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    MCP_SERVER_NAME="FortunaMind-Persistent-MCP-Production"

# Enhanced health check for production
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -f http://localhost:8080/health || exit 1

# Production command
CMD ["python", "src/http_server.py"]

# =============================================================================
# Development stage with debugging tools
# =============================================================================
FROM base AS development

# Development environment variables
ENV ENVIRONMENT=development \
    LOG_LEVEL=DEBUG \
    MCP_SERVER_NAME="FortunaMind-Persistent-MCP-Dev"

# Install development dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt || true

# Install development tools
RUN pip install --no-cache-dir \
    ipython \
    pytest \
    pytest-cov \
    black \
    isort \
    mypy || true

# Development command with more verbose output
CMD ["python", "src/http_server.py"]