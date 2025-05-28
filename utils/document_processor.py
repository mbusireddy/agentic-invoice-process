"""
Document Processor - Utility functions for document processing
"""
import io
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, TYPE_CHECKING

try:
    import PyPDF2
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path, convert_from_bytes
    DOCUMENT_PROCESSING_AVAILABLE = True
except ImportError:
    DOCUMENT_PROCESSING_AVAILABLE = False
    if TYPE_CHECKING:
        from PIL import Image


class DocumentProcessor:
    """Utility class for document processing operations"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']
        self.max_file_size = 50 * 1024 * 1024  # 50MB
    
    def is_supported_format(self, file_path: Union[str, Path]) -> bool:
        """Check if file format is supported"""
        file_path = Path(file_path)
        return file_path.suffix.lower() in self.supported_formats
    
    def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, any]:
        """Get information about a file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stat = file_path.stat()
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        return {
            "name": file_path.name,
            "size": stat.st_size,
            "extension": file_path.suffix.lower(),
            "mime_type": mime_type,
            "is_supported": self.is_supported_format(file_path),
            "modified": stat.st_mtime
        }
    
    def validate_file(self, file_path: Union[str, Path]) -> Tuple[bool, List[str]]:
        """Validate file for processing"""
        errors = []
        
        try:
            file_info = self.get_file_info(file_path)
        except FileNotFoundError as e:
            return False, [str(e)]
        
        # Check file size
        if file_info["size"] > self.max_file_size:
            errors.append(f"File size {file_info['size']} exceeds maximum {self.max_file_size}")
        
        # Check format support
        if not file_info["is_supported"]:
            errors.append(f"File format {file_info['extension']} not supported")
        
        # Check if file is empty
        if file_info["size"] == 0:
            errors.append("File is empty")
        
        return len(errors) == 0, errors
    
    def extract_text_from_pdf(self, file_path: Union[str, Path]) -> Tuple[str, Dict]:
        """Extract text from PDF file"""
        if not DOCUMENT_PROCESSING_AVAILABLE:
            raise RuntimeError("Document processing dependencies not available")
        
        file_path = Path(file_path)
        text_content = []
        metadata = {
            "pages": 0,
            "extraction_method": "direct",
            "file_size": file_path.stat().st_size
        }
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata["pages"] = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content.append(page_text)
                
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from PDF: {e}")
        
        return "\n\n".join(text_content), metadata
    
    def extract_text_from_image(self, file_path: Union[str, Path]) -> Tuple[str, Dict]:
        """Extract text from image using OCR"""
        if not DOCUMENT_PROCESSING_AVAILABLE:
            raise RuntimeError("Document processing dependencies not available")
        
        file_path = Path(file_path)
        metadata = {
            "extraction_method": "ocr",
            "file_size": file_path.stat().st_size
        }
        
        try:
            image = Image.open(file_path)
            metadata["image_size"] = image.size
            metadata["image_mode"] = image.mode
            
            text = pytesseract.image_to_string(image)
            return text.strip(), metadata
            
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from image: {e}")
    
    def convert_pdf_to_images(self, file_path: Union[str, Path], dpi: int = 300) -> List:
        """Convert PDF pages to images"""
        if not DOCUMENT_PROCESSING_AVAILABLE:
            raise RuntimeError("Document processing dependencies not available")
        
        try:
            images = convert_from_path(file_path, dpi=dpi)
            return images
        except Exception as e:
            raise RuntimeError(f"Failed to convert PDF to images: {e}")
    
    def process_document(self, file_path: Union[str, Path]) -> Tuple[str, Dict]:
        """Process document and extract text automatically"""
        file_path = Path(file_path)
        
        # Validate file
        is_valid, errors = self.validate_file(file_path)
        if not is_valid:
            raise ValueError(f"File validation failed: {errors}")
        
        # Extract text based on file type
        if file_path.suffix.lower() == '.pdf':
            return self.extract_text_from_pdf(file_path)
        else:
            return self.extract_text_from_image(file_path)
    
    def get_document_preview(self, file_path: Union[str, Path], max_chars: int = 500) -> str:
        """Get a preview of document text"""
        try:
            text, _ = self.process_document(file_path)
            if len(text) <= max_chars:
                return text
            return text[:max_chars] + "..."
        except Exception:
            return f"Unable to preview {Path(file_path).name}"


# Global document processor instance
document_processor = DocumentProcessor()