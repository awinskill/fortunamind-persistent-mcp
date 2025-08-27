# FortunaMind Persistent MCP Server - Deployment Guide

A comprehensive guide for deploying the FortunaMind Persistent MCP Server with Supabase integration and secure environment variable management.

## 🚀 Quick Start

### Prerequisites
- [Python 3.11+](https://python.org)
- [Git](https://git-scm.com)
- [Supabase account](https://supabase.com) with a configured project
- [Render account](https://render.com) for production deployment

### 30-Second Local Deploy
```bash
# 1. Clone and setup
git clone [repository-url]
cd fortunamind-persistent-mcp

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment (see Environment Setup section)
cp .env.example .env
# Edit .env with your Supabase credentials

# 4. Run database migrations
alembic upgrade head

# 5. Test connection
python scripts/test_connection.py

# 6. Run the server
python server.py
```

## 🏗️ Architecture Overview

The Persistent MCP Server extends the standard FortunaMind MCP Server with:

- **Email-Based Identity**: Privacy-first user identification using normalized emails
- **Subscription Management**: Tier-based access control with caching
- **Persistent Storage**: Supabase/PostgreSQL with Row Level Security (RLS)
- **Rate Limiting**: Sliding window rate limiting based on subscription tiers
- **Secure Credentials**: Environment-based secret management

### Component Architecture

```
FortunaMind Persistent MCP Server
├── Email Identity System        # User ID generation from emails
├── Subscription Validator       # Tier validation with caching
├── Rate Limiter                # Sliding window quotas
├── Supabase Storage            # PostgreSQL with RLS
├── Framework Adapter           # Integration layer
└── MCP Server                  # FastMCP-based server
```

## 🔧 Environment Setup

### 1. Supabase Configuration

#### Create Supabase Project
1. Go to [supabase.com](https://supabase.com) and create new project
2. Wait for project to be fully provisioned
3. Navigate to Project Settings → Database

#### Get Connection Details
From your Supabase dashboard:
- **Project URL**: `https://[project-ref].supabase.co`
- **Anon Key**: Project Settings → API → anon/public key
- **Database URL**: Project Settings → Database → Connection string (URI format)

### 2. Environment Variables

#### Local Development (.env)
Create `.env` file in project root:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.your-project-ref.supabase.co:5432/postgres?sslmode=require

# Server Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO
MCP_SERVER_NAME=FortunaMind Persistent MCP Server

# Optional: Redis for advanced caching
REDIS_URL=redis://localhost:6379/0
```

#### Production (Render) Environment Variables

**🔒 CRITICAL: Use Render's secure environment variables - NEVER hardcode secrets.**

In Render Dashboard → Service → Environment:

```bash
# Supabase Configuration (SECURE)
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.your-project-ref.supabase.co:5432/postgres?sslmode=require

# Production Configuration
ENVIRONMENT=production
LOG_LEVEL=WARNING
MCP_SERVER_NAME=FortunaMind Persistent MCP Server (Production)
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# Health Check Configuration
HEALTH_CHECK_ENDPOINT=/health
STATUS_ENDPOINT=/status
```

### 3. Security Best Practices

#### Environment Variable Security
- ✅ **Use Render's encrypted environment variables** for all secrets
- ✅ **Never commit .env files** to version control (.gitignored)
- ✅ **Use separate credentials** for development and production
- ✅ **Rotate credentials regularly** (quarterly recommended)

#### Database Security
- ✅ **Enable Row Level Security (RLS)** on all user data tables
- ✅ **Use SSL connections** (sslmode=require)
- ✅ **Limit database user permissions** (no DROP, CREATE outside migrations)
- ✅ **Regular backups** (Supabase automatic + manual backups)

## 📦 Database Setup

### 1. Run Migrations

#### Local Development
```bash
# Ensure DATABASE_URL is set in .env
alembic upgrade head
```

#### Production (First Deploy)
```bash
# Set DATABASE_URL environment variable
export DATABASE_URL="postgresql://postgres:[PASSWORD]@db.your-project-ref.supabase.co:5432/postgres?sslmode=require"

# Run migrations
alembic upgrade head
```

### 2. Verify Database Setup

```bash
# Test connection and verify tables
python scripts/test_connection.py

# Expected output:
# ✅ PostgreSQL connection successful
# ✅ Found 4 tables: user_subscriptions, journal_entries, user_preferences, storage_records
# ✅ Supabase API connection successful
# ✅ Persistence library initialization successful
```

### 3. Database Schema Overview

#### Core Tables
- **user_subscriptions**: Email-based user subscriptions with tiers
- **journal_entries**: User trading journal entries with metadata
- **user_preferences**: User-specific settings and preferences
- **storage_records**: Generic key-value storage for extensions

#### Row Level Security (RLS)
All user data tables have RLS enabled with policies that ensure:
- Users can only access their own data
- Data is isolated by user_id_hash
- No cross-user data leakage

## 🚀 Deployment Options

### Option 1: Render Deployment (Recommended)

#### 1. Prepare Repository
```bash
# Ensure render.yaml is configured
cat render.yaml

# Verify all dependencies
pip install -r requirements.txt
python -c "import fortunamind_persistence; print('✅ Library imports successfully')"
```

#### 2. Create Render Service
1. Connect your GitHub repository to Render
2. Create new **Web Service**
3. Configure build and start commands:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server.py`

#### 3. Configure Environment Variables
In Render Dashboard → Environment tab, add:

```bash
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=eyJ...
DATABASE_URL=postgresql://postgres:PASSWORD@db.your-project-ref.supabase.co:5432/postgres?sslmode=require
ENVIRONMENT=production
LOG_LEVEL=WARNING
```

#### 4. Deploy and Verify
```bash
# After deployment, test endpoints
curl https://your-render-app.onrender.com/health
curl https://your-render-app.onrender.com/status
```

### Option 2: Local/Docker Development

#### Docker Deployment
```bash
# Build image
docker build -t fortunamind-persistent-mcp .

# Run container with environment file
docker run -p 8000:8000 --env-file .env fortunamind-persistent-mcp

# Or with individual environment variables
docker run -p 8000:8000 \
  -e SUPABASE_URL=https://your-project.supabase.co \
  -e SUPABASE_ANON_KEY=eyJ... \
  -e DATABASE_URL=postgresql://... \
  fortunamind-persistent-mcp
```

#### Direct Python Execution
```bash
# Ensure environment is configured
source .env  # or export environment variables

# Run server directly
python server.py

# Server will start on http://localhost:8000
```

## 🔑 Authentication & Authorization

### Email-Based Identity System

The server uses email-based identity for privacy and API key rotation resilience:

```python
# User identity is derived from normalized email
user_id_hash = sha256(normalize_email("user@example.com")).hexdigest()

# Gmail normalization examples:
"test.user+label@gmail.com" → "testuser@gmail.com" → consistent user_id
"TEST@EXAMPLE.COM" → "test@example.com" → consistent user_id
```

### Subscription-Based Access Control

#### Subscription Key Format
- Pattern: `fm_sub_<identifier>`
- Example: `fm_sub_premium_user_123`
- Similar to API key format for consistency

#### Subscription Tiers
```python
FREE:       100 API calls/hour,   1,000/day,   10,000/month
BASIC:      500 API calls/hour,   5,000/day,   50,000/month
PREMIUM:  1,000 API calls/hour,  10,000/day,  100,000/month
ENTERPRISE: Unlimited access with custom limits
```

### Client Authentication Flow

#### MCP Client Configuration
Clients (Perplexity, Claude Desktop) must provide:

1. **User Email**: For identity and user context
2. **Subscription Key**: For access control and rate limiting
3. **Coinbase Credentials** (optional): For Coinbase API operations

#### Request Headers
```http
POST /mcp
Content-Type: application/json
X-User-Email: trader@example.com
X-Subscription-Key: fm_sub_premium_123
X-Coinbase-API-Key: organizations/org/apiKeys/key
X-Coinbase-API-Secret: -----BEGIN EC PRIVATE KEY-----...

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "store_journal_entry",
    "arguments": {
      "entry": "Bought 0.1 BTC at $45,000"
    }
  }
}
```

## 📊 Monitoring and Health Checks

### Built-in Health Endpoints

#### `/health` - Basic Health Check
```bash
curl https://your-app.onrender.com/health

# Response:
{
  "status": "healthy",
  "timestamp": "2023-12-01T10:00:00Z",
  "uptime_seconds": 3600
}
```

#### `/status` - Detailed System Status
```bash
curl https://your-app.onrender.com/status

# Response:
{
  "overall": "healthy",
  "timestamp": "2023-12-01T10:00:00Z",
  "components": {
    "storage": "healthy",
    "subscription_validator": "healthy",
    "rate_limiter": "healthy",
    "database": "healthy"
  },
  "metrics": {
    "active_users": 150,
    "requests_per_minute": 45,
    "cache_hit_rate": 0.92
  }
}
```

### Application Monitoring

#### Key Metrics to Monitor
- **Response Time**: Target <100ms for read operations
- **Error Rate**: Target <0.1% error rate
- **Cache Hit Rate**: Target >90% for subscription validation
- **Database Connection Pool**: Monitor active/idle connections
- **Rate Limit Usage**: Track tier-based quota utilization

#### Render Monitoring Integration
```bash
# Enable Render's built-in monitoring
# Render automatically monitors:
# - HTTP response codes and latencies  
# - Memory and CPU usage
# - Application crashes and restarts
# - Custom health check endpoints
```

### Alerting Configuration

#### Critical Alerts
- Database connection failures
- Authentication system failures
- Rate limiting system failures
- High error rates (>1% over 5 minutes)

#### Warning Alerts
- High response times (>500ms p95)
- Low cache hit rates (<80%)
- High memory usage (>80%)
- Approaching rate limits

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. Database Connection Errors
```
ERROR: could not connect to server: Connection timed out
```

**Diagnosis:**
```bash
# Test connection directly
python -c "
import os
from sqlalchemy import create_engine
url = os.getenv('DATABASE_URL')
engine = create_engine(url)
conn = engine.connect()
print('✅ Database connection successful')
"
```

**Solutions:**
- Verify `DATABASE_URL` format includes `?sslmode=require`
- Check Supabase project status (not paused)
- Verify network connectivity from deployment environment
- Confirm database password is correct

#### 2. Supabase Authentication Errors
```
ERROR: Invalid API key or insufficient permissions
```

**Solutions:**
- Verify `SUPABASE_ANON_KEY` is the anon/public key, not service role key
- Check that RLS policies allow anon access with proper conditions
- Confirm Supabase project is active and not paused
- Test Supabase connection directly:

```bash
python -c "
from supabase import create_client
import os
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
print('✅ Supabase client created successfully')
"
```

#### 3. Migration Errors
```
ERROR: relation "alembic_version" does not exist
```

**Solutions:**
```bash
# Initialize Alembic (first time setup)
alembic stamp head

# Then run migrations
alembic upgrade head

# Or force recreate
alembic downgrade base
alembic upgrade head
```

#### 4. Environment Variable Issues
```
ERROR: SUPABASE_URL environment variable is required
```

**Solutions:**
- Verify all required environment variables are set
- Check for typos in variable names (case-sensitive)
- Ensure .env file is in correct location for local development
- For Render: verify environment variables in dashboard

#### 5. Rate Limiting Issues
```
ERROR: Rate limit exceeded for tier FREE
```

**Expected Behavior:** This indicates rate limiting is working correctly.

**Solutions:**
- Wait for rate limit window to reset (shown in error)
- Upgrade user's subscription tier
- Check rate limit configuration matches business requirements

### Debug Mode and Logging

#### Enable Debug Logging
```bash
# Local development
export LOG_LEVEL=DEBUG
python server.py

# Or in .env file
LOG_LEVEL=DEBUG
```

#### Application Logs Structure
```
2023-12-01 10:00:00 INFO  [server] Server starting on port 8000
2023-12-01 10:00:01 INFO  [storage] Supabase connection initialized
2023-12-01 10:00:02 DEBUG [auth] User authenticated: user_id=a1b2c3...
2023-12-01 10:00:03 INFO  [rate_limit] Request allowed for user tier=PREMIUM
2023-12-01 10:00:04 DEBUG [storage] Journal entry stored: entry_id=uuid-123
```

### Performance Tuning

#### Database Performance
```bash
# Monitor slow queries
# In Supabase Dashboard → SQL Editor:
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

#### Connection Pool Tuning
```python
# In storage backend configuration
engine = create_engine(
    database_url,
    pool_size=10,           # Concurrent connections
    max_overflow=20,        # Additional connections under load
    pool_pre_ping=True,     # Verify connections before use
    pool_recycle=3600       # Recycle connections hourly
)
```

#### Cache Performance
```bash
# Monitor cache hit rates
python -c "
from fortunamind_persistence.adapters import FrameworkPersistenceAdapter
adapter = FrameworkPersistenceAdapter()
stats = adapter.subscription_validator.cache.get_stats()
print(f'Cache hit rate: {stats[\"hit_rate\"]:.2%}')
"
```

## 📈 Scaling Considerations

### Horizontal Scaling

#### Database Scaling
- **Read Replicas**: Supabase supports read replicas for read-heavy workloads
- **Connection Pooling**: Use PgBouncer for connection management
- **Query Optimization**: Regular analysis of slow queries and indexing

#### Application Scaling
- **Multiple Render Services**: Deploy multiple instances with load balancing
- **Caching Layer**: Add Redis for advanced caching strategies
- **Background Processing**: Separate worker processes for heavy operations

### Vertical Scaling

#### Render Service Scaling
- **CPU/Memory**: Upgrade Render plan for more resources
- **Database**: Upgrade Supabase plan for better performance
- **Monitoring**: Use Render metrics to identify resource bottlenecks

## 🔄 Migration and Updates

### Database Schema Updates

#### Create New Migration
```bash
# Generate migration after model changes
alembic revision --autogenerate -m "Add new feature table"

# Review generated migration file
# Edit if necessary for data migrations

# Apply migration
alembic upgrade head
```

#### Production Migration Strategy
1. **Test migrations** on staging environment
2. **Backup production database** before applying
3. **Apply during maintenance window** if breaking changes
4. **Monitor application** after migration
5. **Have rollback plan** ready

### Application Updates

#### Zero-Downtime Deployment (Render)
```bash
# Render automatically handles zero-downtime deployments:
# 1. Builds new version
# 2. Starts new instances
# 3. Health checks new instances
# 4. Routes traffic to new instances
# 5. Terminates old instances
```

#### Configuration Updates
- Environment variables can be updated without code changes
- Render restarts service when environment variables change
- Monitor health endpoints after configuration changes

## 📋 Production Checklist

### Pre-Deployment
- [ ] **Database migrations** tested and ready
- [ ] **Environment variables** configured in Render
- [ ] **Health checks** passing locally
- [ ] **Tests** passing (unit and integration)
- [ ] **Performance** tested under expected load
- [ ] **Security review** completed

### Post-Deployment
- [ ] **Health endpoints** responding correctly
- [ ] **Database connections** stable
- [ ] **Rate limiting** working as expected
- [ ] **Authentication** flow tested
- [ ] **Monitoring** alerts configured
- [ ] **Log aggregation** working
- [ ] **Backup strategy** verified

### Ongoing Maintenance
- [ ] **Weekly** health check review
- [ ] **Monthly** performance analysis
- [ ] **Quarterly** security review
- [ ] **Quarterly** credential rotation
- [ ] **Annual** disaster recovery testing

## 🆘 Emergency Procedures

### Service Outage Response

#### 1. Immediate Assessment
```bash
# Check service status
curl https://your-app.onrender.com/health

# Check Render service status
# Dashboard → Service → Logs

# Check Supabase status
# Supabase Dashboard → Project Health
```

#### 2. Common Recovery Actions
```bash
# Restart Render service
# Render Dashboard → Service → Manual Deploy

# Check and fix environment variables
# Render Dashboard → Environment

# Rollback to previous deployment
# Render Dashboard → Deployments → Rollback
```

### Database Emergency Recovery

#### Connection Issues
1. Check Supabase project status
2. Verify connection string format
3. Test from different environment
4. Contact Supabase support if needed

#### Data Issues
1. Check recent migrations
2. Review application logs for data corruption
3. Restore from backup if necessary
4. Implement data validation fixes

### Security Incident Response

#### Credential Compromise
1. **Immediately** rotate compromised credentials
2. Update environment variables in Render
3. Force restart of all services
4. Review access logs for suspicious activity
5. Update documentation with incident details

#### Access Pattern Anomalies
1. Review rate limiting logs
2. Check for unusual authentication patterns
3. Temporarily increase rate limits if needed
4. Investigate and block suspicious sources

---

## 📞 Support and Resources

### Documentation
- **Architecture Guide**: `docs/persistence-library.md`
- **API Reference**: `docs/api-reference.md`
- **Development Guide**: `README.md`

### External Resources
- **Supabase Documentation**: [supabase.com/docs](https://supabase.com/docs)
- **Render Documentation**: [render.com/docs](https://render.com/docs)
- **FastMCP Documentation**: [fastmcp.dev](https://fastmcp.dev)

### Monitoring and Alerting
- **Render Dashboard**: Application metrics and logs
- **Supabase Dashboard**: Database metrics and health
- **Health Endpoints**: Real-time service status

This deployment guide ensures secure, scalable, and maintainable deployment of the FortunaMind Persistent MCP Server with proper credential management and monitoring capabilities.