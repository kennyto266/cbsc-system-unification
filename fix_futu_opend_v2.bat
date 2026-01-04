@echo off
echo Fixing FutuOpenD with pdt_protection=0 - Version 2
echo ================================================

echo 1. Terminating ALL FutuOpenD processes...
taskkill /F /IM FutuOpenD.exe
taskkill /F /IM Futu_OpenD.exe
taskkill /F /IM "FutuOpenD.exe"

echo 2. Waiting for processes to terminate...
timeout /t 3 /nobreak > nul

echo 3. Starting FutuOpenD with pdt_protection=0...
cd /d "C:\Users\Penguin8n\AppData\Roaming\Futu_OpenD\open-d\windows"
start "" "FutuOpenD.exe" --pdt_protection=0

echo 4. Waiting for initialization...
timeout /t 10 /nobreak > nul

echo 5. Process complete!
echo ================================================