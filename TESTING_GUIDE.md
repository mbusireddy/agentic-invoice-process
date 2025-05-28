# 🧪 Invoice Processing System - Complete Testing Guide

This guide covers comprehensive testing of all system functionality including the new secure authentication system.

## 🚀 Quick Start Testing

### 1. Start the System
```bash
# Option A: Development mode
./scripts/start_services.sh

# Option B: Direct Streamlit launch
python main.py web

# Option C: CLI mode
python main.py process --help
```

### 2. Access the Web Interface
- Open browser to: http://localhost:8501
- You should see the secure login screen

## 🔐 Authentication Testing

### Default Credentials
```
Username: admin
Password: Admin123!
```

### Test Cases to Execute

#### 1. Login Functionality
- [ ] **Valid Login**: Use admin/Admin123! - should succeed
- [ ] **Invalid Password**: Try admin/wrongpass - should fail with error
- [ ] **Invalid Username**: Try baduser/Admin123! - should fail
- [ ] **Empty Fields**: Leave fields blank - should show validation error
- [ ] **Account Lockout**: Try 5+ wrong passwords - account should lock for 15 minutes

#### 2. Password Security
- [ ] **Weak Password**: Try changing to "123" - should reject
- [ ] **Strong Password**: Change to "NewPass123!" - should succeed
- [ ] **Password Confirmation**: Mismatched confirm password - should fail
- [ ] **Current Password**: Wrong current password - should fail

#### 3. Session Management
- [ ] **Session Persistence**: Login, close browser, reopen - should stay logged in
- [ ] **Logout**: Click logout button - should return to login screen
- [ ] **Session Timeout**: Wait 2+ hours idle - should auto-logout
- [ ] **Multiple Sessions**: Login from different browsers - both should work

## 👥 User Management Testing (Admin Only)

### Create Test Users
1. Login as admin
2. Go to Administration → Create User tab
3. Create users with different roles:

```
Username: processor1
Password: Process123!
Role: Processor
Email: processor@test.com

Username: viewer1  
Password: View123!
Role: Viewer
Email: viewer@test.com

Username: auditor1
Password: Audit123!
Role: Auditor  
Email: auditor@test.com
```

### Test Role-Based Access Control
- [ ] **Processor Role**: Can access Process Invoices, Dashboard, History
- [ ] **Viewer Role**: Can only access Dashboard, History (read-only)
- [ ] **Auditor Role**: Can access View, Audit, Reports
- [ ] **Admin Role**: Can access everything including Administration
- [ ] **Permission Denied**: Lower roles accessing admin features should be blocked

## 📊 Core System Testing

### 1. System Health Check
```bash
# Test CLI health check
python main.py health

# Expected output:
# - All 6 agents initialized
# - System status: healthy
# - Ollama connection status
```

### 2. Invoice Processing (Web Interface)

#### Test Files Setup
Create test files in `data/invoices/`:
```bash
# Create sample test files
echo "Sample Invoice Content" > data/invoices/test1.txt
echo "Another Invoice Sample" > data/invoices/test2.txt
```

#### Processing Tests
- [ ] **File Upload**: Drag & drop files - should show upload success
- [ ] **Workflow Selection**: Try different workflows (Standard, Fast Track, etc.)
- [ ] **Single Processing**: Process one file - should show progress bar
- [ ] **Batch Processing**: Process multiple files - should handle all files
- [ ] **Error Handling**: Upload invalid file - should show appropriate error
- [ ] **Results Display**: Processing should show confidence scores and status

### 3. Dashboard Testing
- [ ] **System Metrics**: Should show agent health, processing stats
- [ ] **Performance Charts**: Should display processing times and success rates
- [ ] **Recent Activity**: Should show latest processing results
- [ ] **Resource Usage**: Should display system resource information

### 4. History & Audit Testing
- [ ] **Processing History**: Should show previous processing jobs
- [ ] **Audit Logs**: Should display detailed audit trail
- [ ] **Data Export**: Should allow exporting history data
- [ ] **Search/Filter**: Should allow filtering by date, status, etc.

### 5. Settings Testing
- [ ] **Configuration Display**: Should show current system settings
- [ ] **Threshold Values**: Should display confidence and validation thresholds
- [ ] **System Actions**: Clear statistics, restart system should work
- [ ] **Regional Settings**: Should show supported regions

## 🔧 CLI Testing

### Basic Commands
```bash
# Test help
python main.py --help
python main.py process --help
python main.py web --help

# Test health check
python main.py health

# Test single file processing
python main.py process data/invoices/test1.txt

# Test batch processing
python main.py process data/invoices/*.txt --batch

# Test with different workflows
python main.py process test1.txt --workflow fast_track
python main.py process test1.txt --workflow detailed_review
```

### Expected CLI Outputs
- [ ] **Help Messages**: Should show clear usage instructions
- [ ] **Health Check**: Should report system status
- [ ] **Processing Output**: Should show step-by-step progress
- [ ] **Error Handling**: Should display meaningful error messages
- [ ] **Success Messages**: Should confirm successful operations

