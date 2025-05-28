# 🚀 Invoice Processing System - Quick Start Guide

## 🔧 System Requirements
- Python 3.11+
- 2GB RAM minimum
- 1GB disk space
- Internet connection (for Ollama downloads)

## ⚡ Quick Setup & Test

### 1. Install Dependencies
```bash
# Install required Python packages
pip install requests streamlit pandas numpy

# Optional: Install document processing libraries
pip install PyPDF2 Pillow pytesseract pdf2image
```

### 2. Run System Test
```bash
# Run comprehensive system test
python test_system.py

# Expected: 6/7 or 7/7 tests pass
```

### 3. Start the System
```bash
# Option A: Use service scripts
./scripts/start_services.sh

# Option B: Direct launch
python main.py web
```

### 4. Access the Application
1. **Open Browser**: Go to http://localhost:8501
2. **Login**: Use default credentials
   - Username: `admin`
   - Password: `Admin123!`
3. **Change Password**: Immediately change default password

## 🧪 Complete Testing Checklist

### ✅ Authentication Testing
- [ ] **Login Screen**: Should appear immediately on startup
- [ ] **Valid Login**: admin/Admin123! should work
- [ ] **Invalid Login**: Wrong password should fail with security message
- [ ] **Account Lockout**: 5 failed attempts should lock account for 15 minutes
- [ ] **Password Change**: Should enforce strong password policy
- [ ] **Logout**: Should return to login screen
- [ ] **Session Timeout**: Should auto-logout after 2 hours of inactivity

### ✅ User Management (Admin Only)
- [ ] **Create User**: Admin can create new users with different roles
- [ ] **Role Assignment**: Test Processor, Viewer, Auditor roles
- [ ] **User Activation/Deactivation**: Admin can enable/disable accounts
- [ ] **Session Management**: Admin can view and end active sessions

### ✅ Role-Based Access Control
- [ ] **Admin**: Can access all features including Administration panel
- [ ] **Processor**: Can process invoices, view results, upload files
- [ ] **Viewer**: Read-only access to dashboards and history
- [ ] **Auditor**: Can view, audit, and generate reports
- [ ] **Permission Denied**: Users accessing unauthorized pages should be blocked

### ✅ Core Invoice Processing
- [ ] **File Upload**: Drag & drop PDF/image files should work
- [ ] **Format Validation**: Only supported formats should be accepted
- [ ] **Size Limits**: Files over 50MB should be rejected
- [ ] **Preview**: File previews should display correctly
- [ ] **Processing**: Standard workflow should execute without errors
- [ ] **Results**: Should show confidence scores and processing status
- [ ] **Batch Processing**: Multiple files should process successfully

### ✅ Web Interface Features
- [ ] **Navigation**: All sidebar menu items should be accessible
- [ ] **Dashboard**: Should display system metrics and health status
- [ ] **History**: Should show previous processing results
- [ ] **Settings**: Should display current configuration
- [ ] **Administration**: Should show user management (admin only)
- [ ] **Responsive Design**: Should work on different screen sizes

### ✅ CLI Interface Testing
```bash
# Test all CLI commands
python main.py --help                    # Show help
python main.py health                    # System health check
python main.py process test.txt          # Process single file
python main.py process *.txt --batch     # Batch processing
python main.py web                       # Start web interface
```

### ✅ System Health & Monitoring
- [ ] **Agent Status**: All 6 agents should initialize successfully
- [ ] **Health Check**: System status should show as "healthy"
- [ ] **Error Handling**: Should gracefully handle missing dependencies
- [ ] **Logging**: All operations should be logged appropriately
- [ ] **Performance**: Processing should complete within reasonable time

## 🎯 Test Scenarios

### Scenario 1: New User Onboarding
1. Admin logs in with default credentials
2. Creates new processor user account
3. Logs out and logs in as new user
4. New user uploads and processes invoice
5. Views results and history

### Scenario 2: Security Testing
1. Try multiple invalid login attempts
2. Test session timeout
3. Test password strength requirements
4. Test role-based access restrictions
5. Test logout and re-login

### Scenario 3: Document Processing
1. Upload various file formats (PDF, PNG, JPG)
2. Test different workflow types
3. Process single and multiple files
4. Check processing results and confidence scores
5. Review audit logs

### Scenario 4: Admin Management
1. Create users with different roles
2. Test user activation/deactivation
3. Monitor active sessions
4. View system statistics
5. Manage system settings

## 📊 Expected Performance Benchmarks
- **Login Time**: < 2 seconds
- **File Upload**: < 5 seconds for 10MB files
- **Processing Time**: < 30 seconds per standard invoice
- **Page Load**: < 3 seconds for all pages
- **Memory Usage**: < 2GB under normal load

## 🐛 Common Issues & Solutions

### Issue: Login Fails with Default Credentials
**Solution**: Reset user database
```bash
rm -f config/users.json
python -c "from auth import AuthManager; AuthManager()"
```

### Issue: Web Interface Won't Start
**Solution**: Check port availability
```bash
lsof -i :8501  # Check if port is in use
python main.py web --port 8502  # Use different port
```

### Issue: File Processing Fails
**Solution**: Check dependencies
```bash
python main.py health  # Check system status
pip install PyPDF2 Pillow  # Install document processing
```

### Issue: Ollama Connection Errors
**Solution**: Install and start Ollama
```bash
# Install Ollama (Linux/Mac)
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
ollama pull llama2
```

### Issue: Permission Denied Errors
**Solution**: Check file permissions
```bash
chmod -R 755 scripts/
chmod -R 777 data/ logs/
```

## 🔒 Security Best Practices

### Initial Setup
1. **Change Default Password**: Immediately after first login
2. **Create Role-Based Users**: Don't use admin for daily operations
3. **Review Permissions**: Ensure users have minimal required access
4. **Enable Audit Logging**: Monitor all system activities

### Ongoing Security
1. **Regular Password Updates**: Enforce periodic password changes
2. **Session Monitoring**: Review active sessions periodically
3. **Access Reviews**: Audit user permissions quarterly
4. **System Updates**: Keep dependencies up to date

## 📞 Support & Troubleshooting

### Debug Commands
```bash
# System health check
python main.py health

# Test authentication
python -c "from auth import AuthManager; auth = AuthManager(); print('Auth OK')"

# Test web components
python -c "from ui.streamlit_app import InvoiceProcessingApp; print('UI OK')"

# Check service status
./scripts/status.sh
```

### Log Files
- **Application Logs**: `logs/web_interface.log`
- **Service Logs**: `logs/ollama.log`
- **Error Logs**: Check console output

### Getting Help
1. Check this guide first
2. Review error messages in logs
3. Verify all dependencies are installed
4. Check system requirements
5. Test with minimal configuration

## 🎉 Success Criteria

Your system is ready for production use when:
- ✅ All authentication tests pass
- ✅ File processing works end-to-end
- ✅ Role-based access control functions correctly
- ✅ System health shows as "healthy"
- ✅ Web interface loads without errors
- ✅ CLI commands execute successfully
- ✅ Audit logging captures all operations

**Congratulations! You now have a fully functional, secure invoice processing system with enterprise-grade authentication and role-based access control.**