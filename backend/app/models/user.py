"""
User models for authentication and user management.

Bharath's Quality-First Implementation with comprehensive validation,
security best practices, and maintainable code structure.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from enum import Enum

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import re

Base = declarative_base()


class UserRole(str, Enum):
    """User roles with clear permissions hierarchy."""
    ADMIN = "admin"      # Full system access
    MANAGER = "manager"  # Department management access
    USER = "user"        # Standard user access


class User(Base):
    """
    User model with comprehensive authentication and profile management.
    
    Features:
    - UUID primary keys for security
    - Email validation and uniqueness
    - Secure password handling (hash stored separately)
    - Role-based access control
    - User preferences and settings
    - Audit trail with timestamps
    - Soft delete support
    """
    
    __tablename__ = "users"
    
    # Primary key and identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    
    # Password (hash will be stored, never plain text)
    password_hash = Column(String(255), nullable=False)
    
    # Profile information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    
    # Role and permissions
    role = Column(String(20), nullable=False, default=UserRole.USER.value)
    
    # User preferences (stored as JSON)
    preferences = Column(JSON, nullable=False, default={
        "language": "en",
        "theme": "light",
        "notifications": {
            "email": True,
            "push": True,
            "sparky": True
        }
    })
    
    # Account status
    is_active = Column(Boolean, nullable=False, default=True)
    is_email_verified = Column(Boolean, nullable=False, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Avatar/profile image
    avatar_url = Column(String(500), nullable=True)
    
    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format."""
        if not email:
            raise ValueError("Email is required")
        
        email = email.lower().strip()
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_regex, email):
            raise ValueError("Invalid email format")
        
        if len(email) > 255:
            raise ValueError("Email too long (max 255 characters)")
            
        return email
    
    @validates('first_name', 'last_name')
    def validate_names(self, key, value):
        """Validate first and last names."""
        if not value or not value.strip():
            raise ValueError(f"{key.replace('_', ' ').title()} is required")
        
        value = value.strip()
        
        if len(value) < 1:
            raise ValueError(f"{key.replace('_', ' ').title()} must be at least 1 character")
        
        if len(value) > 100:
            raise ValueError(f"{key.replace('_', ' ').title()} too long (max 100 characters)")
        
        # Allow letters, spaces, hyphens, apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", value):
            raise ValueError(f"{key.replace('_', ' ').title()} contains invalid characters")
            
        return value
    
    @validates('role')
    def validate_role(self, key, role):
        """Validate user role."""
        if role not in [r.value for r in UserRole]:
            raise ValueError(f"Invalid role: {role}. Must be one of {[r.value for r in UserRole]}")
        return role
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def permissions(self) -> List[str]:
        """Get user permissions based on role."""
        role_permissions = {
            UserRole.ADMIN: [
                "users:read", "users:write", "users:delete",
                "products:read", "products:write", "products:delete",
                "packages:read", "packages:write", "packages:delete",
                "recommendations:read", "recommendations:write",
                "system:read", "system:write", "analytics:read"
            ],
            UserRole.MANAGER: [
                "users:read", "users:write",
                "products:read", "products:write",
                "packages:read", "packages:write",
                "recommendations:read", "recommendations:write",
                "analytics:read"
            ],
            UserRole.USER: [
                "products:read",
                "packages:read", "packages:write",
                "recommendations:read",
                "profile:read", "profile:write"
            ]
        }
        
        return role_permissions.get(UserRole(self.role), [])
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        return permission in self.permissions
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary representation."""
        user_dict = {
            "id": str(self.id),
            "email": self.email,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "role": self.role,
            "preferences": self.preferences,
            "permissions": self.permissions,
            "isActive": self.is_active,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            "lastLoginAt": self.last_login_at.isoformat() if self.last_login_at else None,
        }
        
        if self.avatar_url:
            user_dict["avatar"] = self.avatar_url
            
        if include_sensitive:
            user_dict["isEmailVerified"] = self.is_email_verified
            
        return user_dict
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class RefreshToken(Base):
    """
    Refresh token model for JWT token management.
    
    Features:
    - Secure token storage with hashing
    - Automatic expiration
    - User relationship tracking
    - Token revocation support
    """
    
    __tablename__ = "refresh_tokens"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Token data (hashed for security)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    
    # Expiration and status
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_revoked = Column(Boolean, nullable=False, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    user_agent = Column(String(500), nullable=True)  # Track device/browser
    ip_address = Column(String(45), nullable=True)   # Track IP for security
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not revoked)."""
        return not self.is_expired and not self.is_revoked
    
    def revoke(self):
        """Revoke the refresh token."""
        self.is_revoked = True
    
    def to_dict(self) -> dict:
        """Convert refresh token to dictionary representation."""
        return {
            "id": str(self.id),
            "userId": str(self.user_id),
            "expiresAt": self.expires_at.isoformat(),
            "isRevoked": self.is_revoked,
            "createdAt": self.created_at.isoformat(),
            "userAgent": self.user_agent,
            "ipAddress": self.ip_address
        }
    
    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"