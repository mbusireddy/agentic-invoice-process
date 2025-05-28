import streamlit as st
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime


def render_results(result: Dict[str, Any]) -> None:
    """Render processing results in a formatted display."""
    if not result:
        st.warning("No results to display")
        return
        
    st.header("Processing Results")
    
    # Display basic information
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Document Information")
        st.write(f"**Status:** {result.get('status', 'Unknown')}")
        st.write(f"**Processed:** {result.get('timestamp', 'Unknown')}")
        st.write(f"**Document Type:** {result.get('document_type', 'Unknown')}")
    
    with col2:
        st.subheader("Processing Summary")
        st.write(f"**Confidence:** {result.get('confidence', 0):.2%}")
        st.write(f"**Validation Passed:** {'✅' if result.get('validation_passed') else '❌'}")
        st.write(f"**Compliance Check:** {'✅' if result.get('compliance_passed') else '❌'}")
    
    # Display extracted data
    if 'extracted_data' in result:
        st.subheader("Extracted Data")
        extracted_data = result['extracted_data']
        
        if isinstance(extracted_data, dict):
            for key, value in extracted_data.items():
                st.write(f"**{key.title()}:** {value}")
        else:
            st.write(extracted_data)
    
    # Display validation results
    if 'validation_results' in result:
        st.subheader("Validation Results")
        validation = result['validation_results']
        
        if validation.get('errors'):
            st.error("Validation Errors:")
            for error in validation['errors']:
                st.write(f"- {error}")
        
        if validation.get('warnings'):
            st.warning("Validation Warnings:")
            for warning in validation['warnings']:
                st.write(f"- {warning}")
    
    # Display compliance results
    if 'compliance_results' in result:
        st.subheader("Compliance Results")
        compliance = result['compliance_results']
        
        if compliance.get('passed_rules'):
            st.success("Passed Rules:")
            for rule in compliance['passed_rules']:
                st.write(f"✅ {rule}")
        
        if compliance.get('failed_rules'):
            st.error("Failed Rules:")
            for rule in compliance['failed_rules']:
                st.write(f"❌ {rule}")


def render_processing_history(history: List[Dict[str, Any]]) -> None:
    """Render processing history as a table."""
    if not history:
        st.info("No processing history available")
        return
    
    st.header("Processing History")
    
    # Convert to DataFrame for better display
    df_data = []
    for item in history:
        df_data.append({
            'Timestamp': item.get('timestamp', ''),
            'Document': item.get('document_name', 'Unknown'),
            'Status': item.get('status', 'Unknown'),
            'Confidence': f"{item.get('confidence', 0):.2%}",
            'Validation': '✅' if item.get('validation_passed') else '❌',
            'Compliance': '✅' if item.get('compliance_passed') else '❌'
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True)


class ResultsComponent:
    """Component for displaying processing results."""
    
    def __init__(self):
        self.current_result = None
        self.processing_history = []
    
    def set_result(self, result: Dict[str, Any]) -> None:
        """Set the current processing result."""
        self.current_result = result
        if result:
            self.processing_history.append(result)
    
    def render(self) -> None:
        """Render the results component."""
        if self.current_result:
            render_results(self.current_result)
        else:
            st.info("No results to display. Upload and process a document to see results here.")


class ProcessingHistoryComponent:
    """Component for displaying processing history."""
    
    def __init__(self):
        self.history = []
    
    def add_result(self, result: Dict[str, Any]) -> None:
        """Add a result to the processing history."""
        if result:
            # Add timestamp if not present
            if 'timestamp' not in result:
                result['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.history.append(result)
    
    def render(self) -> None:
        """Render the processing history component."""
        render_processing_history(self.history)
    
    def clear_history(self) -> None:
        """Clear the processing history."""
        self.history = []