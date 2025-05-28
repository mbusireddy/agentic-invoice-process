#!/bin/bash

# Invoice Processing System - Status Check Script
# This script checks the status of all services

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PIDS_DIR="$PROJECT_DIR/.pids"
LOGS_DIR="$PROJECT_DIR/logs"

# Function to check service status
check_service_status() {
    local service_name=$1
    local pid_file="$PIDS_DIR/${service_name}.pid"
    local log_file="$LOGS_DIR/${service_name}.log"
    
    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            local uptime=$(ps -o etime= -p "$pid" | tr -d ' ')
            echo "✅ $service_name: Running (PID: $pid, Uptime: $uptime)"
            
            # Show recent log entries if available
            if [[ -f "$log_file" ]]; then
                local log_size=$(wc -l < "$log_file" 2>/dev/null || echo "0")
                echo "   📄 Log: $log_file ($log_size lines)"
                
                # Show last error if any
                local last_error=$(tail -20 "$log_file" 2>/dev/null | grep -i "error\|exception\|failed" | tail -1 || true)
                if [[ -n "$last_error" ]]; then
                    echo "   ⚠️  Recent error: $last_error"
                fi
            fi
        else
            echo "❌ $service_name: Not running (stale PID file)"
            return 1
        fi
    else
        echo "❌ $service_name: Not running (no PID file)"
        return 1
    fi
    return 0
}

# Function to check external services
check_external_services() {
    echo ""
    echo "🔍 External Services:"
    echo "===================="
    
    # Check Ollama
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama API: Available at http://localhost:11434"
        
        # List available models
        local models=$(curl -s http://localhost:11434/api/tags | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    models = [model['name'] for model in data.get('models', [])]
    print('   📦 Models: ' + ', '.join(models) if models else '   📦 No models installed')
except:
    print('   ❓ Could not parse models')
" 2>/dev/null || echo "   ❓ Could not check models")
        echo "$models"
    else
        echo "❌ Ollama API: Not available at http://localhost:11434"
    fi
    
    # Check web interface
    if curl -s http://localhost:8501 > /dev/null 2>&1; then
        echo "✅ Web Interface: Available at http://localhost:8501"
    else
        echo "❌ Web Interface: Not available at http://localhost:8501"
    fi
}

# Function to show system resources
show_system_info() {
    echo ""
    echo "💻 System Resources:"
    echo "==================="
    
    # Memory usage
    local mem_info=$(free -h | grep "Mem:" | awk '{print $3 "/" $2 " (" $3/$2*100 "%)"}')
    echo "🧠 Memory: $mem_info"
    
    # Disk usage for project directory
    local disk_usage=$(du -sh "$PROJECT_DIR" 2>/dev/null | cut -f1)
    echo "💾 Project size: $disk_usage"
    
    # Log files size
    if [[ -d "$LOGS_DIR" ]]; then
        local logs_size=$(du -sh "$LOGS_DIR" 2>/dev/null | cut -f1)
        local logs_count=$(find "$LOGS_DIR" -type f -name "*.log" | wc -l)
        echo "📄 Logs: $logs_size ($logs_count files)"
    fi
}

# Function to show recent activity
show_recent_activity() {
    echo ""
    echo "📈 Recent Activity:"
    echo "=================="
    
    if [[ -d "$LOGS_DIR" ]]; then
        # Find most recent log entries across all logs
        echo "🕐 Last 5 log entries:"
        find "$LOGS_DIR" -name "*.log" -type f -exec tail -1 {} \; 2>/dev/null | \
        grep -v "^$" | sort | tail -5 | \
        while read -r line; do
            echo "   • $line"
        done
    else
        echo "ℹ️  No logs directory found"
    fi
}

# Main execution
echo "🔍 Invoice Processing System Status"
echo "===================================="
echo "📍 Project: $PROJECT_DIR"
echo "🕐 Check time: $(date)"
echo ""

echo "🚀 Service Status:"
echo "=================="

# Check each service
services=("web_interface" "ollama")
running_count=0
total_count=${#services[@]}

for service in "${services[@]}"; do
    if check_service_status "$service"; then
        ((running_count++))
    fi
done

echo ""
echo "📊 Summary: $running_count/$total_count services running"

# Check external services
check_external_services

# Show system information
show_system_info

# Show recent activity
show_recent_activity

echo ""
echo "📋 Management Commands:"
echo "======================"
echo "• Start all: ./scripts/start_services.sh"
echo "• Stop all: ./scripts/stop_services.sh"
echo "• View logs: tail -f logs/<service>.log"
echo "• Health check: python main.py health"
echo ""

# Exit with error code if not all services are running
if [[ $running_count -lt $total_count ]]; then
    echo "⚠️  Some services are not running"
    exit 1
else
    echo "✅ All services are healthy"
    exit 0
fi