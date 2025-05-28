#!/bin/bash

# Invoice Processing System - Start Services Script
# This script starts all required services for the invoice processing system

set -e  # Exit on any error

echo "🚀 Starting Invoice Processing System Services..."

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOGS_DIR="$PROJECT_DIR/logs"
PIDS_DIR="$PROJECT_DIR/.pids"

# Create necessary directories
mkdir -p "$LOGS_DIR"
mkdir -p "$PIDS_DIR"

# Function to check if a service is running
check_service() {
    local service_name=$1
    local pid_file="$PIDS_DIR/${service_name}.pid"
    
    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "✅ $service_name is already running (PID: $pid)"
            return 0
        else
            echo "🧹 Cleaning up stale PID file for $service_name"
            rm -f "$pid_file"
        fi
    fi
    return 1
}

# Function to start a service
start_service() {
    local service_name=$1
    local command=$2
    local pid_file="$PIDS_DIR/${service_name}.pid"
    local log_file="$LOGS_DIR/${service_name}.log"
    
    if check_service "$service_name"; then
        return 0
    fi
    
    echo "🔄 Starting $service_name..."
    
    # Start service in background and capture PID
    cd "$PROJECT_DIR"
    nohup $command > "$log_file" 2>&1 &
    local pid=$!
    echo "$pid" > "$pid_file"
    
    # Wait a moment and check if service started successfully
    sleep 2
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "✅ $service_name started successfully (PID: $pid)"
        echo "📄 Logs: $log_file"
    else
        echo "❌ Failed to start $service_name"
        echo "📄 Check logs: $log_file"
        rm -f "$pid_file"
        return 1
    fi
}

# Function to check and start Ollama
start_ollama() {
    echo "🔍 Checking Ollama service..."
    
    # Check if Ollama is installed
    if ! command -v ollama &> /dev/null; then
        echo "⚠️  Ollama not found. Please install Ollama from https://ollama.ai"
        echo "   The system will work in limited mode without LLM capabilities"
        return 1
    fi
    
    # Check if Ollama is already running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama is already running"
        return 0
    fi
    
    echo "🔄 Starting Ollama..."
    ollama serve > "$LOGS_DIR/ollama.log" 2>&1 &
    local ollama_pid=$!
    echo "$ollama_pid" > "$PIDS_DIR/ollama.pid"
    
    # Wait for Ollama to start
    echo "⏳ Waiting for Ollama to start..."
    for i in {1..30}; do
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo "✅ Ollama started successfully"
            return 0
        fi
        sleep 1
    done
    
    echo "❌ Ollama failed to start within 30 seconds"
    return 1
}

# Function to pull required models
setup_ollama_models() {
    echo "🔍 Checking Ollama models..."
    
    # Check if llama2 model is available
    if ollama list | grep -q "llama2"; then
        echo "✅ llama2 model is available"
    else
        echo "📥 Pulling llama2 model (this may take a while)..."
        ollama pull llama2
        echo "✅ llama2 model installed"
    fi
}

# Main execution
echo "📍 Project directory: $PROJECT_DIR"
echo "📂 Logs directory: $LOGS_DIR"
echo "🆔 PIDs directory: $PIDS_DIR"
echo ""

# 1. Start Ollama (optional but recommended)
if start_ollama; then
    setup_ollama_models
fi

echo ""

# 2. Start web interface
start_service "web_interface" "python main.py web --port 8501"

echo ""
echo "🎉 Service startup complete!"
echo ""
echo "📊 Service Status:"
echo "=================="

# Show service status
for service in web_interface ollama; do
    if check_service "$service"; then
        continue
    else
        echo "❌ $service is not running"
    fi
done

echo ""
echo "🌐 Access Points:"
echo "================="
echo "📱 Web Interface: http://localhost:8501"
echo "🤖 Ollama API: http://localhost:11434"
echo ""
echo "📋 Useful Commands:"
echo "==================="
echo "• Check status: ./scripts/status.sh"
echo "• Stop services: ./scripts/stop_services.sh"
echo "• View logs: tail -f logs/<service>.log"
echo "• Process files: python main.py process <file>"
echo ""
echo "✨ Invoice Processing System is ready!"