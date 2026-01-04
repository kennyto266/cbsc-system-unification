@echo off
echo ========================================
echo Starting FutuOpenD with pdt_protection=0
echo ========================================
echo.
echo This will start FutuOpenD with the required setting
echo for API simulation trading access.
echo.
echo IMPORTANT: Please close all existing FutuOpenD instances first!
echo.
pause
echo.
echo Starting FutuOpenD...
"C:\Users\Penguin8n\AppData\Roaming\Futu_OpenD\open-d\windows\FutuOpenD.exe" --pdt_protection=0
echo.
echo FutuOpenD has been started with pdt_protection=0
echo.
echo NEXT STEPS:
echo 1. Login to your Futu account
echo 2. Wait 30 seconds for full initialization
echo 3. Run: python final_account_check.py
echo 4. Look for simulation account success message
echo.
pause