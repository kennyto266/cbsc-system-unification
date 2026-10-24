"""Integration Manager for Cursor CLI and AI Agent system.

This module manages the integration between Cursor CLI project and the AI Agent
trading system, providing a unified interface for all Telegram Bot functionality.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from .bot_interface import TelegramBotInterface, TelegramUser, UserRole
from .cursor_cli_integration import (
    TradingSignalNotification,
    SystemStatusNotification,
    UserCommandResponse
)
from .cursor_cli_bridge import CursorCLIBridge, CursorCLIConfig


class IntegrationManager:
    """Manages integration between Cursor CLI and AI Agent system."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Integration components
        self.bot_interface: Optional[TelegramBotInterface] = None
        self.cursor_bridge: Optional[CursorCLIBridge] = None
        
        # Integration state
        self.is_running = False
        self.start_time: Optional[datetime] = None
        
        # Statistics
        self.stats = {
            'messages_processed': 0,
            'signals_sent': 0,
            'status_updates_sent': 0,
            'commands_executed': 0,
            'errors': 0
        }
    
    async def initialize(self) -> bool:
        """Initialize the integration manager."""
        try:
            self.logger.info("Initializing integration manager...")
            
            # Initialize Cursor CLI bridge
            cursor_config = CursorCLIConfig(
                cursor_cli_path=self.config.get('cursor_cli_path', ''),
                bot_token=self.config.get('bot_token', ''),
                cursor_api_key=self.config.get('cursor_api_key', ''),
                allowed_user_ids=self.config.get('allowed_user_ids'),
                allowed_chat_ids=self.config.get('allowed_chat_ids'),
                command_timeout=self.config.get('command_timeout', 60),
                max_message_length=self.config.get('max_message_length', 6000),
                enable_trading_signals=self.config.get('enable_trading_signals', True),
                enable_system_monitoring=self.config.get('enable_system_monitoring', True),
                enable_cursor_commands=self.config.get('enable_cursor_commands', True)
            )
            
            self.cursor_bridge = CursorCLIBridge(cursor_config)
            
            if not await self.cursor_bridge.initialize():
                self.logger.error("Failed to initialize Cursor CLI bridge")
                return False
            
            # Get bot interface from bridge
            self.bot_interface = self.cursor_bridge.bot_interface
            
            # Register integration handlers
            await self._register_integration_handlers()
            
            self.is_running = True
            self.start_time = datetime.now()
            self.logger.info("Integration manager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize integration manager: {e}")
            return False
    
    async def _register_integration_handlers(self) -> None:
        """Register integration-specific handlers."""
        try:
            # Register trading signal handlers
            self.cursor_bridge.add_trading_handler(self._handle_trading_signal)
            
            # Register system monitoring handlers
            self.cursor_bridge.add_monitoring_handler(self._handle_system_status)
            
            # Register command handlers
            self.cursor_bridge.add_command_handler(self._handle_command_response)
            
            self.logger.info("Integration handlers registered")
            
        except Exception as e:
            self.logger.error(f"Error registering integration handlers: {e}")
    
    async def _handle_trading_signal(self, signal: TradingSignalNotification) -> None:
        """Handle trading signal from the system."""
        try:
            # Log signal
            self.logger.info(f"Processing trading signal: {signal.symbol} {signal.side}")
            
            # Update statistics
            self.stats['signals_sent'] += 1
            
            # Additional processing can be added here
            # e.g., save to database, trigger other actions, etc.
            
        except Exception as e:
            self.logger.error(f"Error handling trading signal: {e}")
            self.stats['errors'] += 1
    
    async def _handle_system_status(self, status: SystemStatusNotification) -> None:
        """Handle system status update."""
        try:
            # Log status
            self.logger.info(f"Processing system status: {status.status_type}")
            
            # Update statistics
            self.stats['status_updates_sent'] += 1
            
            # Additional processing can be added here
            # e.g., save to database, trigger alerts, etc.
            
        except Exception as e:
            self.logger.error(f"Error handling system status: {e}")
            self.stats['errors'] += 1
    
    async def _handle_command_response(self, response: UserCommandResponse) -> None:
        """Handle command response."""
        try:
            # Log command
            self.logger.info(f"Processing command response: {response.command_type}")
            
            # Update statistics
            self.stats['commands_executed'] += 1
            
            # Additional processing can be added here
            # e.g., save to database, trigger actions, etc.
            
        except Exception as e:
            self.logger.error(f"Error handling command response: {e}")
            self.stats['errors'] += 1
    
    # Public methods
    async def send_trading_signal(self, signal: TradingSignalNotification) -> bool:
        """Send trading signal to users."""
        try:
            if not self.cursor_bridge:
                return False
            
            return await self.cursor_bridge.send_trading_signal(signal)
            
        except Exception as e:
            self.logger.error(f"Error sending trading signal: {e}")
            return False
    
    async def send_system_status(self, status: SystemStatusNotification) -> bool:
        """Send system status to users."""
        try:
            if not self.cursor_bridge:
                return False
            
            return await self.cursor_bridge.send_system_status(status)
            
        except Exception as e:
            self.logger.error(f"Error sending system status: {e}")
            return False
    
    async def send_message(self, chat_id: int, text: str) -> bool:
        """Send message to specific chat."""
        try:
            if not self.bot_interface:
                return False
            
            return await self.bot_interface.send_message(chat_id=chat_id, text=text)
            
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return False
    
    async def broadcast_message(self, message: str, role_filter: Optional[UserRole] = None) -> int:
        """Broadcast message to users."""
        try:
            if not self.bot_interface:
                return 0
            
            return await self.bot_interface.broadcast_message(message, role_filter)
            
        except Exception as e:
            self.logger.error(f"Error broadcasting message: {e}")
            return 0
    
    async def get_user(self, user_id: int) -> Optional[TelegramUser]:
        """Get user by ID."""
        try:
            if not self.bot_interface:
                return None
            
            return await self.bot_interface.get_user(user_id)
            
        except Exception as e:
            self.logger.error(f"Error getting user: {e}")
            return None
    
    async def update_user_role(self, user_id: int, new_role: UserRole) -> bool:
        """Update user role."""
        try:
            if not self.bot_interface:
                return False
            
            return await self.bot_interface.update_user_role(user_id, new_role)
            
        except Exception as e:
            self.logger.error(f"Error updating user role: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get integration statistics."""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        stats = {
            'is_running': self.is_running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'uptime_seconds': uptime,
            'integration_stats': self.stats.copy()
        }
        
        # Add component statistics
        if self.cursor_bridge:
            stats['cursor_bridge_stats'] = self.cursor_bridge.get_statistics()
        
        if self.bot_interface:
            stats['bot_interface_stats'] = self.bot_interface.get_statistics()
        
        return stats
    
    async def shutdown(self) -> None:
        """Shutdown the integration manager."""
        try:
            self.logger.info("Shutting down integration manager...")
            self.is_running = False
            
            # Shutdown components
            if self.cursor_bridge:
                await self.cursor_bridge.shutdown()
            
            self.logger.info("Integration manager shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during integration manager shutdown: {e}")
    
    # Configuration management
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update configuration."""
        try:
            self.config.update(new_config)
            self.logger.info("Configuration updated")
            
        except Exception as e:
            self.logger.error(f"Error updating configuration: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config.copy()
    
    # Health check
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        try:
            health = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'components': {}
            }
            
            # Check bot interface
            if self.bot_interface:
                bot_stats = self.bot_interface.get_statistics()
                health['components']['bot_interface'] = {
                    'status': 'healthy' if bot_stats.get('is_running', False) else 'unhealthy',
                    'stats': bot_stats
                }
            else:
                health['components']['bot_interface'] = {'status': 'not_initialized'}
            
            # Check cursor bridge
            if self.cursor_bridge:
                bridge_stats = self.cursor_bridge.get_statistics()
                health['components']['cursor_bridge'] = {
                    'status': 'healthy' if bridge_stats.get('is_running', False) else 'unhealthy',
                    'stats': bridge_stats
                }
            else:
                health['components']['cursor_bridge'] = {'status': 'not_initialized'}
            
            # Overall health
            component_statuses = [comp['status'] for comp in health['components'].values()]
            if 'unhealthy' in component_statuses or 'not_initialized' in component_statuses:
                health['status'] = 'degraded'
            
            return health
            
        except Exception as e:
            self.logger.error(f"Error during health check: {e}")
            return {
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
