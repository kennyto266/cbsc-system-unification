@echo off
echo ========================================
echo Fixing FutuOpenD pdt_protection Issue
echo ========================================
echo.

echo Step 1: Terminating existing FutuOpenD processes...
taskkill /F /IM FutuOpenD.exe >nul 2>&1
timeout /t 2 >nul

echo Step 2: Starting FutuOpenD with pdt_protection=0...
echo.
echo IMPORTANT: Please login to your account when prompted!
echo.
cd /d "C:\Users\Penguin8n\AppData\Roaming\Futu_OpenD\open-d\windows"
start "" "FutuOpenD.exe" --pdt_protection=0

echo.
echo FutuOpenD has been started with pdt_protection=0
echo Please login and wait 30 seconds before testing.

pause