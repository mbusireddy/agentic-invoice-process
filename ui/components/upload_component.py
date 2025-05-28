"""
Upload Component - Streamlit component for file uploads
"""
import streamlit as st
from pathlib import Path
from typing import List, Optional
import tempfile
import os

from utils.document_processor import document_processor


class UploadComponent:
    """Component for handling file uploads"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']
        self.max_file_size = 50 * 1024 * 1024  # 50MB
    
    def render(self) -> Optional[List[str]]:
        """Render the upload component and return uploaded file paths"""
        st.header("📤 Upload Invoice Documents")
        
        # File upload widget
        uploaded_files = st.file_uploader(
            "Choose invoice files to process",
            type=['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'],
            accept_multiple_files=True,
            help=f"Supported formats: {', '.join(self.supported_formats)}. Max size: 50MB per file."
        )
        
        if not uploaded_files:
            st.info("📁 Please upload one or more invoice files to get started")
            return None
        
        # Display uploaded files info
        st.subheader("Uploaded Files")
        file_paths = []
        
        for uploaded_file in uploaded_files:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"📄 **{uploaded_file.name}**")
            
            with col2:
                file_size_mb = uploaded_file.size / (1024 * 1024)
                st.write(f"{file_size_mb:.1f} MB")
            
            with col3:
                if uploaded_file.size > self.max_file_size:
                    st.error("Too large")
                    continue
                else:
                    st.success("Valid")
            
            # Save uploaded file to temporary location
            if uploaded_file.size <= self.max_file_size:
                temp_path = self._save_uploaded_file(uploaded_file)
                if temp_path:
                    file_paths.append(temp_path)
        
        if file_paths:
            st.success(f"� {len(file_paths)} file(s) ready for processing")
            
            # Show file previews
            if st.checkbox("Show file previews"):
                self._show_file_previews(file_paths)
            
            return file_paths
        else:
            st.error("❌ No valid files uploaded")
            return None
    
    def _save_uploaded_file(self, uploaded_file) -> Optional[str]:
        """Save uploaded file to temporary location"""
        try:
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            
            # Write file content
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            return temp_path
            
        except Exception as e:
            st.error(f"Failed to save file {uploaded_file.name}: {e}")
            return None
    
    def _show_file_previews(self, file_paths: List[str]):
        """Show previews of uploaded files"""
        st.subheader("File Previews")
        
        for file_path in file_paths:
            file_name = Path(file_path).name
            
            with st.expander(f"Preview: {file_name}"):
                try:
                    # Get file info
                    file_info = document_processor.get_file_info(file_path)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**File Information:**")
                        st.write(f"- Size: {file_info['size'] / 1024:.1f} KB")
                        st.write(f"- Type: {file_info['extension']}")
                        st.write(f"- MIME: {file_info['mime_type']}")
                    
                    with col2:
                        # Show image preview for image files
                        if file_info['extension'] in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
                            st.image(file_path, width=200, caption=file_name)
                    
                    # Show text preview
                    try:
                        preview_text = document_processor.get_document_preview(file_path, max_chars=300)
                        if preview_text:
                            st.write("**Text Preview:**")
                            st.text_area("", preview_text, height=100, disabled=True)
                        else:
                            st.info("No text preview available")
                    except Exception as e:
                        st.warning(f"Could not generate text preview: {e}")
                
                except Exception as e:
                    st.error(f"Could not load preview for {file_name}: {e}")


def render_upload_component() -> Optional[List[str]]:
    """Render upload component and return uploaded file paths"""
    component = UploadComponent()
    return component.render()