@echo off
REM Memory Fix Script (Windows)

echo 🔧 Fixing Memory Issues...
echo =========================

REM Kill existing processes
echo 🔄 Stopping existing processes...
taskkill /f /im node.exe 2>nul

REM Clear Node.js cache
echo 🧹 Clearing caches...
if exist "frontend\node_modules\.vite" rmdir /s /q "frontend\node_modules\.vite"
if exist "frontend\dist" rmdir /s /q "frontend\dist"
npm cache clean --force 2>nul

REM Set environment variables
echo ⚙️  Setting environment variables...
set NODE_OPTIONS=--max-old-space-size=16384
set VITE_CJS_IGNORE_WARNING=true

echo.
echo ✅ Memory fix complete!
echo.
echo 🚀 To start development with high memory:
echo    cd frontend && npm run dev:high-mem
echo.
echo 📊 To monitor memory usage:
echo    scripts\memory-monitor.bat
echo =========================

pause