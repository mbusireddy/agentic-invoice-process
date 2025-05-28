"""
Validation Agent - Validates extracted invoice data for accuracy and completeness
"""
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from agents.base_agent import BaseAgent
from models.processing_result import ProcessingResult
from models.invoice_model import Invoice, ProcessingStatus


class ValidationAgent(BaseAgent):
    """Agent responsible for validating extracted invoice data"""
    
    def __init__(self, ollama_client=None):
        super().__init__("validation", ollama_client)
        
        # Validation settings
        self.required_fields = ["invoice_number", "vendor_name", "buyer_name", "total_amount", "currency"]
        self.date_tolerance_days = 365  # Allow dates within 1 year
        self.amount_precision = 2
        self.supported_currencies = ["USD", "EUR", "GBP", "CAD", "AUD", "JPY"]
        
        self.logger.info("Validation agent initialized")
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate that the input contains an invoice object"""
        if isinstance(input_data, Invoice):
            return True
        elif isinstance(input_data, dict) and "invoice" in input_data:
            return True
        return False
    
    def process(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """
        Validate extracted invoice data
        
        Args:
            input_data: Invoice object or context containing invoice
            context: Optional context information
            
        Returns:
            ProcessingResult: Validation results and any corrections
        """
        result = ProcessingResult()
        
        try:
            # Extract invoice from input
            if isinstance(input_data, Invoice):
                invoice = input_data
            elif context and "invoice" in context:
                invoice = context["invoice"]
            else:
                raise ValueError("No invoice found in input or context")
            
            result.add_processing_step(
                agent=self.name,
                action="validation_started",
                result=f"Validating invoice {invoice.invoice_number}"
            )
            
            # Perform validation checks
            validation_results = self._validate_invoice(invoice)
            
            # Calculate overall validation score
            validation_score = self._calculate_validation_score(validation_results)
            result.confidence_score = validation_score
            
            # Determine processing status based on validation
            if validation_score >= 0.9:
                invoice.processing_status = ProcessingStatus.VALIDATED
                status_msg = "Invoice passed validation"
            elif validation_score >= 0.7:
                invoice.processing_status = ProcessingStatus.VALIDATED
                status_msg = "Invoice passed validation with warnings"
            else:
                invoice.processing_status = ProcessingStatus.ERROR
                status_msg = "Invoice failed validation"
            
            result.add_processing_step(
                agent=self.name,
                action="validation_completed",
                result=status_msg,
                confidence=validation_score
            )
            
            # Store validation results
            if context is not None:
                context["validation_results"] = validation_results
                context["invoice"] = invoice
            
            # Add any validation errors
            for check_result in validation_results:
                if check_result["status"] == "error":
                    result.add_error(f"Validation error: {check_result['message']}")
                elif check_result["status"] == "warning":
                    result.add_warning(f"Validation warning: {check_result['message']}")
            
        except Exception as e:
            error_msg = f"Validation failed: {str(e)}"
            self.logger.error(error_msg)
            result.add_error(error_msg)
        
        return result
    
    def _validate_invoice(self, invoice: Invoice) -> List[Dict[str, Any]]:
        """Perform comprehensive validation of the invoice"""
        validation_results = []
        
        # Check required fields
        validation_results.extend(self._validate_required_fields(invoice))
        
        # Validate data formats
        validation_results.extend(self._validate_data_formats(invoice))
        
        # Validate business logic
        validation_results.extend(self._validate_business_logic(invoice))
        
        # Validate mathematical calculations
        validation_results.extend(self._validate_calculations(invoice))
        
        # Validate line items
        validation_results.extend(self._validate_line_items(invoice))
        
        return validation_results
    
    def _validate_required_fields(self, invoice: Invoice) -> List[Dict[str, Any]]:
        """Validate that all required fields are present"""
        results = []
        
        for field in self.required_fields:
            value = getattr(invoice, field, None)
            if not value:
                results.append({
                    "check": "required_fields",
                    "field": field,
                    "status": "error",
                    "message": f"Required field '{field}' is missing or empty",
                    "severity": "high"
                })
            else:
                results.append({
                    "check": "required_fields",
                    "field": field,
                    "status": "pass",
                    "message": f"Required field '{field}' is present",
                    "severity": "low"
                })
        
        return results
    
    def _validate_data_formats(self, invoice: Invoice) -> List[Dict[str, Any]]:
        """Validate data formats and types"""
        results = []
        
        # Validate invoice number format
        if invoice.invoice_number:
            if not re.match(r'^[A-Z0-9\-_#]+$', invoice.invoice_number):
                results.append({
                    "check": "data_formats",
                    "field": "invoice_number",
                    "status": "warning",
                    "message": "Invoice number contains unusual characters",
                    "severity": "low"
                })
            else:
                results.append({
                    "check": "data_formats",
                    "field": "invoice_number",
                    "status": "pass",
                    "message": "Invoice number format is valid",
                    "severity": "low"
                })
        
        # Validate dates
        if invoice.date:
            if not self._is_reasonable_date(invoice.date):
                results.append({
                    "check": "data_formats",
                    "field": "date",
                    "status": "error",
                    "message": "Invoice date is unreasonable or outside acceptable range",
                    "severity": "high"
                })
            else:
                results.append({
                    "check": "data_formats",
                    "field": "date",
                    "status": "pass",
                    "message": "Invoice date is valid",
                    "severity": "low"
                })
        
        if invoice.due_date:
            if not self._is_reasonable_date(invoice.due_date):
                results.append({
                    "check": "data_formats",
                    "field": "due_date",
                    "status": "error",
                    "message": "Due date is unreasonable or outside acceptable range",
                    "severity": "high"
                })
            elif invoice.date and invoice.due_date < invoice.date:
                results.append({
                    "check": "data_formats",
                    "field": "due_date",
                    "status": "error",
                    "message": "Due date cannot be before invoice date",
                    "severity": "high"
                })
            else:
                results.append({
                    "check": "data_formats",
                    "field": "due_date",
                    "status": "pass",
                    "message": "Due date is valid",
                    "severity": "low"
                })
        
        # Validate currency
        if invoice.currency:
            if invoice.currency not in self.supported_currencies:
                results.append({
                    "check": "data_formats",
                    "field": "currency",
                    "status": "warning",
                    "message": f"Currency '{invoice.currency}' is not in supported list",
                    "severity": "medium"
                })
            else:
                results.append({
                    "check": "data_formats",
                    "field": "currency",
                    "status": "pass",
                    "message": "Currency is supported",
                    "severity": "low"
                })
        
        # Validate email formats
        if invoice.vendor_email and not self._is_valid_email(invoice.vendor_email):
            results.append({
                "check": "data_formats",
                "field": "vendor_email",
                "status": "warning",
                "message": "Vendor email format appears invalid",
                "severity": "medium"
            })
        
        if invoice.buyer_email and not self._is_valid_email(invoice.buyer_email):
            results.append({
                "check": "data_formats",
                "field": "buyer_email",
                "status": "warning",
                "message": "Buyer email format appears invalid",
                "severity": "medium"
            })
        
        return results
    
    def _validate_business_logic(self, invoice: Invoice) -> List[Dict[str, Any]]:
        """Validate business logic rules"""
        results = []
        
        # Check for duplicate invoice numbers (would need external data source)
        # For now, just validate format uniqueness characteristics
        
        # Validate vendor and buyer are different
        if invoice.vendor_name and invoice.buyer_name:
            if invoice.vendor_name.lower() == invoice.buyer_name.lower():
                results.append({
                    "check": "business_logic",
                    "field": "vendor_buyer",
                    "status": "warning",
                    "message": "Vendor and buyer appear to be the same entity",
                    "severity": "medium"
                })
            else:
                results.append({
                    "check": "business_logic",
                    "field": "vendor_buyer",
                    "status": "pass",
                    "message": "Vendor and buyer are different entities",
                    "severity": "low"
                })
        
        # Validate reasonable amounts
        if invoice.total_amount:
            if invoice.total_amount <= 0:
                results.append({
                    "check": "business_logic",
                    "field": "total_amount",
                    "status": "error",
                    "message": "Total amount must be positive",
                    "severity": "high"
                })
            elif invoice.total_amount > 1000000:  # $1M limit
                results.append({
                    "check": "business_logic",
                    "field": "total_amount",
                    "status": "warning",
                    "message": "Total amount is very high - please verify",
                    "severity": "medium"
                })
            else:
                results.append({
                    "check": "business_logic",
                    "field": "total_amount",
                    "status": "pass",
                    "message": "Total amount is reasonable",
                    "severity": "low"
                })
        
        return results
    
    def _validate_calculations(self, invoice: Invoice) -> List[Dict[str, Any]]:
        """Validate mathematical calculations"""
        results = []
        
        # Validate line items sum to subtotal
        if invoice.line_items and invoice.subtotal:
            calculated_subtotal = sum(item.total for item in invoice.line_items)
            diff = abs(calculated_subtotal - invoice.subtotal)
            
            if diff > 0.01:  # Allow for small rounding differences
                results.append({
                    "check": "calculations",
                    "field": "subtotal",
                    "status": "error",
                    "message": f"Line items total ({calculated_subtotal}) doesn't match subtotal ({invoice.subtotal})",
                    "severity": "high"
                })
            else:
                results.append({
                    "check": "calculations",
                    "field": "subtotal",
                    "status": "pass",
                    "message": "Line items sum matches subtotal",
                    "severity": "low"
                })
        
        # Validate total calculation
        if invoice.subtotal and invoice.total_tax is not None and invoice.total_amount:
            discount = invoice.discount_amount or 0
            calculated_total = invoice.subtotal + invoice.total_tax - discount
            diff = abs(calculated_total - invoice.total_amount)
            
            if diff > 0.01:
                results.append({
                    "check": "calculations",
                    "field": "total_amount",
                    "status": "error",
                    "message": f"Calculated total ({calculated_total}) doesn't match stated total ({invoice.total_amount})",
                    "severity": "high"
                })
            else:
                results.append({
                    "check": "calculations",
                    "field": "total_amount",
                    "status": "pass",
                    "message": "Total amount calculation is correct",
                    "severity": "low"
                })
        
        return results
    
    def _validate_line_items(self, invoice: Invoice) -> List[Dict[str, Any]]:
        """Validate individual line items"""
        results = []
        
        if not invoice.line_items:
            results.append({
                "check": "line_items",
                "field": "line_items",
                "status": "warning",
                "message": "No line items found",
                "severity": "medium"
            })
            return results
        
        for i, item in enumerate(invoice.line_items):
            # Validate line item calculations
            calculated_total = item.quantity * item.unit_price
            diff = abs(calculated_total - item.total)
            
            if diff > 0.01:
                results.append({
                    "check": "line_items",
                    "field": f"line_item_{i}",
                    "status": "error",
                    "message": f"Line item {i+1}: calculated total ({calculated_total}) doesn't match stated total ({item.total})",
                    "severity": "high"
                })
            
            # Validate positive values
            if item.quantity <= 0:
                results.append({
                    "check": "line_items",
                    "field": f"line_item_{i}",
                    "status": "error",
                    "message": f"Line item {i+1}: quantity must be positive",
                    "severity": "high"
                })
            
            if item.unit_price < 0:
                results.append({
                    "check": "line_items",
                    "field": f"line_item_{i}",
                    "status": "error",
                    "message": f"Line item {i+1}: unit price cannot be negative",
                    "severity": "high"
                })
            
            # Validate description
            if not item.description or len(item.description.strip()) < 3:
                results.append({
                    "check": "line_items",
                    "field": f"line_item_{i}",
                    "status": "warning",
                    "message": f"Line item {i+1}: description is too short or missing",
                    "severity": "medium"
                })
        
        return results
    
    def _is_reasonable_date(self, date: datetime) -> bool:
        """Check if a date is within reasonable bounds"""
        now = datetime.now()
        min_date = now - timedelta(days=self.date_tolerance_days)
        max_date = now + timedelta(days=self.date_tolerance_days)
        
        return min_date <= date <= max_date
    
    def _is_valid_email(self, email: str) -> bool:
        """Basic email format validation"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _calculate_validation_score(self, validation_results: List[Dict[str, Any]]) -> float:
        """Calculate overall validation score based on results"""
        if not validation_results:
            return 0.0
        
        total_score = 0.0
        max_score = 0.0
        
        for result in validation_results:
            severity = result.get("severity", "low")
            status = result.get("status", "error")
            
            # Weight by severity
            weight = {"low": 1.0, "medium": 2.0, "high": 3.0}.get(severity, 1.0)
            max_score += weight
            
            # Score by status
            if status == "pass":
                total_score += weight
            elif status == "warning":
                total_score += weight * 0.7
            # Errors get 0 points
        
        return total_score / max_score if max_score > 0 else 0.0