-- Row Level Security (RLS) Policies for FortunaMind Persistent MCP
-- 
-- This script sets up comprehensive RLS policies to ensure:
-- 1. User data isolation (users can only access their own data)
-- 2. Secure anon key access (no direct user_id_hash exposure)
-- 3. Proper authentication flow

-- =============================================================================
-- JOURNAL ENTRIES - User's trading journal data
-- =============================================================================

-- Enable RLS on journal_entries
ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own journal entries
-- Uses user_id_hash from JWT claim or direct comparison
CREATE POLICY "Users can view own journal entries" ON journal_entries
    FOR SELECT USING (
        user_id_hash = auth.jwt() ->> 'user_id_hash'
        OR user_id_hash = current_setting('app.user_id_hash', true)
    );

-- Policy: Users can insert their own journal entries
CREATE POLICY "Users can insert own journal entries" ON journal_entries
    FOR INSERT WITH CHECK (
        user_id_hash = auth.jwt() ->> 'user_id_hash'
        OR user_id_hash = current_setting('app.user_id_hash', true)
    );

-- Policy: Users can update their own journal entries
CREATE POLICY "Users can update own journal entries" ON journal_entries
    FOR UPDATE USING (
        user_id_hash = auth.jwt() ->> 'user_id_hash'
        OR user_id_hash = current_setting('app.user_id_hash', true)
    );

-- Policy: Users can delete their own journal entries
CREATE POLICY "Users can delete own journal entries" ON journal_entries
    FOR DELETE USING (
        user_id_hash = auth.jwt() ->> 'user_id_hash'
        OR user_id_hash = current_setting('app.user_id_hash', true)
    );

-- =============================================================================
-- USER PREFERENCES - User settings and configuration
-- =============================================================================

-- Enable RLS on user_preferences
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Policy: Users can manage their own preferences
CREATE POLICY "Users can manage own preferences" ON user_preferences
    FOR ALL USING (
        user_id_hash = auth.jwt() ->> 'user_id_hash'
        OR user_id_hash = current_setting('app.user_id_hash', true)
    );

-- =============================================================================
-- STORAGE RECORDS - Generic storage for extensions
-- =============================================================================

-- Enable RLS on storage_records
ALTER TABLE storage_records ENABLE ROW LEVEL SECURITY;

-- Policy: Users can manage their own storage records
CREATE POLICY "Users can manage own storage records" ON storage_records
    FOR ALL USING (
        user_id_hash = auth.jwt() ->> 'user_id_hash'
        OR user_id_hash = current_setting('app.user_id_hash', true)
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
CREATE OR REPLACE FUNCTION set_user_context(user_id_hash_param text, user_email_param text)
RETURNS void AS $$
BEGIN
    -- Set the user context for RLS policies
    PERFORM set_config('app.user_id_hash', user_id_hash_param, true);
    PERFORM set_config('app.user_email', lower(trim(user_email_param)), true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to clear user context (called after operations)
CREATE OR REPLACE FUNCTION clear_user_context()
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.user_id_hash', '', true);
    PERFORM set_config('app.user_email', '', true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- SECURITY FUNCTIONS
-- =============================================================================

-- Function to validate user_id_hash format (SHA-256 hex string)
CREATE OR REPLACE FUNCTION is_valid_user_id_hash(hash text)
RETURNS boolean AS $$
BEGIN
    RETURN hash ~ '^[a-f0-9]{64}$';
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
CREATE INDEX IF NOT EXISTS idx_journal_entries_user_id_hash ON journal_entries(user_id_hash);
CREATE INDEX IF NOT EXISTS idx_journal_entries_created_at ON journal_entries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_journal_entries_entry_type ON journal_entries(entry_type);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id_hash ON user_preferences(user_id_hash);
CREATE INDEX IF NOT EXISTS idx_user_preferences_key ON user_preferences(preference_key);

CREATE INDEX IF NOT EXISTS idx_storage_records_user_id_hash ON storage_records(user_id_hash);
CREATE INDEX IF NOT EXISTS idx_storage_records_key ON storage_records(record_key);

CREATE INDEX IF NOT EXISTS idx_user_subscriptions_email ON user_subscriptions(email);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(status);

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Query to verify RLS is enabled on all tables
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE tablename IN ('journal_entries', 'user_preferences', 'storage_records', 'user_subscriptions')
AND schemaname = 'public';

-- Query to list all RLS policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename IN ('journal_entries', 'user_preferences', 'storage_records', 'user_subscriptions')
ORDER BY tablename, policyname;