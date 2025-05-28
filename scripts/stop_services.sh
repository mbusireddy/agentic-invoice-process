#!/bin/bash

# Invoice Processing System - Stop Services Script
# This script stops all running services for the invoice processing system

set -e  # Exit on any error

echo "🛑 Stopping Invoice Processing System Services..."

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PIDS_DIR="$PROJECT_DIR/.pids"

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file="$PIDS_DIR/${service_name}.pid"
    
    if [[ ! -f "$pid_file" ]]; then
        echo "ℹ️  $service_name is not running (no PID file)"
        return 0
    fi
    
    local pid=$(cat "$pid_file")
    
    if ! ps -p "$pid" > /dev/null 2>&1; then
        echo "ℹ️  $service_name is not running (stale PID)"
        rm -f "$pid_file"
        return 0
    fi
    
    echo "🔄 Stopping $service_name (PID: $pid)..."
    
    # Try graceful shutdown first
    kill "$pid" 2>/dev/null || true
    
    # Wait for graceful shutdown
    for i in {1..10}; do
        if ! ps -p "$pid" > /dev/null 2>&1; then
            echo "✅ $service_name stopped gracefully"
            rm -f "$pid_file"
            return 0
        fi
        sleep 1
    done
    
    # Force kill if still running
    echo "⚠️  Force killing $service_name..."
    kill -9 "$pid" 2>/dev/null || true
    sleep 1
    
    if ! ps -p "$pid" > /dev/null 2>&1; then
        echo "✅ $service_name force stopped"
        rm -f "$pid_file"
    else
        echo "❌ Failed to stop $service_name"
        return 1
    fi
}

# Function to stop all Python processes related to the project
stop_python_processes() {
    echo "🔍 Looking for related Python processes..."
    
    local project_name="agentic-invoice-process"
    local pids=$(pgrep -f "$project_name" 2>/dev/null || true)
    
    if [[ -z "$pids" ]]; then
        echo "ℹ️  No related Python processes found"
        return 0
    fi
    
    echo "🔄 Stopping related Python processes..."
    for pid in $pids; do
        local cmd=$(ps -p "$pid" -o cmd= 2>/dev/null || echo "unknown")
        echo "  • Stopping PID $pid: $cmd"
        kill "$pid" 2>/dev/null || true
    done
    
    sleep 2
    
    # Check if any are still running
    local remaining=$(pgrep -f "$project_name" 2>/dev/null || true)
    if [[ -n "$remaining" ]]; then
        echo "⚠️  Force killing remaining processes..."
        pkill -9 -f "$project_name" 2>/dev/null || true
    fi
    
    echo "✅ Python processes cleaned up"
}

# Function to stop Ollama if we started it
stop_ollama() {
    local ollama_pid_file="$PIDS_DIR/ollama.pid"
    
    if [[ -f "$ollama_pid_file" ]]; then
        stop_service "ollama"
    else
        echo "ℹ️  Ollama was not started by this script (external service)"
        echo "   To stop external Ollama: sudo systemctl stop ollama"
    fi
}

# Main execution
echo "📍 Project directory: $PROJECT_DIR"
echo "🆔 PIDs directory: $PIDS_DIR"
echo ""

# Stop individual services
echo "🛑 Stopping services..."
stop_service "web_interface"
stop_ollama

echo ""

# Clean up any remaining processes
stop_python_processes

echo ""

# Clean up PID directory if empty
if [[ -d "$PIDS_DIR" ]] && [[ -z "$(ls -A "$PIDS_DIR")" ]]; then
    rmdir "$PIDS_DIR"
    echo "🧹 Cleaned up empty PID directory"
fi

echo ""
echo "🎉 All services stopped successfully!"
echo ""
echo "📋 Useful Commands:"
echo "==================="
echo "• Start services: ./scripts/start_services.sh"
echo "• Check status: ./scripts/status.sh"
echo "• View logs: ls -la logs/"
echo ""
echo "✨ Invoice Processing System is now stopped"