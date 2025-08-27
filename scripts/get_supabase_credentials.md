# Supabase Credential Collection Guide

## 🔑 Required Credentials for Production Setup

### **1. Project URL**
- **Location**: Supabase Dashboard → Settings → General → Reference ID
- **Format**: `https://[project-ref].supabase.co`
- **Your URL**: `https://mwoculrtskttpkodlykt.supabase.co`

### **2. API Keys**

#### **Anonymous (Public) Key** ⚠️ *This is what we'll use*
- **Location**: Supabase Dashboard → Settings → API → Project API keys
- **Label**: `anon` / `public`
- **Usage**: Client connections with RLS enforcement
- **Security**: Safe to use in client applications (RLS protected)

#### **Service Role Key** 🚨 *Admin use only*
- **Location**: Supabase Dashboard → Settings → API → Project API keys  
- **Label**: `service_role`
- **Usage**: Admin operations, bypasses RLS
- **Security**: NEVER expose in client applications

### **3. Database Connection String**
- **Location**: Supabase Dashboard → Settings → Database → Connection string
- **Format**: `postgresql://postgres:[PASSWORD]@db.[project-ref].supabase.co:5432/postgres`
- **Your Format**: `postgresql://postgres:[PASSWORD]@db.mwoculrtskttpkodlykt.supabase.co:5432/postgres?sslmode=require`

## 📋 **Credential Collection Checklist**

Please gather these values from your dashboard:

```bash
# Project Information
SUPABASE_PROJECT_REF=mwoculrtskttpkodlykt
SUPABASE_URL=https://mwoculrtskttpkodlykt.supabase.co

# API Keys (get from dashboard)
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # Get from dashboard
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # Get from dashboard

# Database Connection (replace [PASSWORD] with your actual password)
DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@db.mwoculrtskttpkodlykt.supabase.co:5432/postgres?sslmode=require
```

## 🔒 **Security Notes**

### **For Production Environment**
- ✅ Use **SUPABASE_ANON_KEY** for application connections
- ✅ Store credentials in Render's secure environment variables
- ✅ Enable SSL connections (`?sslmode=require`)
- ✅ Keep service role key secure (admin use only)

### **Never Do This**
- ❌ Don't use service role key in application code
- ❌ Don't commit credentials to version control  
- ❌ Don't share credentials in plain text communications
- ❌ Don't use the same credentials for dev/prod

## 📊 **Dashboard Navigation Guide**

### **Getting to API Keys**
1. Go to [supabase.com/dashboard](https://supabase.com/dashboard)
2. Select your project: `mwoculrtskttpkodlykt`
3. Click **Settings** (gear icon) in left sidebar
4. Click **API** in the settings menu
5. Copy the `anon` key (long JWT token starting with `eyJ...`)

### **Getting Database Password**
1. Same dashboard location: **Settings → Database**
2. Look for **Connection string** section
3. The password might be masked - you may need to reset it if you don't have it
4. Click "Generate new password" if needed (⚠️ this will break existing connections)

## 🔧 **Password Reset (If Needed)**

If you don't remember your database password:

1. **Settings → Database → Database password**
2. Click **Generate new password**
3. ⚠️ **Warning**: This will disconnect all existing connections
4. Copy the new password immediately
5. Update all applications using the old password

## ✅ **Verification Steps**

Once you have all credentials, test them:

```bash
# Test database connection
psql "postgresql://postgres:[PASSWORD]@db.mwoculrtskttpkodlykt.supabase.co:5432/postgres?sslmode=require" -c "SELECT version();"

# Test API connection (use curl or browser)
curl "https://mwoculrtskttpkodlykt.supabase.co/rest/v1/" \
  -H "apikey: [ANON_KEY]" \
  -H "Authorization: Bearer [ANON_KEY]"
```

## 📝 **Next Steps After Collection**

1. Store credentials securely (never in plain text files)
2. Set up Render environment variables
3. Run database migrations
4. Apply RLS policies
5. Test complete authentication flow