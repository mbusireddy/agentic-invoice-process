"""
Workflow Manager - Manages different processing workflows and pipeline configurations
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Union
from enum import Enum
from pathlib import Path

from orchestrator.agent_coordinator import AgentCoordinator
from models.processing_result import ProcessingResult
from models.invoice_model import Invoice, ProcessingStatus
from config.settings import settings


class WorkflowType(Enum):
    """Available workflow types"""
    STANDARD = "standard"
    FAST_TRACK = "fast_track"
    DETAILED_REVIEW = "detailed_review"
    COMPLIANCE_ONLY = "compliance_only"
    CUSTOM = "custom"


class WorkflowStep:
    """Represents a single step in a workflow"""
    
    def __init__(self, agent_name: str, required: bool = True, condition: Optional[Callable] = None):
        self.agent_name = agent_name
        self.required = required
        self.condition = condition
        self.skip_reason = None
    
    def should_execute(self, context: Dict[str, Any]) -> bool:
        """Determine if this step should be executed"""
        if self.condition:
            return self.condition(context)
        return True


class WorkflowManager:
    """Manages different processing workflows and their execution"""
    
    def __init__(self, agent_coordinator: Optional[AgentCoordinator] = None):
        self.logger = logging.getLogger(__name__)
        self.agent_coordinator = agent_coordinator or AgentCoordinator()
        
        # Define available workflows
        self.workflows = self._define_workflows()
        
        # Workflow execution history
        self.execution_history = []
        
        self.logger.info("Workflow manager initialized with workflows: %s", list(self.workflows.keys()))
    
    def _define_workflows(self) -> Dict[str, List[WorkflowStep]]:
        """Define all available workflows"""
        workflows = {}
        
        # Standard workflow - all agents in sequence
        workflows[WorkflowType.STANDARD.value] = [
            WorkflowStep("document_parser", required=True),
            WorkflowStep("data_extraction", required=True),
            WorkflowStep("validation", required=True),
            WorkflowStep("regional_compliance", required=True),
            WorkflowStep("approval", required=True),
            WorkflowStep("audit", required=False)
        ]
        
        # Fast track - minimal validation for trusted sources
        workflows[WorkflowType.FAST_TRACK.value] = [
            WorkflowStep("document_parser", required=True),
            WorkflowStep("data_extraction", required=True),
            WorkflowStep("validation", required=False, condition=self._check_high_confidence),
            WorkflowStep("regional_compliance", required=True),
            WorkflowStep("approval", required=True),
            WorkflowStep("audit", required=False)
        ]
        
        # Detailed review - extra validation and compliance checks
        workflows[WorkflowType.DETAILED_REVIEW.value] = [
            WorkflowStep("document_parser", required=True),
            WorkflowStep("data_extraction", required=True),
            WorkflowStep("validation", required=True),
            WorkflowStep("regional_compliance", required=True),
            WorkflowStep("approval", required=True),
            WorkflowStep("audit", required=True)
        ]
        
        # Compliance only - skip approval for pre-approved vendors
        workflows[WorkflowType.COMPLIANCE_ONLY.value] = [
            WorkflowStep("document_parser", required=True),
            WorkflowStep("data_extraction", required=True),
            WorkflowStep("validation", required=True),
            WorkflowStep("regional_compliance", required=True),
            WorkflowStep("audit", required=True)
        ]
        
        return workflows
    
    def _check_high_confidence(self, context: Dict[str, Any]) -> bool:
        """Condition function to check if confidence is high enough to skip validation"""
        extraction_result = context.get("data_extraction_result")
        if extraction_result and hasattr(extraction_result, 'confidence_score'):
            return extraction_result.confidence_score >= 0.95
        return False
    
    def execute_workflow(self, 
                        workflow_type: Union[WorkflowType, str],
                        input_data: Union[str, Path, bytes],
                        session_id: Optional[str] = None,
                        workflow_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a specific workflow
        
        Args:
            workflow_type: Type of workflow to execute
            input_data: Input data to process
            session_id: Optional session identifier
            workflow_config: Optional workflow configuration overrides
            
        Returns:
            Dict containing workflow execution results
        """
        start_time = datetime.now()
        
        # Convert enum to string if needed
        if isinstance(workflow_type, WorkflowType):
            workflow_type = workflow_type.value
        
        session_id = session_id or f"workflow_{workflow_type}_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        # Get workflow definition
        workflow_steps = self.workflows.get(workflow_type)
        if not workflow_steps:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
        
        # Initialize workflow context
        context = {
            "session_id": session_id,
            "workflow_type": workflow_type,
            "start_time": start_time,
            "input_type": type(input_data).__name__,
            "workflow_config": workflow_config or {},
            "processing_steps": [],
            "executed_agents": [],
            "skipped_agents": []
        }
        
        workflow_result = {
            "session_id": session_id,
            "workflow_type": workflow_type,
            "status": "processing",
            "invoice": None,
            "results": {},
            "errors": [],
            "warnings": [],
            "processing_time": 0.0,
            "confidence_score": 0.0,
            "workflow_execution": {
                "total_steps": len(workflow_steps),
                "executed_steps": 0,
                "skipped_steps": 0,
                "failed_steps": 0
            }
        }
        
        try:
            self.logger.info(f"Starting workflow {workflow_type} for session {session_id}")
            
            # Execute workflow steps
            for i, step in enumerate(workflow_steps):
                try:
                    # Check if step should be executed
                    if not step.should_execute(context):
                        self.logger.info(f"Skipping step {step.agent_name} - condition not met")
                        context["skipped_agents"].append(step.agent_name)
                        workflow_result["workflow_execution"]["skipped_steps"] += 1
                        continue
                    
                    # Execute the agent
                    self.logger.debug(f"Executing workflow step {i+1}/{len(workflow_steps)}: {step.agent_name}")
                    
                    agent = self.agent_coordinator.agents.get(step.agent_name)
                    if not agent:
                        raise ValueError(f"Agent {step.agent_name} not found")
                    
                    # Determine input for this step
                    step_input = self._determine_step_input(step.agent_name, input_data, context)
                    
                    # Execute the agent
                    result = agent.execute(step_input, context)
                    
                    # Store result
                    workflow_result["results"][step.agent_name] = result
                    context[f"{step.agent_name}_result"] = result
                    context["executed_agents"].append(step.agent_name)
                    workflow_result["workflow_execution"]["executed_steps"] += 1
                    
                    # Check for critical failures
                    if result.errors and step.required:
                        raise Exception(f"Required step {step.agent_name} failed: {result.errors}")
                    
                    self.logger.debug(f"Step {step.agent_name} completed successfully")
                    
                except Exception as e:
                    self.logger.error(f"Workflow step {step.agent_name} failed: {e}")
                    workflow_result["workflow_execution"]["failed_steps"] += 1
                    
                    if step.required:
                        raise Exception(f"Required workflow step {step.agent_name} failed: {e}")
                    else:
                        # Non-required step failure - log and continue
                        workflow_result["errors"].append(f"Optional step {step.agent_name} failed: {e}")
            
            # Finalize workflow results
            final_invoice = context.get("invoice")
            if final_invoice:
                workflow_result["invoice"] = final_invoice
                workflow_result["confidence_score"] = getattr(final_invoice, 'confidence_score', 0.0)
            
            # Determine final status
            workflow_result["status"] = self._determine_workflow_status(workflow_result, final_invoice)
            
            # Collect all errors and warnings
            workflow_result["errors"].extend(self._collect_workflow_errors(workflow_result["results"]))
            workflow_result["warnings"].extend(self._collect_workflow_warnings(workflow_result["results"]))
            
            self.logger.info(f"Workflow {workflow_type} completed successfully for session {session_id}")
            
        except Exception as e:
            self.logger.error(f"Workflow {workflow_type} failed for session {session_id}: {e}")
            workflow_result["status"] = "failed"
            workflow_result["errors"].append(str(e))
        
        finally:
            # Calculate total processing time
            end_time = datetime.now()
            workflow_result["processing_time"] = (end_time - start_time).total_seconds()
            context["end_time"] = end_time
            
            # Store execution history
            self._store_execution_history(workflow_result, context)
        
        return workflow_result
    
    def _determine_step_input(self, agent_name: str, original_input: Any, context: Dict[str, Any]) -> Any:
        """Determine the appropriate input for each agent step"""
        # First agent gets the original input
        if agent_name == "document_parser":
            return original_input
        
        # Subsequent agents typically work with processed data
        if agent_name in ["data_extraction"]:
            return original_input  # Data extraction needs the original input too
        
        # Validation and later agents work with the extracted invoice
        return context.get("invoice", original_input)
    
    def _determine_workflow_status(self, workflow_result: Dict[str, Any], invoice: Optional[Invoice]) -> str:
        """Determine the final workflow status"""
        execution_info = workflow_result["workflow_execution"]
        
        # Check for failures
        if execution_info["failed_steps"] > 0:
            return "failed"
        
        # Check invoice status if available
        if invoice and hasattr(invoice, 'processing_status') and invoice.processing_status:
            if invoice.processing_status == ProcessingStatus.APPROVED:
                return "approved"
            elif invoice.processing_status == ProcessingStatus.REJECTED:
                return "rejected"
            elif invoice.processing_status == ProcessingStatus.ERROR:
                return "failed"
        
        # Check if manual review is required
        approval_result = workflow_result["results"].get("approval")
        if approval_result and hasattr(approval_result, 'requires_manual_review'):
            return "pending_review"
        
        return "completed"
    
    def _collect_workflow_errors(self, results: Dict[str, ProcessingResult]) -> List[str]:
        """Collect all errors from workflow results"""
        all_errors = []
        for agent_name, result in results.items():
            if result and hasattr(result, 'errors') and result.errors:
                for error in result.errors:
                    all_errors.append(f"{agent_name}: {error}")
        return all_errors
    
    def _collect_workflow_warnings(self, results: Dict[str, ProcessingResult]) -> List[str]:
        """Collect all warnings from workflow results"""
        all_warnings = []
        for agent_name, result in results.items():
            if result and hasattr(result, 'warnings') and result.warnings:
                for warning in result.warnings:
                    all_warnings.append(f"{agent_name}: {warning}")
        return all_warnings
    
    def _store_execution_history(self, workflow_result: Dict[str, Any], context: Dict[str, Any]) -> None:
        """Store workflow execution in history"""
        history_entry = {
            "session_id": workflow_result["session_id"],
            "workflow_type": workflow_result["workflow_type"],
            "status": workflow_result["status"],
            "processing_time": workflow_result["processing_time"],
            "executed_agents": context.get("executed_agents", []),
            "skipped_agents": context.get("skipped_agents", []),
            "error_count": len(workflow_result["errors"]),
            "warning_count": len(workflow_result["warnings"]),
            "timestamp": context["start_time"].isoformat()
        }
        
        self.execution_history.append(history_entry)
        
        # Keep only recent history (last 1000 executions)
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
    
    def create_custom_workflow(self, name: str, steps: List[Dict[str, Any]]) -> bool:
        """
        Create a custom workflow
        
        Args:
            name: Name for the custom workflow
            steps: List of step definitions
            
        Returns:
            bool: True if workflow created successfully
        """
        try:
            workflow_steps = []
            
            for step_def in steps:
                agent_name = step_def.get("agent_name")
                required = step_def.get("required", True)
                condition_name = step_def.get("condition")
                
                # Get condition function if specified
                condition = None
                if condition_name == "high_confidence":
                    condition = self._check_high_confidence
                
                workflow_steps.append(WorkflowStep(agent_name, required, condition))
            
            self.workflows[name] = workflow_steps
            self.logger.info(f"Custom workflow '{name}' created with {len(workflow_steps)} steps")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create custom workflow '{name}': {e}")
            return False
    
    def get_workflow_definition(self, workflow_type: str) -> Optional[List[Dict[str, Any]]]:
        """Get the definition of a workflow"""
        workflow_steps = self.workflows.get(workflow_type)
        if not workflow_steps:
            return None
        
        return [
            {
                "agent_name": step.agent_name,
                "required": step.required,
                "has_condition": step.condition is not None
            }
            for step in workflow_steps
        ]
    
    def get_available_workflows(self) -> List[str]:
        """Get list of available workflow types"""
        return list(self.workflows.keys())
    
    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent workflow execution history"""
        return self.execution_history[-limit:] if self.execution_history else []
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get statistics about workflow executions"""
        if not self.execution_history:
            return {"total_executions": 0}
        
        stats = {
            "total_executions": len(self.execution_history),
            "by_workflow_type": {},
            "by_status": {},
            "average_processing_time": 0.0,
            "success_rate": 0.0
        }
        
        total_time = 0.0
        successful = 0
        
        for entry in self.execution_history:
            # Count by workflow type
            workflow_type = entry["workflow_type"]
            stats["by_workflow_type"][workflow_type] = stats["by_workflow_type"].get(workflow_type, 0) + 1
            
            # Count by status
            status = entry["status"]
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # Accumulate processing time
            total_time += entry["processing_time"]
            
            # Count successful executions
            if status in ["approved", "completed"]:
                successful += 1
        
        # Calculate averages
        stats["average_processing_time"] = total_time / len(self.execution_history)
        stats["success_rate"] = successful / len(self.execution_history)
        
        return stats
    
    def validate_workflow_config(self, workflow_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate workflow configuration
        
        Args:
            workflow_type: Type of workflow to validate
            config: Configuration to validate
            
        Returns:
            Dict with validation results
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Check if workflow type exists
        if workflow_type not in self.workflows:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Unknown workflow type: {workflow_type}")
            return validation_result
        
        # Validate configuration parameters
        valid_config_keys = [
            "skip_validation", "force_manual_review", "confidence_threshold",
            "auto_approve", "detailed_logging", "priority"
        ]
        
        for key in config.keys():
            if key not in valid_config_keys:
                validation_result["warnings"].append(f"Unknown configuration key: {key}")
        
        # Check for conflicting configurations
        if config.get("skip_validation") and config.get("force_manual_review"):
            validation_result["warnings"].append("skip_validation and force_manual_review are conflicting")
        
        # Add recommendations
        if workflow_type == WorkflowType.FAST_TRACK.value and not config.get("confidence_threshold"):
            validation_result["recommendations"].append("Consider setting a high confidence_threshold for fast track workflows")
        
        return validation_result