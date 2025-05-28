"""
Dashboard Component - Main dashboard for invoice processing system
"""
import streamlit as st
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from orchestrator import AgentCoordinator, WorkflowManager, WorkflowType


class DashboardComponent:
    """Main dashboard component"""
    
    def __init__(self, agent_coordinator: AgentCoordinator, workflow_manager: WorkflowManager):
        self.agent_coordinator = agent_coordinator
        self.workflow_manager = workflow_manager
    
    def render(self):
        """Render the main dashboard"""
        st.title("📊 Invoice Processing Dashboard")
        
        # Sidebar for navigation
        with st.sidebar:
            self._render_sidebar()
        
        # Main dashboard content
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔧 System Health", "📈 Analytics", "⚙️ Settings"])
        
        with tab1:
            self._render_overview_tab()
        
        with tab2:
            self._render_system_health_tab()
        
        with tab3:
            self._render_analytics_tab()
        
        with tab4:
            self._render_settings_tab()
    
    def _render_sidebar(self):
        """Render sidebar navigation"""
        st.header("Navigation")
        
        if st.button("🔄 Refresh Data"):
            st.rerun()
        
        st.divider()
        
        # Quick actions
        st.subheader("Quick Actions")
        
        if st.button("🧹 Clear Statistics"):
            self.agent_coordinator.reset_statistics()
            st.success("Statistics cleared!")
            st.rerun()
        
        if st.button("🗑️ Clear Index"):
            from utils.llama_index_manager import llama_index_manager
            if llama_index_manager.clear_index():
                st.success("Index cleared!")
            else:
                st.error("Failed to clear index")
        
        st.divider()
        
        # System info
        st.subheader("System Info")
        health = self.agent_coordinator.get_system_health()
        
        if health["overall_status"] == "healthy":
            st.success("System Healthy ✅")
        elif health["overall_status"] == "degraded":
            st.warning("System Degraded ⚠️")
        else:
            st.error("System Unhealthy ❌")
        
        st.write(f"Agents: {health['healthy_agents']}/{health['total_agents']}")
        st.write(f"Ollama: {'✅' if health['ollama_connected'] else '❌'}")
    
    def _render_overview_tab(self):
        """Render overview tab"""
        col1, col2, col3, col4 = st.columns(4)
        
        # Get processing statistics
        stats = self.agent_coordinator.get_processing_statistics()
        coordinator_stats = stats["coordinator_stats"]
        
        with col1:
            st.metric(
                "Total Processed",
                coordinator_stats["total_processed"],
                delta=None
            )
        
        with col2:
            st.metric(
                "Successful",
                coordinator_stats["successful"],
                delta=None
            )
        
        with col3:
            success_rate = (
                coordinator_stats["successful"] / coordinator_stats["total_processed"] 
                if coordinator_stats["total_processed"] > 0 else 0
            )
            st.metric(
                "Success Rate",
                f"{success_rate:.1%}",
                delta=None
            )
        
        with col4:
            st.metric(
                "Avg Processing Time",
                f"{coordinator_stats['average_processing_time']:.2f}s",
                delta=None
            )
        
        st.divider()
        
        # Recent activity
        st.subheader("📊 Recent Activity")
        
        # Get workflow execution history
        workflow_history = self.workflow_manager.get_execution_history(limit=10)
        
        if workflow_history:
            history_df = pd.DataFrame(workflow_history)
            history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
            
            # Display recent executions
            st.dataframe(
                history_df[['timestamp', 'workflow_type', 'status', 'processing_time', 'error_count']],
                use_container_width=True
            )
        else:
            st.info("No recent activity")
        
        st.divider()
        
        # Processing status distribution
        st.subheader("📊 Processing Status Distribution")
        
        if coordinator_stats["total_processed"] > 0:
            status_data = {
                "Successful": coordinator_stats["successful"],
                "Failed": coordinator_stats["failed"],
                "Pending Review": coordinator_stats["pending_review"]
            }
            
            fig = px.pie(
                values=list(status_data.values()),
                names=list(status_data.keys()),
                title="Processing Results"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No processing data available")
    
    def _render_system_health_tab(self):
        """Render system health tab"""
        st.subheader("🔧 System Health Overview")
        
        # Overall system health
        health = self.agent_coordinator.get_system_health()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_color = {
                "healthy": "✅",
                "degraded": "⚠️", 
                "unhealthy": "❌"
            }
            st.metric(
                "Overall Status",
                f"{status_color.get(health['overall_status'], '❓')} {health['overall_status'].title()}"
            )
        
        with col2:
            st.metric(
                "Healthy Agents",
                f"{health['healthy_agents']}/{health['total_agents']}"
            )
        
        with col3:
            st.metric(
                "Ollama Connection",
                "✅ Connected" if health['ollama_connected'] else "❌ Disconnected"
            )
        
        st.divider()
        
        # Agent-specific health
        st.subheader("🔧 Agent Health Details")
        
        agent_status = self.agent_coordinator.get_agent_status()
        
        for agent_name, status in agent_status.items():
            with st.expander(f"Agent: {agent_name}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Health Status:**")
                    health_info = status["health"]
                    st.write(f"Status: {health_info.get('status', 'unknown')}")
                    if health_info.get('issues'):
                        st.write("Issues:")
                        for issue in health_info['issues']:
                            st.write(f"- {issue}")
                
                with col2:
                    st.write("**Statistics:**")
                    stats_info = status["stats"]
                    if 'stats' in stats_info:
                        agent_stats = stats_info['stats']
                        st.write(f"Executions: {agent_stats.get('executions', 0)}")
                        st.write(f"Successes: {agent_stats.get('successes', 0)}")
                        st.write(f"Failures: {agent_stats.get('failures', 0)}")
                        st.write(f"Avg Time: {agent_stats.get('average_time', 0):.2f}s")
        
        # Agent restart controls
        st.divider()
        st.subheader("🔄 Agent Management")
        
        selected_agent = st.selectbox(
            "Select agent to restart:",
            list(agent_status.keys())
        )
        
        if st.button(f"🔄 Restart {selected_agent}"):
            if self.agent_coordinator.restart_agent(selected_agent):
                st.success(f"Agent {selected_agent} restarted successfully!")
            else:
                st.error(f"Failed to restart agent {selected_agent}")
    
    def _render_analytics_tab(self):
        """Render analytics tab"""
        st.subheader("📈 Processing Analytics")
        
        # Workflow statistics
        workflow_stats = self.workflow_manager.get_workflow_statistics()
        
        if workflow_stats["total_executions"] > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Workflow Type Distribution**")
                workflow_types = workflow_stats["by_workflow_type"]
                if workflow_types:
                    fig = px.bar(
                        x=list(workflow_types.keys()),
                        y=list(workflow_types.values()),
                        title="Executions by Workflow Type"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.write("**Status Distribution**")
                status_dist = workflow_stats["by_status"]
                if status_dist:
                    fig = px.pie(
                        values=list(status_dist.values()),
                        names=list(status_dist.keys()),
                        title="Execution Status"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Performance metrics
            st.divider()
            st.subheader("⚡ Performance Metrics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Total Executions",
                    workflow_stats["total_executions"]
                )
            
            with col2:
                st.metric(
                    "Success Rate",
                    f"{workflow_stats['success_rate']:.1%}"
                )
            
            with col3:
                st.metric(
                    "Avg Processing Time", 
                    f"{workflow_stats['average_processing_time']:.2f}s"
                )
            
            # Execution history timeline
            st.divider()
            st.subheader("📈 Execution Timeline")
            
            history = self.workflow_manager.get_execution_history(limit=50)
            if history:
                history_df = pd.DataFrame(history)
                history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
                history_df = history_df.sort_values('timestamp')
                
                fig = go.Figure()
                
                for status in history_df['status'].unique():
                    status_data = history_df[history_df['status'] == status]
                    fig.add_trace(go.Scatter(
                        x=status_data['timestamp'],
                        y=status_data['processing_time'],
                        mode='markers',
                        name=status,
                        text=status_data['workflow_type'],
                        hovertemplate='<b>%{text}</b><br>Time: %{y:.2f}s<br>%{x}<extra></extra>'
                    ))
                
                fig.update_layout(
                    title="Processing Time Over Time",
                    xaxis_title="Time",
                    yaxis_title="Processing Time (seconds)"
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No analytics data available")
    
    def _render_settings_tab(self):
        """Render settings tab"""
        st.subheader("⚙️ System Settings")
        
        # Workflow configuration
        st.write("**Available Workflows:**")
        workflows = self.workflow_manager.get_available_workflows()
        
        for workflow in workflows:
            with st.expander(f"Workflow: {workflow}"):
                definition = self.workflow_manager.get_workflow_definition(workflow)
                if definition:
                    for i, step in enumerate(definition):
                        st.write(f"{i+1}. {step['agent_name']} ({'Required' if step['required'] else 'Optional'})")
                        if step['has_condition']:
                            st.write("   - Has execution condition")
        
        st.divider()
        
        # System configuration
        st.write("**System Configuration:**")
        
        from config.settings import settings
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Thresholds:**")
            st.write(f"- Confidence: {settings.CONFIDENCE_THRESHOLD}")
            st.write(f"- Validation: {settings.VALIDATION_THRESHOLD}")
            st.write(f"- Auto Approve: {settings.AUTO_APPROVE_THRESHOLD}")
        
        with col2:
            st.write("**Ollama Config:**")
            st.write(f"- Base URL: {settings.OLLAMA_BASE_URL}")
            st.write(f"- Model: {settings.OLLAMA_MODEL}")
            st.write(f"- Embedding Model: {settings.OLLAMA_EMBEDDING_MODEL}")


def render_dashboard(agent_coordinator: AgentCoordinator, workflow_manager: WorkflowManager):
    """Render the dashboard component"""
    dashboard = DashboardComponent(agent_coordinator, workflow_manager)
    dashboard.render()