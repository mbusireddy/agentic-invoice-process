#!/usr/bin/env python3
"""
Demo of Qwen2.5:14b Enhanced Capabilities
Shows the improved invoice processing with locally hosted Ollama
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.ollama_client import OllamaClient
from agents.data_extraction_agent import DataExtractionAgent
from config.settings import Settings

def demo_complex_invoice_extraction():
    """Demonstrate Qwen2.5 handling complex invoice with multiple currencies and items"""
    print("🧠 Demo: Complex Invoice Processing with Qwen2.5:14b")
    print("=" * 60)
    
    complex_invoice = """
    FACTURA / INVOICE #F-2024-789
    
    VENDOR: International Tech Services GmbH
    Address: Berliner Str. 123, 10115 Berlin, Germany
    VAT: DE123456789
    
    CUSTOMER: Global Corp USA Inc.
    1000 Corporate Blvd, Suite 500
    Austin, TX 78701, USA
    
    Date: 2024-05-28
    Due Date: 2024-06-27
    Payment Terms: NET 30
    
    SERVICES PROVIDED:
    1. Cloud Infrastructure Consulting      €8,500.00
    2. AI/ML Implementation Services        €12,000.00  
    3. Security Audit & Penetration Test   €4,500.00
    4. Staff Training (40 hours @ €150/hr) €6,000.00
    5. Documentation & Knowledge Transfer  €2,500.00
    
    SUBTOTAL:                              €33,500.00
    VAT (19%):                             €6,365.00
    TOTAL AMOUNT:                          €39,865.00
    
    EXCHANGE RATE: 1 EUR = 1.08 USD (May 28, 2024)
    USD EQUIVALENT: $43,054.20
    
    Payment Instructions:
    - EUR Bank: IBAN DE89 3704 0044 0532 0130 00
    - USD Bank: Account 1234567890, Routing 021000021
    """
    
    client = OllamaClient()
    
    # Enhanced schema for complex invoices
    schema = {
        "type": "object",
        "required": ["invoice_number", "vendor_name", "customer_name", "date", "total_amount", "currency"],
        "properties": {
            "invoice_number": {"type": "string", "description": "Invoice/Factura number"},
            "vendor_name": {"type": "string", "description": "Company providing the service"},
            "vendor_country": {"type": "string", "description": "Vendor country"},
            "customer_name": {"type": "string", "description": "Company receiving the service"},
            "customer_country": {"type": "string", "description": "Customer country"},
            "date": {"type": "string", "format": "date", "description": "Invoice date in YYYY-MM-DD"},
            "due_date": {"type": "string", "format": "date", "description": "Payment due date"},
            "currency": {"type": "string", "description": "Primary currency (EUR, USD, etc.)"},
            "total_amount": {"type": "number", "description": "Total amount in primary currency"},
            "usd_equivalent": {"type": "number", "description": "USD equivalent if different currency"},
            "vat_rate": {"type": "number", "description": "VAT/tax rate as decimal"},
            "vat_amount": {"type": "number", "description": "VAT/tax amount"},
            "payment_terms": {"type": "string", "description": "Payment terms"},
            "services": {"type": "array", "items": {"type": "string"}, "description": "List of services provided"}
        }
    }
    
    print("📊 Extracting complex invoice data with Qwen2.5...")
    extracted_data = client.extract_structured_data(complex_invoice, schema)
    
    print("\n✅ EXTRACTION RESULTS:")
    print("-" * 40)
    for key, value in extracted_data.items():
        if isinstance(value, list):
            print(f"{key.replace('_', ' ').title()}: {len(value)} items")
            for i, item in enumerate(value[:3], 1):  # Show first 3 items
                print(f"  {i}. {item}")
        else:
            print(f"{key.replace('_', ' ').title()}: {value}")
    
    # Validate completeness
    required_fields = schema["required"]
    missing_fields = [field for field in required_fields if not extracted_data.get(field)]
    
    print(f"\n📈 EXTRACTION QUALITY:")
    print(f"Required fields extracted: {len(required_fields) - len(missing_fields)}/{len(required_fields)}")
    print(f"Total fields extracted: {len(extracted_data)}")
    print(f"Missing fields: {missing_fields if missing_fields else 'None'}")
    
    return len(missing_fields) == 0

def demo_multilingual_support():
    """Test Qwen2.5 with multilingual invoice content"""
    print("\n🌍 Demo: Multilingual Invoice Processing")
    print("=" * 60)
    
    multilingual_invoice = """
    RECHNUNG / INVOICE / FACTURE #ML-2024-456
    
    Von/From/De: Müller & Associates AG
    Bahnhofstrasse 12, 8001 Zürich, Schweiz
    
    An/To/À: Société Internationale SARL  
    123 Avenue des Champs-Élysées, 75008 Paris, France
    
    Datum/Date: 28. Mai 2024
    Fällig/Due/Échéance: 27. Juni 2024
    
    Leistungen/Services/Prestations:
    • Beratung/Consulting/Conseil: CHF 5,000.-
    • Entwicklung/Development/Développement: CHF 8,500.-
    • Schulung/Training/Formation: CHF 2,500.-
    
    Zwischensumme/Subtotal/Sous-total: CHF 16,000.-
    MwSt./VAT/TVA (7.7%): CHF 1,232.-
    Gesamtbetrag/Total/Total: CHF 17,232.-
    """
    
    client = OllamaClient()
    
    schema = {
        "type": "object",
        "required": ["invoice_number", "vendor_name", "total_amount", "currency"],
        "properties": {
            "invoice_number": {"type": "string"},
            "vendor_name": {"type": "string"},
            "customer_name": {"type": "string"},
            "date": {"type": "string"},
            "total_amount": {"type": "number"},
            "currency": {"type": "string"},
            "languages_detected": {"type": "array", "items": {"type": "string"}}
        }
    }
    
    print("🔍 Processing multilingual content...")
    extracted_data = client.extract_structured_data(multilingual_invoice, schema)
    
    print("\n✅ MULTILINGUAL EXTRACTION:")
    print("-" * 40)
    for key, value in extracted_data.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    return extracted_data.get("total_amount") == 17232.0

def demo_enhanced_data_extraction_agent():
    """Show the enhanced DataExtractionAgent with Qwen2.5 improvements"""
    print("\n🤖 Demo: Enhanced Data Extraction Agent")
    print("=" * 60)
    
    challenging_invoice = """
    URGENT: OVERDUE NOTICE
    
    Original Invoice: #INV-Q1-2024-3301
    
    Dear Acme Industries Ltd.,
    
    This is a reminder that payment for the following services 
    remains outstanding:
    
    Project: "Enterprise Data Migration & Cloud Transition"
    
    Work Performed:
    - Data analysis and migration planning: 40 hrs @ $200/hr = $8,000
    - Cloud infrastructure setup: Fixed price = $15,000  
    - Testing and validation: 25 hrs @ $180/hr = $4,500
    - Project management overhead: 15% = $4,125
    
    Original Invoice Date: March 15, 2024
    Payment Due: April 14, 2024  
    Days Overdue: 45 days (as of May 28, 2024)
    
    Amount Due: $31,625.00
    Late Fee (2% monthly): $632.50
    Total Amount Now Due: $32,257.50
    
    Please remit payment immediately to avoid collection proceedings.
    
    TechSolutions Pro LLC
    Payment Dept: accounting@techsolutions.pro
    """
    
    print("⚡ Processing challenging invoice format...")
    agent = DataExtractionAgent()
    result = agent.process(challenging_invoice)
    
    if result and result.is_successful():
        print("\n✅ AGENT PROCESSING SUCCESS:")
        print(f"Confidence Score: {result.confidence_score:.2f}")
        print(f"Processing Steps: {len(result.processing_steps)}")
        print(f"Warnings: {len(result.warnings)}")
        print(f"Errors: {len(result.errors)}")
        
        for i, step in enumerate(result.processing_steps, 1):
            print(f"\nStep {i}: {step.get('action', 'Unknown')}")
            print(f"  Agent: {step.get('agent', 'Unknown')}")
            print(f"  Result: {step.get('result', 'No details')[:100]}...")
        
        return True
    else:
        print(f"\n❌ PROCESSING FAILED: {result.errors if result else 'No result'}")
        return False

def main():
    """Run all Qwen2.5 capability demonstrations"""
    print("🚀 Qwen2.5:14b Enhanced Capabilities Demo")
    print("Local Ollama Instance with Advanced Invoice Processing")
    print("=" * 70)
    
    # Check Ollama connection first
    settings = Settings()
    print(f"🔗 Ollama URL: {settings.OLLAMA_BASE_URL}")
    print(f"🧠 Model: {settings.OLLAMA_MODEL}")
    print(f"📊 Embedding Model: {settings.OLLAMA_EMBEDDING_MODEL}")
    
    demos = [
        ("Complex Multi-Currency Invoice", demo_complex_invoice_extraction),
        ("Multilingual Content Processing", demo_multilingual_support),
        ("Enhanced Agent Pipeline", demo_enhanced_data_extraction_agent)
    ]
    
    passed = 0
    total = len(demos)
    
    for demo_name, demo_func in demos:
        print(f"\n{'='*70}")
        try:
            if demo_func():
                passed += 1
                print(f"\n✅ {demo_name}: SUCCESS")
            else:
                print(f"\n❌ {demo_name}: FAILED")
        except Exception as e:
            print(f"\n💥 {demo_name}: ERROR - {e}")
    
    print(f"\n{'='*70}")
    print(f"📊 DEMO RESULTS: {passed}/{total} demonstrations successful")
    print(f"🎯 Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All Qwen2.5:14b capabilities demonstrated successfully!")
        print("Your locally hosted Ollama with Qwen2.5:14b is performing excellently!")
    else:
        print(f"\n⚠️  {total - passed} demonstration(s) had issues")

if __name__ == "__main__":
    main()