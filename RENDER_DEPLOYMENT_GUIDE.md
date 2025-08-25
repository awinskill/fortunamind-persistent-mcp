# Render Deployment Guide

## 🚀 Deploying FortunaMind Persistent MCP Server to Render

This guide walks you through deploying the HTTP MCP server to Render with automatic deployments from GitHub.

## 📋 Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Push your code to GitHub (already done ✅)
3. **Supabase Database**: Set up Supabase for persistent storage

## 🔧 Quick Setup

### Step 1: Create Render Service

1. **Connect GitHub Repository**:
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Web Service" 
   - Connect your GitHub account
   - Select `awinskill/fortunamind-persistent-mcp`

2. **Configure Service**:
   ```
   Name: fortunamind-persistent-mcp
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python src/http_server.py
   ```

3. **Set Environment Variables**:
   - Add all required environment variables (see below)

### Step 2: Environment Variables

**Required Variables:**
```bash
# Server Configuration
SERVER_MODE=http
SERVER_HOST=0.0.0.0
SERVER_PORT=10000
ENVIRONMENT=production
LOG_LEVEL=INFO

# Database (Supabase)
DATABASE_URL=postgresql://user:pass@host:port/dbname
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Security
JWT_SECRET_KEY=your-32-character-secret-key
SECURITY_PROFILE=STRICT

# Optional: Subscription API
SUBSCRIPTION_API_URL=https://api.fortunamind.com/v1/subscriptions  
SUBSCRIPTION_API_KEY=your-subscription-api-key
```

### Step 3: Automatic Deployment Setup

The repository is configured for automatic deployments via GitHub Actions.

**Configure GitHub Secrets:**
1. Go to GitHub repository → Settings → Secrets and variables → Actions
2. Add these repository secrets:

```bash
RENDER_API_KEY=your-render-api-key
RENDER_SERVICE_ID=your-render-service-id
```

