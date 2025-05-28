"""
Processing Result Models - Simple and consistent interface for agent results
"""
from datetime import datetime
from typing import Any, Dict, List, Optional


class ProcessingResult:
    """Simple processing result used by all agents"""
    
    def __init__(self):
        self.confidence_score: float = 0.0
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.processing_steps: List[Dict[str, Any]] = []
        self.processing_time: Optional[float] = None
        
    def add_error(self, error: str) -> None:
        """Add an error message"""
        self.errors.append(error)
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message"""
        self.warnings.append(warning)
    
    def add_processing_step(self, agent: str, action: str, result: str, confidence: Optional[float] = None) -> None:
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
        return len(self.errors) == 0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the processing result"""
        return {
            "confidence_score": self.confidence_score,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "processing_steps": len(self.processing_steps),
            "successful": self.is_successful(),
            "processing_time": self.processing_time
        }