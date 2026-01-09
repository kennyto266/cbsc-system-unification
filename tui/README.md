# CBSC Textual TUI

Textual-based Terminal User Interface for CBSC Quantitative Trading System.

## Features

- **Main Menu**: Unified navigation system
- **Strategy Management**: View, create, edit, and delete trading strategies
- **System Monitoring**: Real-time CPU and memory metrics
- **Log Viewer**: Real-time log streaming with filtering
- **Database Browser**: Browse tables and execute SQL queries
- **Settings**: Configure API endpoints, theme, and preferences

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API endpoints
```

## Usage

```bash
# Run the TUI
python main.py

# Run tests
python test_basic.py
```

## Project Structure

```
tui/
├── main.py                 # Application entry point
├── api/                   # API clients
│   ├── client.py         # HTTP client for FastAPI
│   └── websocket_client.py  # WebSocket client
├── widgets/               # Custom widgets
│   ├── strategy_list.py  # Strategy table
│   ├── system_metrics.py # System metrics display
│   ├── log_viewer.py     # Log viewer
│   └── table_browser.py  # Database table browser
├── screens/               # Application screens
│   ├── main_menu.py      # Main menu
│   ├── strategies.py     # Strategy management
│   ├── monitor.py        # System monitoring
│   ├── logs.py           # Log viewing
│   ├── database.py       # Database browser
│   └── settings.py       # Settings
├── styles/                # CSS styles
│   └── base.css          # Base styles
├── utils/                 # Utilities
│   └── config.py         # Configuration management
├── requirements.txt       # Python dependencies
└── .env.example          # Environment template
```

## Key Bindings

- `q` or `ctrl+c`: Quit application
- `esc`: Return to main menu

## Configuration

Edit `.env` file to configure:

```bash
CBSC_API_URL=http://localhost:3004
CBSC_WS_URL=ws://localhost:3004/ws
```

## Requirements

- Python 3.10+
- FastAPI backend running on port 3004
- PostgreSQL database (optional for database browser)

