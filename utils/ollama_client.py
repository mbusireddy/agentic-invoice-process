"""
Ollama client for local LLM inference and embeddings
"""
import json
import requests
from typing import List, Dict, Any, Optional
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API"""

    def __init__(self, base_url: str = None, model: str = None, embedding_model: str = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL
        self.embedding_model = embedding_model or settings.OLLAMA_EMBEDDING_MODEL
        self.session = requests.Session()

    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to Ollama API"""
        try:
            url = f"{self.base_url}/api/{endpoint}"
            response = self.session.post(url, json=data, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API request failed: {e}")
            raise

    def generate(self, prompt: str, model: str = None, system: str = None,
                 context: List[int] = None, options: Dict[str, Any] = None) -> str:
        """Generate text completion"""
        data = {
            "model": model or self.model,
            "prompt": prompt,
            "stream": False
        }

        if system:
            data["system"] = system
        if context:
            data["context"] = context
        if options:
            data["options"] = options

        try:
            response = self._make_request("generate", data)
            return response.get("response", "")
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return ""

    def chat(self, messages: List[Dict[str, str]], model: str = None,
             options: Dict[str, Any] = None) -> str:
        """Chat completion"""
        data = {
            "model": model or self.model,
            "messages": messages,
            "stream": False
        }

        if options:
            data["options"] = options

        try:
            response = self._make_request("chat", data)
            return response.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            return ""

    def embed(self, text: str, model: str = None) -> List[float]:
        """Generate embeddings for text"""
        data = {
            "model": model or self.embedding_model,
            "prompt": text
        }

        try:
            response = self._make_request("embeddings", data)
            return response.get("embedding", [])
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return []

    def embed_batch(self, texts: List[str], model: str = None) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embedding = self.embed(text, model)
            embeddings.append(embedding)
        return embeddings

    def extract_structured_data(self, text: str, schema: Dict[str, Any],
                                model: str = None) -> Dict[str, Any]:
        """Extract structured data from text using JSON schema optimized for Qwen2.5"""
        system_prompt = f"""You are an expert invoice data extraction AI powered by Qwen2.5. Your task is to extract structured information from invoice documents.

SCHEMA:
{json.dumps(schema, indent=2)}

EXTRACTION RULES:
1. Extract ONLY information explicitly present in the text
2. Use null for missing optional fields  
3. Ensure all required fields have values
4. Follow exact field names and data types from schema
5. For dates, use ISO format (YYYY-MM-DD)
6. For numbers, use decimal format (e.g., 1234.56)
7. For currency, extract numeric value only
8. Be precise with company names, addresses, and invoice numbers

OUTPUT FORMAT:
Return ONLY a valid JSON object matching the schema. No explanations, no markdown, no additional text."""

        user_prompt = f"""Extract invoice data from this text:

{text}

Respond with JSON only:"""

        try:
            # Use chat format for better Qwen2.5 performance
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self.chat(messages, model)
            
            # Parse JSON from response with enhanced error handling
            try:
                # Clean response - remove any markdown formatting
                clean_response = response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()
                
                return json.loads(clean_response)
            except json.JSONDecodeError as je:
                logger.error(f"Failed to parse LLM JSON response: {je}")
                # Enhanced JSON extraction with multiple strategies
                import re
                
                # Strategy 1: Extract first complete JSON object
                json_match = re.search(r'\{[^}]*(?:\{[^}]*\}[^}]*)*\}', response, re.DOTALL)
                if json_match:
                    try:
                        json_str = json_match.group()
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        logger.debug("Strategy 1 failed, trying strategy 2")
                
                # Strategy 2: Find JSON between first { and last }
                first_brace = response.find('{')
                last_brace = response.rfind('}')
                if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                    try:
                        json_str = response[first_brace:last_brace + 1]
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        logger.debug("Strategy 2 failed, trying strategy 3")
                
                # Strategy 3: Split by lines and find JSON block
                lines = response.split('\n')
                json_lines = []
                in_json = False
                brace_count = 0
                
                for line in lines:
                    if '{' in line and not in_json:
                        in_json = True
                        brace_count += line.count('{') - line.count('}')
                        json_lines.append(line)
                    elif in_json:
                        brace_count += line.count('{') - line.count('}')
                        json_lines.append(line)
                        if brace_count <= 0:
                            break
                
                if json_lines:
                    try:
                        json_str = '\n'.join(json_lines)
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        logger.debug("Strategy 3 failed")
                
                logger.error("All JSON extraction strategies failed")
                return {}
                    
        except Exception as e:
            logger.error(f"Structured data extraction failed: {e}")
            return {}

    def validate_invoice_data(self, text: str, extracted_data: Dict[str, Any],
                             model: str = None) -> Dict[str, Any]:
        """Validate extracted invoice data using Qwen2.5"""
        system_prompt = """You are an invoice validation expert. Review the extracted data against the original text and identify any errors, inconsistencies, or missing critical information.

Return a JSON object with validation results:
{
  "is_valid": boolean,
  "confidence_score": float (0.0-1.0),
  "errors": ["list of specific errors found"],
  "warnings": ["list of potential issues"],
  "corrections": {"field": "corrected_value"}
}"""

        user_prompt = f"""Original text:
{text}

Extracted data:
{json.dumps(extracted_data, indent=2)}

Validate the extraction accuracy:"""

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self.chat(messages, model)
            
            # Parse validation response
            try:
                clean_response = response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()
                
                return json.loads(clean_response)
            except json.JSONDecodeError:
                return {
                    "is_valid": False,
                    "confidence_score": 0.0,
                    "errors": ["Failed to parse validation response"],
                    "warnings": [],
                    "corrections": {}
                }
                
        except Exception as e:
            logger.error(f"Invoice validation failed: {e}")
            return {
                "is_valid": False,
                "confidence_score": 0.0,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "corrections": {}
            }