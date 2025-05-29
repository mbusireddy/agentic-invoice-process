"""
LlamaIndex Manager - Manages document indexing and retrieval using LlamaIndex
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from llama_index.core import (
        VectorStoreIndex,
        Document,
        StorageContext,
        Settings
    )
    from llama_index.core.node_parser import SentenceSplitter
    LLAMA_INDEX_CORE_AVAILABLE = True
except ImportError:
    LLAMA_INDEX_CORE_AVAILABLE = False

# Try to import Ollama components - these may be in different packages
try:
    from llama_index.embeddings.ollama import OllamaEmbedding
    OLLAMA_EMBEDDINGS_AVAILABLE = True
except ImportError:
    OLLAMA_EMBEDDINGS_AVAILABLE = False

try:
    from llama_index.llms.ollama import Ollama
    OLLAMA_LLM_AVAILABLE = True
except ImportError:
    OLLAMA_LLM_AVAILABLE = False

LLAMA_INDEX_AVAILABLE = LLAMA_INDEX_CORE_AVAILABLE

from config.settings import settings


class LlamaIndexManager:
    """Manages document indexing and retrieval using LlamaIndex"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.index_dir = settings.INDEX_DIR
        self.index: Optional[Any] = None
        self.storage_context: Optional[Any] = None
        
        if LLAMA_INDEX_AVAILABLE:
            self._initialize_llama_index()
        else:
            self.logger.warning("LlamaIndex not available - indexing features disabled")
    
    def _initialize_llama_index(self):
        """Initialize LlamaIndex components"""
        try:
            # Configure LLM if available
            if OLLAMA_LLM_AVAILABLE:
                Settings.llm = Ollama(
                    model=settings.OLLAMA_MODEL,
                    base_url=settings.OLLAMA_BASE_URL
                )
                self.logger.info("Ollama LLM configured")
            else:
                self.logger.warning("Ollama LLM not available - using default")
            
            # Configure embeddings if available
            if OLLAMA_EMBEDDINGS_AVAILABLE:
                Settings.embed_model = OllamaEmbedding(
                    model_name=settings.OLLAMA_EMBEDDING_MODEL,
                    base_url=settings.OLLAMA_BASE_URL
                )
                self.logger.info("Ollama embeddings configured")
            else:
                self.logger.warning("Ollama embeddings not available - using default")
            
            # Configure node parser
            Settings.node_parser = SentenceSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            
            # Create storage context
            self.storage_context = StorageContext.from_defaults(
                persist_dir=str(self.index_dir)
            )
            
            # Try to load existing index
            self._load_or_create_index()
            
            self.logger.info("LlamaIndex initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize LlamaIndex: {e}")
            # Don't raise - allow system to continue without LlamaIndex
            self.logger.warning("Continuing without LlamaIndex integration")
    
    def _load_or_create_index(self):
        """Load existing index or create new one"""
        try:
            if self.index_dir.exists() and any(self.index_dir.iterdir()):
                # Load existing index using correct method
                from llama_index.core import load_index_from_storage
                self.index = load_index_from_storage(self.storage_context)
                self.logger.info("Loaded existing index")
            else:
                # Create new empty index
                self.index = VectorStoreIndex([], storage_context=self.storage_context)
                self.logger.info("Created new index")
                
        except Exception as e:
            self.logger.error(f"Failed to load/create index: {e}")
            # Create new index as fallback
            self.index = VectorStoreIndex([])
    
    def add_document(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add a document to the index"""
        if not LLAMA_INDEX_AVAILABLE or not self.index:
            self.logger.warning("LlamaIndex not available")
            return False
        
        try:
            # Create document
            doc = Document(text=text, metadata=metadata or {})
            
            # Add to index using correct method
            if hasattr(self.index, 'insert'):
                self.index.insert(doc)
            else:
                # For newer versions, rebuild index with new document
                existing_docs = []
                if hasattr(self.index, '_docstore') and self.index._docstore:
                    existing_docs = list(self.index._docstore.docs.values())
                existing_docs.append(doc)
                self.index = VectorStoreIndex.from_documents(existing_docs, storage_context=self.storage_context)
            
            # Persist index
            self.index.storage_context.persist(persist_dir=str(self.index_dir))
            
            self.logger.debug("Document added to index")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add document to index: {e}")
            return False
    
    def add_invoice_document(self, invoice_text: str, invoice_data: Dict[str, Any]) -> bool:
        """Add an invoice document with structured metadata"""
        metadata = {
            "document_type": "invoice",
            "invoice_number": invoice_data.get("invoice_number"),
            "vendor_name": invoice_data.get("vendor_name"),
            "total_amount": invoice_data.get("total_amount"),
            "currency": invoice_data.get("currency"),
            "region": invoice_data.get("region"),
            "processing_date": invoice_data.get("processed_at"),
        }
        
        # Remove None values
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        return self.add_document(invoice_text, metadata)
    
    def search_similar_invoices(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar invoices"""
        if not LLAMA_INDEX_AVAILABLE or not self.index:
            self.logger.warning("LlamaIndex not available")
            return []
        
        try:
            # Create query engine
            query_engine = self.index.as_query_engine(
                similarity_top_k=top_k,
                response_mode="no_text"
            )
            
            # Perform search
            response = query_engine.query(query)
            
            results = []
            for node in response.source_nodes:
                results.append({
                    "text": node.text,
                    "metadata": node.metadata,
                    "score": node.score if hasattr(node, 'score') else 0.0
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
    
    def find_similar_vendors(self, vendor_name: str, top_k: int = 5) -> List[str]:
        """Find similar vendor names"""
        query = f"vendor similar to {vendor_name}"
        results = self.search_similar_invoices(query, top_k)
        
        vendors = []
        for result in results:
            vendor = result.get("metadata", {}).get("vendor_name")
            if vendor and vendor not in vendors:
                vendors.append(vendor)
        
        return vendors
    
    def get_vendor_statistics(self, vendor_name: str) -> Dict[str, Any]:
        """Get statistics for a specific vendor"""
        query = f"vendor name {vendor_name}"
        results = self.search_similar_invoices(query, top_k=50)
        
        # Filter for exact vendor matches
        vendor_invoices = [
            r for r in results 
            if r.get("metadata", {}).get("vendor_name", "").lower() == vendor_name.lower()
        ]
        
        if not vendor_invoices:
            return {"vendor_name": vendor_name, "invoice_count": 0}
        
        amounts = [
            r.get("metadata", {}).get("total_amount", 0) 
            for r in vendor_invoices
            if r.get("metadata", {}).get("total_amount")
        ]
        
        stats = {
            "vendor_name": vendor_name,
            "invoice_count": len(vendor_invoices),
            "total_amount": sum(amounts) if amounts else 0,
            "average_amount": sum(amounts) / len(amounts) if amounts else 0,
            "min_amount": min(amounts) if amounts else 0,
            "max_amount": max(amounts) if amounts else 0
        }
        
        return stats
    
    def get_processing_insights(self, query: str) -> str:
        """Get insights from processed invoices"""
        if not LLAMA_INDEX_AVAILABLE or not self.index:
            return "LlamaIndex not available for insights"
        
        try:
            query_engine = self.index.as_query_engine(
                similarity_top_k=settings.SIMILARITY_TOP_K
            )
            
            response = query_engine.query(query)
            return str(response)
            
        except Exception as e:
            self.logger.error(f"Failed to get insights: {e}")
            return f"Failed to get insights: {e}"
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the index"""
        if not LLAMA_INDEX_AVAILABLE or not self.index:
            return {"available": False}
        
        try:
            # Get document count (approximate)
            doc_count = len(self.index.docstore.docs) if hasattr(self.index, 'docstore') else 0
            
            return {
                "available": True,
                "document_count": doc_count,
                "index_directory": str(self.index_dir),
                "storage_exists": self.index_dir.exists()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get index stats: {e}")
            return {"available": True, "error": str(e)}
    
    def clear_index(self) -> bool:
        """Clear all documents from the index"""
        if not LLAMA_INDEX_AVAILABLE:
            return False
        
        try:
            # Create new empty index
            self.index = VectorStoreIndex([])
            
            # Clear storage directory
            import shutil
            if self.index_dir.exists():
                shutil.rmtree(self.index_dir)
            
            self.index_dir.mkdir(parents=True, exist_ok=True)
            
            self.logger.info("Index cleared successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear index: {e}")
            return False


# Global LlamaIndex manager instance
llama_index_manager = LlamaIndexManager()