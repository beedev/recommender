"""
PostgreSQL repository for user data and application state.

Provides safe, parameterized queries for user management, sessions,
preferences, and other relational data operations.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import json
import hashlib

from ..postgresql import PostgreSQLConnection, get_postgres_connection

logger = logging.getLogger(__name__)


class PostgreSQLRepository:
    """
    Repository for PostgreSQL database operations.
    
    Handles user data, sessions, preferences, caching, and other
    relational data with parameterized queries for security.
    """
    
    def __init__(self, connection: PostgreSQLConnection):
        """
        Initialize repository with PostgreSQL connection.
        
        Args:
            connection: PostgreSQL connection instance
        """
        self.connection = connection
    
    # =============================================================================
    # USER MANAGEMENT
    # =============================================================================
    
    async def create_user_table(self) -> None:
        """Create users table if it doesn't exist."""
        query = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            preferences JSONB DEFAULT '{}'::jsonb
        );
        
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
        """
        await self.connection.execute_command(query)
    
    async def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        full_name: Optional[str] = None,
        is_admin: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new user.
        
        Args:
            username: Unique username
            email: User email address
            password_hash: Hashed password
            full_name: User's full name
            is_admin: Whether user has admin privileges
            
        Returns:
            Created user data or None if creation failed
        """
        query = """
        INSERT INTO users (username, email, password_hash, full_name, is_admin)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, username, email, full_name, is_active, is_admin, created_at
        """
        
        try:
            result = await self.connection.execute_query_one(
                query, username, email, password_hash, full_name, is_admin
            )
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.
        
        Args:
            user_id: User identifier
            
        Returns:
            User data or None if not found
        """
        query = """
        SELECT id, username, email, full_name, is_active, is_admin, 
               created_at, updated_at, last_login, preferences
        FROM users
        WHERE id = $1 AND is_active = TRUE
        """
        
        result = await self.connection.execute_query_one(query, user_id)
        return dict(result) if result else None
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username.
        
        Args:
            username: Username
            
        Returns:
            User data or None if not found
        """
        query = """
        SELECT id, username, email, full_name, is_active, is_admin,
               password_hash, created_at, updated_at, last_login, preferences
        FROM users
        WHERE username = $1 AND is_active = TRUE
        """
        
        result = await self.connection.execute_query_one(query, username)
        return dict(result) if result else None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email.
        
        Args:
            email: Email address
            
        Returns:
            User data or None if not found
        """
        query = """
        SELECT id, username, email, full_name, is_active, is_admin,
               password_hash, created_at, updated_at, last_login, preferences
        FROM users
        WHERE email = $1 AND is_active = TRUE
        """
        
        result = await self.connection.execute_query_one(query, email)
        return dict(result) if result else None
    
    async def update_user_login(self, user_id: int) -> bool:
        """
        Update user's last login timestamp.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if update successful
        """
        query = """
        UPDATE users 
        SET last_login = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
        """
        
        try:
            await self.connection.execute_command(query, user_id)
            return True
        except Exception as e:
            logger.error(f"Error updating user login: {e}")
            return False
    
    async def update_user_preferences(
        self,
        user_id: int,
        preferences: Dict[str, Any]
    ) -> bool:
        """
        Update user preferences.
        
        Args:
            user_id: User identifier
            preferences: User preferences as JSON
            
        Returns:
            True if update successful
        """
        query = """
        UPDATE users 
        SET preferences = $2, updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
        """
        
        try:
            await self.connection.execute_command(
                query, user_id, json.dumps(preferences)
            )
            return True
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False
    
    # =============================================================================
    # SESSION MANAGEMENT
    # =============================================================================
    
    async def create_session_table(self) -> None:
        """Create sessions table if it doesn't exist."""
        query = """
        CREATE TABLE IF NOT EXISTS user_sessions (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) UNIQUE NOT NULL,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            user_agent TEXT,
            ip_address INET,
            refresh_token_hash VARCHAR(255)
        );
        
        CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON user_sessions(session_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_active ON user_sessions(is_active);
        CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at);
        """
        await self.connection.execute_command(query)
    
    async def create_session(
        self,
        session_id: str,
        user_id: int,
        expires_at: datetime,
        refresh_token_hash: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new user session.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
            expires_at: Session expiration time
            refresh_token_hash: Hashed refresh token
            user_agent: Client user agent
            ip_address: Client IP address
            
        Returns:
            Created session data or None if creation failed
        """
        query = """
        INSERT INTO user_sessions (session_id, user_id, expires_at, refresh_token_hash, user_agent, ip_address)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, session_id, user_id, created_at, expires_at, is_active
        """
        
        try:
            result = await self.connection.execute_query_one(
                query, session_id, user_id, expires_at, 
                refresh_token_hash, user_agent, ip_address
            )
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session by session ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found/expired
        """
        query = """
        SELECT s.*, u.username, u.email, u.full_name, u.is_admin
        FROM user_sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.session_id = $1 
          AND s.is_active = TRUE 
          AND s.expires_at > CURRENT_TIMESTAMP
          AND u.is_active = TRUE
        """
        
        result = await self.connection.execute_query_one(query, session_id)
        return dict(result) if result else None
    
    async def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if invalidation successful
        """
        query = """
        UPDATE user_sessions 
        SET is_active = FALSE
        WHERE session_id = $1
        """
        
        try:
            await self.connection.execute_command(query, session_id)
            return True
        except Exception as e:
            logger.error(f"Error invalidating session: {e}")
            return False
    
    async def invalidate_user_sessions(self, user_id: int) -> bool:
        """
        Invalidate all sessions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if invalidation successful
        """
        query = """
        UPDATE user_sessions 
        SET is_active = FALSE
        WHERE user_id = $1 AND is_active = TRUE
        """
        
        try:
            await self.connection.execute_command(query, user_id)
            return True
        except Exception as e:
            logger.error(f"Error invalidating user sessions: {e}")
            return False
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        query = """
        DELETE FROM user_sessions 
        WHERE expires_at < CURRENT_TIMESTAMP OR is_active = FALSE
        """
        
        try:
            result = await self.connection.execute_command(query)
            # Parse the result to get number of affected rows
            affected_rows = int(result.split()[-1]) if result else 0
            logger.info(f"Cleaned up {affected_rows} expired sessions")
            return affected_rows
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0
    
    # =============================================================================
    # CACHING LAYER
    # =============================================================================
    
    async def create_cache_table(self) -> None:
        """Create cache table if it doesn't exist."""
        query = """
        CREATE TABLE IF NOT EXISTS cache_entries (
            id SERIAL PRIMARY KEY,
            cache_key VARCHAR(255) UNIQUE NOT NULL,
            cache_value JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            tags TEXT[] DEFAULT '{}'
        );
        
        CREATE INDEX IF NOT EXISTS idx_cache_key ON cache_entries(cache_key);
        CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache_entries(expires_at);
        CREATE INDEX IF NOT EXISTS idx_cache_tags ON cache_entries USING GIN(tags);
        """
        await self.connection.execute_command(query)
    
    async def set_cache(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 3600,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Set cache entry.
        
        Args:
            key: Cache key
            value: Cache value (will be JSON serialized)
            ttl_seconds: Time to live in seconds
            tags: Optional tags for cache invalidation
            
        Returns:
            True if cache set successfully
        """
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        tags = tags or []
        
        query = """
        INSERT INTO cache_entries (cache_key, cache_value, expires_at, tags)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (cache_key) 
        DO UPDATE SET 
            cache_value = $2,
            expires_at = $3,
            tags = $4,
            created_at = CURRENT_TIMESTAMP
        """
        
        try:
            await self.connection.execute_command(
                query, key, json.dumps(value), expires_at, tags
            )
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """
        Get cache entry.
        
        Args:
            key: Cache key
            
        Returns:
            Cache value or None if not found/expired
        """
        query = """
        SELECT cache_value
        FROM cache_entries
        WHERE cache_key = $1 AND expires_at > CURRENT_TIMESTAMP
        """
        
        try:
            result = await self.connection.execute_query_one(query, key)
            if result:
                return json.loads(result["cache_value"])
            return None
        except Exception as e:
            logger.error(f"Error getting cache: {e}")
            return None
    
    async def delete_cache(self, key: str) -> bool:
        """
        Delete cache entry.
        
        Args:
            key: Cache key
            
        Returns:
            True if deletion successful
        """
        query = "DELETE FROM cache_entries WHERE cache_key = $1"
        
        try:
            await self.connection.execute_command(query, key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache: {e}")
            return False
    
    async def invalidate_cache_by_tags(self, tags: List[str]) -> int:
        """
        Invalidate cache entries by tags.
        
        Args:
            tags: Tags to invalidate
            
        Returns:
            Number of entries invalidated
        """
        query = """
        DELETE FROM cache_entries 
        WHERE tags && $1
        """
        
        try:
            result = await self.connection.execute_command(query, tags)
            affected_rows = int(result.split()[-1]) if result else 0
            logger.info(f"Invalidated {affected_rows} cache entries with tags: {tags}")
            return affected_rows
        except Exception as e:
            logger.error(f"Error invalidating cache by tags: {e}")
            return 0
    
    async def cleanup_expired_cache(self) -> int:
        """
        Clean up expired cache entries.
        
        Returns:
            Number of entries cleaned up
        """
        query = "DELETE FROM cache_entries WHERE expires_at < CURRENT_TIMESTAMP"
        
        try:
            result = await self.connection.execute_command(query)
            affected_rows = int(result.split()[-1]) if result else 0
            logger.info(f"Cleaned up {affected_rows} expired cache entries")
            return affected_rows
        except Exception as e:
            logger.error(f"Error cleaning up expired cache: {e}")
            return 0
    
    # =============================================================================
    # ANALYTICS AND LOGGING
    # =============================================================================
    
    async def create_analytics_table(self) -> None:
        """Create analytics table if it doesn't exist."""
        query = """
        CREATE TABLE IF NOT EXISTS user_analytics (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            event_type VARCHAR(100) NOT NULL,
            event_data JSONB DEFAULT '{}'::jsonb,
            session_id VARCHAR(255),
            ip_address INET,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_analytics_user_id ON user_analytics(user_id);
        CREATE INDEX IF NOT EXISTS idx_analytics_event_type ON user_analytics(event_type);
        CREATE INDEX IF NOT EXISTS idx_analytics_created_at ON user_analytics(created_at);
        CREATE INDEX IF NOT EXISTS idx_analytics_session_id ON user_analytics(session_id);
        """
        await self.connection.execute_command(query)
    
    async def log_user_event(
        self,
        user_id: Optional[int],
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Log user analytics event.
        
        Args:
            user_id: User identifier (can be None for anonymous events)
            event_type: Type of event
            event_data: Additional event data
            session_id: Session identifier
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            True if logging successful
        """
        query = """
        INSERT INTO user_analytics (user_id, event_type, event_data, session_id, ip_address, user_agent)
        VALUES ($1, $2, $3, $4, $5, $6)
        """
        
        try:
            await self.connection.execute_command(
                query, user_id, event_type, 
                json.dumps(event_data or {}),
                session_id, ip_address, user_agent
            )
            return True
        except Exception as e:
            logger.error(f"Error logging user event: {e}")
            return False
    
    async def get_user_analytics(
        self,
        user_id: int,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get user analytics events.
        
        Args:
            user_id: User identifier
            event_type: Optional filter by event type
            limit: Maximum number of events to return
            offset: Number of events to skip
            
        Returns:
            List of analytics events
        """
        if event_type:
            query = """
            SELECT event_type, event_data, session_id, created_at
            FROM user_analytics
            WHERE user_id = $1 AND event_type = $2
            ORDER BY created_at DESC
            LIMIT $3 OFFSET $4
            """
            parameters = (user_id, event_type, limit, offset)
        else:
            query = """
            SELECT event_type, event_data, session_id, created_at
            FROM user_analytics
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """
            parameters = (user_id, limit, offset)
        
        result = await self.connection.execute_query(query, *parameters)
        return [dict(record) for record in result]


# Dependency for getting PostgreSQL repository
async def get_postgres_repository() -> PostgreSQLRepository:
    """
    Factory function to get PostgreSQL repository instance.
    
    Returns:
        PostgreSQL repository with active connection
    """
    connection = await get_postgres_connection()
    return PostgreSQLRepository(connection)