## 🐳 Docker Testing (Optional)

### Build and Run
```bash
# Build the container
docker build -t invoice-processor .

# Run with docker-compose
docker-compose up -d

# Check container health
docker-compose ps
docker-compose logs app
```

### Container Tests
- [ ] **Container Startup**: Should start without errors
- [ ] **Web Access**: Should be accessible on port 8501
- [ ] **Ollama Integration**: Should connect to Ollama service
- [ ] **Data Persistence**: Volumes should persist data
- [ ] **Service Health**: Health checks should pass

## 🚨 Error Scenarios Testing

### System Resilience
- [ ] **Ollama Offline**: System should work in limited mode
- [ ] **Missing Dependencies**: Should gracefully handle missing OCR/PDF libraries
- [ ] **Network Issues**: Should handle connection failures gracefully
- [ ] **Disk Space**: Should handle low disk space scenarios
- [ ] **Memory Pressure**: Should handle high memory usage

### Authentication Edge Cases
- [ ] **Corrupted Session**: Delete session files while logged in
- [ ] **Concurrent Logins**: Multiple users with same account
- [ ] **Password File Corruption**: Test recovery mechanisms
- [ ] **Session File Permissions**: Test with restricted file permissions

## 📈 Performance Testing

### Load Testing
```bash
# Stress test with multiple files
for i in {1..10}; do
    python main.py process data/invoices/test1.txt &
done
wait

# Monitor system resources
htop  # or top
```

### Performance Metrics
- [ ] **Processing Speed**: Time per document
- [ ] **Memory Usage**: RAM consumption during processing
- [ ] **CPU Utilization**: Processor usage patterns
- [ ] **Disk I/O**: File read/write performance
- [ ] **Concurrent Users**: Multiple simultaneous web sessions

## 🔍 Security Testing

### Authentication Security
- [ ] **SQL Injection**: Try SQL injection in login fields
- [ ] **XSS Attempts**: Try script injection in forms
- [ ] **Session Hijacking**: Test session token security
- [ ] **Brute Force**: Test account lockout mechanisms
- [ ] **Password Strength**: Test password policy enforcement

### File Security
- [ ] **Malicious Uploads**: Try uploading executable files
- [ ] **Path Traversal**: Test for directory traversal vulnerabilities
- [ ] **File Size Limits**: Test large file handling
- [ ] **File Type Validation**: Test unsupported file types

## 📋 Test Checklist Summary

### ✅ Authentication System
- [ ] Login/logout functionality
- [ ] Password policy enforcement
- [ ] Session management
- [ ] Role-based access control
- [ ] User management (admin)
- [ ] Account lockout protection

### ✅ Core Processing
- [ ] File upload and validation
- [ ] Invoice processing workflows
- [ ] Results generation and display
- [ ] Error handling and recovery
- [ ] Batch processing capabilities

### ✅ Web Interface
- [ ] All pages accessible by appropriate roles
- [ ] Navigation and user experience
- [ ] Data visualization and charts
- [ ] Forms and input validation
- [ ] Responsive design

### ✅ CLI Interface
- [ ] All commands functional
- [ ] Help documentation
- [ ] Output formatting
- [ ] Error reporting
- [ ] Batch operations

### ✅ System Integration
- [ ] Ollama LLM integration
- [ ] Document processing pipeline
- [ ] Audit logging
- [ ] Configuration management
- [ ] Service management scripts

## 🎯 Expected Results

### Successful System Operation
- Login screen appears immediately
- Admin can access all features
- Different user roles have appropriate access
- File processing works end-to-end
- All agents initialize successfully
- System health shows as "healthy"
- Audit logs capture all operations

### Performance Benchmarks
- Login response: < 2 seconds
- File upload: < 5 seconds for 10MB files
- Processing: < 30 seconds per standard invoice
- Page load times: < 3 seconds
- Memory usage: < 2GB for normal operations

## 🐛 Troubleshooting

### Common Issues
1. **Import Errors**: Check Python dependencies installed
2. **Port Conflicts**: Ensure port 8501 is available
3. **Ollama Connection**: Verify Ollama service is running
4. **File Permissions**: Check read/write access to data directories
5. **Authentication Issues**: Verify config/users.json exists and is readable

### Debug Commands
```bash
# Check system health
python main.py health

# Verify authentication system
python -c "from auth import AuthManager; AuthManager()"

# Test component imports
python -c "from ui.streamlit_app import InvoiceProcessingApp"

# Check service status
./scripts/status.sh
```

## 📞 Support

If you encounter issues:
1. Check the logs in the `logs/` directory
2. Verify all dependencies are installed
3. Ensure proper file permissions
4. Check network connectivity for Ollama
5. Review the error messages for specific guidance

---

**🎉 Congratulations!** If all tests pass, you have a fully functional, secure invoice processing system ready for production use!