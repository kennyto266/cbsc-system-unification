"""Cursor CLI Bridge for integrating CURSOR CLI project with AI Agent system.

This module provides a bridge between the CURSOR CLI Telegram Bot and the
main AI Agent trading system, enabling seamless integration of trading signals,
system monitoring, and user interactions.
"""

import asyncio
import logging
import os
import subprocess
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from pydantic import BaseModel, Field

from .bot_interface import TelegramBotInterface, TelegramUser, UserRole, MessageType
from .cursor_cli_integration import (
    TradingSignalNotification,
    SystemStatusNotification,
    UserCommandResponse
)


class CursorCLIConfig(BaseModel):
    """Configuration for Cursor CLI integration."""
    cursor_cli_path: str = Field(..., description="Path to CURSOR CLI project")
    bot_token: str = Field(..., description="Telegram Bot token")
    cursor_api_key: str = Field(..., description="Cursor API key")
    
    # User access control
    allowed_user_ids: Optional[List[int]] = Field(None, description="Allowed user IDs")
    allowed_chat_ids: Optional[List[int]] = Field(None, description="Allowed chat IDs")
    
    # Command settings
    command_timeout: int = Field(60, description="Command execution timeout in seconds")
    max_message_length: int = Field(6000, description="Maximum message length")
    
    # Integration settings
    enable_trading_signals: bool = Field(True, description="Enable trading signal integration")
    enable_system_monitoring: bool = Field(True, description="Enable system monitoring")
    enable_cursor_commands: bool = Field(True, description="Enable Cursor CLI commands")
    
    class Config:
        env_prefix = "CURSOR_"