**Get Render API Key:**
1. Go to [Render Account Settings](https://dashboard.render.com/account/api-keys)
2. Create new API key
3. Copy the key to GitHub secrets

**Get Service ID:**
1. Go to your Render service dashboard
2. Copy the service ID from the URL: `srv-xxxxxxxxxxxxxxxxxx`

## 🎯 Deployment Methods

### Method 1: Automatic GitHub Integration (Recommended)

**How it works:**
1. Push code to `main` branch
2. GitHub Actions runs tests
3. Triggers Render deployment via API
4. Runs health checks
5. Reports deployment status

**Triggers:**
- Push to `main` branch
- Merged pull request to `main`

### Method 2: Manual Render Deploy

**Using Render Dashboard:**
1. Go to your service dashboard
2. Click "Manual Deploy"
3. Select branch and deploy

**Using render.yaml:**
The included `render.yaml` file provides infrastructure-as-code deployment:
1. Render automatically detects the file
2. Configures service based on the specification
3. Deploys with predefined settings

## 📊 Monitoring and Health Checks

### Health Check Endpoint
```
GET https://your-service.onrender.com/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "FortunaMind-Persistent-MCP-Production", 
  "version": "1.0.0",
  "components": {
    "storage": "healthy",
    "auth": "healthy", 
    "tools": "2 tools registered"
  }
}
```

### Service URLs

After deployment, your service will be available at:
- **Main Service**: `https://your-service-name.onrender.com`
- **Health Check**: `https://your-service-name.onrender.com/health`
- **MCP Endpoint**: `https://your-service-name.onrender.com/mcp`
- **API Docs**: `https://your-service-name.onrender.com/docs` (staging only)

## 🔐 Production Configuration

### Security Settings

```yaml
# In render.yaml
envVars:
  - key: SECURITY_PROFILE
    value: STRICT
  - key: JWT_SECRET_KEY
    generateValue: true  # Render auto-generates secure key
  - key: API_RATE_LIMIT_PER_MINUTE
    value: 100
```

### Database Configuration

**Option 1: Supabase (Recommended)**
```yaml
envVars:
  - key: DATABASE_URL
    value: postgresql://[supabase-connection-string]
  - key: SUPABASE_URL
    value: https://your-project.supabase.co
```

**Option 2: Render PostgreSQL**
```yaml
services:
  - type: pserv
    name: fortunamind-persistent-db
    runtime: postgresql
    plan: starter
```

### Scaling Configuration

```yaml
services:
  - type: web
    # ... other config
    plan: starter     # Free tier: 512MB RAM, 0.1 CPU
    # plan: standard  # Paid tier: 2GB RAM, 1 CPU
    # plan: pro       # High performance: 4GB RAM, 2 CPU
```

## 🚀 Deployment Workflow

### GitHub Actions Workflow

1. **Test Phase**:
   - Runs import tests
   - Validates configuration
   - Checks code quality

2. **Deploy Phase**:
   - Triggers Render deployment via API
   - Waits for deployment completion
   - Runs health checks
   - Updates deployment status

3. **Notification**:
   - Reports success/failure
   - Provides service URLs
   - Updates GitHub deployment status

### Manual Deployment

```bash
# Using Render CLI (install: npm install -g @render/cli)
render services deploy srv-your-service-id

# Using cURL to trigger deployment
curl -X POST "https://api.render.com/v1/services/srv-your-service-id/deploys" \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"clearCache": false}'
```

## 📈 Monitoring and Logs

### View Logs
```bash
# Using Render CLI
render services logs srv-your-service-id --tail

# Via Dashboard
# Go to service → Logs tab
```

### Metrics

Render provides built-in metrics:
- **CPU Usage**
- **Memory Usage** 
- **Request Rate**
- **Response Time**
- **Error Rate**

### Custom Health Checks

The service includes comprehensive health monitoring:
```python
# Health check includes:
{
  "status": "healthy|degraded|unhealthy",
  "components": {
    "storage": "healthy",     # Database connection
    "auth": "healthy",        # Subscription API
    "tools": "2 tools"        # Tool registry status
  }
}
```

## 🐛 Troubleshooting

### Common Issues

**1. Build Failures**
```bash
# Check build logs in Render dashboard
# Common causes:
- Missing requirements.txt dependencies
- Python version mismatch
- Environment variable errors
```

**2. Health Check Failures**
```bash
# Check service logs for:
- Database connection errors
- Missing environment variables
- Supabase configuration issues
```

**3. Port Binding Issues**
```bash
# Ensure your app binds to 0.0.0.0:$PORT
# Render provides PORT environment variable
SERVER_HOST=0.0.0.0
SERVER_PORT=10000  # or use $PORT
```

### Debug Commands

```bash
# Test configuration locally
python -c "
import os
os.environ.update({
    'DATABASE_URL': 'your-db-url',
    'SUPABASE_URL': 'your-supabase-url', 
    'JWT_SECRET_KEY': 'your-secret-key'
})
from src.config import get_settings
print(get_settings())
"

# Test HTTP server startup
SERVER_MODE=http python src/http_server.py
```

### Support Resources

- **Render Status**: [status.render.com](https://status.render.com)
- **Render Docs**: [render.com/docs](https://render.com/docs)
- **GitHub Actions Logs**: Repository → Actions tab
- **Service Logs**: Render Dashboard → Service → Logs

## 🔄 CI/CD Pipeline

The complete pipeline includes:

1. **Code Quality** (GitHub Actions):
   - Linting with ruff
   - Type checking with mypy
   - Security scanning
   - Import validation

2. **Testing**:
   - Unit tests
   - Integration tests
   - Configuration validation

3. **Deployment**:
   - Automatic on main branch
   - Manual trigger available
   - Rolling updates with zero downtime

4. **Post-Deployment**:
   - Health checks
   - Service validation
   - Status reporting

## 📚 Additional Configuration

### Custom Domain

```yaml
# In render.yaml (for custom domains)
services:
  - type: web
    # ... other config
    customDomains:
      - name: api.fortunamind.com
```

### SSL/TLS

Render provides automatic SSL certificates for:
- `*.onrender.com` domains (automatic)
- Custom domains (automatic with DNS verification)

### Backup Strategy

```yaml
# Database backups (if using Render PostgreSQL)
services:
  - type: pserv
    # ... other config
    ipAllowList: []  # Restrict access
```

For Supabase, backups are handled automatically by Supabase.

---

Your FortunaMind Persistent MCP Server is now ready for production deployment on Render with automatic CI/CD! 🚀