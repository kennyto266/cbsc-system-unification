"""Cursor CLI integration for Telegram Bot.

This module integrates the CURSOR CLI project's Telegram Bot functionality
with the main trading system.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
import json
from pydantic import BaseModel, Field

from .bot_interface import TelegramBotInterface, TelegramUser, UserRole, MessageType


class TradingSignalNotification(BaseModel):
    """Trading signal notification model."""
    signal_id: str = Field(..., description="Signal identifier")
    symbol: str = Field(..., description="Trading symbol")
    side: str = Field(..., description="Signal side (BUY/SELL/HOLD)")
    strength: float = Field(..., ge=0.0, le=1.0, description="Signal strength")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Signal confidence")
    price: float = Field(..., description="Current price")
    reasoning: str = Field(..., description="Signal reasoning")
    timestamp: datetime = Field(default_factory=datetime.now, description="Signal timestamp")
    
    # Additional signal data
    agent_id: str = Field(..., description="Agent that generated the signal")
    strategy_name: str = Field(..., description="Strategy name")
    risk_level: str = Field("medium", description="Risk level")
    expected_return: Optional[float] = Field(None, description="Expected return")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")


class SystemStatusNotification(BaseModel):
    """System status notification model."""
    status_id: str = Field(..., description="Status identifier")
    status_type: str = Field(..., description="Status type")
    message: str = Field(..., description="Status message")
    severity: str = Field("info", description="Severity level")
    timestamp: datetime = Field(default_factory=datetime.now, description="Status timestamp")
    
    # System metrics
    cpu_usage: Optional[float] = Field(None, description="CPU usage percentage")
    memory_usage: Optional[float] = Field(None, description="Memory usage percentage")
    disk_usage: Optional[float] = Field(None, description="Disk usage percentage")
    network_latency: Optional[float] = Field(None, description="Network latency in ms")
    
    # Agent status
    agents_status: Dict[str, str] = Field(default_factory=dict, description="Agent statuses")
    active_strategies: int = Field(0, description="Number of active strategies")
    total_trades: int = Field(0, description="Total number of trades")


class UserCommandResponse(BaseModel):
    """User command response model."""
    command_id: str = Field(..., description="Command identifier")
    user_id: int = Field(..., description="User ID")
    command_type: str = Field(..., description="Command type")
    response: str = Field(..., description="Command response")
    success: bool = Field(True, description="Command success status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    # Response data
    data: Dict[str, Any] = Field(default_factory=dict, description="Response data")


class CursorCLIIntegration:
    """Cursor CLI integration for Telegram Bot."""
    
    def __init__(self, bot_interface: TelegramBotInterface, cursor_cli_path: str):
        self.bot_interface = bot_interface
        self.cursor_cli_path = cursor_cli_path
        self.logger = logging.getLogger(__name__)
        
        # Integration state
        self.is_connected = False
        self.cursor_cli_process = None
        
        # Notification handlers
        self.signal_handlers: List[Callable] = []
        self.status_handlers: List[Callable] = []
        self.command_handlers: List[Callable] = []
        
        # Message templates
        self.message_templates = {
            'trading_signal': self._format_trading_signal_message,
            'system_status': self._format_system_status_message,
            'command_response': self._format_command_response_message
        }
        
        # Statistics
        self.stats = {
            'signals_sent': 0,
            'status_updates_sent': 0,
            'commands_processed': 0,
            'errors': 0
        }
    
    async def initialize(self) -> bool:
        """Initialize Cursor CLI integration."""
        try:
            self.logger.info("Initializing Cursor CLI integration...")
            
            # Connect to Cursor CLI
            if not await self._connect_to_cursor_cli():
                self.logger.error("Failed to connect to Cursor CLI")
                return False
            
            # Register notification handlers
            await self._register_notification_handlers()
            
            # Start monitoring
            asyncio.create_task(self._monitor_cursor_cli())
            
            self.is_connected = True
            self.logger.info("Cursor CLI integration initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Cursor CLI integration: {e}")
            return False
    
    async def _connect_to_cursor_cli(self) -> bool:
        """Connect to Cursor CLI project."""
        try:
            # In real implementation, this would establish connection to Cursor CLI
            # For now, we'll simulate the connection
            self.logger.info(f"Connecting to Cursor CLI at: {self.cursor_cli_path}")
            
            # Simulate connection success
            await asyncio.sleep(0.1)
            
            self.logger.info("Cursor CLI connection established")
            return True
            
        except Exception as e:
            self.logger.error(f"Error connecting to Cursor CLI: {e}")
            return False
    
    async def _register_notification_handlers(self) -> None:
        """Register notification handlers."""
        try:
            # Register signal notification handler
            self.signal_handlers.append(self._handle_trading_signal)
            
            # Register status notification handler
            self.status_handlers.append(self._handle_system_status)
            
            # Register command response handler
            self.command_handlers.append(self._handle_command_response)
            
            self.logger.info("Notification handlers registered")
            
        except Exception as e:
            self.logger.error(f"Error registering notification handlers: {e}")
    
    async def _monitor_cursor_cli(self) -> None:
        """Monitor Cursor CLI for updates."""
        while self.is_connected:
            try:
                # In real implementation, this would monitor Cursor CLI output
                # For now, we'll simulate periodic updates
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Simulate receiving updates from Cursor CLI
                await self._simulate_cursor_cli_updates()
                
            except Exception as e:
                self.logger.error(f"Error monitoring Cursor CLI: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _simulate_cursor_cli_updates(self) -> None:
        """Simulate updates from Cursor CLI (for demonstration)."""
        try:
            # Simulate trading signal
            if asyncio.get_event_loop().time() % 300 < 30:  # Every 5 minutes
                signal = TradingSignalNotification(
                    signal_id=f"signal_{int(datetime.now().timestamp())}",
                    symbol="0700.HK",
                    side="BUY",
                    strength=0.8,
                    confidence=0.85,
                    price=325.50,
                    reasoning="Strong momentum detected with high confidence",
                    agent_id="quantitative_analyst",
                    strategy_name="momentum_strategy",
                    risk_level="medium",
                    expected_return=0.05,
                    stop_loss=310.00,
                    take_profit=340.00
                )
                await self._handle_trading_signal(signal)
            
            # Simulate system status update
            if asyncio.get_event_loop().time() % 180 < 30:  # Every 3 minutes
                status = SystemStatusNotification(
                    status_id=f"status_{int(datetime.now().timestamp())}",
                    status_type="performance_update",
                    message="System performance is optimal",
                    severity="info",
                    cpu_usage=25.5,
                    memory_usage=45.2,
                    disk_usage=60.1,
                    network_latency=12.3,
                    agents_status={
                        "quantitative_analyst": "active",
                        "quantitative_trader": "active",
                        "portfolio_manager": "active",
                        "risk_analyst": "active",
                        "data_scientist": "active",
                        "quantitative_engineer": "active",
                        "research_analyst": "active"
                    },
                    active_strategies=5,
                    total_trades=150
                )
                await self._handle_system_status(status)
            
        except Exception as e:
            self.logger.error(f"Error simulating Cursor CLI updates: {e}")
    
    async def _handle_trading_signal(self, signal: TradingSignalNotification) -> None:
        """Handle trading signal notification."""
        try:
            # Format message
            message = await self._format_trading_signal_message(signal)
            
            # Send to relevant users
            await self._send_signal_notification(signal, message)
            
            # Update statistics
            self.stats['signals_sent'] += 1
            
            # Process handlers
            for handler in self.signal_handlers:
                try:
                    await handler(signal)
                except Exception as e:
                    self.logger.error(f"Error in signal handler: {e}")
            
        except Exception as e:
            self.logger.error(f"Error handling trading signal: {e}")
            self.stats['errors'] += 1
    
    async def _handle_system_status(self, status: SystemStatusNotification) -> None:
        """Handle system status notification."""
        try:
            # Format message
            message = await self._format_system_status_message(status)
            
            # Send to relevant users based on severity
            await self._send_status_notification(status, message)
            
            # Update statistics
            self.stats['status_updates_sent'] += 1
            
            # Process handlers
            for handler in self.status_handlers:
                try:
                    await handler(status)
                except Exception as e:
                    self.logger.error(f"Error in status handler: {e}")
            
        except Exception as e:
            self.logger.error(f"Error handling system status: {e}")
            self.stats['errors'] += 1
    
    async def _handle_command_response(self, response: UserCommandResponse) -> None:
        """Handle command response."""
        try:
            # Format message
            message = await self._format_command_response_message(response)
            
            # Send response to user
            await self.bot_interface.send_message(
                chat_id=response.user_id,
                text=message
            )
            
            # Update statistics
            self.stats['commands_processed'] += 1
            
            # Process handlers
            for handler in self.command_handlers:
                try:
                    await handler(response)
                except Exception as e:
                    self.logger.error(f"Error in command handler: {e}")
            
        except Exception as e:
            self.logger.error(f"Error handling command response: {e}")
            self.stats['errors'] += 1
    
    async def _format_trading_signal_message(self, signal: TradingSignalNotification) -> str:
        """Format trading signal message."""
        try:
            side_emoji = "🟢" if signal.side == "BUY" else "🔴" if signal.side == "SELL" else "🟡"
            strength_bar = "█" * int(signal.strength * 10) + "░" * (10 - int(signal.strength * 10))
            confidence_bar = "█" * int(signal.confidence * 10) + "░" * (10 - int(signal.confidence * 10))
            
            message = (
                f"📊 Trading Signal Alert\n\n"
                f"{side_emoji} {signal.symbol} {signal.side}\n"
                f"Price: HKD {signal.price:.2f}\n"
                f"Strength: {strength_bar} {signal.strength:.1f}\n"
                f"Confidence: {confidence_bar} {signal.confidence:.1%}\n"
                f"Strategy: {signal.strategy_name}\n"
                f"Agent: {signal.agent_id}\n"
                f"Risk: {signal.risk_level.upper()}\n\n"
                f"💡 {signal.reasoning}\n\n"
            )
            
            if signal.expected_return:
                message += f"Expected Return: {signal.expected_return:+.1%}\n"
            if signal.stop_loss:
                message += f"Stop Loss: HKD {signal.stop_loss:.2f}\n"
            if signal.take_profit:
                message += f"Take Profit: HKD {signal.take_profit:.2f}\n"
            
            message += f"\n⏰ {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error formatting trading signal message: {e}")
            return f"Trading Signal: {signal.symbol} {signal.side} at {signal.price}"
    
    async def _format_system_status_message(self, status: SystemStatusNotification) -> str:
        """Format system status message."""
        try:
            severity_emoji = {
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '❌',
                'critical': '🚨'
            }.get(status.severity.lower(), 'ℹ️')
            
            message = (
                f"{severity_emoji} System Status Update\n\n"
                f"Type: {status.status_type.replace('_', ' ').title()}\n"
                f"Message: {status.message}\n"
                f"Severity: {status.severity.upper()}\n\n"
            )
            
            if status.cpu_usage is not None:
                message += f"CPU: {status.cpu_usage:.1f}%\n"
            if status.memory_usage is not None:
                message += f"Memory: {status.memory_usage:.1f}%\n"
            if status.disk_usage is not None:
                message += f"Disk: {status.disk_usage:.1f}%\n"
            if status.network_latency is not None:
                message += f"Latency: {status.network_latency:.1f}ms\n"
            
            if status.agents_status:
                message += f"\nAgents: {len([s for s in status.agents_status.values() if s == 'active'])}/{len(status.agents_status)} active\n"
            
            if status.active_strategies > 0:
                message += f"Strategies: {status.active_strategies} active\n"
            
            if status.total_trades > 0:
                message += f"Trades: {status.total_trades} total\n"
            
            message += f"\n⏰ {status.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error formatting system status message: {e}")
            return f"System Status: {status.message}"
    
    async def _format_command_response_message(self, response: UserCommandResponse) -> str:
        """Format command response message."""
        try:
            status_emoji = "✅" if response.success else "❌"
            
            message = (
                f"{status_emoji} Command Response\n\n"
                f"Command: {response.command_type}\n"
                f"Status: {'Success' if response.success else 'Failed'}\n\n"
                f"{response.response}\n"
            )
            
            if not response.success and response.error_message:
                message += f"\nError: {response.error_message}"
            
            if response.data:
                message += f"\n\nData: {json.dumps(response.data, indent=2)}"
            
            message += f"\n\n⏰ {response.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error formatting command response message: {e}")
            return f"Command Response: {response.response}"
    
    async def _send_signal_notification(self, signal: TradingSignalNotification, message: str) -> None:
        """Send trading signal notification to relevant users."""
        try:
            # Send to traders and analysts
            await self.bot_interface.broadcast_message(
                message=message,
                role_filter=UserRole.TRADER
            )
            
            await self.bot_interface.broadcast_message(
                message=message,
                role_filter=UserRole.ANALYST
            )
            
        except Exception as e:
            self.logger.error(f"Error sending signal notification: {e}")
    
    async def _send_status_notification(self, status: SystemStatusNotification, message: str) -> None:
        """Send system status notification to relevant users."""
        try:
            # Send to all users based on severity
            if status.severity in ['critical', 'error']:
                # Send to all users for critical issues
                await self.bot_interface.broadcast_message(message)
            elif status.severity == 'warning':
                # Send to traders, analysts, and admins
                for role in [UserRole.TRADER, UserRole.ANALYST, UserRole.ADMIN]:
                    await self.bot_interface.broadcast_message(message, role_filter=role)
            else:
                # Send to admins only for info messages
                await self.bot_interface.broadcast_message(message, role_filter=UserRole.ADMIN)
            
        except Exception as e:
            self.logger.error(f"Error sending status notification: {e}")
    
    # Public methods
    async def send_trading_signal(self, signal: TradingSignalNotification) -> bool:
        """Send trading signal notification."""
        try:
            await self._handle_trading_signal(signal)
            return True
        except Exception as e:
            self.logger.error(f"Error sending trading signal: {e}")
            return False
    
    async def send_system_status(self, status: SystemStatusNotification) -> bool:
        """Send system status notification."""
        try:
            await self._handle_system_status(status)
            return True
        except Exception as e:
            self.logger.error(f"Error sending system status: {e}")
            return False
    
    async def send_command_response(self, response: UserCommandResponse) -> bool:
        """Send command response."""
        try:
            await self._handle_command_response(response)
            return True
        except Exception as e:
            self.logger.error(f"Error sending command response: {e}")
            return False
    
    def add_signal_handler(self, handler: Callable) -> None:
        """Add custom signal handler."""
        self.signal_handlers.append(handler)
    
    def add_status_handler(self, handler: Callable) -> None:
        """Add custom status handler."""
        self.status_handlers.append(handler)
    
    def add_command_handler(self, handler: Callable) -> None:
        """Add custom command handler."""
        self.command_handlers.append(handler)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get integration statistics."""
        return {
            'is_connected': self.is_connected,
            'cursor_cli_path': self.cursor_cli_path,
            'stats': self.stats.copy()
        }
    
    async def shutdown(self) -> None:
        """Shutdown the integration."""
        try:
            self.logger.info("Shutting down Cursor CLI integration...")
            self.is_connected = False
            
            # Stop monitoring
            if self.cursor_cli_process:
                self.cursor_cli_process.terminate()
                await self.cursor_cli_process.wait()
            
            self.logger.info("Cursor CLI integration shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during integration shutdown: {e}")
