"""
Agent Coordinator - Manages the instantiation, execution, and coordination of all agents
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from agents.document_parser_agent import DocumentParserAgent
from agents.data_extraction_agent import DataExtractionAgent
from agents.validation_agent import ValidationAgent
from agents.regional_compliance_agent import RegionalComplianceAgent
from agents.approval_agent import ApprovalAgent
from agents.audit_agent import AuditAgent
from models.processing_result import ProcessingResult
from models.invoice_model import Invoice, ProcessingStatus
from utils.ollama_client import OllamaClient
from config.settings import settings


class AgentCoordinator:
    """Coordinates the execution of all agents in the invoice processing pipeline"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize Ollama client
        self.ollama_client = OllamaClient()
        
        # Initialize all agents
        self.agents = self._initialize_agents()
        
        # Processing statistics
        self.processing_stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "pending_review": 0,
            "average_processing_time": 0.0
        }
        
        self.logger.info("Agent coordinator initialized with agents: %s", list(self.agents.keys()))
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all processing agents"""
        agents = {}
        
        try:
            agents["document_parser"] = DocumentParserAgent(self.ollama_client)
            agents["data_extraction"] = DataExtractionAgent(self.ollama_client)
            agents["validation"] = ValidationAgent(self.ollama_client)
            agents["regional_compliance"] = RegionalComplianceAgent(self.ollama_client)
            agents["approval"] = ApprovalAgent(self.ollama_client)
            agents["audit"] = AuditAgent(self.ollama_client)
            
            self.logger.info("All agents initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
            raise
        
        return agents
    
    def process_invoice(self, input_data: Union[str, Path, bytes], session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a single invoice through the complete pipeline
        
        Args:
            input_data: File path, bytes, or text content to process
            session_id: Optional session identifier for tracking
            
        Returns:
            Dict containing processing results and final invoice
        """
        start_time = datetime.now()
        session_id = session_id or f"session_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize processing context
        context = {
            "session_id": session_id,
            "start_time": start_time,
            "input_type": type(input_data).__name__,
            "processing_steps": []
        }
        
        pipeline_result = {
            "session_id": session_id,
            "status": "processing",
            "invoice": None,
            "results": {},
            "errors": [],
            "warnings": [],
            "processing_time": 0.0,
            "confidence_score": 0.0
        }
        
        try:
            self.logger.info(f"Starting invoice processing pipeline for session {session_id}")
            
            # Step 1: Document Parsing
            parser_result = self._execute_agent("document_parser", input_data, context)
            pipeline_result["results"]["document_parser"] = parser_result
            
            if parser_result.errors:
                raise Exception(f"Document parsing failed: {parser_result.errors}")
            
            # Step 2: Data Extraction
            extraction_result = self._execute_agent("data_extraction", input_data, context)
            pipeline_result["results"]["data_extraction"] = extraction_result
            
            if extraction_result.errors:
                raise Exception(f"Data extraction failed: {extraction_result.errors}")
            
            # Step 3: Validation
            validation_result = self._execute_agent("validation", context.get("invoice"), context)
            pipeline_result["results"]["validation"] = validation_result
            
            # Step 4: Regional Compliance
            compliance_result = self._execute_agent("regional_compliance", context.get("invoice"), context)
            pipeline_result["results"]["regional_compliance"] = compliance_result
            
            # Step 5: Approval Decision
            approval_result = self._execute_agent("approval", context.get("invoice"), context)
            pipeline_result["results"]["approval"] = approval_result
            
            # Step 6: Audit Logging
            audit_result = self._execute_agent("audit", context.get("invoice"), context)
            pipeline_result["results"]["audit"] = audit_result
            
            # Finalize results
            final_invoice = context.get("invoice")
            if final_invoice:
                pipeline_result["invoice"] = final_invoice
                pipeline_result["confidence_score"] = final_invoice.confidence_score or 0.0
            
            # Determine final status
            pipeline_result["status"] = self._determine_final_status(pipeline_result["results"], final_invoice)
            
            # Collect all errors and warnings
            pipeline_result["errors"] = self._collect_errors(pipeline_result["results"])
            pipeline_result["warnings"] = self._collect_warnings(pipeline_result["results"])
            
            # Update statistics
            self._update_statistics(pipeline_result)
            
        except Exception as e:
            self.logger.error(f"Pipeline processing failed for session {session_id}: {e}")
            pipeline_result["status"] = "failed"
            pipeline_result["errors"].append(str(e))
            self.processing_stats["failed"] += 1
        
        finally:
            # Calculate total processing time
            end_time = datetime.now()
            pipeline_result["processing_time"] = (end_time - start_time).total_seconds()
            context["end_time"] = end_time
            
            self.logger.info(f"Pipeline processing completed for session {session_id} in {pipeline_result['processing_time']:.2f}s")
        
        return pipeline_result
    
    def _execute_agent(self, agent_name: str, input_data: Any, context: Dict[str, Any]) -> ProcessingResult:
        """Execute a specific agent with error handling and logging"""
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent {agent_name} not found")
        
        try:
            self.logger.debug(f"Executing agent: {agent_name}")
            
            # Execute the agent
            result = agent.execute(input_data, context)
            
            # Store agent-specific results in context
            context[f"{agent_name}_result"] = result
            
            self.logger.debug(f"Agent {agent_name} completed with confidence: {result.confidence_score}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Agent {agent_name} execution failed: {e}")
            
            # Create error result
            error_result = ProcessingResult()
            error_result.add_error(f"Agent {agent_name} failed: {str(e)}")
            
            return error_result
    
    def _determine_final_status(self, results: Dict[str, ProcessingResult], invoice: Optional[Invoice]) -> str:
        """Determine the final processing status based on all agent results"""
        
        # Check if any critical agents failed
        critical_agents = ["document_parser", "data_extraction"]
        for agent_name in critical_agents:
            result = results.get(agent_name)
            if result and result.errors:
                return "failed"
        
        # Check invoice processing status
        if invoice and invoice.processing_status:
            if invoice.processing_status == ProcessingStatus.APPROVED:
                return "approved"
            elif invoice.processing_status == ProcessingStatus.REJECTED:
                return "rejected"
            elif invoice.processing_status == ProcessingStatus.ERROR:
                return "failed"
        
        # Check if manual review is required
        approval_result = results.get("approval")
        if approval_result and hasattr(approval_result, 'requires_manual_review'):
            return "pending_review"
        
        # Default to completed if no specific status
        return "completed"
    
    def _collect_errors(self, results: Dict[str, ProcessingResult]) -> List[str]:
        """Collect all errors from agent results"""
        all_errors = []
        
        for agent_name, result in results.items():
            if result and result.errors:
                for error in result.errors:
                    all_errors.append(f"{agent_name}: {error}")
        
        return all_errors
    
    def _collect_warnings(self, results: Dict[str, ProcessingResult]) -> List[str]:
        """Collect all warnings from agent results"""
        all_warnings = []
        
        for agent_name, result in results.items():
            if result and result.warnings:
                for warning in result.warnings:
                    all_warnings.append(f"{agent_name}: {warning}")
        
        return all_warnings
    
    def _update_statistics(self, pipeline_result: Dict[str, Any]) -> None:
        """Update processing statistics"""
        self.processing_stats["total_processed"] += 1
        
        status = pipeline_result["status"]
        if status == "approved":
            self.processing_stats["successful"] += 1
        elif status == "failed":
            self.processing_stats["failed"] += 1
        elif status == "pending_review":
            self.processing_stats["pending_review"] += 1
        
        # Update average processing time
        total_time = self.processing_stats.get("total_time", 0.0)
        total_time += pipeline_result["processing_time"]
        self.processing_stats["total_time"] = total_time
        self.processing_stats["average_processing_time"] = (
            total_time / self.processing_stats["total_processed"]
        )
    
    def process_batch(self, input_files: List[Union[str, Path]], batch_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process multiple invoices in batch
        
        Args:
            input_files: List of file paths to process
            batch_id: Optional batch identifier
            
        Returns:
            Dict containing batch processing results
        """
        start_time = datetime.now()
        batch_id = batch_id or f"batch_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        batch_result = {
            "batch_id": batch_id,
            "total_files": len(input_files),
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "pending_review": 0,
            "results": [],
            "processing_time": 0.0,
            "start_time": start_time.isoformat()
        }
        
        self.logger.info(f"Starting batch processing {batch_id} with {len(input_files)} files")
        
        for i, input_file in enumerate(input_files):
            try:
                session_id = f"{batch_id}_item_{i+1}"
                result = self.process_invoice(input_file, session_id)
                batch_result["results"].append(result)
                batch_result["processed"] += 1
                
                # Update batch statistics
                if result["status"] == "approved":
                    batch_result["successful"] += 1
                elif result["status"] == "failed":
                    batch_result["failed"] += 1
                elif result["status"] == "pending_review":
                    batch_result["pending_review"] += 1
                
            except Exception as e:
                self.logger.error(f"Failed to process file {input_file}: {e}")
                batch_result["failed"] += 1
                batch_result["results"].append({
                    "file": str(input_file),
                    "status": "failed",
                    "error": str(e)
                })
        
        # Finalize batch results
        end_time = datetime.now()
        batch_result["processing_time"] = (end_time - start_time).total_seconds()
        batch_result["end_time"] = end_time.isoformat()
        
        self.logger.info(f"Batch processing {batch_id} completed: {batch_result['successful']}/{batch_result['total_files']} successful")
        
        return batch_result
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        agent_status = {}
        
        for agent_name, agent in self.agents.items():
            try:
                health = agent.health_check()
                stats = agent.get_stats()
                
                agent_status[agent_name] = {
                    "health": health,
                    "stats": stats,
                    "available": health.get("status") != "unhealthy"
                }
                
            except Exception as e:
                agent_status[agent_name] = {
                    "health": {"status": "error", "error": str(e)},
                    "stats": {},
                    "available": False
                }
        
        return agent_status
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get overall processing statistics"""
        return {
            "coordinator_stats": self.processing_stats.copy(),
            "agent_stats": {name: agent.get_stats() for name, agent in self.agents.items()},
            "system_health": self.get_system_health()
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        agent_statuses = self.get_agent_status()
        
        healthy_agents = sum(1 for status in agent_statuses.values() if status["available"])
        total_agents = len(agent_statuses)
        
        overall_health = "healthy" if healthy_agents == total_agents else "degraded"
        if healthy_agents < total_agents / 2:
            overall_health = "unhealthy"
        
        return {
            "overall_status": overall_health,
            "healthy_agents": healthy_agents,
            "total_agents": total_agents,
            "agent_details": agent_statuses,
            "ollama_connected": self._check_ollama_health()
        }
    
    def _check_ollama_health(self) -> bool:
        """Check if Ollama is healthy and responsive"""
        try:
            response = self.ollama_client.generate("test", model=settings.OLLAMA_MODEL)
            return bool(response)
        except Exception:
            return False
    
    def reset_statistics(self) -> None:
        """Reset all processing statistics"""
        self.processing_stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "pending_review": 0,
            "average_processing_time": 0.0
        }
        
        # Reset agent statistics
        for agent in self.agents.values():
            agent.reset_stats()
        
        self.logger.info("Processing statistics reset")
    
    def restart_agent(self, agent_name: str) -> bool:
        """Restart a specific agent"""
        try:
            if agent_name not in self.agents:
                return False
            
            # Reinitialize the agent
            if agent_name == "document_parser":
                self.agents[agent_name] = DocumentParserAgent(self.ollama_client)
            elif agent_name == "data_extraction":
                self.agents[agent_name] = DataExtractionAgent(self.ollama_client)
            elif agent_name == "validation":
                self.agents[agent_name] = ValidationAgent(self.ollama_client)
            elif agent_name == "regional_compliance":
                self.agents[agent_name] = RegionalComplianceAgent(self.ollama_client)
            elif agent_name == "approval":
                self.agents[agent_name] = ApprovalAgent(self.ollama_client)
            elif agent_name == "audit":
                self.agents[agent_name] = AuditAgent(self.ollama_client)
            
            self.logger.info(f"Agent {agent_name} restarted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restart agent {agent_name}: {e}")
            return False