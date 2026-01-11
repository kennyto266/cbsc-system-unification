#!/bin/bash

echo "🔧 Fixing Memory Issues..."
echo "========================="

# Kill existing processes
echo "🔄 Stopping existing processes..."
pkill -f "node.*vite" 2>/dev/null || true
pkill -f "node.*react" 2>/dev/null || true

# Clear Node.js cache
echo "🧹 Clearing caches..."
rm -rf frontend/node_modules/.vite 2>/dev/null || true
rm -rf frontend/dist 2>/dev/null || true
npm cache clean --force 2>/dev/null || true

# Set environment variables
echo "⚙️  Setting environment variables..."
export NODE_OPTIONS="--max-old-space-size=16384"
export VITE_CJS_IGNORE_WARNING=true

echo ""
echo "✅ Memory fix complete!"
echo ""
echo "🚀 To start development with high memory:"
echo "   cd frontend && npm run dev:high-mem"
echo ""
echo "📊 To monitor memory usage:"
echo "   ./scripts/memory-monitor.sh"
echo "========================="