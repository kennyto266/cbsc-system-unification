"""Demo script for Telegram integration with Cursor CLI.

This script demonstrates how to use the Telegram integration system
with the Cursor CLI project for Hong Kong quantitative trading.
"""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path

# Add src to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.telegram.integration_manager import IntegrationManager
from src.telegram.cursor_cli_integration import (
    TradingSignalNotification,
    SystemStatusNotification
)


async def main():
    """Main demo function."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Telegram integration demo...")
    
    # Configuration
    config = {
        'cursor_cli_path': r'C:\Users\Penguin8n\Desktop\CURSOR CLI',
        'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', 'your_bot_token_here'),
        'cursor_api_key': os.getenv('CURSOR_API_KEY', 'your_cursor_api_key_here'),
        'allowed_user_ids': [123456789],  # Replace with actual user IDs
        'allowed_chat_ids': [123456789],  # Replace with actual chat IDs
        'command_timeout': 60,
        'max_message_length': 6000,
        'enable_trading_signals': True,
        'enable_system_monitoring': True,
        'enable_cursor_commands': True
    }
    
    # Initialize integration manager
    integration_manager = IntegrationManager(config)
    
    try:
        # Initialize the integration
        if not await integration_manager.initialize():
            logger.error("Failed to initialize integration manager")
            return
        
        logger.info("Integration manager initialized successfully")
        
        # Demo 1: Send a trading signal
        logger.info("Demo 1: Sending trading signal...")
        signal = TradingSignalNotification(
            signal_id=f"demo_signal_{int(datetime.now().timestamp())}",
            symbol="0700.HK",
            side="BUY",
            strength=0.8,
            confidence=0.85,
            price=325.50,
            reasoning="Demo trading signal with strong momentum",
            agent_id="quantitative_analyst",
            strategy_name="momentum_strategy",
            risk_level="medium",
            expected_return=0.05,
            stop_loss=310.00,
            take_profit=340.00
        )
        
        success = await integration_manager.send_trading_signal(signal)
        logger.info(f"Trading signal sent: {success}")
        
        # Demo 2: Send system status
        logger.info("Demo 2: Sending system status...")
        status = SystemStatusNotification(
            status_id=f"demo_status_{int(datetime.now().timestamp())}",
            status_type="demo_update",
            message="Demo system status update",
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
        
        success = await integration_manager.send_system_status(status)
        logger.info(f"System status sent: {success}")
        
        # Demo 3: Send broadcast message
        logger.info("Demo 3: Sending broadcast message...")
        message = "🤖 Demo broadcast message from Hong Kong Quantitative Trading System"
        sent_count = await integration_manager.broadcast_message(message)
        logger.info(f"Broadcast message sent to {sent_count} users")
        
        # Demo 4: Get statistics
        logger.info("Demo 4: Getting statistics...")
        stats = integration_manager.get_statistics()
        logger.info(f"Integration statistics: {stats}")
        
        # Demo 5: Health check
        logger.info("Demo 5: Performing health check...")
        health = await integration_manager.health_check()
        logger.info(f"Health check result: {health}")
        
        # Demo 6: Simulate running for a while
        logger.info("Demo 6: Running integration for 30 seconds...")
        await asyncio.sleep(30)
        
        # Final statistics
        logger.info("Final statistics:")
        final_stats = integration_manager.get_statistics()
        logger.info(f"Final stats: {final_stats}")
        
    except Exception as e:
        logger.error(f"Demo error: {e}")
    
    finally:
        # Shutdown
        logger.info("Shutting down integration manager...")
        await integration_manager.shutdown()
        logger.info("Demo completed")


async def demo_cursor_commands():
    """Demo Cursor CLI commands."""
    logger = logging.getLogger(__name__)
    logger.info("Starting Cursor CLI commands demo...")
    
    # This would require actual bot token and API key
    # For demo purposes, we'll just show the structure
    
    config = {
        'cursor_cli_path': r'C:\Users\Penguin8n\Desktop\CURSOR CLI',
        'bot_token': 'your_bot_token_here',
        'cursor_api_key': 'your_cursor_api_key_here',
        'enable_cursor_commands': True
    }
    
    integration_manager = IntegrationManager(config)
    
    try:
        if await integration_manager.initialize():
            logger.info("Integration manager initialized for Cursor commands demo")
            
            # In a real scenario, users would send commands like:
            # /cursor_query "What is the current market trend for Hong Kong stocks?"
            # /trading_signals
            # /portfolio_status
            # /agent_status
            # /system_metrics
            # /risk_alerts
            
            logger.info("Cursor CLI commands demo completed")
        else:
            logger.error("Failed to initialize integration manager for Cursor commands demo")
    
    except Exception as e:
        logger.error(f"Cursor commands demo error: {e}")
    
    finally:
        await integration_manager.shutdown()


if __name__ == "__main__":
    print("Hong Kong Quantitative Trading - Telegram Integration Demo")
    print("=" * 60)
    print()
    print("This demo shows how to integrate the Cursor CLI project")
    print("with the AI Agent trading system via Telegram Bot.")
    print()
    print("Features demonstrated:")
    print("• Trading signal notifications")
    print("• System status monitoring")
    print("• User command processing")
    print("• Cursor AI integration")
    print("• Health monitoring")
    print()
    print("Note: This demo requires valid Telegram Bot token and Cursor API key")
    print("Set TELEGRAM_BOT_TOKEN and CURSOR_API_KEY environment variables")
    print()
    
    # Run main demo
    asyncio.run(main())
    
    print()
    print("Demo completed!")
    print("Check the logs above for detailed information.")
