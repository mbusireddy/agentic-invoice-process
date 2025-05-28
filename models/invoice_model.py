"""
Data models for invoice processing
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class ProcessingStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    VALIDATED = "validated"
    APPROVED = "approved"
    REJECTED = "rejected"
    ERROR = "error"


class InvoiceLineItem:
    """Individual line item in an invoice"""
    def __init__(self, description: str, quantity: float, unit_price: float, 
                 total: float, tax_rate: Optional[float] = None, 
                 tax_amount: Optional[float] = None):
        self.description = description
        self.quantity = quantity
        self.unit_price = unit_price
        self.total = total
        self.tax_rate = tax_rate
        self.tax_amount = tax_amount
        
        # Validate total
        expected_total = quantity * unit_price
        if abs(total - expected_total) > 0.01:
            raise ValueError(f"Total {total} doesn't match quantity * unit_price {expected_total}")


class Address:
    """Address information"""
    def __init__(self, street: Optional[str] = None, city: Optional[str] = None,
                 state: Optional[str] = None, postal_code: Optional[str] = None,
                 country: Optional[str] = None):
        self.street = street
        self.city = city
        self.state = state
        self.postal_code = postal_code
        self.country = country

    def __str__(self):
        parts = [self.street, self.city, self.state, self.postal_code, self.country]
        return ", ".join([part for part in parts if part])


class TaxDetail:
    """Tax details"""
    def __init__(self, tax_type: str, tax_rate: float, taxable_amount: float, tax_amount: float):
        self.tax_type = tax_type
        self.tax_rate = tax_rate
        self.taxable_amount = taxable_amount
        self.tax_amount = tax_amount


class Invoice:
    """Complete invoice data model"""
    def __init__(self, invoice_number: str, date: datetime, vendor_name: str, buyer_name: str,
                 line_items: List[InvoiceLineItem], currency: str, subtotal: float, 
                 total_tax: float, total_amount: float, region: str,
                 due_date: Optional[datetime] = None,
                 vendor_address: Optional[Address] = None,
                 vendor_tax_id: Optional[str] = None,
                 vendor_email: Optional[str] = None,
                 vendor_phone: Optional[str] = None,
                 buyer_address: Optional[Address] = None,
                 buyer_tax_id: Optional[str] = None,
                 buyer_email: Optional[str] = None,
                 buyer_phone: Optional[str] = None,
                 tax_details: Optional[List[TaxDetail]] = None,
                 discount_amount: Optional[float] = 0,
                 processing_status: ProcessingStatus = ProcessingStatus.PENDING,
                 confidence_score: Optional[float] = None,
                 source_file: Optional[str] = None,
                 processed_at: Optional[datetime] = None,
                 processed_by: Optional[str] = None):
        
        # Basic Information
        self.invoice_number = invoice_number
        self.date = date
        self.due_date = due_date
        
        # Vendor Information
        self.vendor_name = vendor_name
        self.vendor_address = vendor_address
        self.vendor_tax_id = vendor_tax_id
        self.vendor_email = vendor_email
        self.vendor_phone = vendor_phone
        
        # Buyer Information
        self.buyer_name = buyer_name
        self.buyer_address = buyer_address
        self.buyer_tax_id = buyer_tax_id
        self.buyer_email = buyer_email
        self.buyer_phone = buyer_phone
        
        # Line Items
        self.line_items = line_items or []
        
        # Financial Information
        self.currency = currency
        self.subtotal = subtotal
        self.tax_details = tax_details or []
        self.total_tax = total_tax
        self.discount_amount = discount_amount or 0
        self.total_amount = total_amount
        
        # Processing Information
        self.region = region
        self.processing_status = processing_status
        self.confidence_score = confidence_score
        
        # Metadata
        self.source_file = source_file
        self.processed_at = processed_at
        self.processed_by = processed_by
        
        # Validate totals
        if line_items:
            items_total = sum(item.total for item in line_items)
            if abs(items_total - subtotal) > 0.01:
                raise ValueError(f"Line items total {items_total} doesn't match subtotal {subtotal}")
        
        expected_total = subtotal + total_tax - self.discount_amount
        if abs(total_amount - expected_total) > 0.01:
            raise ValueError(f"Total amount {total_amount} doesn't match calculated total {expected_total}")


class ProcessingResult:
    """Result of invoice processing"""
    def __init__(self):
        self.invoice: Optional[Invoice] = None
        self.status: ProcessingStatus = ProcessingStatus.PENDING
        self.confidence_score: float = 0.0
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.processing_steps: List[Dict[str, Any]] = []
        self.processing_time: Optional[float] = None

    def add_error(self, error: str):
        """Add an error to the result"""
        self.errors.append(error)
        if self.status != ProcessingStatus.ERROR:
            self.status = ProcessingStatus.ERROR

    def add_warning(self, warning: str):
        """Add a warning to the result"""
        self.warnings.append(warning)

    def add_processing_step(self, agent: str, action: str, result: str, confidence: float = None):
        """Add a processing step"""
        step = {
            "agent": agent,
            "action": action,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        if confidence is not None:
            step["confidence"] = confidence
        self.processing_steps.append(step)

    def is_successful(self) -> bool:
        """Check if processing was successful"""
        return self.status in [ProcessingStatus.VALIDATED, ProcessingStatus.APPROVED] and not self.errors

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the processing result"""
        return {
            "status": self.status.value,
            "confidence_score": self.confidence_score,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "processing_steps": len(self.processing_steps),
            "has_invoice": self.invoice is not None,
            "processing_time": self.processing_time
        }