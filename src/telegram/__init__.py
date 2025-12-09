"""Telegram Bot integration package for Hong Kong quantitative trading system.

This package provides Telegram Bot integration for real-time notifications,
user interaction, and system monitoring through Telegram messaging.
"""

from .bot_interface import (
    TelegramBotInterface,
    TelegramMessage,
    TelegramUser,
    TelegramCommand,
    MessageType,
    UserRole,
    CommandType
)
from .cursor_cli_integration import (
    CursorCLIIntegration,
    TradingSignalNotification,
    SystemStatusNotification,
    UserCommandResponse
)
from .cursor_cli_bridge import (
    CursorCLIBridge,
    CursorCLIConfig
)
from .integration_manager import IntegrationManager

__all__ = [
    # Bot interface
    'TelegramBotInterface',
    'TelegramMessage',
    'TelegramUser',
    'TelegramCommand',
    'MessageType',
    'UserRole',
    'CommandType',
    
    # Cursor CLI integration
    'CursorCLIIntegration',
    'TradingSignalNotification',
    'SystemStatusNotification',
    'UserCommandResponse',
    
    # Cursor CLI bridge
    'CursorCLIBridge',
    'CursorCLIConfig',
    
    # Integration manager
    'IntegrationManager'
]
