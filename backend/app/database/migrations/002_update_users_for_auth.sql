-- ====================================================================
-- Authentication System Update Migration
-- Bharath's Quality-First Implementation
--
-- Updates existing users table to support JWT authentication while
-- preserving existing data and maintaining backward compatibility.
--
-- Features:
-- - Adds missing authentication fields to existing users table
-- - Creates refresh_tokens table with proper foreign key relationships
-- - Preserves existing user data
-- - Adds proper indexes and constraints
-- ====================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ====================================================================
-- UPDATE EXISTING USERS TABLE
-- ====================================================================

-- Add missing columns to existing users table
DO $$
BEGIN
    -- Add preferences column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'preferences') THEN
        ALTER TABLE users ADD COLUMN preferences JSONB NOT NULL DEFAULT '{
            "language": "en",
            "theme": "light",
            "notifications": {
                "email": true,
                "push": true,
                "sparky": true
            }
        }'::jsonb;
    END IF;
    
    -- Add email verification column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'is_email_verified') THEN
        ALTER TABLE users ADD COLUMN is_email_verified BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
    
    -- Add avatar URL column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'avatar_url') THEN
        ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500);
    END IF;
    
    -- Add last login timestamp if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'last_login_at') THEN
        ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP WITH TIME ZONE;
    END IF;
    
    -- Update timestamps to include timezone if needed
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'users' AND column_name = 'created_at' 
               AND data_type = 'timestamp without time zone') THEN
        ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'users' AND column_name = 'updated_at' 
               AND data_type = 'timestamp without time zone') THEN
        ALTER TABLE users ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE;
    END IF;
END
$$;

-- Add constraints to users table
DO $$
BEGIN
    -- Add email validation constraint if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints 
                   WHERE constraint_name = 'valid_email') THEN
        ALTER TABLE users ADD CONSTRAINT valid_email CHECK (
            email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
            AND LENGTH(email) >= 5
            AND LENGTH(email) <= 255
        );
    END IF;
    
    -- Add role validation constraint if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints 
                   WHERE constraint_name = 'valid_role_auth') THEN
        ALTER TABLE users ADD CONSTRAINT valid_role_auth CHECK (
            role IN ('admin', 'manager', 'user')
        );
    END IF;
    
    -- Add avatar URL validation constraint if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints 
                   WHERE constraint_name = 'valid_avatar_url') THEN
        ALTER TABLE users ADD CONSTRAINT valid_avatar_url CHECK (
            avatar_url IS NULL OR (
                LENGTH(avatar_url) <= 500
                AND avatar_url ~* '^https?://'
            )
        );
    END IF;
END
$$;

-- ====================================================================
-- CREATE REFRESH TOKENS TABLE
-- ====================================================================

CREATE TABLE IF NOT EXISTS refresh_tokens (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- User relationship (using integer ID to match existing users table)
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Token data (hashed for security)
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    
    -- Expiration and status
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Metadata for security tracking
    user_agent VARCHAR(500),
    ip_address INET,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_expiration CHECK (
        expires_at > created_at
    )
);

-- ====================================================================
-- CREATE INDEXES FOR PERFORMANCE
-- ====================================================================

