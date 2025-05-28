"""
Data Extraction Agent - Extracts structured data from invoice text using LLM
"""
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from agents.base_agent import BaseAgent
from models.processing_result import ProcessingResult
from models.invoice_model import Invoice, InvoiceLineItem, Address, TaxDetail


class DataExtractionAgent(BaseAgent):
    """Agent responsible for extracting structured data from invoice text"""
    
    def __init__(self, ollama_client=None):
        super().__init__("data_extraction", ollama_client)
        
        # Extraction settings
        self.date_formats = [
            "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%d-%m-%Y", "%B %d, %Y", "%b %d, %Y"
        ]
        
        self.logger.info("Data extraction agent initialized")
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate that the input contains extractable text"""
        if isinstance(input_data, str):
            return len(input_data.strip()) > 10
        elif isinstance(input_data, dict) and "raw_text" in input_data:
            return len(input_data["raw_text"].strip()) > 10
        return False
    
    def process(self, input_data: Union[str, Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """
        Extract structured data from invoice text
        
        Args:
            input_data: Raw text or context containing raw_text
            context: Optional context information
            
        Returns:
            ProcessingResult: Contains extracted invoice data
        """
        result = ProcessingResult()
        
        try:
            # Extract text from input
            if isinstance(input_data, str):
                raw_text = input_data
            elif context and "raw_text" in context:
                raw_text = context["raw_text"]
            else:
                raise ValueError("No raw text found in input or context")
            
            if not self.validate_input(raw_text):
                raise ValueError("Input text too short or empty")
            
            result.add_processing_step(
                agent=self.name,
                action="text_preprocessing",
                result=f"Processing {len(raw_text)} characters"
            )
            
            # Clean and preprocess text
            cleaned_text = self._preprocess_text(raw_text)
            
            # Extract structured data using LLM
            extracted_data = self._extract_with_llm(cleaned_text)
            
            # Post-process and validate extracted data
            processed_data = self._post_process_extraction(extracted_data, cleaned_text)
            
            # Create Invoice object
            invoice = self._create_invoice_object(processed_data)
            
            # Calculate confidence score
            confidence = self._calculate_extraction_confidence(processed_data, cleaned_text, invoice)
            result.confidence_score = confidence
            
            result.add_processing_step(
                agent=self.name,
                action="data_extraction",
                result=f"Extracted {len(processed_data)} fields",
                confidence=confidence
            )
            
            # Store results in context for next agents
            if context is not None:
                context["extracted_data"] = processed_data
                if invoice:
                    context["invoice"] = invoice
            
        except Exception as e:
            error_msg = f"Data extraction failed: {str(e)}"
            self.logger.error(error_msg)
            result.add_error(error_msg)
        
        return result
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess the raw text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize currency symbols
        text = re.sub(r'[$]', 'USD ', text)
        text = re.sub(r'[€]', 'EUR ', text)
        text = re.sub(r'[£]', 'GBP ', text)
        
        # Normalize date separators
        text = re.sub(r'(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})', r'\1/\2/\3', text)
        
        return text.strip()
    
    def _extract_with_llm(self, text: str) -> Dict[str, Any]:
        """Use Qwen2.5:14b LLM to extract structured data from text with enhanced validation"""
        
        # Enhanced schema for Qwen2.5
        schema = {
            "type": "object",
            "required": ["invoice_number", "date", "vendor_name", "total_amount"],
            "properties": {
                "invoice_number": {
                    "type": "string",
                    "description": "Invoice number or reference ID"
                },
                "date": {
                    "type": "string", 
                    "format": "date",
                    "description": "Invoice date in YYYY-MM-DD format"
                },
                "due_date": {
                    "type": "string", 
                    "format": "date",
                    "description": "Payment due date in YYYY-MM-DD format"
                },
                "vendor_name": {
                    "type": "string",
                    "description": "Supplier/vendor company name"
                },
                "vendor_address": {
                    "type": "string",
                    "description": "Complete vendor address"
                },
                "vendor_tax_id": {
                    "type": "string",
                    "description": "Vendor tax ID, VAT number, or EIN"
                },
                "buyer_name": {
                    "type": "string",
                    "description": "Customer/buyer company name"
                },
                "buyer_address": {
                    "type": "string",
                    "description": "Complete buyer address"
                },
                "line_items": {
                    "type": "array",
                    "description": "List of invoice line items",
                    "items": {
                        "type": "object",
                        "required": ["description", "quantity", "unit_price", "total"],
                        "properties": {
                            "description": {"type": "string"},
                            "quantity": {"type": "number"},
                            "unit_price": {"type": "number"},
                            "total": {"type": "number"}
                        }
                    }
                },
                "currency": {"type": "string"},
                "subtotal": {"type": "number"},
                "tax_amount": {"type": "number"},
                "total_amount": {"type": "number"},
                "region": {"type": "string"}
            }
        }
        
        try:
            # Use enhanced Qwen2.5 extraction with schema
            extracted_data = self.ollama_client.extract_structured_data(text[:3000], schema)
            
            # Validate extraction using Qwen2.5 validation
            if extracted_data:
                validation_result = self.ollama_client.validate_invoice_data(text[:2000], extracted_data)
                
                # Apply corrections if suggested
                if validation_result.get("corrections"):
                    for field, corrected_value in validation_result["corrections"].items():
                        if field in extracted_data:
                            self.logger.info(f"Applied Qwen2.5 correction for {field}: {corrected_value}")
                            extracted_data[field] = corrected_value
                
                # Store validation metadata
                extracted_data["_qwen_validation"] = {
                    "confidence": validation_result.get("confidence_score", 0.5),
                    "errors": validation_result.get("errors", []),
                    "warnings": validation_result.get("warnings", [])
                }
            
            return extracted_data
            
        except Exception as e:
            self.logger.error(f"Qwen2.5 extraction failed: {e}")
            return self._fallback_extraction(text)
    
    def _fallback_extraction(self, text: str) -> Dict[str, Any]:
        """Fallback rule-based extraction when LLM fails"""
        extracted = {}
        
        # Extract invoice number
        invoice_patterns = [
            r'invoice\s*#?\s*:?\s*([A-Z0-9\-]+)',
            r'inv\s*#?\s*:?\s*([A-Z0-9\-]+)',
            r'reference\s*#?\s*:?\s*([A-Z0-9\-]+)'
        ]
        for pattern in invoice_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted["invoice_number"] = match.group(1)
                break
        
        # Extract dates
        date_patterns = [
            r'invoice\s+date\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            r'date\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            r'due\s+date\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                if "due" in pattern:
                    extracted["due_date"] = self._parse_date(date_str)
                else:
                    extracted["date"] = self._parse_date(date_str)
        
        # Extract total amount
        total_patterns = [
            r'total\s*:?\s*[$€£]?(\d+[,.]?\d*)',
            r'amount\s+due\s*:?\s*[$€£]?(\d+[,.]?\d*)',
            r'balance\s+due\s*:?\s*[$€£]?(\d+[,.]?\d*)'
        ]
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    extracted["total_amount"] = float(amount_str)
                    break
                except ValueError:
                    continue
        
        # Extract currency
        if 'USD' in text or '$' in text:
            extracted["currency"] = "USD"
        elif 'EUR' in text or '€' in text:
            extracted["currency"] = "EUR"
        elif 'GBP' in text or '£' in text:
            extracted["currency"] = "GBP"
        else:
            extracted["currency"] = "USD"  # Default
        
        return extracted
    
    def _post_process_extraction(self, data: Dict[str, Any], original_text: str) -> Dict[str, Any]:
        """Post-process and validate extracted data"""
        processed = data.copy()
        
        # Validate and format dates
        for date_field in ["date", "due_date"]:
            if date_field in processed:
                parsed_date = self._parse_date(processed[date_field])
                if parsed_date:
                    processed[date_field] = parsed_date
                else:
                    processed.pop(date_field, None)
        
        # Validate amounts
        for amount_field in ["subtotal", "total_tax", "discount_amount", "total_amount"]:
            if amount_field in processed:
                try:
                    amount = float(str(processed[amount_field]).replace(',', ''))
                    processed[amount_field] = amount
                except (ValueError, TypeError):
                    processed.pop(amount_field, None)
        
        # Process line items
        if "line_items" in processed and isinstance(processed["line_items"], list):
            valid_items = []
            for item in processed["line_items"]:
                if isinstance(item, dict) and "description" in item:
                    # Validate numeric fields
                    for field in ["quantity", "unit_price", "total"]:
                        if field in item:
                            try:
                                item[field] = float(str(item[field]).replace(',', ''))
                            except (ValueError, TypeError):
                                item.pop(field, None)
                    valid_items.append(item)
            processed["line_items"] = valid_items
        
        # Set defaults
        if "currency" not in processed:
            processed["currency"] = "USD"
        
        if "region" not in processed:
            processed["region"] = "US"
        
        return processed
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string into datetime object"""
        if not date_str:
            return None
        
        date_str = str(date_str).strip()
        
        for fmt in self.date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Try some common variations
        try:
            # Handle formats like "Jan 15, 2024"
            return datetime.strptime(date_str, "%b %d, %Y")
        except ValueError:
            pass
        
        return None
    
    def _create_invoice_object(self, data: Dict[str, Any]) -> Optional[Invoice]:
        """Create an Invoice object from extracted data"""
        try:
            # Prepare vendor address
            vendor_address = None
            if data.get("vendor_address"):
                # Simple address parsing - could be enhanced
                addr_parts = data["vendor_address"].split(",")
                vendor_address = Address(
                    street=addr_parts[0].strip() if len(addr_parts) > 0 else None,
                    city=addr_parts[1].strip() if len(addr_parts) > 1 else None,
                    state=addr_parts[2].strip() if len(addr_parts) > 2 else None,
                    country=addr_parts[-1].strip() if len(addr_parts) > 3 else None
                )
            
            # Prepare buyer address
            buyer_address = None
            if data.get("buyer_address"):
                addr_parts = data["buyer_address"].split(",")
                buyer_address = Address(
                    street=addr_parts[0].strip() if len(addr_parts) > 0 else None,
                    city=addr_parts[1].strip() if len(addr_parts) > 1 else None,
                    state=addr_parts[2].strip() if len(addr_parts) > 2 else None,
                    country=addr_parts[-1].strip() if len(addr_parts) > 3 else None
                )
            
            # Prepare line items
            line_items = []
            if "line_items" in data and isinstance(data["line_items"], list):
                for item_data in data["line_items"]:
                    if isinstance(item_data, dict) and item_data.get("description"):
                        line_item = InvoiceLineItem(
                            description=item_data["description"],
                            quantity=item_data.get("quantity", 1.0),
                            unit_price=item_data.get("unit_price", 0.0),
                            total=item_data.get("total", 0.0)
                        )
                        line_items.append(line_item)
            
            # Calculate missing values
            subtotal = data.get("subtotal", 0.0)
            total_tax = data.get("total_tax", 0.0)
            discount_amount = data.get("discount_amount", 0.0)
            total_amount = data.get("total_amount", 0.0)
            
            # If we have line items but no subtotal, calculate it
            if line_items and not subtotal:
                subtotal = sum(item.total for item in line_items)
            
            # If we have subtotal and total but no tax, calculate it
            if subtotal and total_amount and not total_tax:
                total_tax = total_amount - subtotal + discount_amount
            
            # Create invoice
            invoice = Invoice(
                invoice_number=data.get("invoice_number", ""),
                date=data.get("date", datetime.now()),
                due_date=data.get("due_date"),
                vendor_name=data.get("vendor_name", ""),
                vendor_address=vendor_address,
                vendor_tax_id=data.get("vendor_tax_id"),
                vendor_email=data.get("vendor_email"),
                vendor_phone=data.get("vendor_phone"),
                buyer_name=data.get("buyer_name", ""),
                buyer_address=buyer_address,
                buyer_tax_id=data.get("buyer_tax_id"),
                buyer_email=data.get("buyer_email"),
                buyer_phone=data.get("buyer_phone"),
                line_items=line_items,
                currency=data.get("currency", "USD"),
                subtotal=subtotal,
                total_tax=total_tax,
                discount_amount=discount_amount,
                total_amount=total_amount,
                region=data.get("region", "US")
            )
            
            return invoice
            
        except Exception as e:
            self.logger.error(f"Failed to create Invoice object: {e}")
            return None
    
    def _calculate_extraction_confidence(self, data: Dict[str, Any], text: str, invoice: Optional[Invoice]) -> float:
        """Calculate confidence score for the extraction"""
        confidence = 0.0
        
        # Base confidence for having extracted data
        if data:
            confidence += 0.3
        
        # Critical fields present
        critical_fields = ["invoice_number", "total_amount", "vendor_name"]
        present_critical = sum(1 for field in critical_fields if field in data and data[field])
        confidence += (present_critical / len(critical_fields)) * 0.4
        
        # Additional fields boost confidence
        optional_fields = ["date", "due_date", "buyer_name", "line_items"]
        present_optional = sum(1 for field in optional_fields if field in data and data[field])
        confidence += (present_optional / len(optional_fields)) * 0.2
        
        # Valid Invoice object created
        if invoice:
            confidence += 0.1
        
        return min(confidence, 1.0)