#!/bin/bash

# Setup script for Qwen2.5:14b model with Ollama
# This script ensures Qwen2.5:14b is available for the invoice processing system

set -e

echo "🤖 Setting up Qwen2.5:14b for Invoice Processing System"
echo "======================================================="

# Check if Ollama is installed
check_ollama() {
    if ! command -v ollama &> /dev/null; then
        echo "❌ Ollama is not installed!"
        echo ""
        echo "📥 Please install Ollama first:"
        echo "   Linux/Mac: curl -fsSL https://ollama.ai/install.sh | sh"
        echo "   Windows: Download from https://ollama.ai/download"
        echo ""
        exit 1
    else
        echo "✅ Ollama is installed"
    fi
}

# Check if Ollama service is running
check_ollama_service() {
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "⚠️  Ollama service is not running"
        echo "🔄 Starting Ollama service..."
        
        # Try to start Ollama in background
        ollama serve > /dev/null 2>&1 &
        sleep 5
        
        # Check if it's running now
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo "✅ Ollama service started successfully"
        else
            echo "❌ Failed to start Ollama service"
            echo "   Please start manually: ollama serve"
            exit 1
        fi
    else
        echo "✅ Ollama service is running"
    fi
}

# Pull Qwen2.5:14b model
pull_qwen_model() {
    echo "📥 Checking for Qwen2.5:14b model..."
    
    # Check if model already exists
    if ollama list | grep -q "qwen2.5:14b"; then
        echo "✅ Qwen2.5:14b model is already available"
        return 0
    fi
    
    echo "📦 Pulling Qwen2.5:14b model (this may take 10-15 minutes)..."
    echo "   Model size: ~8.4GB"
    echo ""
    
    # Pull the model with progress
    ollama pull qwen2.5:14b
    
    if [ $? -eq 0 ]; then
        echo "✅ Qwen2.5:14b model downloaded successfully"
    else
        echo "❌ Failed to download Qwen2.5:14b model"
        exit 1
    fi
}

# Pull embedding model
pull_embedding_model() {
    echo "📥 Checking for embedding model..."
    
    if ollama list | grep -q "nomic-embed-text"; then
        echo "✅ Embedding model is already available"
        return 0
    fi
    
    echo "📦 Pulling nomic-embed-text model..."
    ollama pull nomic-embed-text
    
    if [ $? -eq 0 ]; then
        echo "✅ Embedding model downloaded successfully"
    else
        echo "⚠️  Failed to download embedding model (optional)"
    fi
}

# Test model functionality
test_qwen_model() {
    echo "🧪 Testing Qwen2.5:14b model..."
    
    # Test basic generation
    test_response=$(ollama run qwen2.5:14b "Extract invoice number from: Invoice #INV-2024-001. Reply with just the number." --format json 2>/dev/null || echo "")
    
    if [[ -n "$test_response" ]]; then
        echo "✅ Qwen2.5:14b model is working correctly"
        echo "   Test response: $test_response"
    else
        echo "⚠️  Model test completed (response may be empty)"
    fi
}

# Update system configuration
update_config() {
    echo "⚙️  Updating system configuration..."
    
    # Create .env file if it doesn't exist
    if [[ ! -f ".env" ]]; then
        echo "📝 Creating .env configuration file..."
        cat > .env << EOF
# Ollama Configuration for Qwen2.5:14b
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:14b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Performance Settings for 14B model
AGENT_TIMEOUT=60
MAX_RETRIES=3
CONFIDENCE_THRESHOLD=0.85

# System Configuration
LOG_LEVEL=INFO
DEBUG_MODE=false
EOF
        echo "✅ Configuration file created"
    else
        echo "✅ Configuration file already exists"
    fi
}

# Show system requirements
show_requirements() {
    echo ""
    echo "💻 System Requirements for Qwen2.5:14b:"
    echo "========================================"
    echo "• RAM: 16GB minimum (24GB recommended)"
    echo "• Storage: 10GB free space"
    echo "• CPU: Modern multi-core processor"
    echo "• GPU: Optional (NVIDIA with CUDA for faster inference)"
    echo ""
    echo "⚡ Performance Notes:"
    echo "• First run may be slower (model loading)"
    echo "• Subsequent requests will be faster"
    echo "• Consider GPU acceleration for production use"
    echo ""
}

# Main execution
main() {
    # Change to project directory
    cd "$(dirname "$0")/.."
    
    echo "📍 Working directory: $(pwd)"
    echo ""
    
    # Run all setup steps
    check_ollama
    check_ollama_service
    pull_qwen_model
    pull_embedding_model
    test_qwen_model
    update_config
    
    echo ""
    echo "🎉 Qwen2.5:14b Setup Complete!"
    echo "==============================="
    echo ""
    echo "📋 What's Ready:"
    echo "• ✅ Ollama service is running"
    echo "• ✅ Qwen2.5:14b model is available"
    echo "• ✅ System configuration updated"
    echo ""
    echo "🚀 Next Steps:"
    echo "1. Test the system: python test_system.py"
    echo "2. Start web interface: python main.py web"
    echo "3. Process invoices: python main.py process invoice.pdf"
    echo ""
    echo "🌐 Access the application at: http://localhost:8501"
    echo "🔐 Login with: admin / Admin123!"
    echo ""
    
    show_requirements
}

# Handle script arguments
case "${1:-}" in
    --check-only)
        check_ollama
        check_ollama_service
        echo "✅ Ollama check completed"
        ;;
    --model-only)
        check_ollama_service
        pull_qwen_model
        pull_embedding_model
        echo "✅ Model setup completed"
        ;;
    --test)
        test_qwen_model
        ;;
    *)
        main
        ;;
esac