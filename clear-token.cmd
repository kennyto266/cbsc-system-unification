@echo off
echo Clearing GitHub authentication...

REM Clear all GitHub related environment variables
for /f "delims==" %%i in ('set') do (
    echo %%i | findstr /i GITHUB_TOKEN >nul 2>&1 && set "%%i="
)

echo Environment variables cleared
echo.
echo Testing GitHub authentication...
gh auth status

echo.
echo If still showing token issues, please:
echo 1. Open new Command Prompt
echo 2. Run: gh auth login
echo 3. Or set GITHUB_TOKEN= in current session

pause