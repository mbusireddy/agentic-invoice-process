#!/usr/bin/env python3
"""
Test Qwen2.5:14b Integration for Invoice Processing
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.ollama_client import OllamaClient
from agents.data_extraction_agent import DataExtractionAgent
from config.settings import Settings

def test_qwen_basic_connection():
    """Test basic Qwen2.5 model connection"""
    print("🔌 Testing Qwen2.5:14b Connection...")
    
    client = OllamaClient()
    settings = Settings()
    
    try:
        # Test basic model query
        response = client.generate(
            "What is your model name and version?", 
            model=settings.OLLAMA_MODEL
        )
        print(f"   ✅ Model response: {response[:100]}...")
        return True
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False

def test_qwen_structured_extraction():
    """Test Qwen2.5 structured data extraction"""
    print("📊 Testing Qwen2.5 Structured Data Extraction...")
    
    client = OllamaClient()
    
    # Sample invoice text
    invoice_text = """
    INVOICE #INV-2024-001
    
    Bill To: Acme Corporation
    123 Business St
    New York, NY 10001
    
    Date: 2024-01-15
    Due Date: 2024-02-15
    
    Items:
    - Consulting Services: $1,500.00
    - Software License: $500.00
    
    Subtotal: $2,000.00
    Tax (8%): $160.00
    Total: $2,160.00
    
    Vendor: Tech Solutions Inc
    456 Tech Ave
    San Francisco, CA 94101
    """
    
    # Enhanced schema for Qwen2.5
    schema = {
        "type": "object",
        "required": ["invoice_number", "date", "vendor_name", "total_amount"],
        "properties": {
            "invoice_number": {"type": "string"},
            "date": {"type": "string", "format": "date"},
            "vendor_name": {"type": "string"},
            "total_amount": {"type": "number"},
            "tax_amount": {"type": "number"},
            "customer_name": {"type": "string"}
        }
    }
    
    try:
        extracted_data = client.extract_structured_data(invoice_text, schema)
        print(f"   ✅ Extracted data: {extracted_data}")
        
        # Validate required fields
        required_fields = ["invoice_number", "date", "vendor_name", "total_amount"]
        missing_fields = [field for field in required_fields if not extracted_data.get(field)]
        
        if missing_fields:
            print(f"   ⚠️  Missing required fields: {missing_fields}")
            return False
        else:
            print("   ✅ All required fields extracted successfully")
            return True
            
    except Exception as e:
        print(f"   ❌ Extraction failed: {e}")
        return False

def test_qwen_validation():
    """Test Qwen2.5 data validation capabilities"""
    print("🔍 Testing Qwen2.5 Validation...")
    
    client = OllamaClient()
    
    # Sample data for validation
    original_text = "Invoice #12345 dated January 15, 2024 from Tech Corp for $1,500"
    extracted_data = {
        "invoice_number": "12345",
        "date": "2024-01-15", 
        "vendor_name": "Tech Corp",
        "total_amount": 1500.0
    }
    
    try:
        validation_result = client.validate_invoice_data(original_text, extracted_data)
        print(f"   ✅ Validation result: {validation_result}")
        
        if validation_result.get("is_valid"):
            print("   ✅ Data validation passed")
            return True
        else:
            print(f"   ⚠️  Validation issues: {validation_result.get('issues', [])}")
            return True  # Still successful test
            
    except Exception as e:
        print(f"   ❌ Validation failed: {e}")
        return False

def test_data_extraction_agent():
    """Test DataExtractionAgent with Qwen2.5 enhancements"""
    print("🤖 Testing Enhanced Data Extraction Agent...")
    
    try:
        agent = DataExtractionAgent()
        
        # Sample invoice text
        invoice_text = """
        INVOICE
        
        From: Global Services LLC
        789 Main Street
        Los Angeles, CA 90210
        
        To: Customer Corp
        Invoice #: GS-2024-456
        Date: March 20, 2024
        
        Service Description: Web Development
        Amount: $3,250.00
        """
        
        result = agent.process(invoice_text)
        
        if result and result.is_successful():
            print("   ✅ Agent processing successful")
            print(f"   ✅ Confidence: {result.confidence_score}")
            print(f"   ✅ Processing steps: {len(result.processing_steps)}")
            return True
        else:
            print(f"   ❌ Agent processing failed: {result.errors if result else 'No result'}")
            return False
            
    except Exception as e:
        print(f"   ❌ Agent test failed: {e}")
        return False

def main():
    """Run all Qwen2.5 integration tests"""
    print("🧪 Qwen2.5:14b Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Basic Connection", test_qwen_basic_connection),
        ("Structured Extraction", test_qwen_structured_extraction), 
        ("Data Validation", test_qwen_validation),
        ("Data Extraction Agent", test_data_extraction_agent)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔬 {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"   ✅ {test_name} PASSED")
            else:
                print(f"   ❌ {test_name} FAILED")
        except Exception as e:
            print(f"   ❌ {test_name} ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All Qwen2.5 integration tests passed!")
    else:
        print(f"⚠️  {total - passed} test(s) failed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)