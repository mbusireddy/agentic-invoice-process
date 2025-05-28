"""
Session management for the invoice processing system
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

import streamlit as st

from .password_utils import PasswordUtils


class Session:
    """Session data class"""
    def __init__(self, session_id: str, username: str, created_at: datetime = None,
                 last_activity: datetime = None, expires_at: datetime = None):
        self.session_id = session_id
        self.username = username
        self.created_at = created_at or datetime.now()
        self.last_activity = last_activity or datetime.now()
        self.expires_at = expires_at or (datetime.now() + timedelta(hours=24))
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now() > self.expires_at
    
    def is_inactive(self, max_inactive_time: timedelta = timedelta(hours=2)) -> bool:
        """Check if session has been inactive too long"""
        return datetime.now() - self.last_activity > max_inactive_time
    
    def refresh(self):
        """Refresh session activity"""
        self.last_activity = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert session to dictionary"""
        return {
            'session_id': self.session_id,
            'username': self.username,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'expires_at': self.expires_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Session':
        """Create session from dictionary"""
        return cls(
            session_id=data['session_id'],
            username=data['username'],
            created_at=datetime.fromisoformat(data['created_at']),
            last_activity=datetime.fromisoformat(data['last_activity']),
            expires_at=datetime.fromisoformat(data['expires_at'])
        )


class SessionManager:
    """Manages user sessions"""
    
    def __init__(self, sessions_file: str = "config/sessions.json"):
        self.sessions_file = Path(sessions_file)
        self.sessions: Dict[str, Session] = {}
        self.session_timeout = timedelta(hours=24)
        self.inactive_timeout = timedelta(hours=2)
        
        # Ensure config directory exists
        self.sessions_file.parent.mkdir(exist_ok=True)
        
        # Load existing sessions
        self._load_sessions()
        
        # Clean up expired sessions
        self._cleanup_sessions()
    
    def _load_sessions(self):
        """Load sessions from file"""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, 'r') as f:
                    sessions_data = json.load(f)
                    for session_id, session_data in sessions_data.items():
                        self.sessions[session_id] = Session.from_dict(session_data)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading sessions file: {e}")
                self.sessions = {}
    
    def _save_sessions(self):
        """Save sessions to file"""
        sessions_data = {session_id: session.to_dict() 
                        for session_id, session in self.sessions.items()}
        with open(self.sessions_file, 'w') as f:
            json.dump(sessions_data, f, indent=2)
    
    def _cleanup_sessions(self):
        """Remove expired and inactive sessions"""
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if session.is_expired() or session.is_inactive(self.inactive_timeout):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        if expired_sessions:
            self._save_sessions()
    
    def create_session(self, username: str) -> str:
        """Create a new session for user"""
        session_id = PasswordUtils.generate_secure_token()
        session = Session(session_id, username)
        
        self.sessions[session_id] = session
        self._save_sessions()
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        self._cleanup_sessions()
        
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        if session.is_expired() or session.is_inactive(self.inactive_timeout):
            self.destroy_session(session_id)
            return None
        
        # Refresh session activity
        session.refresh()
        self._save_sessions()
        
        return session
    
    def destroy_session(self, session_id: str):
        """Destroy a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._save_sessions()
    
    def destroy_user_sessions(self, username: str):
        """Destroy all sessions for a user"""
        user_sessions = [session_id for session_id, session in self.sessions.items()
                        if session.username == username]
        
        for session_id in user_sessions:
            del self.sessions[session_id]
        
        if user_sessions:
            self._save_sessions()
    
    def get_active_sessions(self, username: str = None) -> list:
        """Get list of active sessions"""
        self._cleanup_sessions()
        
        if username:
            return [session for session in self.sessions.values()
                   if session.username == username]
        else:
            return list(self.sessions.values())


class StreamlitSessionManager:
    """Session manager integrated with Streamlit"""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
    
    def login_user(self, username: str) -> str:
        """Login user and create session in Streamlit"""
        session_id = self.session_manager.create_session(username)
        
        # Store in Streamlit session state
        st.session_state['session_id'] = session_id
        st.session_state['username'] = username
        st.session_state['logged_in'] = True
        
        return session_id
    
    def logout_user(self):
        """Logout user and destroy session"""
        if 'session_id' in st.session_state:
            self.session_manager.destroy_session(st.session_state['session_id'])
        
        # Clear Streamlit session state
        for key in ['session_id', 'username', 'logged_in', 'user_role']:
            if key in st.session_state:
                del st.session_state[key]
    
    def get_current_user(self) -> Optional[str]:
        """Get current logged-in user"""
        if not st.session_state.get('logged_in', False):
            return None
        
        session_id = st.session_state.get('session_id')
        if not session_id:
            return None
        
        session = self.session_manager.get_session(session_id)
        if not session:
            # Session expired, logout
            self.logout_user()
            return None
        
        return session.username
    
    def is_logged_in(self) -> bool:
        """Check if user is logged in"""
        return self.get_current_user() is not None
    
    def require_login(self):
        """Decorator/function to require login"""
        if not self.is_logged_in():
            st.error("Please log in to access this page")
            st.stop()
    
    def require_permission(self, permission: str, auth_manager):
        """Require specific permission"""
        username = self.get_current_user()
        if not username:
            st.error("Please log in to access this page")
            st.stop()
        
        user = auth_manager.get_user(username)
        if not user or not auth_manager.has_permission(user, permission):
            st.error("You don't have permission to access this page")
            st.stop()