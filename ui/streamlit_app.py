"""
Streamlit App - Main user interface for invoice processing system
"""
import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator import AgentCoordinator, WorkflowManager, WorkflowType
from ui.components.upload_component import UploadComponent
from ui.components.dashboard_component import DashboardComponent
from ui.components.results_component import render_results, render_processing_history
from ui.components.login_component import LoginComponent, AdminComponent
from auth import UserRole, AuthManager
from config.settings import create_directories


def initialize_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Dashboard'
    if 'agent_coordinator' not in st.session_state:
        st.session_state.agent_coordinator = None
    if 'workflow_manager' not in st.session_state:
        st.session_state.workflow_manager = None


def initialize_components():
    """Initialize system components"""
    if st.session_state.agent_coordinator is None:
        st.session_state.agent_coordinator = AgentCoordinator()
    if st.session_state.workflow_manager is None:
        st.session_state.workflow_manager = WorkflowManager(st.session_state.agent_coordinator)


def render_sidebar():
    """Render the navigation sidebar"""
    with st.sidebar:
        st.title("Invoice Processing")
        
        if st.session_state.authenticated:
            st.write(f"Welcome, {st.session_state.username}")
            st.write(f"Role: {st.session_state.user_role.value}")
            
            # Navigation menu
            st.subheader("Navigation")
            
            pages = {
                "Dashboard": "🏠 Dashboard",
                "Upload": "📤 Upload Invoice",
                "Results": "📊 Results",
                "History": "📋 History"
            }
            
            # Add admin page for admin users
            if st.session_state.user_role == UserRole.ADMIN:
                pages["Admin"] = "⚙️ Admin Panel"
            
            # Create navigation buttons
            for page_key, page_label in pages.items():
                if st.button(page_label, key=f"nav_{page_key}", use_container_width=True):
                    st.session_state.current_page = page_key
                    st.rerun()
            
            st.divider()
            
            # Logout button
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user_role = None
                st.session_state.username = None
                st.session_state.current_page = 'Dashboard'
                st.rerun()
        else:
            st.write("Please log in to continue")


def render_main_content():
    """Render the main content area based on current page"""
    if not st.session_state.authenticated:
        # Show login form
        login_component = LoginComponent()
        if login_component.render_login_form():
            st.session_state.authenticated = True
            st.session_state.user_role = login_component.streamlit_session.get_user_role()
            st.session_state.username = login_component.streamlit_session.get_username()
            st.rerun()
        return
    
    # Initialize components if authenticated
    initialize_components()
    
    # Render page based on current selection
    page = st.session_state.current_page
    
    if page == "Dashboard":
        st.title("📊 Dashboard")
        dashboard = DashboardComponent(
            st.session_state.agent_coordinator,
            st.session_state.workflow_manager
        )
        dashboard.render()
        
    elif page == "Upload":
        st.title("📤 Upload Invoice")
        upload_component = UploadComponent()
        uploaded_files = upload_component.render()
        
        if uploaded_files:
            st.success(f"Successfully uploaded {len(uploaded_files)} file(s)")
            # Process the uploaded files
            with st.spinner("Processing invoice..."):
                try:
                    results = []
                    for file_path in uploaded_files:
                        result = st.session_state.workflow_manager.execute_workflow(
                            WorkflowType.STANDARD,
                            file_path
                        )
                        results.append(result)
                    
                    st.session_state.last_results = results
                    st.success("Processing completed!")
                    
                    # Show results
                    for i, result in enumerate(results):
                        with st.expander(f"Result {i+1}: {Path(uploaded_files[i]).name}"):
                            render_results(result)
                            
                except Exception as e:
                    st.error(f"Processing failed: {e}")
    
    elif page == "Results":
        st.title("📊 Processing Results")
        if hasattr(st.session_state, 'last_results') and st.session_state.last_results:
            for i, result in enumerate(st.session_state.last_results):
                with st.expander(f"Result {i+1}", expanded=True):
                    render_results(result)
        else:
            st.info("No recent results to display. Upload and process an invoice first.")
    
    elif page == "History":
        st.title("📋 Processing History")
        render_processing_history(st.session_state.agent_coordinator)
    
    elif page == "Admin" and st.session_state.user_role == UserRole.ADMIN:
        st.title("⚙️ Admin Panel")
        auth_manager = AuthManager()
        admin_component = AdminComponent(auth_manager)
        admin_component.render_admin_panel()
    
    else:
        st.error("Page not found or access denied")


def main():
    """Main application entry point"""
    # Configure Streamlit page
    st.set_page_config(
        page_title="Invoice Processing System",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Create necessary directories
    create_directories()
    
    # Initialize session state
    initialize_session_state()
    
    # Render UI
    render_sidebar()
    render_main_content()
    
    # Add footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Invoice Processing System v1.0**")


if __name__ == "__main__":
    main()