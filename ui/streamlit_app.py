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
from config.settings import create_directories


def initialize_session_state():
    """Initialize session state variables"""
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
        
        # Navigation menu
        st.subheader("Navigation")
        
        pages = {
            "Dashboard": "🏠 Dashboard",
            "Upload": "📤 Upload Invoice",
            "Results": "📊 Results",
            "History": "📋 History"
        }
        
        # Create navigation buttons
        for page_key, page_label in pages.items():
            if st.button(page_label, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()


def render_main_content():
    """Render the main content area based on current page"""
    # Initialize components
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
        # Get history from workflow manager if available
        try:
            if hasattr(st.session_state, 'workflow_manager') and st.session_state.workflow_manager:
                history = st.session_state.workflow_manager.get_execution_history()
            else:
                history = []
            render_processing_history(history)
        except Exception as e:
            st.error(f"Error loading processing history: {e}")
            render_processing_history([])
    
    else:
        st.error("Page not found")


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