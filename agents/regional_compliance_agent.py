"""
Regional Compliance Agent - Applies region-specific rules and regulations
"""
import re
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent
from models.processing_result import ProcessingResult
from models.invoice_model import Invoice, ProcessingStatus
from config.regional_rules import (
    get_regional_rules, get_validation_rules, validate_region,
    get_supported_currencies, get_tax_types, get_approval_limits
)


class RegionalComplianceAgent(BaseAgent):
    """Agent responsible for applying region-specific compliance rules"""
    
    def __init__(self, ollama_client=None):
        super().__init__("regional_compliance", ollama_client)
        
        self.validation_rules = get_validation_rules()
        
        self.logger.info("Regional compliance agent initialized")
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate that the input contains an invoice object"""
        if isinstance(input_data, Invoice):
            return True
        elif isinstance(input_data, dict) and "invoice" in input_data:
            return True
        return False
    
    def process(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """
        Apply regional compliance rules to the invoice
        
        Args:
            input_data: Invoice object or context containing invoice
            context: Optional context information
            
        Returns:
            ProcessingResult: Compliance check results
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
            
            # Determine region
            region = invoice.region or "US"
            if not validate_region(region):
                region = "US"
                result.add_warning(f"Invalid region, defaulting to US")
            
            result.add_processing_step(
                agent=self.name,
                action="compliance_check_started",
                result=f"Checking compliance for region {region}"
            )
            
            # Get regional rules
            regional_rules = get_regional_rules(region)
            
            # Perform compliance checks
            compliance_results = self._check_compliance(invoice, region, regional_rules)
            
            # Calculate compliance score
            compliance_score = self._calculate_compliance_score(compliance_results)
            result.confidence_score = compliance_score
            
            # Determine approval requirements
            approval_info = self._determine_approval_requirements(invoice, region)
            
            # Update processing status based on compliance
            if compliance_score >= 0.9:
                status_msg = "Invoice meets regional compliance requirements"
            elif compliance_score >= 0.7:
                status_msg = "Invoice has minor compliance issues"
            else:
                invoice.processing_status = ProcessingStatus.ERROR
                status_msg = "Invoice fails regional compliance"
            
            result.add_processing_step(
                agent=self.name,
                action="compliance_check_completed",
                result=status_msg,
                confidence=compliance_score
            )
            
            # Store compliance results
            if context is not None:
                context["compliance_results"] = compliance_results
                context["approval_info"] = approval_info
                context["invoice"] = invoice
            
            # Add compliance errors and warnings
            for check_result in compliance_results:
                if check_result["status"] == "error":
                    result.add_error(f"Compliance error: {check_result['message']}")
                elif check_result["status"] == "warning":
                    result.add_warning(f"Compliance warning: {check_result['message']}")
            
        except Exception as e:
            error_msg = f"Regional compliance check failed: {str(e)}"
            self.logger.error(error_msg)
            result.add_error(error_msg)
        
        return result
    
    def _check_compliance(self, invoice: Invoice, region: str, regional_rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform comprehensive compliance checks"""
        compliance_results = []
        
        # Check currency compliance
        compliance_results.extend(self._check_currency_compliance(invoice, region, regional_rules))
        
        # Check tax compliance
        compliance_results.extend(self._check_tax_compliance(invoice, region, regional_rules))
        
        # Check required fields
        compliance_results.extend(self._check_required_fields(invoice, regional_rules))
        
        # Check vendor/buyer requirements
        compliance_results.extend(self._check_entity_requirements(invoice, region, regional_rules))
        
        # Check amount limits
        compliance_results.extend(self._check_amount_limits(invoice, regional_rules))
        
        # Check date format compliance
        compliance_results.extend(self._check_date_compliance(invoice, regional_rules))
        
        return compliance_results
    
    def _check_currency_compliance(self, invoice: Invoice, region: str, regional_rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check currency compliance for the region"""
        results = []
        
        supported_currencies = regional_rules.get("currency", ["USD"])
        
        if invoice.currency not in supported_currencies:
            results.append({
                "check": "currency_compliance",
                "status": "error",
                "message": f"Currency '{invoice.currency}' not supported in region {region}. Supported: {supported_currencies}",
                "severity": "high"
            })
        else:
            results.append({
                "check": "currency_compliance",
                "status": "pass",
                "message": f"Currency '{invoice.currency}' is supported in region {region}",
                "severity": "low"
            })
        
        return results
    
    def _check_tax_compliance(self, invoice: Invoice, region: str, regional_rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check tax compliance for the region"""
        results = []
        
        tax_rates = regional_rules.get("tax_rates", {})
        expected_tax_types = regional_rules.get("tax_types", [])
        
        # Check if tax amount is reasonable
        if invoice.subtotal and invoice.total_tax is not None:
            if invoice.subtotal > 0:
                actual_tax_rate = invoice.total_tax / invoice.subtotal
                standard_rate = tax_rates.get("standard", 0.08)
                max_rate = standard_rate * 1.5  # Allow some flexibility
                
                if actual_tax_rate > max_rate:
                    results.append({
                        "check": "tax_compliance",
                        "status": "warning",
                        "message": f"Tax rate ({actual_tax_rate:.2%}) seems high for region {region} (standard: {standard_rate:.2%})",
                        "severity": "medium"
                    })
                elif actual_tax_rate < 0:
                    results.append({
                        "check": "tax_compliance",
                        "status": "error",
                        "message": "Tax amount cannot be negative",
                        "severity": "high"
                    })
                else:
                    results.append({
                        "check": "tax_compliance",
                        "status": "pass",
                        "message": f"Tax rate ({actual_tax_rate:.2%}) is within acceptable range for region {region}",
                        "severity": "low"
                    })
        
        return results
    
    def _check_required_fields(self, invoice: Invoice, regional_rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check region-specific required fields"""
        results = []
        
        required_fields = regional_rules.get("required_fields", [])
        
        # Map invoice fields to regional field names
        field_mapping = {
            "invoice_number": invoice.invoice_number,
            "date": invoice.date,
            "vendor_name": invoice.vendor_name,
            "vendor_address": invoice.vendor_address,
            "vendor_tax_id": invoice.vendor_tax_id,
            "vendor_vat_number": invoice.vendor_tax_id,  # EU specific
            "vendor_gstin": invoice.vendor_tax_id,       # APAC specific
            "buyer_name": invoice.buyer_name,
            "buyer_address": invoice.buyer_address,
            "buyer_tax_id": invoice.buyer_tax_id,
            "buyer_vat_number": invoice.buyer_tax_id,    # EU specific
            "buyer_gstin": invoice.buyer_tax_id,         # APAC specific
            "line_items": invoice.line_items,
            "subtotal": invoice.subtotal,
            "tax_amount": invoice.total_tax,
            "vat_amount": invoice.total_tax,             # EU specific
            "total_amount": invoice.total_amount
        }
        
        for field in required_fields:
            value = field_mapping.get(field)
            if not value:
                results.append({
                    "check": "required_fields",
                    "status": "error",
                    "message": f"Regional required field '{field}' is missing or empty",
                    "severity": "high"
                })
            else:
                results.append({
                    "check": "required_fields",
                    "status": "pass",
                    "message": f"Regional required field '{field}' is present",
                    "severity": "low"
                })
        
        return results
    
    def _check_entity_requirements(self, invoice: Invoice, region: str, regional_rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check vendor/buyer specific requirements for the region"""
        results = []
        
        vendor_validation = regional_rules.get("vendor_validation", {})
        
        # Check vendor tax ID format if required
        if vendor_validation.get("require_tax_id") and invoice.vendor_tax_id:
            tax_id_pattern = vendor_validation.get("tax_id_format")
            if tax_id_pattern and not re.match(tax_id_pattern, invoice.vendor_tax_id):
                results.append({
                    "check": "entity_requirements",
                    "status": "error",
                    "message": f"Vendor tax ID format invalid for region {region}",
                    "severity": "high"
                })
            else:
                results.append({
                    "check": "entity_requirements",
                    "status": "pass",
                    "message": f"Vendor tax ID format valid for region {region}",
                    "severity": "low"
                })
        
        # Check VAT number format for EU
        if vendor_validation.get("require_vat_number") and invoice.vendor_tax_id:
            vat_pattern = vendor_validation.get("vat_number_format")
            if vat_pattern and not re.match(vat_pattern, invoice.vendor_tax_id):
                results.append({
                    "check": "entity_requirements",
                    "status": "error",
                    "message": f"Vendor VAT number format invalid for region {region}",
                    "severity": "high"
                })
            else:
                results.append({
                    "check": "entity_requirements",
                    "status": "pass",
                    "message": f"Vendor VAT number format valid for region {region}",
                    "severity": "low"
                })
        
        # Check GSTIN format for APAC
        if vendor_validation.get("require_gstin") and invoice.vendor_tax_id:
            gstin_pattern = vendor_validation.get("gstin_format")
            if gstin_pattern and not re.match(gstin_pattern, invoice.vendor_tax_id):
                results.append({
                    "check": "entity_requirements",
                    "status": "error",
                    "message": f"Vendor GSTIN format invalid for region {region}",
                    "severity": "high"
                })
            else:
                results.append({
                    "check": "entity_requirements",
                    "status": "pass",
                    "message": f"Vendor GSTIN format valid for region {region}",
                    "severity": "low"
                })
        
        return results
    
    def _check_amount_limits(self, invoice: Invoice, regional_rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check amount limits for the region"""
        results = []
        
        amount_validation = regional_rules.get("amount_validation", {})
        
        if invoice.total_amount:
            max_amount = amount_validation.get("max_amount")
            min_amount = amount_validation.get("min_amount", 0.01)
            
            if max_amount and invoice.total_amount > max_amount:
                results.append({
                    "check": "amount_limits",
                    "status": "error",
                    "message": f"Total amount ({invoice.total_amount}) exceeds regional limit ({max_amount})",
                    "severity": "high"
                })
            elif invoice.total_amount < min_amount:
                results.append({
                    "check": "amount_limits",
                    "status": "error",
                    "message": f"Total amount ({invoice.total_amount}) below regional minimum ({min_amount})",
                    "severity": "high"
                })
            else:
                results.append({
                    "check": "amount_limits",
                    "status": "pass",
                    "message": f"Total amount ({invoice.total_amount}) within regional limits",
                    "severity": "low"
                })
        
        return results
    
    def _check_date_compliance(self, invoice: Invoice, regional_rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check date format compliance (informational)"""
        results = []
        
        date_format = regional_rules.get("date_format", "MM/DD/YYYY")
        
        # This is informational - the actual date parsing happens in data extraction
        results.append({
            "check": "date_compliance",
            "status": "info",
            "message": f"Regional date format preference: {date_format}",
            "severity": "low"
        })
        
        return results
    
    def _determine_approval_requirements(self, invoice: Invoice, region: str) -> Dict[str, Any]:
        """Determine approval requirements based on regional rules and amount"""
        approval_limits = get_approval_limits(region)
        
        approval_info = {
            "region": region,
            "amount": invoice.total_amount,
            "required_approver": "system",
            "approval_level": "auto",
            "reason": "Within auto-approval limits"
        }
        
        if not approval_limits:
            approval_info["required_approver"] = "manager"
            approval_info["approval_level"] = "manual"
            approval_info["reason"] = "No approval limits defined for region"
            return approval_info
        
        auto_limit = approval_limits.get("auto_approve_limit", 0)
        manager_limit = approval_limits.get("manager_approval_limit", 10000)
        executive_limit = approval_limits.get("executive_approval_limit", 50000)
        
        if invoice.total_amount <= auto_limit:
            approval_info["required_approver"] = "system"
            approval_info["approval_level"] = "auto"
        elif invoice.total_amount <= manager_limit:
            approval_info["required_approver"] = "manager"
            approval_info["approval_level"] = "manager"
            approval_info["reason"] = f"Amount exceeds auto-approval limit ({auto_limit})"
        elif invoice.total_amount <= executive_limit:
            approval_info["required_approver"] = "executive"
            approval_info["approval_level"] = "executive"
            approval_info["reason"] = f"Amount exceeds manager approval limit ({manager_limit})"
        else:
            approval_info["required_approver"] = "board"
            approval_info["approval_level"] = "board"
            approval_info["reason"] = f"Amount exceeds executive approval limit ({executive_limit})"
        
        return approval_info
    
    def _calculate_compliance_score(self, compliance_results: List[Dict[str, Any]]) -> float:
        """Calculate overall compliance score"""
        if not compliance_results:
            return 0.0
        
        total_score = 0.0
        max_score = 0.0
        
        for result in compliance_results:
            severity = result.get("severity", "low")
            status = result.get("status", "error")
            
            # Skip informational messages
            if status == "info":
                continue
            
            # Weight by severity
            weight = {"low": 1.0, "medium": 2.0, "high": 3.0}.get(severity, 1.0)
            max_score += weight
            
            # Score by status
            if status == "pass":
                total_score += weight
            elif status == "warning":
                total_score += weight * 0.7
            # Errors get 0 points
        
        return total_score / max_score if max_score > 0 else 1.0