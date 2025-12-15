@echo off
REM Memory Monitor Script for Development (Windows)

echo 🔍 Starting Memory Monitor...
echo ================================

REM Check Node.js processes
echo 🔎 Checking Node.js processes...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq node.exe" /fo csv ^| find "node.exe"') do (
    echo 📊 Node.js Process PID: %%i
    tasklist /fi "PID eq %%i" /fo csv | find "node.exe"
)

echo.
echo 💾 System Memory Info:
wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /format:table

echo.
echo 💡 Tips to reduce memory usage:
echo    1. Close unused browser tabs
echo    2. Restart development server periodically
echo    3. Use: npm run dev:high-mem for more memory
echo    4. Disable source maps in development
echo ================================

pause