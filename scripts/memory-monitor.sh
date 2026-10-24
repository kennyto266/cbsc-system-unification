#!/bin/bash

# Memory Monitor Script for Development
# This script monitors memory usage and provides warnings

echo "🔍 Starting Memory Monitor..."
echo "================================"

# Check current memory usage
check_memory() {
    local process_name=$1
    local pid=$2

    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        local memory=$(ps -o pid,ppid,cmd,%mem,%cpu --sort=-%mem -p "$pid" | tail -1 | awk '{print $4}')
        echo "📊 $process_name (PID: $pid) Memory Usage: ${memory}%"

        # Convert to number for comparison
        local memory_num=$(echo "$memory" | sed 's/%//')

        if (( $(echo "$memory_num > 80" | bc -l) )); then
            echo "⚠️  WARNING: High memory usage detected!"
            echo "   Consider increasing Node.js memory limit:"
            echo "   export NODE_OPTIONS=\"--max-old-space-size=16384\""
        fi
    fi
}

# Monitor Node.js processes
echo "🔎 Checking Node.js processes..."
node_pids=$(pgrep -f "node.*vite\|node.*react\|node.*next")

if [ -n "$node_pids" ]; then
    while read -r pid; do
        check_memory "Node.js" "$pid"
    done <<< "$node_pids"
else
    echo "ℹ️  No Node.js development servers found running"
fi

# System memory info
echo ""
echo "💾 System Memory Info:"
if command -v free >/dev/null 2>&1; then
    free -h
elif command -v vm_stat >/dev/null 2>&1; then
    # macOS
    vm_stat | head -10
else
    # Windows fallback
    echo "Use Task Manager to check system memory"
fi

echo ""
echo "💡 Tips to reduce memory usage:"
echo "   1. Close unused browser tabs"
echo "   2. Restart development server periodically"
echo "   3. Use: npm run dev:high-mem for more memory"
echo "   4. Disable source maps in development"
echo "================================"