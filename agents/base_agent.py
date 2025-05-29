"""
Base agent class for invoice processing system
"""
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime

from config.settings import settings, AGENT_CONFIGS
from models.processing_result import ProcessingResult
from utils.ollama_client import OllamaClient


class BaseAgent(ABC):
    """Base class for all processing agents"""

    def __init__(self, agent_type: str, ollama_client: Optional[OllamaClient] = None):
        self.agent_type = agent_type
        self.config = AGENT_CONFIGS.get(agent_type, {})
        self.name = self.config.get("name", f"{agent_type} Agent")
        self.description = self.config.get("description", "")
        self.timeout = self.config.get("timeout", settings.AGENT_TIMEOUT)
        self.max_retries = self.config.get("max_retries", settings.MAX_RETRIES)
        
        self.ollama_client = ollama_client or OllamaClient()
        self.logger = logging.getLogger(f"agents.{agent_type}")
        
        self.processing_stats = {
            "executions": 0,
            "successes": 0,
            "failures": 0,
            "total_time": 0.0,
            "average_time": 0.0
        }

    @abstractmethod
    def process(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """
        Process input data and return result
        
        Args:
            input_data: The data to process
            context: Optional context information
            
        Returns:
            ProcessingResult: The processing result
        """
        pass

    def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """
        Execute the agent with retry logic and timing
        
        Args:
            input_data: The data to process
            context: Optional context information
            
        Returns:
            ProcessingResult: The processing result
        """
        start_time = time.time()
        self.processing_stats["executions"] += 1
        
        result = ProcessingResult()
        result.add_processing_step(
            agent=self.name,
            action="execution_started",
            result="Agent execution started"
        )
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.info(f"Executing {self.name} (attempt {attempt + 1})")
                
                # Process with timeout
                processing_result = self._execute_with_timeout(input_data, context)
                
                # If successful, update stats and return
                # Note: validation/compliance errors are expected and don't indicate processing failure
                if processing_result:
                    self.processing_stats["successes"] += 1
                    processing_time = time.time() - start_time
                    self.processing_stats["total_time"] += processing_time
                    self.processing_stats["average_time"] = (
                        self.processing_stats["total_time"] / self.processing_stats["executions"]
                    )
                    
                    processing_result.processing_time = processing_time
                    processing_result.add_processing_step(
                        agent=self.name,
                        action="execution_completed",
                        result=f"Successfully completed in {processing_time:.2f}s"
                    )
                    
                    self.logger.info(f"{self.name} completed successfully in {processing_time:.2f}s")
                    return processing_result
                    
            except Exception as e:
                error_msg = f"Attempt {attempt + 1} failed: {str(e)}"
                self.logger.error(error_msg)
                result.add_error(error_msg)
                
                if attempt < self.max_retries:
                    self.logger.info(f"Retrying {self.name} (attempt {attempt + 2})")
                    time.sleep(1)  # Brief pause before retry
        
        # All attempts failed
        self.processing_stats["failures"] += 1
        processing_time = time.time() - start_time
        result.processing_time = processing_time
        
        result.add_processing_step(
            agent=self.name,
            action="execution_failed",
            result=f"Failed after {self.max_retries + 1} attempts"
        )
        
        self.logger.error(f"{self.name} failed after all retry attempts")
        return result

    def _execute_with_timeout(self, input_data: Any, context: Optional[Dict[str, Any]]) -> ProcessingResult:
        """Execute processing with timeout handling"""
        # For now, direct execution - could be enhanced with threading/asyncio for true timeout
        return self.process(input_data, context)

    def validate_input(self, input_data: Any) -> bool:
        """
        Validate input data before processing
        
        Args:
            input_data: The data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        return input_data is not None

    def get_stats(self) -> Dict[str, Any]:
        """Get agent processing statistics"""
        return {
            "agent": self.name,
            "type": self.agent_type,
            "description": self.description,
            "stats": self.processing_stats.copy(),
            "config": {
                "timeout": self.timeout,
                "max_retries": self.max_retries
            }
        }

    def reset_stats(self):
        """Reset processing statistics"""
        self.processing_stats = {
            "executions": 0,
            "successes": 0,
            "failures": 0,
            "total_time": 0.0,
            "average_time": 0.0
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform health check of the agent"""
        health_status = {
            "agent": self.name,
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "ollama_connected": False,
            "issues": []
        }
        
        try:
            # Test Ollama connection
            test_response = self.ollama_client.generate("test", model=settings.OLLAMA_MODEL)
            health_status["ollama_connected"] = bool(test_response)
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["issues"].append(f"Ollama connection failed: {str(e)}")
        
        # Check success rate
        if self.processing_stats["executions"] > 0:
            success_rate = self.processing_stats["successes"] / self.processing_stats["executions"]
            if success_rate < 0.5:  # Less than 50% success rate
                health_status["status"] = "degraded"
                health_status["issues"].append(f"Low success rate: {success_rate:.2%}")
        
        return health_status

    def __str__(self):
        return f"{self.name} ({self.agent_type})"

    def __repr__(self):
        return f"<{self.__class__.__name__}(type={self.agent_type}, name={self.name})>"