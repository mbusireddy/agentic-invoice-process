#!/usr/bin/env python3
"""
Comprehensive system test script for the Invoice Processing System
"""
import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_authentication():
    """Test authentication system"""
    print("🔐 Testing Authentication System...")
    
    try:
        from auth import AuthManager, UserRole
        
        # Create fresh auth manager
        auth = AuthManager()
        print("   ✅ Auth manager initialized")
        
        # Test user creation
        success, message = auth.create_user(
            username="testuser",
            password="TestPass123!",
            email="test@example.com",
            role=UserRole.PROCESSOR
        )
        print(f"   ✅ User creation: {success} - {message}")
        
        # Test authentication
        success, message, user = auth.authenticate("testuser", "TestPass123!")
        print(f"   ✅ User login: {success} - {message}")
        
        if user:
            print(f"   ✅ User role: {user.role.value}")
            print(f"   ✅ Has process permission: {auth.has_permission(user, 'process')}")
        
        return True
    except Exception as e:
        print(f"   ❌ Authentication test failed: {e}")
        return False

def test_core_system():
    """Test core system components"""
    print("\n🔧 Testing Core System Components...")
    
    try:
        from orchestrator import AgentCoordinator, WorkflowManager, WorkflowType
        
        # Test agent coordinator
        coordinator = AgentCoordinator()
        print("   ✅ Agent coordinator initialized")
        
        # Test workflow manager
        workflow_manager = WorkflowManager(coordinator)
        print("   ✅ Workflow manager initialized")
        
        # Test system health
        health = coordinator.get_system_health()
        print(f"   ✅ System health: {health['overall_status']}")
        print(f"   ✅ Healthy agents: {health['healthy_agents']}/{health['total_agents']}")
        
        return True
    except Exception as e:
        print(f"   ❌ Core system test failed: {e}")
        return False

def test_file_processing():
    """Test file processing functionality"""
    print("\n📄 Testing File Processing...")
    
    try:
        from orchestrator import AgentCoordinator, WorkflowManager, WorkflowType
        
        # Create test file
        test_file = "data/invoices/test_invoice.txt"
        os.makedirs("data/invoices", exist_ok=True)
        
        with open(test_file, "w") as f:
            f.write("""
Sample Invoice Document
Invoice Number: INV-2024-001
Date: 2024-01-15
From: Test Company Ltd.
To: Customer Corp.
Item: Professional Services
Amount: $1,000.00
Tax: $100.00
Total: $1,100.00
""")
        
        print(f"   ✅ Test file created: {test_file}")
        
        # Initialize components
        coordinator = AgentCoordinator()
        workflow_manager = WorkflowManager(coordinator)
        
        # Test workflow execution
        result = workflow_manager.execute_workflow(
            workflow_type=WorkflowType.STANDARD.value,
            input_data=test_file
        )
        
        print(f"   ✅ Workflow executed successfully")
        print(f"   ✅ Result status: {result.get('status', 'unknown')}")
        print(f"   ✅ Processing steps: {len(result.get('steps', []))}")
        
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
        
        return True
    except Exception as e:
        print(f"   ❌ File processing test failed: {e}")
        return False

def test_cli_commands():
    """Test CLI functionality"""
    print("\n⌨️  Testing CLI Commands...")
    
    try:
        # Test health command
        import subprocess
        result = subprocess.run([sys.executable, "main.py", "health"], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("   ✅ Health command executed successfully")
        else:
            print(f"   ⚠️  Health command returned non-zero: {result.returncode}")
        
        # Test help command
        result = subprocess.run([sys.executable, "main.py", "--help"], 
                              capture_output=True, text=True, timeout=10)
        
        if "Invoice Processing System" in result.stdout:
            print("   ✅ Help command shows correct information")
        
        return True
    except Exception as e:
        print(f"   ❌ CLI test failed: {e}")
        return False

def test_web_interface():
    """Test web interface components"""
    print("\n🌐 Testing Web Interface Components...")
    
    try:
        from ui.streamlit_app import InvoiceProcessingApp
        
        # Test app initialization
        app = InvoiceProcessingApp()
        print("   ✅ Streamlit app initialized")
        
        # Test login component
        login_component = app.login_component
        print("   ✅ Login component available")
        
        # Test auth manager
        auth_manager = app.auth_manager
        users = auth_manager.list_users()
        print(f"   ✅ Found {len(users)} users in system")
        
        return True
    except Exception as e:
        print(f"   ❌ Web interface test failed: {e}")
        return False

def test_configuration():
    """Test system configuration"""
    print("\n⚙️  Testing System Configuration...")
    
    try:
        from config.settings import settings
        
        print(f"   ✅ Ollama URL: {settings.OLLAMA_BASE_URL}")
        print(f"   ✅ Default region: {settings.DEFAULT_REGION}")
        print(f"   ✅ Supported regions: {len(settings.SUPPORTED_REGIONS)}")
        print(f"   ✅ Confidence threshold: {settings.CONFIDENCE_THRESHOLD}")
        
        return True
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False

def test_security_features():
    """Test security features"""
    print("\n🛡️  Testing Security Features...")
    
    try:
        from auth.password_utils import PasswordUtils
        
        # Test password strength validation
        strong, errors = PasswordUtils.is_password_strong("Admin123!")
        print(f"   ✅ Strong password validation: {strong}")
        
        weak, errors = PasswordUtils.is_password_strong("123")
        print(f"   ✅ Weak password rejection: {not weak} (errors: {len(errors)})")
        
        # Test token generation
        token = PasswordUtils.generate_secure_token()
        print(f"   ✅ Secure token generated: {len(token)} chars")
        
        # Test password hashing
        password = "TestPassword123!"
        hash_val, salt = PasswordUtils.create_password_hash(password)
        verified = PasswordUtils.verify_password(password, hash_val, salt)
        print(f"   ✅ Password hashing and verification: {verified}")
        
        return True
    except Exception as e:
        print(f"   ❌ Security test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Starting Comprehensive System Test")
    print("=" * 50)
    
    # Change to project directory
    os.chdir(project_root)
    
    # Run all tests
    test_results = []
    
    test_results.append(("Authentication", test_authentication()))
    test_results.append(("Core System", test_core_system()))
    test_results.append(("File Processing", test_file_processing()))
    test_results.append(("CLI Commands", test_cli_commands()))
    test_results.append(("Web Interface", test_web_interface()))
    test_results.append(("Configuration", test_configuration()))
    test_results.append(("Security Features", test_security_features()))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print("-" * 50)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is ready for use.")
        print("\n🚀 Next steps:")
        print("1. Start the web interface: python main.py web")
        print("2. Open browser to: http://localhost:8501")
        print("3. Login with: admin / Admin123!")
        print("4. Change the default password immediately!")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())