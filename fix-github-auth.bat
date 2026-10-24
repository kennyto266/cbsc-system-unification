@echo off
echo Clearing GitHub authentication...

REM Clear environment variable
set GITHUB_TOKEN=

REM Verify it's cleared
echo GITHUB_TOKEN is: "%GITHUB_TOKEN%"

REM Test GitHub connection
gh auth status

echo.
echo If authentication is working above, you can now run PM sync!
pause