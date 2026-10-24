@echo off
set ENV_PATH=.env

cd /d %~dp0
cd ..

echo Installing requirements (if needed)...
pip install --quiet python-telegram-bot[rate-limiter,http2]==21.6 python-dotenv==1.0.1 >nul 2>nul

echo Starting Telegram Integration demo...
start "telegram-bot" /min cmd /c python -X utf8 examples\telegram_integration_demo.py
echo Launched. Check your Telegram bot for messages.


