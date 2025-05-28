#!/bin/bash

# Invoice Processing System - Production Installation Script
# This script sets up the system for production deployment with systemd

set -e  # Exit on any error

echo "🚀 Installing Invoice Processing System for Production"
echo "====================================================="

# Configuration
SERVICE_NAME="invoice-processing"
INSTALL_DIR="/opt/agentic-invoice-process"
SERVICE_USER="invoiceuser"
SERVICE_GROUP="invoiceuser"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)"
   exit 1
fi

echo "📋 Installation Configuration:"
echo "• Service name: $SERVICE_NAME"
echo "• Install directory: $INSTALL_DIR"
echo "• Service user: $SERVICE_USER"
echo "• Project source: $PROJECT_DIR"
echo ""

# Create service user
echo "👤 Creating service user..."
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd --system --shell /bin/bash --home-dir "$INSTALL_DIR" --create-home "$SERVICE_USER"
    echo "✅ Created user: $SERVICE_USER"
else
    echo "ℹ️  User already exists: $SERVICE_USER"
fi

# Create installation directory
echo "📁 Setting up installation directory..."
mkdir -p "$INSTALL_DIR"
chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"

# Copy application files
echo "📦 Copying application files..."
sudo -u "$SERVICE_USER" cp -r "$PROJECT_DIR"/* "$INSTALL_DIR/"

# Create necessary directories
echo "📂 Creating runtime directories..."
sudo -u "$SERVICE_USER" mkdir -p "$INSTALL_DIR"/{logs,.pids,data/processed,data/invoices}

# Set up Python virtual environment
echo "🐍 Setting up Python virtual environment..."
cd "$INSTALL_DIR"
sudo -u "$SERVICE_USER" python3 -m venv venv
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if [[ -f "$INSTALL_DIR/requirements.txt" ]]; then
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
elif [[ -f "$INSTALL_DIR/pyproject.toml" ]]; then
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install poetry
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/poetry" install --no-dev
else
    # Install minimal required dependencies
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install requests streamlit
fi

# Make scripts executable
echo "🔧 Setting script permissions..."
chmod +x "$INSTALL_DIR/scripts"/*.sh

# Update script paths for production
echo "⚙️  Updating script configurations..."
sed -i "s|python main.py|$INSTALL_DIR/venv/bin/python $INSTALL_DIR/main.py|g" "$INSTALL_DIR/scripts/start_services.sh"

# Install systemd service
echo "🔧 Installing systemd service..."
cp "$INSTALL_DIR/scripts/install.service" "/etc/systemd/system/$SERVICE_NAME.service"

# Update service file with correct paths
sed -i "s|/opt/agentic-invoice-process|$INSTALL_DIR|g" "/etc/systemd/system/$SERVICE_NAME.service"
sed -i "s|invoiceuser|$SERVICE_USER|g" "/etc/systemd/system/$SERVICE_NAME.service"

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

# Create log rotation configuration
echo "📄 Setting up log rotation..."
cat > "/etc/logrotate.d/$SERVICE_NAME" << EOF
$INSTALL_DIR/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su $SERVICE_USER $SERVICE_GROUP
}
EOF

# Create environment file
echo "🔧 Creating environment configuration..."
cat > "$INSTALL_DIR/.env" << EOF
# Invoice Processing System Environment Configuration
OLLAMA_BASE_URL=http://localhost:11434
PYTHONPATH=$INSTALL_DIR
LOG_LEVEL=INFO
WEB_PORT=8501
EOF

chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/.env"

# Install and configure Ollama (optional)
echo ""
read -p "📥 Install Ollama for LLM functionality? (y/N): " install_ollama
if [[ $install_ollama =~ ^[Yy]$ ]]; then
    echo "📥 Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
    
    # Enable and start Ollama service
    systemctl enable ollama
    systemctl start ollama
    
    echo "⏳ Waiting for Ollama to start..."
    sleep 5
    
    # Pull default model
    echo "📦 Pulling llama2 model..."
    sudo -u ollama ollama pull llama2
    
    echo "✅ Ollama installed and configured"
fi

# Set up firewall rules (if ufw is available)
if command -v ufw &> /dev/null; then
    echo "🔒 Configuring firewall..."
    ufw allow 8501/tcp comment "Invoice Processing Web Interface"
    echo "✅ Firewall configured (port 8501 opened)"
fi

# Final permissions check
echo "🔐 Setting final permissions..."
chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
chmod 750 "$INSTALL_DIR"
chmod 755 "$INSTALL_DIR/scripts"/*.sh

echo ""
echo "🎉 Production installation completed successfully!"
echo ""
echo "📋 Service Management Commands:"
echo "==============================="
echo "• Start service:    sudo systemctl start $SERVICE_NAME"
echo "• Stop service:     sudo systemctl stop $SERVICE_NAME"
echo "• Restart service:  sudo systemctl restart $SERVICE_NAME"
echo "• Check status:     sudo systemctl status $SERVICE_NAME"
echo "• View logs:        sudo journalctl -u $SERVICE_NAME -f"
echo "• Enable startup:   sudo systemctl enable $SERVICE_NAME"
echo "• Disable startup:  sudo systemctl disable $SERVICE_NAME"
echo ""
echo "🌐 Access Points:"
echo "================="
echo "• Web Interface: http://$(hostname -I | awk '{print $1}'):8501"
echo "• Service logs:  $INSTALL_DIR/logs/"
echo "• Configuration: $INSTALL_DIR/.env"
echo ""
echo "🚀 To start the service now:"
echo "sudo systemctl start $SERVICE_NAME"
echo ""
echo "✨ Invoice Processing System is ready for production use!"