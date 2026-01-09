# CBSC TUI Startup Guide

## Quick Start

### 1. Install Dependencies
```bash
cd tui
pip install textual httpx websockets pydantic python-dotenv rich
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env if needed to change API endpoints
```

### 3. Start the TUI
```bash
python main.py
```

## Requirements

- Python 3.10+
- Textual 0.47.1+ (installed)
- httpx 0.25.2+ (installed)
- websockets 13.0+ (installed)
- pydantic 2.0+ (installed)
- python-dotenv 1.0+ (installed)
- rich 13.7+ (installed)

## Features

- Main Menu: Unified navigation system
- Strategy Management: View, create, edit, delete strategies
- System Monitoring: Real-time CPU and memory metrics
- Log Viewer: Real-time log streaming with filtering
- Database Browser: Browse tables and execute SQL queries
- Settings: Configure API endpoints, theme, and preferences

## Key Bindings

- `q` or `ctrl+c`: Quit application
- `esc`: Return to main menu

## Troubleshooting

### CSS Encoding Issues
If you see encoding errors, ensure the CSS file contains only ASCII characters.
Chinese comments have been removed from base.css to fix Windows encoding issues.

### API Connection Errors
Ensure your FastAPI backend is running on port 3004:
```bash
# Check if backend is running
curl http://localhost:3004/health
```

### WebSocket Connection Errors
Ensure WebSocket endpoint is accessible:
```bash
# Check WebSocket endpoint
wscat -c ws://localhost:3004/ws
```

## Verification

Run the verification script to check if everything is set up correctly:
```bash
python verify_app.py
```

Expected output:
```
[PASS] CBSCApp initialization successful!
[PASS] All screens can be imported!
[PASS] Application is ready to run!
```

## Project Structure

```
tui/
├── main.py                  # Application entry point
├── api/                     # API clients
│   ├── client.py           # HTTP client
│   └── websocket_client.py # WebSocket client
├── widgets/                 # Custom widgets
│   ├── strategy_list.py    # Strategy table
│   ├── system_metrics.py   # System metrics display
│   ├── log_viewer.py       # Log viewer
│   └── table_browser.py    # Database table browser
├── screens/                 # Application screens
│   ├── main_menu.py        # Main menu
│   ├── strategies.py       # Strategy management
│   ├── monitor.py          # System monitoring
│   ├── logs.py             # Log viewing
│   ├── database.py         # Database browser
│   └── settings.py         # Settings
├── styles/                  # CSS styles
│   └── base.css            # Base styles
└── utils/                   # Utilities
    └── config.py           # Configuration management
```

## Status

- All dependencies installed: Yes
- CSS file fixed: Yes (removed Chinese comments)
- Application verified: Yes
- Ready to run: Yes

Last updated: 2026-01-09
