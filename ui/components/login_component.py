"""
Login component for the invoice processing system
"""
import streamlit as st
from typing import Optional

from auth import AuthManager, UserRole
from auth.session_manager import SessionManager, StreamlitSessionManager


class LoginComponent:
    """Handles login UI and authentication"""
    
    def __init__(self):
        self.auth_manager = AuthManager()
        self.session_manager = SessionManager()
        self.streamlit_session = StreamlitSessionManager(self.session_manager)
    
    def render_login_form(self) -> bool:
        """Render login form and handle authentication"""
        st.title("🔐 Invoice Processing System")
        st.markdown("---")
        
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                st.subheader("Login")
                
                with st.form("login_form"):
                    username = st.text_input("Username", placeholder="Enter your username")
                    password = st.text_input("Password", type="password", 
                                           placeholder="Enter your password")
                    
                    col_login, col_forgot = st.columns(2)
                    
                    with col_login:
                        login_button = st.form_submit_button("Login", use_container_width=True)
                    
                    with col_forgot:
                        forgot_button = st.form_submit_button("Forgot Password?", 
                                                            use_container_width=True)
                
                if login_button:
                    if not username or not password:
                        st.error("Please enter both username and password")
                        return False
                    
                    success, message, user = self.auth_manager.authenticate(username, password)
                    
                    if success:
                        session_id = self.streamlit_session.login_user(username)
                        st.session_state['user_role'] = user.role.value
                        st.success(f"Welcome back, {user.username}!")
                        st.rerun()
                        return True
                    else:
                        st.error(message)
                        return False
                
                if forgot_button:
                    self.show_password_reset()
                
                # Show default credentials hint
                if not st.session_state.get('hide_default_creds', False):
                    with st.expander("ℹ️ Default Credentials", expanded=False):
                        st.info("""
                        **Default Admin Account:**
                        - Username: `admin`
                        - Password: `Admin123!`
                        
                        ⚠️ **Security Warning:** Change the default password immediately after first login!
                        """)
        
        return False
    
    def show_password_reset(self):
        """Show password reset interface"""
        st.subheader("Password Reset")
        st.warning("Password reset functionality is not yet implemented. "
                  "Please contact your system administrator.")
    
    def render_user_menu(self):
        """Render user menu in sidebar"""
        if not self.streamlit_session.is_logged_in():
            return
        
        username = self.streamlit_session.get_current_user()
        user = self.auth_manager.get_user(username)
        
        if not user:
            return
        
        with st.sidebar:
            st.markdown("---")
            st.subheader(f"👤 {user.username}")
            st.caption(f"Role: {user.role.value.title()}")
            
            if st.button("🔓 Logout", use_container_width=True):
                self.streamlit_session.logout_user()
                st.rerun()
            
            if st.button("🔑 Change Password", use_container_width=True):
                self.show_change_password_form()
            
            # Show user info
            with st.expander("👤 Account Info"):
                st.write(f"**Email:** {user.email}")
                st.write(f"**Role:** {user.role.value.title()}")
                st.write(f"**Last Login:** {user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'}")
                st.write(f"**Account Status:** {'Active' if user.is_active else 'Inactive'}")
    
    def show_change_password_form(self):
        """Show change password form"""
        st.subheader("🔑 Change Password")
        
        with st.form("change_password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            change_button = st.form_submit_button("Change Password")
            
            if change_button:
                if not all([current_password, new_password, confirm_password]):
                    st.error("Please fill in all fields")
                    return
                
                if new_password != confirm_password:
                    st.error("New passwords do not match")
                    return
                
                username = self.streamlit_session.get_current_user()
                success, message = self.auth_manager.change_password(
                    username, current_password, new_password
                )
                
                if success:
                    st.success(message)
                    # Hide the default credentials hint
                    st.session_state['hide_default_creds'] = True
                else:
                    st.error(message)
    
    def check_authentication(self) -> bool:
        """Check if user is authenticated"""
        return self.streamlit_session.is_logged_in()
    
    def require_permission(self, permission: str):
        """Require specific permission"""
        self.streamlit_session.require_permission(permission, self.auth_manager)
    
    def get_current_user_role(self) -> Optional[UserRole]:
        """Get current user's role"""
        username = self.streamlit_session.get_current_user()
        if not username:
            return None
        
        user = self.auth_manager.get_user(username)
        return user.role if user else None


class AdminComponent:
    """Admin panel for user management"""
    
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
    
    def render_admin_panel(self):
        """Render admin panel"""
        st.header("👨‍💼 Administration Panel")
        
        tab1, tab2, tab3 = st.tabs(["👥 Users", "➕ Create User", "📊 Sessions"])
        
        with tab1:
            self.render_users_list()
        
        with tab2:
            self.render_create_user_form()
        
        with tab3:
            self.render_sessions_info()
    
    def render_users_list(self):
        """Render list of users"""
        st.subheader("👥 User Management")
        
        users = self.auth_manager.list_users()
        
        if not users:
            st.info("No users found")
            return
        
        for user in users:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.write(f"**{user.username}** ({user.email})")
                    st.caption(f"Role: {user.role.value.title()}")
                
                with col2:
                    status = "🟢 Active" if user.is_active else "🔴 Inactive"
                    st.write(status)
                
                with col3:
                    if user.username != "admin":  # Don't allow deactivating admin
                        if user.is_active:
                            if st.button("Deactivate", key=f"deactivate_{user.username}"):
                                success, message = self.auth_manager.deactivate_user(user.username)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                        else:
                            if st.button("Activate", key=f"activate_{user.username}"):
                                success, message = self.auth_manager.activate_user(user.username)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                
                with col4:
                    last_login = user.last_login.strftime('%Y-%m-%d') if user.last_login else "Never"
                    st.caption(f"Last: {last_login}")
                
                st.markdown("---")
    
    def render_create_user_form(self):
        """Render create user form"""
        st.subheader("➕ Create New User")
        
        with st.form("create_user_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            role = st.selectbox("Role", [role.value.title() for role in UserRole])
            
            create_button = st.form_submit_button("Create User")
            
            if create_button:
                if not all([username, email, password, confirm_password]):
                    st.error("Please fill in all fields")
                    return
                
                if password != confirm_password:
                    st.error("Passwords do not match")
                    return
                
                # Convert role back to enum
                role_enum = UserRole(role.lower())
                
                success, message = self.auth_manager.create_user(
                    username, password, email, role_enum
                )
                
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    def render_sessions_info(self):
        """Render sessions information"""
        st.subheader("📊 Active Sessions")
        
        session_manager = SessionManager()
        active_sessions = session_manager.get_active_sessions()
        
        if not active_sessions:
            st.info("No active sessions")
            return
        
        for session in active_sessions:
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**{session.username}**")
                    st.caption(f"Session: {session.session_id[:8]}...")
                
                with col2:
                    st.write(f"Created: {session.created_at.strftime('%Y-%m-%d %H:%M')}")
                    st.caption(f"Last Activity: {session.last_activity.strftime('%Y-%m-%d %H:%M')}")
                
                with col3:
                    if st.button("End", key=f"end_{session.session_id}"):
                        session_manager.destroy_session(session.session_id)
                        st.success("Session ended")
                        st.rerun()
                
                st.markdown("---")