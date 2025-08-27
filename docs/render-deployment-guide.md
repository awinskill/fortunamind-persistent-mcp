# FortunaMind Persistent MCP Server - Render Deployment Guide

Step-by-step guide to deploy the FortunaMind Persistent MCP Server to Render with secure environment variables.

## 🚀 **Quick Deploy (5 Minutes)**

### **Step 1: Connect Repository to Render**

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click "New +"** → **Web Service**
3. **Connect GitHub Repository**:
   - Repository: `awinskill/fortunamind-persistent-mcp` (or your fork)
   - Branch: `main`

### **Step 2: Configure Basic Settings**

- **Name**: `fortunamind-persistent-mcp`
- **Runtime**: `Python 3`
- **Build Command**: Leave empty (will use render.yaml)
- **Start Command**: Leave empty (will use render.yaml)
- **Plan**: Start with **Starter** ($7/month), upgrade as needed

### **Step 3: Set Environment Variables**

⚠️ **CRITICAL**: Set these as **encrypted environment variables** in Render:

#### **Required Environment Variables**

```bash
# Supabase Configuration
SUPABASE_URL=https://mwoculrtskttpkodlykt.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im13b2N1bHJ0c2t0dHBrb2RseWt0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUwMjM1MTUsImV4cCI6MjA3MDU5OTUxNX0.WS8N77SakAIUzSHJbOZQ6Y8NCJnri3Vm52YSSltplmo
DATABASE_URL=postgresql://postgres:F745wvnAPY50t@db.mwoculrtskttpkodlykt.supabase.co:5432/postgres?sslmode=require

# Server Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
MCP_SERVER_NAME=FortunaMind Persistent MCP Server (Render)
```

#### **How to Set Environment Variables in Render**

1. **In Render Dashboard** → Your Service → **Environment** tab
2. **Click "Add Environment Variable"** for each one:
   - **Key**: `SUPABASE_URL`
   - **Value**: `https://mwoculrtskttpkodlykt.supabase.co`
   - ✅ **Check "Secret"** (encrypts the value)
3. **Repeat for all variables above**

### **Step 4: Deploy**

1. **Click "Create Web Service"**
2. **Watch the build logs** - should see:
   - 🔧 Installing dependencies...
   - 🗄️ Running database migrations...
   - ✅ Database migrations completed
   - 🧪 Testing persistence library...
   - ✅ Persistence library modules imported successfully
3. **Deployment should complete** in 3-5 minutes

### **Step 5: Verify Deployment**

Test your endpoints:

```bash
# Health check
curl https://your-service-name.onrender.com/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2023-12-01T10:00:00.000000",
  "uptime_seconds": 123.45,
  "server": "FortunaMind Persistent MCP Server (Render)"
}

# Detailed status
curl https://your-service-name.onrender.com/status

# Expected response:
{
  "overall": "healthy",
  "timestamp": "2023-12-01T10:00:00.000000",
  "components": {
    "storage": "healthy",
    "subscription_validator": "healthy",
    "rate_limiter": "healthy"
  }
}
```

## 📋 **Detailed Configuration Guide**

### **Environment Variables Reference**

#### **Required (Security Critical)**
```bash
SUPABASE_URL                # Your Supabase project URL
SUPABASE_ANON_KEY          # Supabase anon/public API key
DATABASE_URL               # PostgreSQL connection string
```

#### **Server Configuration**
```bash
ENVIRONMENT=production     # Deployment environment
LOG_LEVEL=INFO            # Logging verbosity (DEBUG, INFO, WARNING, ERROR)
MCP_SERVER_NAME           # Server identification string
PORT=8000                 # Port (auto-set by Render)
```

#### **Optional Advanced Configuration**
```bash
# Database Connection Pool
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30

# Rate Limiting Override
DEFAULT_RATE_LIMIT_HOUR=100
DEFAULT_RATE_LIMIT_DAY=1000

# Feature Flags
ENABLE_DEBUG_ENDPOINTS=false    # Set true for development only
```

### **Custom Domain Setup (Optional)**

If you want a custom domain:

1. **Render Dashboard** → Your Service → **Settings**
2. **Custom Domains** → **Add Custom Domain**
3. **Add CNAME record** in your DNS:
   ```
   CNAME api your-service-name.onrender.com
   ```
4. **Verify domain** in Render dashboard
5. **SSL certificate** is automatic

### **Scaling Configuration**

#### **Vertical Scaling (More Resources)**
- **Starter Plan**: 0.5 CPU, 512 MB RAM - Good for testing
- **Standard Plan**: 1 CPU, 2 GB RAM - Recommended for production
- **Pro Plan**: 2 CPU, 4 GB RAM - High traffic

#### **Horizontal Scaling (Multiple Instances)**
Available on Standard+ plans:
- **Auto-scaling**: Based on CPU/memory usage
- **Manual scaling**: Set min/max instances

## 🔧 **API Usage Examples**

### **Store Journal Entry**

```bash
curl -X POST https://your-service.onrender.com/store_journal_entry \
  -H "Content-Type: application/json" \
  -H "X-User-Email: trader@example.com" \
  -H "X-Subscription-Key: fm_sub_premium123" \
  -d '{
    "entry": "Bought 0.1 BTC at $45,000. Strong technical breakout above resistance.",
    "metadata": {
      "symbol": "BTC",
      "action": "BUY",
      "amount": 0.1,
      "price": 45000.0,
      "confidence": "high"
    }
  }'
```

### **Get Journal Entries**

```bash
curl -X GET "https://your-service.onrender.com/get_journal_entries?limit=5" \
  -H "X-User-Email: trader@example.com" \
  -H "X-Subscription-Key: fm_sub_premium123"
```

