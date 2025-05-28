"""
Configuration settings for the Invoice Processing System
"""
import os
from pathlib import Path
from typing import Dict, Any


class Settings:
    """Application settings"""

    def __init__(self):
        # Base paths
        self.BASE_DIR = Path(__file__).resolve().parent.parent
        self.DATA_DIR = self.BASE_DIR / "data"
        self.LOGS_DIR = self.BASE_DIR / "logs"
        self.INDEX_DIR = self.DATA_DIR / "index"
        self.INVOICES_DIR = self.DATA_DIR / "invoices"
        self.PROCESSED_DIR = self.DATA_DIR / "processed"

        # Ollama Configuration
        self.OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
        self.OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

        # LlamaIndex Configuration
        self.CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1024"))
        self.CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "128"))
        self.SIMILARITY_TOP_K = int(os.getenv("SIMILARITY_TOP_K", "5"))

        # Agent Configuration
        self.MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
        self.AGENT_TIMEOUT = int(os.getenv("AGENT_TIMEOUT", "30"))

        # Regional Settings
        self.SUPPORTED_REGIONS = ["US", "EU", "APAC", "LATAM"]
        self.DEFAULT_REGION = os.getenv("DEFAULT_REGION", "US")

        # Processing Configuration
        self.CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.85"))
        self.VALIDATION_THRESHOLD = float(os.getenv("VALIDATION_THRESHOLD", "0.75"))
        self.AUTO_APPROVE_THRESHOLD = float(os.getenv("AUTO_APPROVE_THRESHOLD", "0.95"))

        # UI Configuration
        self.STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
        self.DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"

        # Logging Configuration
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


# Global settings instance
settings = Settings()


# Ensure required directories exist
def create_directories():
    """Create necessary directories if they don't exist"""
    dirs_to_create = [
        settings.DATA_DIR,
        settings.LOGS_DIR,
        settings.INDEX_DIR,
        settings.INVOICES_DIR,
        settings.PROCESSED_DIR
    ]

    for directory in dirs_to_create:
        directory.mkdir(parents=True, exist_ok=True)


# Agent configuration
AGENT_CONFIGS = {
    "document_parser": {
        "name": "Document Parser Agent",
        "description": "Parses and extracts text from invoice documents",
        "timeout": 30,
        "max_retries": 3
    },
    "data_extraction": {
        "name": "Data Extraction Agent",
        "description": "Extracts structured data from invoice text",
        "timeout": 45,
        "max_retries": 3
    },
    "validation": {
        "name": "Validation Agent",
        "description": "Validates extracted invoice data",
        "timeout": 30,
        "max_retries": 2
    },
    "regional_compliance": {
        "name": "Regional Compliance Agent",
        "description": "Applies region-specific rules and regulations",
        "timeout": 60,
        "max_retries": 2
    },
    "approval": {
        "name": "Approval Agent",
        "description": "Makes final approval decisions",
        "timeout": 30,
        "max_retries": 1
    },
    "audit": {
        "name": "Audit Agent",
        "description": "Logs and tracks processing activities",
        "timeout": 15,
        "max_retries": 1
    }
}