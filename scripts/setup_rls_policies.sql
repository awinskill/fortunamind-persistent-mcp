-- Row Level Security (RLS) Policies for FortunaMind Persistent MCP
-- 
-- This script sets up comprehensive RLS policies to ensure:
-- 1. User data isolation (users can only access their own data)
-- 2. Secure anon key access (no direct user_id_hash exposure)
-- 3. Proper authentication flow

-- =============================================================================
-- TRADING JOURNAL - User's trading journal data
-- =============================================================================

-- Enable RLS on trading_journal
ALTER TABLE trading_journal ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own journal entries
-- Uses user_id from JWT claim or direct comparison
CREATE POLICY "Users can view own journal entries" ON trading_journal
    FOR SELECT USING (
        user_id = auth.jwt() ->> 'user_id'
        OR user_id = current_setting('app.user_id', true)
    );

-- Policy: Users can insert their own journal entries
CREATE POLICY "Users can insert own journal entries" ON trading_journal
    FOR INSERT WITH CHECK (
        user_id = auth.jwt() ->> 'user_id'
        OR user_id = current_setting('app.user_id', true)
    );

-- Policy: Users can update their own journal entries
CREATE POLICY "Users can update own journal entries" ON trading_journal
    FOR UPDATE USING (
        user_id = auth.jwt() ->> 'user_id'
        OR user_id = current_setting('app.user_id', true)
    );

-- Policy: Users can delete their own journal entries
CREATE POLICY "Users can delete own journal entries" ON trading_journal
    FOR DELETE USING (
        user_id = auth.jwt() ->> 'user_id'
        OR user_id = current_setting('app.user_id', true)
    );

-- =============================================================================
-- USER PREFERENCES - User settings and configuration
-- =============================================================================

-- Enable RLS on user_preferences
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Policy: Users can manage their own preferences
CREATE POLICY "Users can manage own preferences" ON user_preferences
    FOR ALL USING (
        user_id = auth.jwt() ->> 'user_id'
        OR user_id = current_setting('app.user_id', true)
    );

-- =============================================================================
-- STORAGE RECORDS - Generic storage for extensions
-- =============================================================================

-- Enable RLS on storage_records
ALTER TABLE storage_records ENABLE ROW LEVEL SECURITY;

-- Policy: Users can manage their own storage records
CREATE POLICY "Users can manage own storage records" ON storage_records
    FOR ALL USING (
        user_id = auth.jwt() ->> 'user_id'
        OR user_id = current_setting('app.user_id', true)
    );

-- =============================================================================
-- USER SUBSCRIPTIONS - Subscription and tier management
-- =============================================================================

-- Enable RLS on user_subscriptions
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view subscription info (read-only for users)
-- Note: This table is primarily managed by the application, not directly by users
CREATE POLICY "Users can view own subscription" ON user_subscriptions
    FOR SELECT USING (
        -- Allow access if the user_id_hash matches the email hash
        -- This is calculated by the application layer
        email = lower(trim(auth.jwt() ->> 'email'))
        OR email = current_setting('app.user_email', true)
    );

-- Policy: Service role can manage all subscriptions (for admin operations)
CREATE POLICY "Service role can manage subscriptions" ON user_subscriptions
    FOR ALL USING (auth.role() = 'service_role');

-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Function to set user context (called by application)
CREATE OR REPLACE FUNCTION set_user_context(user_id_param text, user_email_param text)
RETURNS void AS $$
BEGIN
    -- Set the user context for RLS policies
    PERFORM set_config('app.user_id', user_id_param, true);
    PERFORM set_config('app.user_email', lower(trim(user_email_param)), true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to clear user context (called after operations)
CREATE OR REPLACE FUNCTION clear_user_context()
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.user_id', '', true);
    PERFORM set_config('app.user_email', '', true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- SECURITY FUNCTIONS
-- =============================================================================

-- Function to validate user_id format (hash string)
CREATE OR REPLACE FUNCTION is_valid_user_id(user_id text)
RETURNS boolean AS $$
BEGIN
    RETURN user_id ~ '^[a-zA-Z0-9_-]{8,64}$';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to validate email format
CREATE OR REPLACE FUNCTION is_valid_email(email text)
RETURNS boolean AS $$
BEGIN
    RETURN email ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =============================================================================
-- PERFORMANCE INDEXES
-- =============================================================================

-- Indexes for efficient RLS policy enforcement
CREATE INDEX IF NOT EXISTS idx_trading_journal_user_id ON trading_journal(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_journal_created_at ON trading_journal(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_key ON user_preferences(preference_key);

CREATE INDEX IF NOT EXISTS idx_storage_records_user_id ON storage_records(user_id);
CREATE INDEX IF NOT EXISTS idx_storage_records_type ON storage_records(record_type);

CREATE INDEX IF NOT EXISTS idx_user_subscriptions_email ON user_subscriptions(email);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(status);

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Query to verify RLS is enabled on all tables
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE tablename IN ('trading_journal', 'user_preferences', 'storage_records', 'user_subscriptions')
AND schemaname = 'public';

-- Query to list all RLS policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename IN ('trading_journal', 'user_preferences', 'storage_records', 'user_subscriptions')
ORDER BY tablename, policyname;