### **Get User Statistics**

```bash
curl -X GET https://your-service.onrender.com/user_stats \
  -H "X-User-Email: trader@example.com" \
  -H "X-Subscription-Key: fm_sub_premium123"
```

### **Validate Subscription**

```bash
curl -X POST https://your-service.onrender.com/validate_subscription \
  -H "X-User-Email: trader@example.com" \
  -H "X-Subscription-Key: fm_sub_premium123"
```

## 🚨 **Troubleshooting**

### **Common Deployment Issues**

#### **Build Fails with "Import Error"**
```
❌ Import error: No module named 'fortunamind_persistence'
```

**Solution**: Check that `src/` directory is included in your repository.

#### **Database Migration Fails**
```
❌ Database connection failed: could not connect to server
```

**Solutions**:
1. Verify `DATABASE_URL` is set correctly in Render environment variables
2. Ensure Supabase project is active (not paused)
3. Check that SSL mode is included: `?sslmode=require`

#### **Server Starts But Health Check Fails**
```
❌ Server startup failed: Missing environment variables
```

**Solutions**:
1. Verify all required environment variables are set
2. Check environment variable names (case-sensitive)
3. Ensure variables are marked as "Secret" in Render

#### **403/404 Errors on API Calls**
```
❌ 400 Bad Request: Missing required headers
```

**Solutions**:
1. Include required headers: `X-User-Email` and `X-Subscription-Key`
2. Verify subscription key format: `fm_sub_*`
3. Check that email format is valid

### **Performance Issues**

#### **Slow Response Times**
- Upgrade to Standard plan (more CPU/memory)
- Check database connection pool settings
- Enable connection pooling in Supabase

#### **Rate Limiting Errors**
- Check user's subscription tier and limits
- Verify rate limiting configuration
- Consider upgrading user's subscription

### **Database Issues**

#### **RLS Policy Errors**
```
❌ new row violates row-level security policy
```

**Solutions**:
1. Verify RLS policies are applied in Supabase
2. Check that user context is set correctly
3. Ensure Supabase anon key has correct permissions

#### **Connection Pool Exhaustion**
- Reduce `DATABASE_POOL_SIZE` if needed
- Check for connection leaks in application code
- Upgrade database plan in Supabase

## 📊 **Monitoring and Alerts**

### **Built-in Monitoring**

Render provides automatic monitoring for:
- **Response times and status codes**
- **Memory and CPU usage**
- **Error rates and crashes**
- **Custom health check endpoints**

### **Health Check Endpoints**

Monitor these endpoints:
- `/health` - Basic server health
- `/status` - Detailed component status

### **Log Monitoring**

```bash
# View live logs in Render dashboard
# Or use Render CLI:
render logs -f your-service-name
```

### **Custom Alerting**

Set up alerts in Render dashboard:
- **Health check failures**
- **High error rates (>5%)**
- **High response times (>500ms)**
- **Memory usage (>80%)**

## 🔄 **Updates and Maintenance**

### **Automatic Deployments**

- **Push to main branch** → Automatic deployment
- **Build and test** → Automatic verification
- **Health checks** → Automatic rollback if failed

### **Manual Deployments**

1. **Render Dashboard** → Your Service
2. **Manual Deploy** → Choose commit/branch
3. **Deploy** → Monitor build logs

### **Rollback Procedure**

1. **Render Dashboard** → Your Service → **Deployments**
2. **Find last working deployment**
3. **"Rollback to this deploy"**
4. **Confirm rollback**

### **Database Migrations**

Future schema changes:
```bash
# Create migration locally
alembic revision --autogenerate -m "Add new feature"

# Test migration locally
DATABASE_URL="your-local-db" alembic upgrade head

# Push to GitHub - Render will run migration automatically
git push origin main
```

## 🔒 **Security Best Practices**

### **Environment Variables**
- ✅ Always mark secrets as "Secret" in Render
- ✅ Use different credentials for dev/staging/production
- ✅ Rotate credentials quarterly
- ✅ Never commit real credentials to version control

### **Access Control**
- ✅ Restrict CORS origins in production
- ✅ Use strong subscription keys
- ✅ Implement rate limiting per user
- ✅ Monitor for suspicious activity

### **Database Security**
- ✅ Use SSL connections (already configured)
- ✅ Apply RLS policies (required)
- ✅ Regular backups (Supabase automatic)
- ✅ Monitor access patterns

## 📞 **Support and Resources**

### **Render Support**
- **Documentation**: https://render.com/docs
- **Status Page**: https://status.render.com
- **Support**: https://help.render.com

### **FortunaMind Support**
- **GitHub Issues**: Repository issue tracker
- **Documentation**: `docs/` directory
- **Health Endpoints**: `/health` and `/status`

### **Useful Commands**

```bash
# Check service status
curl https://your-service.onrender.com/health

# Monitor logs (requires Render CLI)
render logs -f your-service-name

# View environment variables
render env list your-service-name

# Manual deploy
render deploy your-service-name
```

---

## 🎉 **Deployment Complete!**

Your FortunaMind Persistent MCP Server should now be running on Render with:

✅ **Secure environment variables**  
✅ **Automatic database migrations**  
✅ **Health monitoring endpoints**  
✅ **SSL/TLS encryption**  
✅ **Auto-scaling capabilities**  
✅ **Row Level Security (RLS)**  

**Next Steps**: Test the API endpoints and integrate with your MCP clients!

**Your server is ready to handle production traffic with privacy-preserving, tier-based persistent storage.** 🚀