"""
Email-Based Identity System

Provides stable user identification based on email addresses that:
- Survives API key rotation
- Works across exchanges (Coinbase, Binance, etc.)
- Generates consistent user IDs for storage and billing
- Maintains privacy through hashing
"""

import hashlib
import re
from typing import Optional, Any
import structlog

logger = structlog.get_logger(__name__)


class EmailIdentity:
    """
    Stable email-based identity system for FortunaMind services.
    
    Generates consistent user IDs that survive API key rotations and 
    work across different exchanges and services.
    """
    
    VERSION = "v1"  # Version for future migration support
    NAMESPACE = "fortunamind"
    
    @classmethod
    def generate_user_id(cls, email: str) -> str:
        """
        Generate stable user ID from email address.
        
        Creates a deterministic 64-character hex string that uniquely
        identifies a user across all FortunaMind services.
        
        Args:
            email: User's email address
            
        Returns:
            64-character hex string user ID
            
        Examples:
            >>> identity = EmailIdentity()
            >>> user_id = identity.generate_user_id("user@example.com")
            >>> len(user_id)
            64
            >>> user_id == identity.generate_user_id("user@example.com")
            True
        """
        if not cls.validate_email(email):
            raise ValueError(f"Invalid email format: {email}")
        
        # Normalize email
        normalized = email.lower().strip()
        
        # Create deterministic identifier
        identifier = f"{cls.NAMESPACE}:{cls.VERSION}:{normalized}"
        
        # Generate SHA-256 hash
        user_id = hashlib.sha256(identifier.encode('utf-8')).hexdigest()
        
        logger.debug(
            "Generated user ID",
            email_hash=hashlib.sha256(email.encode()).hexdigest()[:8],
            user_id_prefix=user_id[:8]
        )
        
        return user_id
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format using RFC-compliant regex.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid email format, False otherwise
            
        Examples:
            >>> EmailIdentity.validate_email("user@example.com")
            True
            >>> EmailIdentity.validate_email("invalid-email")
            False
        """
        if not email or not isinstance(email, str):
            return False
            
        # RFC 5322 compliant regex (simplified)
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))
    
    @classmethod
    def normalize_email(cls, email: str) -> str:
        """
        Normalize email address for consistent processing.
        
        Args:
            email: Raw email address
            
        Returns:
            Normalized email address
            
        Raises:
            ValueError: If email format is invalid
        """
        if not cls.validate_email(email):
            raise ValueError(f"Invalid email format: {email}")
            
        return email.lower().strip()
    
    @classmethod
    def extract_from_auth_context(cls, auth_context: Any) -> Optional[str]:
        """
        Extract email from various auth context types.
        
        Supports multiple auth context formats from different frameworks.
        
        Args:
            auth_context: Auth context object from various sources
            
        Returns:
            Email address if found, None otherwise
        """
        if not auth_context:
            return None
            
        # Try common attribute names
        for attr in ['email', 'user_email', 'account_email']:
            if hasattr(auth_context, attr):
                email = getattr(auth_context, attr)
                if email and cls.validate_email(email):
                    return cls.normalize_email(email)
        
        # Try signature field (we sometimes store email there)
        if hasattr(auth_context, 'signature'):
            email = auth_context.signature
            if email and cls.validate_email(email):
                return cls.normalize_email(email)
        
        # Try metadata
        if hasattr(auth_context, 'metadata') and auth_context.metadata:
            if isinstance(auth_context.metadata, dict):
                email = auth_context.metadata.get('email')
                if email and cls.validate_email(email):
                    return cls.normalize_email(email)
        
        # Try as dict
        if isinstance(auth_context, dict):
            email = auth_context.get('email')
            if email and cls.validate_email(email):
                return cls.normalize_email(email)
        
        return None
    
    @classmethod
    def is_valid_user_id(cls, user_id: str) -> bool:
        """
        Validate if a string is a valid user ID generated by this system.
        
        Args:
            user_id: User ID to validate
            
        Returns:
            True if valid user ID format, False otherwise
        """
        if not user_id or not isinstance(user_id, str):
            return False
            
        # Check if it's a 64-character hex string
        if len(user_id) != 64:
            return False
            
        try:
            int(user_id, 16)  # Try to parse as hex
            return True
        except ValueError:
            return False
    
    @classmethod
    def get_user_id_from_email(cls, email: str) -> str:
        """
        Convenience method to get user ID from email.
        
        Alias for generate_user_id() with better naming for clarity.
        
        Args:
            email: User's email address
            
        Returns:
            64-character hex string user ID
        """
        return cls.generate_user_id(email)


# Convenience instance for backward compatibility
default_identity = EmailIdentity()

# Convenience functions
generate_user_id = default_identity.generate_user_id
validate_email = EmailIdentity.validate_email
normalize_email = EmailIdentity.normalize_email