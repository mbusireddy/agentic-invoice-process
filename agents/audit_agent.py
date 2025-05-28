"""
Audit Agent - Logs and tracks all processing activities for compliance and monitoring
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from agents.base_agent import BaseAgent
from models.processing_result import ProcessingResult
from models.invoice_model import Invoice
from config.settings import settings


class AuditAgent(BaseAgent):
    """Agent responsible for logging and tracking processing activities"""
    
    def __init__(self, ollama_client=None):
        super().__init__("audit", ollama_client)
        
        # Audit settings
        self.audit_log_path = settings.LOGS_DIR / "audit.jsonl"
        self.detailed_audit = True
        self.retain_sensitive_data = False
        
        # Ensure audit log directory exists
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Audit agent initialized")
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate that there is some processing context to audit"""
        return True  # Audit agent can process any input
    
    def process(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """
        Log and audit the complete processing workflow
        
        Args:
            input_data: Any input data (typically invoice or results)
            context: Complete processing context from all previous agents
            
        Returns:
            ProcessingResult: Audit logging results
        """
        result = ProcessingResult()
        
        try:
            # Extract invoice if available
            invoice = None
            if isinstance(input_data, Invoice):
                invoice = input_data
            elif context and "invoice" in context:
                invoice = context["invoice"]
            
            result.add_processing_step(
                agent=self.name,
                action="audit_started",
                result="Beginning audit logging process"
            )
            
            # Create comprehensive audit record
            audit_record = self._create_audit_record(invoice, context)
            
            # Log to audit file
            self._write_audit_log(audit_record)
            
            # Generate audit summary
            audit_summary = self._generate_audit_summary(audit_record)
            
            result.add_processing_step(
                agent=self.name,
                action="audit_completed",
                result=f"Audit record created with ID: {audit_record['audit_id']}"
            )
            
            # Store audit information
            if context is not None:
                context["audit_record"] = audit_record
                context["audit_summary"] = audit_summary
            
            result.confidence_score = 1.0  # Audit logging is always successful if no errors
            
        except Exception as e:
            error_msg = f"Audit logging failed: {str(e)}"
            self.logger.error(error_msg)
            result.add_error(error_msg)
        
        return result
    
    def _create_audit_record(self, invoice: Optional[Invoice], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a comprehensive audit record"""
        audit_id = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Basic audit information
        audit_record = {
            "audit_id": audit_id,
            "timestamp": datetime.now().isoformat(),
            "session_id": context.get("session_id") if context else None,
            "processing_type": "invoice_processing",
            "status": "in_progress"
        }
        
        # Invoice information
        if invoice:
            invoice_data = {
                "invoice_number": invoice.invoice_number,
                "vendor_name": invoice.vendor_name,
                "buyer_name": invoice.buyer_name,
                "total_amount": invoice.total_amount,
                "currency": invoice.currency,
                "region": invoice.region,
                "processing_status": invoice.processing_status.value if invoice.processing_status else None,
                "confidence_score": invoice.confidence_score,
                "processed_at": invoice.processed_at.isoformat() if invoice.processed_at else None,
                "processed_by": invoice.processed_by
            }
            
            # Remove sensitive data if configured
            if not self.retain_sensitive_data:
                invoice_data = self._sanitize_sensitive_data(invoice_data)
            
            audit_record["invoice"] = invoice_data
        
        # Processing workflow information
        if context:
            workflow_info = self._extract_workflow_info(context)
            audit_record["workflow"] = workflow_info
        
        # Performance metrics
        audit_record["performance"] = self._calculate_performance_metrics(context)
        
        # Quality metrics
        audit_record["quality"] = self._calculate_quality_metrics(context)
        
        # Compliance information
        audit_record["compliance"] = self._extract_compliance_info(context)
        
        # System information
        audit_record["system"] = {
            "agent_version": "1.0.0",
            "processing_node": "local",
            "configuration": {
                "confidence_threshold": settings.CONFIDENCE_THRESHOLD,
                "validation_threshold": settings.VALIDATION_THRESHOLD,
                "auto_approve_threshold": settings.AUTO_APPROVE_THRESHOLD
            }
        }
        
        # Determine final status
        if invoice and invoice.processing_status:
            if invoice.processing_status.value in ["approved", "validated"]:
                audit_record["status"] = "completed_success"
            elif invoice.processing_status.value in ["rejected", "error"]:
                audit_record["status"] = "completed_failure"
            else:
                audit_record["status"] = "completed_pending"
        else:
            audit_record["status"] = "completed_unknown"
        
        return audit_record
    
    def _extract_workflow_info(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract workflow execution information"""
        workflow_info = {
            "agents_executed": [],
            "total_processing_steps": 0,
            "errors": [],
            "warnings": []
        }
        
        # Collect information from all agent results
        for key, value in context.items():
            if key.endswith("_results") and isinstance(value, list):
                agent_name = key.replace("_results", "")
                workflow_info["agents_executed"].append(agent_name)
                
                for item in value:
                    if isinstance(item, dict):
                        if item.get("status") == "error":
                            workflow_info["errors"].append({
                                "agent": agent_name,
                                "message": item.get("message", "Unknown error")
                            })
                        elif item.get("status") == "warning":
                            workflow_info["warnings"].append({
                                "agent": agent_name,
                                "message": item.get("message", "Unknown warning")
                            })
        
        # Count processing steps
        if "processing_steps" in context:
            workflow_info["total_processing_steps"] = len(context["processing_steps"])
        
        return workflow_info
    
    def _calculate_performance_metrics(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance metrics for the processing"""
        metrics = {
            "total_processing_time": 0.0,
            "agent_performance": {},
            "throughput": 0.0
        }
        
        if not context:
            return metrics
        
        # Calculate total processing time and per-agent times
        start_time = None
        end_time = None
        
        for key, value in context.items():
            if "processing_time" in str(value):
                if isinstance(value, dict) and "processing_time" in value:
                    agent_time = value["processing_time"]
                    agent_name = key.replace("_results", "")
                    metrics["agent_performance"][agent_name] = {
                        "processing_time": agent_time,
                        "status": "completed"
                    }
                    metrics["total_processing_time"] += agent_time
        
        # Calculate throughput (documents per second)
        if metrics["total_processing_time"] > 0:
            metrics["throughput"] = 1.0 / metrics["total_processing_time"]
        
        return metrics
    
    def _calculate_quality_metrics(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate quality metrics for the processing"""
        metrics = {
            "overall_confidence": 0.0,
            "validation_score": 0.0,
            "compliance_score": 0.0,
            "data_completeness": 0.0,
            "error_rate": 0.0
        }
        
        if not context:
            return metrics
        
        # Extract confidence scores
        confidence_scores = []
        for key, value in context.items():
            if isinstance(value, dict) and "confidence" in value:
                confidence_scores.append(value["confidence"])
        
        if confidence_scores:
            metrics["overall_confidence"] = sum(confidence_scores) / len(confidence_scores)
        
        # Calculate validation and compliance scores
        validation_results = context.get("validation_results", [])
        compliance_results = context.get("compliance_results", [])
        
        metrics["validation_score"] = self._calculate_result_score(validation_results)
        metrics["compliance_score"] = self._calculate_result_score(compliance_results)
        
        # Calculate error rate
        total_checks = len(validation_results) + len(compliance_results)
        error_checks = sum(1 for r in validation_results + compliance_results if r.get("status") == "error")
        
        if total_checks > 0:
            metrics["error_rate"] = error_checks / total_checks
        
        return metrics
    
    def _extract_compliance_info(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract compliance-related information"""
        compliance_info = {
            "region": "US",
            "regulatory_requirements_met": True,
            "approval_requirements": {},
            "compliance_issues": []
        }
        
        if not context:
            return compliance_info
        
        # Extract approval information
        approval_info = context.get("approval_info", {})
        if approval_info:
            compliance_info["approval_requirements"] = {
                "required_approver": approval_info.get("required_approver", "system"),
                "approval_level": approval_info.get("approval_level", "auto"),
                "amount_threshold": approval_info.get("amount", 0.0)
            }
        
        # Extract compliance issues
        compliance_results = context.get("compliance_results", [])
        for result in compliance_results:
            if result.get("status") in ["error", "warning"]:
                compliance_info["compliance_issues"].append({
                    "type": result.get("check", "unknown"),
                    "severity": result.get("severity", "low"),
                    "message": result.get("message", "Unknown issue")
                })
        
        # Determine if regulatory requirements are met
        critical_issues = [i for i in compliance_info["compliance_issues"] if i["severity"] == "high"]
        compliance_info["regulatory_requirements_met"] = len(critical_issues) == 0
        
        return compliance_info
    
    def _sanitize_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove or mask sensitive data from audit records"""
        sanitized = data.copy()
        
        # Mask vendor and buyer names (keep first 3 characters)
        if "vendor_name" in sanitized and sanitized["vendor_name"]:
            name = sanitized["vendor_name"]
            sanitized["vendor_name"] = name[:3] + "*" * (len(name) - 3) if len(name) > 3 else "***"
        
        if "buyer_name" in sanitized and sanitized["buyer_name"]:
            name = sanitized["buyer_name"]
            sanitized["buyer_name"] = name[:3] + "*" * (len(name) - 3) if len(name) > 3 else "***"
        
        # Round amounts to nearest 100 for privacy
        if "total_amount" in sanitized and sanitized["total_amount"]:
            amount = sanitized["total_amount"]
            sanitized["total_amount"] = round(amount / 100) * 100
        
        return sanitized
    
    def _calculate_result_score(self, results: List[Dict[str, Any]]) -> float:
        """Calculate a score from validation/compliance results"""
        if not results:
            return 1.0
        
        total_score = 0.0
        max_score = 0.0
        
        for result in results:
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
        
        return total_score / max_score if max_score > 0 else 1.0
    
    def _write_audit_log(self, audit_record: Dict[str, Any]) -> None:
        """Write audit record to log file"""
        try:
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(audit_record) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write audit log: {e}")
            raise
    
    def _generate_audit_summary(self, audit_record: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the audit record"""
        return {
            "audit_id": audit_record["audit_id"],
            "timestamp": audit_record["timestamp"],
            "status": audit_record["status"],
            "invoice_number": audit_record.get("invoice", {}).get("invoice_number"),
            "total_amount": audit_record.get("invoice", {}).get("total_amount"),
            "processing_time": audit_record.get("performance", {}).get("total_processing_time", 0.0),
            "overall_confidence": audit_record.get("quality", {}).get("overall_confidence", 0.0),
            "compliance_met": audit_record.get("compliance", {}).get("regulatory_requirements_met", False),
            "error_count": len(audit_record.get("workflow", {}).get("errors", [])),
            "warning_count": len(audit_record.get("workflow", {}).get("warnings", []))
        }
    
    def get_audit_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit records"""
        audit_records = []
        
        try:
            if self.audit_log_path.exists():
                with open(self.audit_log_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    
                # Get the last 'limit' records
                for line in lines[-limit:]:
                    try:
                        record = json.loads(line.strip())
                        audit_records.append(record)
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            self.logger.error(f"Failed to read audit history: {e}")
        
        return audit_records
    
    def search_audit_logs(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search audit logs based on criteria"""
        matching_records = []
        
        try:
            if not self.audit_log_path.exists():
                return matching_records
                
            with open(self.audit_log_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                        
                        # Check if record matches criteria
                        if self._matches_criteria(record, criteria):
                            matching_records.append(record)
                            
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            self.logger.error(f"Failed to search audit logs: {e}")
        
        return matching_records
    
    def _matches_criteria(self, record: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Check if audit record matches search criteria"""
        for key, value in criteria.items():
            if "." in key:
                # Nested key like "invoice.invoice_number"
                keys = key.split(".")
                record_value = record
                for k in keys:
                    if isinstance(record_value, dict) and k in record_value:
                        record_value = record_value[k]
                    else:
                        record_value = None
                        break
            else:
                record_value = record.get(key)
            
            if record_value != value:
                return False
        
        return True