-- ====================================================================
-- Authentication System Database Migration
-- Bharath's Quality-First Implementation
--
-- Creates user tables with comprehensive security, validation, and indexing
-- for the Pconfig Recommender API authentication system.
--
-- Features:
-- - UUID primary keys for security
-- - Email validation with constraints
-- - Proper indexing for performance
-- - Role-based access control
-- - Refresh token management
-- - Audit trail with timestamps
-- ====================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ====================================================================
-- USERS TABLE
-- ====================================================================

CREATE TABLE IF NOT EXISTS users (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    
    -- Authentication
    password_hash VARCHAR(255) NOT NULL,
    
    -- Profile information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    
    -- Role and permissions
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    
    -- User preferences (JSON)
    preferences JSONB NOT NULL DEFAULT '{
        "language": "en",
        "theme": "light",
        "notifications": {
            "email": true,
            "push": true,
            "sparky": true
        }
    }'::jsonb,
    
    -- Account status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Profile
    avatar_url VARCHAR(500),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT valid_email CHECK (
        email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
        AND LENGTH(email) >= 5
        AND LENGTH(email) <= 255
    ),
    CONSTRAINT valid_names CHECK (
        LENGTH(TRIM(first_name)) >= 1 
        AND LENGTH(TRIM(last_name)) >= 1
        AND LENGTH(first_name) <= 100
        AND LENGTH(last_name) <= 100
    ),
    CONSTRAINT valid_role CHECK (
        role IN ('admin', 'manager', 'user')
    ),
    CONSTRAINT valid_avatar_url CHECK (
        avatar_url IS NULL OR (
            LENGTH(avatar_url) <= 500
            AND avatar_url ~* '^https?://'
        )
    )
);

-- ====================================================================
-- REFRESH TOKENS TABLE
-- ====================================================================

CREATE TABLE IF NOT EXISTS refresh_tokens (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- User relationship
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
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
-- INDEXES FOR PERFORMANCE
-- ====================================================================

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login_at);

-- Composite index for active user lookups
CREATE INDEX IF NOT EXISTS idx_users_email_active ON users(email, is_active) 
WHERE is_active = TRUE;

-- Refresh tokens table indexes
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash ON refresh_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_created_at ON refresh_tokens(created_at);

-- Composite index for valid tokens
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_valid ON refresh_tokens(user_id, is_revoked, expires_at)
WHERE is_revoked = FALSE;

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

-- Trigger for users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ====================================================================
-- SECURITY FUNCTIONS
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
-- INITIAL DATA
-- ====================================================================

-- Create default admin user (password: Admin123!)
-- Note: In production, this should be changed immediately
INSERT INTO users (
    email,
    password_hash,
    first_name,
    last_name,
    role,
    is_active,
    is_email_verified
) VALUES (
    'admin@pconfig.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeEiKTQ0QQYNGKd.K',  -- Admin123!
    'System',
    'Administrator',
    'admin',
    TRUE,
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- Create sample user for testing (password: User123!)
-- Note: Remove in production
INSERT INTO users (
    email,
    password_hash,
    first_name,
    last_name,
    role,
    is_active,
    is_email_verified
) VALUES (
    'user@pconfig.com',
    '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',  -- User123!
    'Test',
    'User',
    'user',
    TRUE,
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- ====================================================================
-- COMMENTS AND DOCUMENTATION
-- ====================================================================

-- Table comments
COMMENT ON TABLE users IS 'User accounts with authentication and profile information';
COMMENT ON TABLE refresh_tokens IS 'JWT refresh tokens for secure session management';

-- Column comments for users table
COMMENT ON COLUMN users.id IS 'Unique user identifier (UUID)';
COMMENT ON COLUMN users.email IS 'User email address (unique, validated)';
COMMENT ON COLUMN users.password_hash IS 'Bcrypt hashed password (never store plain text)';
COMMENT ON COLUMN users.role IS 'User role: admin, manager, or user';
COMMENT ON COLUMN users.preferences IS 'User preferences stored as JSON';
COMMENT ON COLUMN users.is_active IS 'Whether user account is active';
COMMENT ON COLUMN users.is_email_verified IS 'Whether email address has been verified';

-- Column comments for refresh_tokens table
COMMENT ON COLUMN refresh_tokens.user_id IS 'Reference to users table';
COMMENT ON COLUMN refresh_tokens.token_hash IS 'SHA256 hash of refresh token';
COMMENT ON COLUMN refresh_tokens.expires_at IS 'When token expires';
COMMENT ON COLUMN refresh_tokens.is_revoked IS 'Whether token has been revoked';
COMMENT ON COLUMN refresh_tokens.user_agent IS 'Client user agent string';
COMMENT ON COLUMN refresh_tokens.ip_address IS 'Client IP address';

-- ====================================================================
-- VERIFICATION QUERIES
-- ====================================================================

-- Verify tables were created successfully
DO $$
BEGIN
    -- Check users table
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        RAISE EXCEPTION 'Users table was not created successfully';
    END IF;
    
    -- Check refresh_tokens table
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'refresh_tokens') THEN
        RAISE EXCEPTION 'Refresh_tokens table was not created successfully';
    END IF;
    
    -- Check admin user was created
    IF NOT EXISTS (SELECT 1 FROM users WHERE email = 'admin@pconfig.com') THEN
        RAISE EXCEPTION 'Default admin user was not created';
    END IF;
    
    RAISE NOTICE 'Authentication system migration completed successfully';
    RAISE NOTICE 'Tables created: users, refresh_tokens';
    RAISE NOTICE 'Default admin user: admin@pconfig.com (password: Admin123!)';
    RAISE NOTICE 'IMPORTANT: Change default admin password immediately in production!';
END
$$;