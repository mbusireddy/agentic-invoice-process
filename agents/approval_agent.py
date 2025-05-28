"""
Approval Agent - Makes final approval decisions for invoices
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent
from models.processing_result import ProcessingResult
from models.invoice_model import Invoice, ProcessingStatus
from config.settings import settings


class ApprovalAgent(BaseAgent):
    """Agent responsible for making final approval decisions"""
    
    def __init__(self, ollama_client=None):
        super().__init__("approval", ollama_client)
        
        # Approval thresholds
        self.auto_approve_threshold = settings.AUTO_APPROVE_THRESHOLD
        self.validation_threshold = settings.VALIDATION_THRESHOLD
        self.confidence_threshold = settings.CONFIDENCE_THRESHOLD
        
        self.logger.info("Approval agent initialized")
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate that the input contains an invoice and processing context"""
        if isinstance(input_data, Invoice):
            return True
        elif isinstance(input_data, dict) and "invoice" in input_data:
            return True
        return False
    
    def process(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """
        Make approval decision for the invoice
        
        Args:
            input_data: Invoice object or context containing invoice
            context: Optional context information including previous agent results
            
        Returns:
            ProcessingResult: Approval decision and reasoning
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
                action="approval_started",
                result=f"Evaluating approval for invoice {invoice.invoice_number}"
            )
            
            # Gather all processing information
            approval_factors = self._gather_approval_factors(invoice, context)
            
            # Make approval decision
            approval_decision = self._make_approval_decision(invoice, approval_factors)
            
            # Apply decision to invoice
            self._apply_approval_decision(invoice, approval_decision)
            
            # Calculate confidence in decision
            decision_confidence = self._calculate_decision_confidence(approval_factors, approval_decision)
            result.confidence_score = decision_confidence
            
            result.add_processing_step(
                agent=self.name,
                action="approval_completed",
                result=f"Decision: {approval_decision['decision']} - {approval_decision['reason']}",
                confidence=decision_confidence
            )
            
            # Store approval decision
            if context is not None:
                context["approval_decision"] = approval_decision
                context["invoice"] = invoice
            
            # Add any approval warnings
            for warning in approval_decision.get("warnings", []):
                result.add_warning(f"Approval warning: {warning}")
            
        except Exception as e:
            error_msg = f"Approval decision failed: {str(e)}"
            self.logger.error(error_msg)
            result.add_error(error_msg)
        
        return result
    
    def _gather_approval_factors(self, invoice: Invoice, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Gather all factors that influence approval decision"""
        factors = {
            "invoice": {
                "amount": invoice.total_amount,
                "currency": invoice.currency,
                "region": invoice.region,
                "vendor": invoice.vendor_name,
                "buyer": invoice.buyer_name,
                "processing_status": invoice.processing_status.value if invoice.processing_status else None,
                "confidence_score": invoice.confidence_score
            },
            "validation_results": context.get("validation_results", []) if context else [],
            "compliance_results": context.get("compliance_results", []) if context else [],
            "approval_info": context.get("approval_info", {}) if context else {},
            "processing_history": []
        }
        
        # Extract processing history from context
        if context:
            for key, value in context.items():
                if key.endswith("_results") and isinstance(value, list):
                    factors["processing_history"].extend(value)
        
        return factors
    
    def _make_approval_decision(self, invoice: Invoice, factors: Dict[str, Any]) -> Dict[str, Any]:
        """Make the approval decision based on all factors"""
        decision = {
            "decision": "rejected",
            "reason": "Initial state",
            "approver": "system",
            "timestamp": datetime.now(),
            "factors_considered": [],
            "warnings": [],
            "requires_manual_review": False
        }
        
        # Check if invoice has critical errors
        critical_errors = self._check_critical_errors(factors)
        if critical_errors:
            decision.update({
                "decision": "rejected",
                "reason": f"Critical errors found: {', '.join(critical_errors)}",
                "factors_considered": ["critical_errors"]
            })
            return decision
        
        # Check confidence scores
        confidence_checks = self._evaluate_confidence(factors)
        decision["factors_considered"].extend(confidence_checks["factors"])
        
        if not confidence_checks["passed"]:
            if confidence_checks["manual_review_recommended"]:
                decision.update({
                    "decision": "manual_review",
                    "reason": "Low confidence scores require manual review",
                    "requires_manual_review": True
                })
            else:
                decision.update({
                    "decision": "rejected",
                    "reason": "Confidence scores below acceptable threshold"
                })
            return decision
        
        # Check compliance requirements
        compliance_checks = self._evaluate_compliance(factors)
        decision["factors_considered"].extend(compliance_checks["factors"])
        
        if not compliance_checks["passed"]:
            decision.update({
                "decision": "rejected",
                "reason": "Compliance requirements not met",
                "warnings": compliance_checks["issues"]
            })
            return decision
        
        # Check approval authority requirements
        approval_authority = self._check_approval_authority(factors)
        decision["factors_considered"].extend(approval_authority["factors"])
        
        if approval_authority["requires_manual"]:
            decision.update({
                "decision": "manual_review",
                "reason": f"Amount requires {approval_authority['level']} approval",
                "approver": approval_authority["required_approver"],
                "requires_manual_review": True
            })
            return decision
        
        # Check validation quality
        validation_checks = self._evaluate_validation(factors)
        decision["factors_considered"].extend(validation_checks["factors"])
        
        if not validation_checks["passed"]:
            decision["warnings"].extend(validation_checks["warnings"])
            if validation_checks["severe"]:
                decision.update({
                    "decision": "rejected",
                    "reason": "Severe validation issues found"
                })
                return decision
        
        # If all checks pass, approve
        decision.update({
            "decision": "approved",
            "reason": "All validation and compliance checks passed",
            "approver": "system"
        })
        
        # Add any warnings from sub-checks
        if validation_checks.get("warnings"):
            decision["warnings"].extend(validation_checks["warnings"])
        if compliance_checks.get("warnings"):
            decision["warnings"].extend(compliance_checks["warnings"])
        
        return decision
    
    def _check_critical_errors(self, factors: Dict[str, Any]) -> List[str]:
        """Check for critical errors that would prevent approval"""
        critical_errors = []
        
        # Check for processing errors
        validation_results = factors.get("validation_results", [])
        compliance_results = factors.get("compliance_results", [])
        
        for result in validation_results + compliance_results:
            if result.get("status") == "error" and result.get("severity") == "high":
                critical_errors.append(result.get("message", "Unknown error"))
        
        # Check invoice status
        invoice_status = factors["invoice"].get("processing_status")
        if invoice_status == "error":
            critical_errors.append("Invoice processing resulted in error status")
        
        return critical_errors
    
    def _evaluate_confidence(self, factors: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate confidence scores"""
        result = {
            "passed": False,
            "factors": ["confidence_evaluation"],
            "manual_review_recommended": False
        }
        
        confidence_score = factors["invoice"].get("confidence_score", 0.0)
        
        if confidence_score >= self.auto_approve_threshold:
            result["passed"] = True
        elif confidence_score >= self.validation_threshold:
            result["passed"] = True
            result["manual_review_recommended"] = True
        else:
            result["passed"] = False
        
        return result
    
    def _evaluate_compliance(self, factors: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate compliance results"""
        result = {
            "passed": True,
            "factors": ["compliance_evaluation"],
            "issues": [],
            "warnings": []
        }
        
        compliance_results = factors.get("compliance_results", [])
        
        for compliance_result in compliance_results:
            status = compliance_result.get("status")
            severity = compliance_result.get("severity", "low")
            message = compliance_result.get("message", "Unknown issue")
            
            if status == "error":
                if severity == "high":
                    result["passed"] = False
                    result["issues"].append(message)
                else:
                    result["warnings"].append(message)
            elif status == "warning":
                result["warnings"].append(message)
        
        return result
    
    def _check_approval_authority(self, factors: Dict[str, Any]) -> Dict[str, Any]:
        """Check if manual approval is required based on amount/authority"""
        result = {
            "requires_manual": False,
            "factors": ["approval_authority"],
            "level": "auto",
            "required_approver": "system"
        }
        
        approval_info = factors.get("approval_info", {})
        
        if approval_info:
            approval_level = approval_info.get("approval_level", "auto")
            required_approver = approval_info.get("required_approver", "system")
            
            if approval_level != "auto":
                result.update({
                    "requires_manual": True,
                    "level": approval_level,
                    "required_approver": required_approver
                })
        
        return result
    
    def _evaluate_validation(self, factors: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate validation results"""
        result = {
            "passed": True,
            "factors": ["validation_evaluation"],
            "warnings": [],
            "severe": False
        }
        
        validation_results = factors.get("validation_results", [])
        
        error_count = 0
        warning_count = 0
        
        for validation_result in validation_results:
            status = validation_result.get("status")
            severity = validation_result.get("severity", "low")
            message = validation_result.get("message", "Unknown issue")
            
            if status == "error":
                error_count += 1
                if severity == "high":
                    result["severe"] = True
                    result["passed"] = False
                result["warnings"].append(message)
            elif status == "warning":
                warning_count += 1
                result["warnings"].append(message)
        
        # Too many issues might indicate poor data quality
        if error_count > 5 or warning_count > 10:
            result["severe"] = True
            result["passed"] = False
            result["warnings"].append("Too many validation issues detected")
        
        return result
    
    def _apply_approval_decision(self, invoice: Invoice, decision: Dict[str, Any]) -> None:
        """Apply the approval decision to the invoice"""
        decision_value = decision["decision"]
        
        if decision_value == "approved":
            invoice.processing_status = ProcessingStatus.APPROVED
        elif decision_value == "rejected":
            invoice.processing_status = ProcessingStatus.REJECTED
        elif decision_value == "manual_review":
            # Keep current status but mark for manual review
            pass
        
        # Update processed metadata
        invoice.processed_at = datetime.now()
        invoice.processed_by = f"{self.name}_agent"
    
    def _calculate_decision_confidence(self, factors: Dict[str, Any], decision: Dict[str, Any]) -> float:
        """Calculate confidence in the approval decision"""
        base_confidence = factors["invoice"].get("confidence_score", 0.0)
        
        # Adjust based on decision type
        if decision["decision"] == "approved":
            # High confidence for clear approvals
            return min(base_confidence + 0.1, 1.0)
        elif decision["decision"] == "rejected":
            # High confidence for clear rejections
            return min(base_confidence + 0.05, 1.0)
        else:  # manual_review
            # Lower confidence for uncertain cases
            return max(base_confidence - 0.1, 0.0)
    
    def get_approval_summary(self, invoice: Invoice, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get a summary of the approval status and factors"""
        approval_decision = context.get("approval_decision", {}) if context else {}
        
        return {
            "invoice_number": invoice.invoice_number,
            "total_amount": invoice.total_amount,
            "currency": invoice.currency,
            "status": invoice.processing_status.value if invoice.processing_status else None,
            "decision": approval_decision.get("decision", "unknown"),
            "reason": approval_decision.get("reason", "No decision made"),
            "approver": approval_decision.get("approver", "unknown"),
            "requires_manual_review": approval_decision.get("requires_manual_review", False),
            "warnings": approval_decision.get("warnings", []),
            "processed_at": invoice.processed_at.isoformat() if invoice.processed_at else None,
            "confidence_score": invoice.confidence_score
        }