class CursorCLIBridge:
    """Bridge between CURSOR CLI and AI Agent system."""
    
    def __init__(self, config: CursorCLIConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Integration state
        self.is_running = False
        self.cursor_process = None
        self.bot_interface = None
        
        # Command handlers
        self.trading_handlers: List[Callable] = []
        self.monitoring_handlers: List[Callable] = []
        self.command_handlers: List[Callable] = []
        
        # Statistics
        self.stats = {
            'commands_executed': 0,
            'signals_sent': 0,
            'status_updates_sent': 0,
            'errors': 0,
            'start_time': None
        }
    
    async def initialize(self) -> bool:
        """Initialize the Cursor CLI bridge."""
        try:
            self.logger.info("Initializing Cursor CLI bridge...")
            
            # Initialize bot interface
            self.bot_interface = TelegramBotInterface(
                bot_token=self.config.bot_token,
                webhook_url=None
            )
            
            if not await self.bot_interface.initialize():
                self.logger.error("Failed to initialize bot interface")
                return False
            
            # Register custom command handlers
            await self._register_custom_handlers()
            
            # Start Cursor CLI process
            if not await self._start_cursor_cli():
                self.logger.error("Failed to start Cursor CLI")
                return False
            
            # Start monitoring tasks
            asyncio.create_task(self._monitor_trading_signals())
            asyncio.create_task(self._monitor_system_status())
            asyncio.create_task(self._process_cursor_commands())
            
            self.is_running = True
            self.stats['start_time'] = datetime.now()
            self.logger.info("Cursor CLI bridge initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Cursor CLI bridge: {e}")
            return False
    
    async def _register_custom_handlers(self) -> None:
        """Register custom command handlers for trading system integration."""
        try:
            # Register trading-related commands
            self.bot_interface.add_command_handler(
                "trading_signals",
                self._handle_trading_signals_command
            )
            
            self.bot_interface.add_command_handler(
                "portfolio_status",
                self._handle_portfolio_status_command
            )
            
            self.bot_interface.add_command_handler(
                "agent_status",
                self._handle_agent_status_command
            )
            
            self.bot_interface.add_command_handler(
                "system_metrics",
                self._handle_system_metrics_command
            )
            
            self.bot_interface.add_command_handler(
                "risk_alerts",
                self._handle_risk_alerts_command
            )
            
            # Register Cursor CLI specific commands
            if self.config.enable_cursor_commands:
                self.bot_interface.add_command_handler(
                    "cursor_help",
                    self._handle_cursor_help_command
                )
                
                self.bot_interface.add_command_handler(
                    "cursor_query",
                    self._handle_cursor_query_command
                )
            
            self.logger.info("Custom command handlers registered")
            
        except Exception as e:
            self.logger.error(f"Error registering custom handlers: {e}")
    
    async def _start_cursor_cli(self) -> bool:
        """Start the Cursor CLI process."""
        try:
            cursor_path = Path(self.config.cursor_cli_path)
            if not cursor_path.exists():
                self.logger.error(f"Cursor CLI path does not exist: {cursor_path}")
                return False
            
            # Set up environment variables
            env = os.environ.copy()
            env['TELEGRAM_BOT_TOKEN'] = self.config.bot_token
            env['CURSOR_API_KEY'] = self.config.cursor_api_key
            
            if self.config.allowed_user_ids:
                env['TG_ALLOWED_USER_IDS'] = ','.join(map(str, self.config.allowed_user_ids))
            
            if self.config.allowed_chat_ids:
                env['TG_ALLOWED_CHAT_IDS'] = ','.join(map(str, self.config.allowed_chat_ids))
            
            # Start Cursor CLI process
            self.cursor_process = await asyncio.create_subprocess_exec(
                'python', 'main.py',
                cwd=cursor_path,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            self.logger.info("Cursor CLI process started")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting Cursor CLI: {e}")
            return False
    
    async def _monitor_trading_signals(self) -> None:
        """Monitor and process trading signals."""
        while self.is_running:
            try:
                # In real implementation, this would monitor the trading system
                # For now, we'll simulate signal generation
                await asyncio.sleep(30)  # Check every 30 seconds
                
                if self.config.enable_trading_signals:
                    await self._generate_sample_trading_signal()
                
            except Exception as e:
                self.logger.error(f"Error monitoring trading signals: {e}")
                await asyncio.sleep(5)
    
    async def _monitor_system_status(self) -> None:
        """Monitor and process system status updates."""
        while self.is_running:
            try:
                # In real implementation, this would monitor the system
                # For now, we'll simulate status updates
                await asyncio.sleep(60)  # Check every minute
                
                if self.config.enable_system_monitoring:
                    await self._generate_sample_system_status()
                
            except Exception as e:
                self.logger.error(f"Error monitoring system status: {e}")
                await asyncio.sleep(5)
    
    async def _process_cursor_commands(self) -> None:
        """Process Cursor CLI commands."""
        while self.is_running:
            try:
                # Monitor Cursor CLI process
                if self.cursor_process and self.cursor_process.returncode is not None:
                    self.logger.warning("Cursor CLI process terminated, restarting...")
                    await self._start_cursor_cli()
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Error processing Cursor commands: {e}")
                await asyncio.sleep(5)
    
    async def _generate_sample_trading_signal(self) -> None:
        """Generate sample trading signal for demonstration."""
        try:
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
            
            # Send signal to relevant users
            await self._send_trading_signal(signal)
            
            # Process handlers
            for handler in self.trading_handlers:
                try:
                    await handler(signal)
                except Exception as e:
                    self.logger.error(f"Error in trading signal handler: {e}")
            
            self.stats['signals_sent'] += 1
            
        except Exception as e:
            self.logger.error(f"Error generating trading signal: {e}")
            self.stats['errors'] += 1
    
    async def _generate_sample_system_status(self) -> None:
        """Generate sample system status for demonstration."""
        try:
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
            
            # Send status to relevant users
            await self._send_system_status(status)
            
            # Process handlers
            for handler in self.monitoring_handlers:
                try:
                    await handler(status)
                except Exception as e:
                    self.logger.error(f"Error in system status handler: {e}")
            
            self.stats['status_updates_sent'] += 1
            
        except Exception as e:
            self.logger.error(f"Error generating system status: {e}")
            self.stats['errors'] += 1
    
    async def _send_trading_signal(self, signal: TradingSignalNotification) -> None:
        """Send trading signal to users."""
        try:
            # Format signal message
            message = await self._format_trading_signal_message(signal)
            
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
            self.logger.error(f"Error sending trading signal: {e}")
    
    async def _send_system_status(self, status: SystemStatusNotification) -> None:
        """Send system status to users."""
        try:
            # Format status message
            message = await self._format_system_status_message(status)
            
            # Send based on severity
            if status.severity in ['critical', 'error']:
                await self.bot_interface.broadcast_message(message)
            elif status.severity == 'warning':
                for role in [UserRole.TRADER, UserRole.ANALYST, UserRole.ADMIN]:
                    await self.bot_interface.broadcast_message(message, role_filter=role)
            else:
                await self.bot_interface.broadcast_message(message, role_filter=UserRole.ADMIN)
            
        except Exception as e:
            self.logger.error(f"Error sending system status: {e}")
    
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
                active_agents = len([s for s in status.agents_status.values() if s == 'active'])
                total_agents = len(status.agents_status)
                message += f"\nAgents: {active_agents}/{total_agents} active\n"
            
            if status.active_strategies > 0:
                message += f"Strategies: {status.active_strategies} active\n"
            
            if status.total_trades > 0:
                message += f"Trades: {status.total_trades} total\n"
            
            message += f"\n⏰ {status.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error formatting system status message: {e}")
            return f"System Status: {status.message}"
    
    # Command handlers
    async def _handle_trading_signals_command(self, command) -> str:
        """Handle /trading_signals command."""
        try:
            # Query latest signal & metrics from dashboard API
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://127.0.0.1:8000/api/dashboard/signals/latest") as resp:
                    if resp.status != 200:
                        return "❌ 无法获取最新信号。"
                    data = await resp.json()

            decision = data.get("decision") or {}
            metrics = data.get("metrics") or {}

            side = decision.get("decision", "-")
            confidence = decision.get("confidence", 0.0)
            ts = decision.get("timestamp", "-")
            sharpe = metrics.get("sharpe_ratio")
            max_dd = metrics.get("max_drawdown")

            side_emoji = "🟢" if str(side).upper() == 'BUY' else "🔴" if str(side).upper() == 'SELL' else "🟡"
            sharpe_text = f"{sharpe:.3f}" if isinstance(sharpe, (int, float)) and sharpe is not None else "-"
            maxdd_text = f"{max_dd:.2%}" if isinstance(max_dd, (int, float)) and max_dd is not None else "-"

            text = (
                "📊 最新交易信号\n\n"
                f"{side_emoji} 决策: {side}  置信度: {confidence:.2f}\n"
                f"Sharpe: {sharpe_text}   MaxDD: {maxdd_text}\n"
                f"时间: {ts}\n"
            )
            return text
            
        except Exception as e:
            self.logger.error(f"Error handling trading signals command: {e}")
            return "❌ Error retrieving trading signals."
    
    async def _handle_portfolio_status_command(self, command) -> str:
        """Handle /portfolio_status command."""
        try:
            # Get portfolio status (simulated)
            portfolio = {
                'total_value': 1000000.00,
                'cash': 200000.00,
                'invested': 800000.00,
                'daily_pnl': 5000.00,
                'total_pnl': 50000.00,
                'positions': 5
            }
            
            portfolio_text = (
                f"💼 Portfolio Status\n\n"
                f"Total Value: HKD {portfolio['total_value']:,.2f}\n"
                f"Cash: HKD {portfolio['cash']:,.2f}\n"
                f"Invested: HKD {portfolio['invested']:,.2f}\n"
                f"Daily P&L: HKD {portfolio['daily_pnl']:+,.2f}\n"
                f"Total P&L: HKD {portfolio['total_pnl']:+,.2f}\n"
                f"Positions: {portfolio['positions']}\n\n"
                f"📈 Portfolio performing well"
            )
            
            return portfolio_text
            
        except Exception as e:
            self.logger.error(f"Error handling portfolio status command: {e}")
            return "❌ Error retrieving portfolio status."
    
    async def _handle_agent_status_command(self, command) -> str:
        """Handle /agent_status command."""
        try:
            # Get agent status (simulated)
            agents = {
                'quantitative_analyst': {'status': 'active', 'performance': 0.85, 'last_update': '2024-01-15 12:00:00'},
                'quantitative_trader': {'status': 'active', 'performance': 0.92, 'last_update': '2024-01-15 12:00:00'},
                'portfolio_manager': {'status': 'active', 'performance': 0.88, 'last_update': '2024-01-15 12:00:00'},
                'risk_analyst': {'status': 'active', 'performance': 0.90, 'last_update': '2024-01-15 12:00:00'},
                'data_scientist': {'status': 'active', 'performance': 0.87, 'last_update': '2024-01-15 12:00:00'},
                'quantitative_engineer': {'status': 'active', 'performance': 0.95, 'last_update': '2024-01-15 12:00:00'},
                'research_analyst': {'status': 'active', 'performance': 0.89, 'last_update': '2024-01-15 12:00:00'}
            }
            
            agents_text = "🤖 Agent Status\n\n"
            
            for agent_id, info in agents.items():
                status_emoji = "🟢" if info['status'] == 'active' else "🔴"
                performance_bar = "█" * int(info['performance'] * 10) + "░" * (10 - int(info['performance'] * 10))
                
                agents_text += (
                    f"{status_emoji} {agent_id.replace('_', ' ').title()}\n"
                    f"   Performance: {performance_bar} {info['performance']:.1%}\n"
                    f"   Last Update: {info['last_update']}\n\n"
                )
            
            return agents_text
            
        except Exception as e:
            self.logger.error(f"Error handling agent status command: {e}")
            return "❌ Error retrieving agent status."
    
    async def _handle_system_metrics_command(self, command) -> str:
        """Handle /system_metrics command."""
        try:
            # Get system metrics (simulated)
            metrics = {
                'cpu_usage': 25.5,
                'memory_usage': 45.2,
                'disk_usage': 60.1,
                'network_latency': 12.3,
                'uptime': '2 days, 5 hours',
                'active_connections': 15
            }
            
            metrics_text = (
                f"📊 System Metrics\n\n"
                f"CPU Usage: {metrics['cpu_usage']:.1f}%\n"
                f"Memory Usage: {metrics['memory_usage']:.1f}%\n"
                f"Disk Usage: {metrics['disk_usage']:.1f}%\n"
                f"Network Latency: {metrics['network_latency']:.1f}ms\n"
                f"Uptime: {metrics['uptime']}\n"
                f"Active Connections: {metrics['active_connections']}\n\n"
                f"✅ System running smoothly"
            )
            
            return metrics_text
            
        except Exception as e:
            self.logger.error(f"Error handling system metrics command: {e}")
            return "❌ Error retrieving system metrics."
    
    async def _handle_risk_alerts_command(self, command) -> str:
        """Handle /risk_alerts command."""
        try:
            # Get risk alerts (simulated)
            alerts = [
                {'level': 'WARNING', 'message': 'High volatility detected in 0700.HK', 'time': '2024-01-15 12:30:00'},
                {'level': 'INFO', 'message': 'Portfolio rebalancing completed', 'time': '2024-01-15 11:00:00'},
                {'level': 'CRITICAL', 'message': 'System memory usage above 90%', 'time': '2024-01-15 10:45:00'}
            ]
            
            alerts_text = "🚨 Risk Alerts\n\n"
            
            for alert in alerts:
                level_emoji = {
                    'INFO': 'ℹ️',
                    'WARNING': '⚠️',
                    'CRITICAL': '🚨'
                }.get(alert['level'], 'ℹ️')
                
                alerts_text += (
                    f"{level_emoji} {alert['level']}\n"
                    f"   {alert['message']}\n"
                    f"   Time: {alert['time']}\n\n"
                )
            
            return alerts_text
            
        except Exception as e:
            self.logger.error(f"Error handling risk alerts command: {e}")
            return "❌ Error retrieving risk alerts."
    
    async def _handle_cursor_help_command(self, command) -> str:
        """Handle /cursor_help command."""
        try:
            help_text = (
                "🤖 Cursor CLI Integration Help\n\n"
                "Available Commands:\n"
                "/trading_signals - Recent trading signals\n"
                "/portfolio_status - Portfolio status\n"
                "/agent_status - Agent status\n"
                "/system_metrics - System metrics\n"
                "/risk_alerts - Risk alerts\n"
                "/cursor_query <query> - Query Cursor AI\n"
                "/cursor_help - This help message\n\n"
                "Integration Features:\n"
                "• Real-time trading signal notifications\n"
                "• System status monitoring\n"
                "• Agent performance tracking\n"
                "• Risk alert notifications\n"
                "• Cursor AI integration\n\n"
                "Use /help for general bot commands."
            )
            
            return help_text
            
        except Exception as e:
            self.logger.error(f"Error handling cursor help command: {e}")
            return "❌ Error retrieving help information."
    
    async def _handle_cursor_query_command(self, command) -> str:
        """Handle /cursor_query command."""
        try:
            if not command.parameters:
                return "❌ Please provide a query. Usage: /cursor_query <your question>"
            
            query = " ".join(command.parameters)
            
            # Execute Cursor CLI command
            result = await self._execute_cursor_command(query)
            
            if result['success']:
                return f"🤖 Cursor AI Response:\n\n{result['output']}"
            else:
                return f"❌ Error: {result['error']}"
            
        except Exception as e:
            self.logger.error(f"Error handling cursor query command: {e}")
            return "❌ Error processing query."
    
    async def _execute_cursor_command(self, query: str) -> Dict[str, Any]:
        """Execute Cursor CLI command."""
        try:
            # Prepare command
            cmd = [
                'bash', '-lc',
                f'cursor-agent --print --output-format text -m "gpt-5" -a "$CURSOR_API_KEY"'
            ]
            
            # Set environment
            env = os.environ.copy()
            env['CURSOR_API_KEY'] = self.config.cursor_api_key
            
            # Execute command
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=query.encode('utf-8')),
                    timeout=self.config.command_timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                return {'success': False, 'error': 'Command timeout'}
            
            if proc.returncode != 0:
                error = stderr.decode('utf-8', 'ignore').strip() or 'Unknown error'
                return {'success': False, 'error': error}
            
            output = stdout.decode('utf-8', 'ignore').strip()
            if not output:
                output = "No response generated"
            
            # Truncate if too long
            if len(output) > self.config.max_message_length:
                output = output[:self.config.max_message_length] + "\n... (truncated)"
            
            self.stats['commands_executed'] += 1
            
            return {'success': True, 'output': output}
            
        except Exception as e:
            self.logger.error(f"Error executing Cursor command: {e}")
            return {'success': False, 'error': str(e)}
    
    # Public methods
    def add_trading_handler(self, handler: Callable) -> None:
        """Add trading signal handler."""
        self.trading_handlers.append(handler)
    
    def add_monitoring_handler(self, handler: Callable) -> None:
        """Add system monitoring handler."""
        self.monitoring_handlers.append(handler)
    
    def add_command_handler(self, handler: Callable) -> None:
        """Add command handler."""
        self.command_handlers.append(handler)
    
    async def send_trading_signal(self, signal: TradingSignalNotification) -> bool:
        """Send trading signal to users."""
        try:
            await self._send_trading_signal(signal)
            return True
        except Exception as e:
            self.logger.error(f"Error sending trading signal: {e}")
            return False
    
    async def send_system_status(self, status: SystemStatusNotification) -> bool:
        """Send system status to users."""
        try:
            await self._send_system_status(status)
            return True
        except Exception as e:
            self.logger.error(f"Error sending system status: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get bridge statistics."""
        uptime = None
        if self.stats['start_time']:
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            'is_running': self.is_running,
            'cursor_cli_path': self.config.cursor_cli_path,
            'uptime_seconds': uptime,
            'stats': self.stats.copy()
        }
    
    async def shutdown(self) -> None:
        """Shutdown the bridge."""
        try:
            self.logger.info("Shutting down Cursor CLI bridge...")
            self.is_running = False
            
            # Stop Cursor CLI process
            if self.cursor_process:
                self.cursor_process.terminate()
                await self.cursor_process.wait()
            
            # Shutdown bot interface
            if self.bot_interface:
                await self.bot_interface.shutdown()
            
            self.logger.info("Cursor CLI bridge shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during bridge shutdown: {e}")