-- Users table indexes (add only if they don't exist)
DO $$
BEGIN
    -- Email index
    IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_users_email_auth') THEN
        CREATE INDEX idx_users_email_auth ON users(email);
    END IF;
    
    -- Role index
    IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_users_role_auth') THEN
        CREATE INDEX idx_users_role_auth ON users(role);
    END IF;
    
    -- Active users index
    IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_users_active_auth') THEN
        CREATE INDEX idx_users_active_auth ON users(is_active);
    END IF;
    
    -- Last login index
    IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_users_last_login_auth') THEN
        CREATE INDEX idx_users_last_login_auth ON users(last_login_at);
    END IF;
    
    -- Composite index for email + active
    IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_users_email_active_auth') THEN
        CREATE INDEX idx_users_email_active_auth ON users(email, is_active) WHERE is_active = TRUE;
    END IF;
END
$$;

-- Refresh tokens table indexes
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_refresh_tokens_user_id') THEN
        CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_refresh_tokens_hash') THEN
        CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_refresh_tokens_expires_at') THEN
        CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_refresh_tokens_valid') THEN
        CREATE INDEX idx_refresh_tokens_valid ON refresh_tokens(user_id, is_revoked, expires_at)
        WHERE is_revoked = FALSE;
    END IF;
END
$$;

-- ====================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- ====================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for users table (drop and recreate to ensure it exists)
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ====================================================================
-- UTILITY FUNCTIONS
-- ====================================================================

-- Function to clean up expired refresh tokens
CREATE OR REPLACE FUNCTION cleanup_expired_refresh_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM refresh_tokens 
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Log cleanup if any tokens were deleted
    IF deleted_count > 0 THEN
        RAISE NOTICE 'Cleaned up % expired refresh tokens', deleted_count;
    END IF;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ====================================================================
-- UPDATE EXISTING DATA
-- ====================================================================

-- Set default preferences for existing users without preferences
UPDATE users 
SET preferences = '{
    "language": "en",
    "theme": "light",
    "notifications": {
        "email": true,
        "push": true,
        "sparky": true
    }
}'::jsonb
WHERE preferences IS NULL;

-- Ensure all users have valid roles
UPDATE users 
SET role = 'user' 
WHERE role NOT IN ('admin', 'manager', 'user') OR role IS NULL;

-- Set email verification to false for existing users
UPDATE users 
SET is_email_verified = FALSE 
WHERE is_email_verified IS NULL;

-- ====================================================================
-- CREATE DEFAULT ADMIN USER (if doesn't exist)
-- ====================================================================

-- Create default admin user (password: Admin123!)
-- Note: In production, this should be changed immediately
INSERT INTO users (
    username,
    email,
    password_hash,
    first_name,
    last_name,
    role,
    is_active,
    is_email_verified,
    created_at,
    updated_at
) VALUES (
    'admin',
    'admin@pconfig.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeEiKTQ0QQYNGKd.K',  -- Admin123!
    'System',
    'Administrator',
    'admin',
    TRUE,
    TRUE,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (email) DO NOTHING;

-- Create sample user for testing (password: User123!)
-- Note: Remove in production
INSERT INTO users (
    username,
    email,
    password_hash,
    first_name,
    last_name,
    role,
    is_active,
    is_email_verified,
    created_at,
    updated_at
) VALUES (
    'testuser',
    'user@pconfig.com',
    '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',  -- User123!
    'Test',
    'User',
    'user',
    TRUE,
    TRUE,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (email) DO NOTHING;

-- ====================================================================
-- VERIFICATION AND FINAL CHECKS
-- ====================================================================

-- Verify migration completed successfully
DO $$
DECLARE
    users_count INTEGER;
    admin_count INTEGER;
    tokens_table_exists BOOLEAN;
BEGIN
    -- Check users table
    SELECT COUNT(*) INTO users_count FROM users;
    
    -- Check admin users
    SELECT COUNT(*) INTO admin_count FROM users WHERE role = 'admin';
    
    -- Check refresh_tokens table exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'refresh_tokens'
    ) INTO tokens_table_exists;
    
    -- Verification
    IF users_count = 0 THEN
        RAISE EXCEPTION 'No users found in users table';
    END IF;
    
    IF admin_count = 0 THEN
        RAISE EXCEPTION 'No admin users found';
    END IF;
    
    IF NOT tokens_table_exists THEN
        RAISE EXCEPTION 'Refresh tokens table was not created';
    END IF;
    
    -- Success message
    RAISE NOTICE 'Authentication system migration completed successfully!';
    RAISE NOTICE 'Users table updated with % users', users_count;
    RAISE NOTICE 'Admin users: %', admin_count;
    RAISE NOTICE 'Refresh tokens table created';
    RAISE NOTICE 'Default admin: admin@pconfig.com (password: Admin123!)';
    RAISE NOTICE 'Test user: user@pconfig.com (password: User123!)';
    RAISE NOTICE 'IMPORTANT: Change default passwords immediately in production!';
END
$$;