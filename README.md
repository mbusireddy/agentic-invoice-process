# 🧾 Invoice Processing System

An AI-powered invoice processing system with secure authentication, multi-agent workflow, and role-based access control.

## ✨ Features

- **🔐 Secure Authentication**: Multi-user system with role-based access control
- **🤖 Multi-Agent Processing**: Specialized agents for parsing, validation, compliance, and approval
- **📊 Web Interface**: Modern Streamlit-based UI with real-time processing
- **⌨️ CLI Interface**: Complete command-line tools for automation
- **🛡️ Enterprise Security**: Account lockout, session management, audit logging
- **🌍 Multi-Region Support**: Compliance rules for US, EU, APAC, LATAM
- **📈 Monitoring**: System health checks and performance metrics

## 🚀 Quick Start

### Installation

```bash
# Using Poetry (recommended)
poetry install
poetry shell

# Or using pip
pip install -r requirements.txt
```

### Start the System

```bash
# Web interface
python main.py web

# CLI processing
python main.py process invoice.pdf

# System health check
python main.py health
```

### Access the Application

1. Open browser to: http://localhost:8501
2. Login with default credentials:
   - Username: `admin`
   - Password: `Admin123!`
3. **Important**: Change the default password immediately!

## 📋 User Roles

- **Admin**: Full system access + user management
- **Processor**: Process invoices, view results, approve documents
- **Viewer**: Read-only access to dashboards and history
- **Auditor**: View, audit, and generate compliance reports

## 🧪 Testing

```bash
# Run comprehensive system test
python test_system.py

# Check system health
python main.py health

# Test authentication
python -c "from auth import AuthManager; AuthManager()"
```

## 🔧 Configuration

### Environment Variables

- `OLLAMA_BASE_URL`: Ollama server URL (default: http://localhost:11434)
- `LOG_LEVEL`: Logging level (default: INFO)
- `WEB_PORT`: Web interface port (default: 8501)

### Optional Dependencies

```bash
# Document processing (PDF, OCR)
poetry install --extras docs

# AI/LLM features  
poetry install --extras ai

# All features
poetry install --extras all
```

## 📖 Documentation

- [Testing Guide](TESTING_GUIDE.md) - Comprehensive testing instructions
- [Quick Start](QUICK_START.md) - Fast setup and basic usage
- [Project Structure](ProjectStructure.md) - System architecture overview

## 🛠️ Development

### Poetry Commands

```bash
# Install dependencies
poetry install

# Update lock file
poetry lock

# Run tests
poetry run pytest

# Format code
poetry run black .
poetry run isort .
```

### Service Management

```bash
# Start all services
./scripts/start_services.sh

# Check status
./scripts/status.sh

# Stop services
./scripts/stop_services.sh
```

## 🐳 Docker Deployment

```bash
# Build and run
docker-compose up -d

# Production deployment
sudo ./scripts/install_production.sh
```

## 📊 System Requirements

- Python 3.11+
- 2GB RAM minimum
- 1GB disk space
- Internet connection (for AI features)

## 🔒 Security Features

- PBKDF2 password hashing with salt
- Session-based authentication with timeouts
- Account lockout protection (5 attempts)
- Role-based permission system
- Comprehensive audit logging
- Secure token generation

## 📈 Performance

- **Login**: < 2 seconds
- **File Upload**: < 5 seconds (10MB files)
- **Processing**: < 30 seconds per invoice
- **Memory Usage**: < 2GB normal operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the documentation
2. Review error logs in `logs/` directory
3. Run system health check: `python main.py health`
4. Verify dependencies: `poetry check`

---

**🎉 Ready to process invoices with enterprise-grade security and AI-powered automation!**