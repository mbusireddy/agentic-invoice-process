"""
Authentication manager for the invoice processing system
"""
import json
import os
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .password_utils import PasswordUtils


class UserRole(Enum):
    """User roles for role-based access control"""
    ADMIN = "admin"
    PROCESSOR = "processor"
    VIEWER = "viewer"
    AUDITOR = "auditor"


class User:
    """User data class"""
    def __init__(self, username: str, email: str, role: UserRole, 
                 password_hash: str, salt: str, created_at: datetime = None,
                 last_login: datetime = None, is_active: bool = True):
        self.username = username
        self.email = email
        self.role = role
        self.password_hash = password_hash
        self.salt = salt
        self.created_at = created_at or datetime.now()
        self.last_login = last_login
        self.is_active = is_active
    
    def to_dict(self) -> Dict:
        """Convert user to dictionary for storage"""
        return {
            'username': self.username,
            'email': self.email,
            'role': self.role.value,
            'password_hash': self.password_hash,
            'salt': self.salt,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """Create user from dictionary"""
        return cls(
            username=data['username'],
            email=data['email'],
            role=UserRole(data['role']),
            password_hash=data['password_hash'],
            salt=data['salt'],
            created_at=datetime.fromisoformat(data['created_at']),
            last_login=datetime.fromisoformat(data['last_login']) if data['last_login'] else None,
            is_active=data.get('is_active', True)
        )


class AuthManager:
    """Manages user authentication and authorization"""
    
    def __init__(self, users_file: str = "config/users.json"):
        self.users_file = Path(users_file)
        self.users: Dict[str, User] = {}
        self.failed_attempts: Dict[str, List[datetime]] = {}
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
        
        # Ensure config directory exists
        self.users_file.parent.mkdir(exist_ok=True)
        
        # Load existing users or create default admin
        self._load_users()
        if not self.users:
            self._create_default_admin()
    
    def _load_users(self):
        """Load users from file"""
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r') as f:
                    users_data = json.load(f)
                    for username, user_data in users_data.items():
                        self.users[username] = User.from_dict(user_data)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading users file: {e}")
                self.users = {}
    
    def _save_users(self):
        """Save users to file"""
        users_data = {username: user.to_dict() for username, user in self.users.items()}
        with open(self.users_file, 'w') as f:
            json.dump(users_data, f, indent=2)
    
    def _create_default_admin(self):
        """Create default admin user"""
        default_password = "Admin123!"
        password_hash, salt = PasswordUtils.create_password_hash(default_password)
        
        admin_user = User(
            username="admin",
            email="admin@company.com",
            role=UserRole.ADMIN,
            password_hash=password_hash,
            salt=salt
        )
        
        self.users["admin"] = admin_user
        self._save_users()
        
        print("🔐 Default admin user created:")
        print(f"   Username: admin")
        print(f"   Password: {default_password}")
        print("   ⚠️  Please change the default password immediately!")
    
    def _is_account_locked(self, username: str) -> bool:
        """Check if account is locked due to failed attempts"""
        if username not in self.failed_attempts:
            return False
        
        recent_attempts = [
            attempt for attempt in self.failed_attempts[username]
            if datetime.now() - attempt < self.lockout_duration
        ]
        
        return len(recent_attempts) >= self.max_failed_attempts
    
    def _record_failed_attempt(self, username: str):
        """Record a failed login attempt"""
        if username not in self.failed_attempts:
            self.failed_attempts[username] = []
        
        self.failed_attempts[username].append(datetime.now())
        
        # Clean up old attempts
        cutoff = datetime.now() - self.lockout_duration
        self.failed_attempts[username] = [
            attempt for attempt in self.failed_attempts[username]
            if attempt > cutoff
        ]
    
    def _clear_failed_attempts(self, username: str):
        """Clear failed attempts for successful login"""
        if username in self.failed_attempts:
            del self.failed_attempts[username]
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """Authenticate a user"""
        # Check if account is locked
        if self._is_account_locked(username):
            return False, "Account is temporarily locked due to multiple failed attempts", None
        
        # Check if user exists
        if username not in self.users:
            self._record_failed_attempt(username)
            return False, "Invalid username or password", None
        
        user = self.users[username]
        
        # Check if user is active
        if not user.is_active:
            return False, "Account is disabled", None
        
        # Verify password
        if not PasswordUtils.verify_password(password, user.password_hash, user.salt):
            self._record_failed_attempt(username)
            return False, "Invalid username or password", None
        
        # Successful login
        self._clear_failed_attempts(username)
        user.last_login = datetime.now()
        self._save_users()
        
        return True, "Login successful", user
    
    def create_user(self, username: str, password: str, email: str, 
                   role: UserRole) -> Tuple[bool, str]:
        """Create a new user"""
        # Check if username already exists
        if username in self.users:
            return False, "Username already exists"
        
        # Validate password strength
        is_strong, errors = PasswordUtils.is_password_strong(password)
        if not is_strong:
            return False, "; ".join(errors)
        
        # Create user
        password_hash, salt = PasswordUtils.create_password_hash(password)
        user = User(
            username=username,
            email=email,
            role=role,
            password_hash=password_hash,
            salt=salt
        )
        
        self.users[username] = user
        self._save_users()
        
        return True, "User created successfully"
    
    def change_password(self, username: str, old_password: str, 
                       new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        if username not in self.users:
            return False, "User not found"
        
        user = self.users[username]
        
        # Verify old password
        if not PasswordUtils.verify_password(old_password, user.password_hash, user.salt):
            return False, "Current password is incorrect"
        
        # Validate new password strength
        is_strong, errors = PasswordUtils.is_password_strong(new_password)
        if not is_strong:
            return False, "; ".join(errors)
        
        # Update password
        password_hash, salt = PasswordUtils.create_password_hash(new_password)
        user.password_hash = password_hash
        user.salt = salt
        
        self._save_users()
        
        return True, "Password changed successfully"
    
    def get_user(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.users.get(username)
    
    def list_users(self) -> List[User]:
        """List all users"""
        return list(self.users.values())
    
    def deactivate_user(self, username: str) -> Tuple[bool, str]:
        """Deactivate a user account"""
        if username not in self.users:
            return False, "User not found"
        
        if username == "admin":
            return False, "Cannot deactivate admin user"
        
        self.users[username].is_active = False
        self._save_users()
        
        return True, "User deactivated successfully"
    
    def activate_user(self, username: str) -> Tuple[bool, str]:
        """Activate a user account"""
        if username not in self.users:
            return False, "User not found"
        
        self.users[username].is_active = True
        self._save_users()
        
        return True, "User activated successfully"
    
    def has_permission(self, user: User, action: str) -> bool:
        """Check if user has permission for an action"""
        role_permissions = {
            UserRole.ADMIN: ["*"],  # Admin has all permissions
            UserRole.PROCESSOR: ["process", "view", "upload", "approve"],
            UserRole.VIEWER: ["view"],
            UserRole.AUDITOR: ["view", "audit", "report"]
        }
        
        permissions = role_permissions.get(user.role, [])
        return "*" in permissions or action in permissions