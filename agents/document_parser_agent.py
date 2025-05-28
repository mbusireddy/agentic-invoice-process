"""
Document Parser Agent - Handles parsing of invoice documents (PDF, images)
"""
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import PyPDF2
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path, convert_from_bytes
    DOCUMENT_PROCESSING_AVAILABLE = True
except ImportError:
    PyPDF2 = None
    pytesseract = None
    Image = None
    convert_from_path = None
    convert_from_bytes = None
    DOCUMENT_PROCESSING_AVAILABLE = False

from agents.base_agent import BaseAgent
from models.processing_result import ProcessingResult


class DocumentParserAgent(BaseAgent):
    """Agent responsible for parsing various document formats into text"""
    
    def __init__(self, ollama_client=None):
        super().__init__("document_parser", ollama_client)
        
        # Document processing settings
        self.supported_formats = [".pdf", ".png", ".jpg", ".jpeg", ".tiff"]
        self.ocr_enabled = DOCUMENT_PROCESSING_AVAILABLE
        self.pdf_extract_images = True
        self.image_dpi = 300
        self.tesseract_config = "--oem 3 --psm 6"
        
        if not DOCUMENT_PROCESSING_AVAILABLE:
            self.logger.warning("Document processing dependencies not available")
        
        self.logger.info(f"Document parser initialized with formats: {self.supported_formats}")
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate that the input is a valid file path or bytes"""
        if isinstance(input_data, (str, Path)):
            file_path = Path(input_data)
            return file_path.exists() and file_path.suffix.lower() in self.supported_formats
        elif isinstance(input_data, bytes):
            return True
        return False
    
    def process(self, input_data: Union[Path, str, bytes], context: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """
        Parse a document and extract text content
        
        Args:
            input_data: File path or bytes of the document to parse
            context: Optional context information
            
        Returns:
            ProcessingResult: Contains extracted text and metadata
        """
        result = ProcessingResult()
        
        try:
            if not DOCUMENT_PROCESSING_AVAILABLE:
                raise ValueError("Document processing dependencies not installed")
                
            # Validate input
            if not self.validate_input(input_data):
                raise ValueError(f"Invalid input data for document parser: {type(input_data)}")
            
            # Determine file type and process accordingly
            if isinstance(input_data, (str, Path)):
                file_path = Path(input_data)
                
                result.add_processing_step(
                    agent=self.name,
                    action="file_validation",
                    result=f"Processing file: {file_path.name}"
                )
                
                if file_path.suffix.lower() == ".pdf":
                    extracted_text, metadata = self._process_pdf(file_path)
                else:
                    extracted_text, metadata = self._process_image(file_path)
            else:
                # Process bytes data
                extracted_text, metadata = self._process_bytes(input_data)
            
            # Store results
            result.confidence_score = self._calculate_confidence(extracted_text, metadata)
            
            result.add_processing_step(
                agent=self.name,
                action="text_extraction",
                result=f"Extracted {len(extracted_text)} characters",
                confidence=result.confidence_score
            )
            
            # Store extracted data in context for next agents
            if context is not None:
                context["raw_text"] = extracted_text
                context["document_metadata"] = metadata
            
        except Exception as e:
            error_msg = f"Document parsing failed: {str(e)}"
            self.logger.error(error_msg)
            result.add_error(error_msg)
        
        return result
    
    def _process_pdf(self, file_path: Path) -> tuple[str, Dict[str, Any]]:
        """Process a PDF file and extract text"""
        text_content = []
        metadata = {
            "file_type": "pdf",
            "pages": 0,
            "extraction_method": []
        }
        
        try:
            # First, try direct text extraction from PDF
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata["pages"] = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content.append(page_text)
                        metadata["extraction_method"].append(f"page_{page_num}_direct")
                    else:
                        # If no direct text, fall back to OCR
                        if self.ocr_enabled and self.pdf_extract_images:
                            ocr_text = self._ocr_pdf_page(file_path, page_num)
                            if ocr_text:
                                text_content.append(ocr_text)
                                metadata["extraction_method"].append(f"page_{page_num}_ocr")
            
        except Exception as e:
            # If PDF reading fails, try converting to images and OCR
            if self.ocr_enabled:
                self.logger.warning(f"Direct PDF reading failed, trying OCR: {e}")
                try:
                    images = convert_from_path(file_path, dpi=self.image_dpi)
                    metadata["pages"] = len(images)
                    
                    for i, image in enumerate(images):
                        ocr_text = self._ocr_image(image)
                        if ocr_text:
                            text_content.append(ocr_text)
                            metadata["extraction_method"].append(f"page_{i}_ocr_fallback")
                except Exception as ocr_error:
                    raise Exception(f"Both PDF reading and OCR failed: {e}, {ocr_error}")
            else:
                raise e
        
        full_text = "\n\n".join(text_content)
        return full_text, metadata
    
    def _process_image(self, file_path: Path) -> tuple[str, Dict[str, Any]]:
        """Process an image file using OCR"""
        if not self.ocr_enabled:
            raise ValueError("OCR is disabled but image processing was requested")
        
        metadata = {
            "file_type": "image",
            "format": file_path.suffix.lower(),
            "extraction_method": ["ocr"]
        }
        
        try:
            image = Image.open(file_path)
            metadata["image_size"] = image.size
            metadata["image_mode"] = image.mode
            
            extracted_text = self._ocr_image(image)
            return extracted_text, metadata
            
        except Exception as e:
            raise Exception(f"Image processing failed: {e}")
    
    def _process_bytes(self, data: bytes) -> tuple[str, Dict[str, Any]]:
        """Process document from bytes data"""
        metadata = {
            "file_type": "bytes",
            "size": len(data),
            "extraction_method": []
        }
        
        # Try to determine if it's a PDF or image
        if data.startswith(b'%PDF'):
            # It's a PDF
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(data))
                text_content = []
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content.append(page_text)
                        metadata["extraction_method"].append(f"page_{page_num}_direct")
                
                metadata["pages"] = len(pdf_reader.pages)
                return "\n\n".join(text_content), metadata
                
            except Exception as e:
                if self.ocr_enabled:
                    # Try OCR on PDF bytes
                    images = convert_from_bytes(data, dpi=self.image_dpi)
                    text_content = []
                    
                    for i, image in enumerate(images):
                        ocr_text = self._ocr_image(image)
                        if ocr_text:
                            text_content.append(ocr_text)
                            metadata["extraction_method"].append(f"page_{i}_ocr")
                    
                    return "\n\n".join(text_content), metadata
                else:
                    raise e
        else:
            # Assume it's an image
            if not self.ocr_enabled:
                raise ValueError("OCR is disabled but image processing was requested")
            
            image = Image.open(io.BytesIO(data))
            metadata["image_size"] = image.size
            metadata["image_mode"] = image.mode
            metadata["extraction_method"] = ["ocr"]
            
            extracted_text = self._ocr_image(image)
            return extracted_text, metadata
    
    def _ocr_pdf_page(self, file_path: Path, page_num: int) -> str:
        """Extract text from a specific PDF page using OCR"""
        try:
            images = convert_from_path(file_path, first_page=page_num+1, last_page=page_num+1, dpi=self.image_dpi)
            if images:
                return self._ocr_image(images[0])
        except Exception as e:
            self.logger.warning(f"OCR failed for PDF page {page_num}: {e}")
        return ""
    
    def _ocr_image(self, image) -> str:
        """Extract text from an image using OCR"""
        try:
            text = pytesseract.image_to_string(image, config=self.tesseract_config)
            return text.strip()
        except Exception as e:
            self.logger.warning(f"OCR failed: {e}")
            return ""
    
    def _calculate_confidence(self, text: str, metadata: Dict[str, Any]) -> float:
        """Calculate confidence score for extracted text"""
        if not text.strip():
            return 0.0
        
        confidence = 0.5  # Base confidence
        
        # Higher confidence for longer text
        if len(text) > 100:
            confidence += 0.2
        if len(text) > 500:
            confidence += 0.1
        
        # Higher confidence for direct PDF extraction
        if "direct" in str(metadata.get("extraction_method", [])):
            confidence += 0.2
        
        # Check for common invoice indicators
        invoice_keywords = ["invoice", "bill", "receipt", "total", "amount", "date", "due"]
        keyword_count = sum(1 for keyword in invoice_keywords if keyword.lower() in text.lower())
        confidence += min(keyword_count * 0.05, 0.2)
        
        return min(confidence, 1.0)
    
    def get_supported_formats(self) -> List[str]:
        """Return list of supported file formats"""
        return self.supported_formats.copy()