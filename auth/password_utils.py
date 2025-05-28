"""
Password utilities for secure authentication
"""
import hashlib
import secrets
import hmac
from typing import Tuple


class PasswordUtils:
    """Utility class for secure password handling"""
    
    @staticmethod
    def generate_salt() -> str:
        """Generate a random salt for password hashing"""
        return secrets.token_hex(32)
    
    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        """Hash a password with salt using PBKDF2"""
        # Use PBKDF2 with SHA-256, 100,000 iterations
        password_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        
        hashed = hashlib.pbkdf2_hmac('sha256', password_bytes, salt_bytes, 100000)
        return hashed.hex()
    
    @staticmethod
    def create_password_hash(password: str) -> Tuple[str, str]:
        """Create a salted hash for a password"""
        salt = PasswordUtils.generate_salt()
        password_hash = PasswordUtils.hash_password(password, salt)
        return password_hash, salt
    
    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """Verify a password against stored hash and salt"""
        computed_hash = PasswordUtils.hash_password(password, salt)
        return hmac.compare_digest(stored_hash, computed_hash)
    
    @staticmethod
    def is_password_strong(password: str) -> Tuple[bool, list]:
        """Check if password meets security requirements"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def generate_secure_token() -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)