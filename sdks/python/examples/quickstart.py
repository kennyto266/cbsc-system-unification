"""
Quickstart example for CBSC Trading API Python SDK

This example demonstrates basic usage of the SDK including:
- Authentication
- Getting user information
- Managing strategies
- Fetching market data
"""

import os
from cbsc_trading_api import CBSCClient
from cbsc_trading_api.exceptions import AuthenticationError, CBSCAPIError


def main():
    # Initialize client with credentials from environment variables
    client = CBSCClient(
        base_url="https://api.cbsc.com",
        client_id=os.getenv("CBSC_CLIENT_ID"),
        client_secret=os.getenv("CBSC_CLIENT_SECRET"),
    )

    try:
        # Alternative: Use existing token
        # client = CBSCClient(
        #     base_url="https://api.cbsc.com",
        #     access_token="your_access_token_here"
        # )

        print("✅ CBSC Trading API Client initialized successfully!")

        # Example 1: Get authentication token
        print("\n=== Authentication ===")
        token = client.auth.get_token()
        print(f"Access Token: {token.access_token[:20]}...")
        print(f"Expires in: {token.expires_in} seconds")

        # Example 2: Get current user information
        print("\n=== User Information ===")
        users = client.users.get_users()
        if users.data:
            user = users.data[0]
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Active: {user.is_active}")

        # Example 3: List strategies
        print("\n=== Strategies ===")
        strategies = client.strategies.get_strategies()
        print(f"Found {len(strategies.data)} strategies:")
        for strategy in strategies.data[:3]:  # Show first 3
            print(f"  - {strategy.name} ({strategy.type})")

        # Example 4: Create a new strategy
        print("\n=== Create Strategy ===")
        from cbsc_trading_api.models import StrategyCreate, StrategyType

        new_strategy = StrategyCreate(
            name="Example RSI Strategy",
            type=StrategyType.RSI,
            description="A simple RSI-based trading strategy",
            config={
                "rsi_period": 14,
                "oversold": 30,
                "overbought": 70,
            }
        )

        created_strategy = client.strategies.create_strategy(new_strategy.dict())
        print(f"Created strategy: {created_strategy.name} (ID: {created_strategy.id})")

        # Example 5: Get market data
        print("\n=== Market Data ===")
        symbols = client.market_data.get_symbols()
        print(f"Available symbols: {len(symbols.data)}")

        if symbols.data:
            # Get details for first symbol
            symbol = symbols.data[0]
            print(f"\nSymbol: {symbol.symbol}")
            print(f"Name: {symbol.name}")
            print(f"Exchange: {symbol.exchange}")

            # Get quote for the symbol
            quote = client.market_data.get_symbol_quote(symbol.symbol)
            print(f"Current Price: ${quote.price}")
            print(f"Bid: ${quote.bid}")
            print(f"Ask: ${quote.ask}")

        # Example 6: Portfolio information
        print("\n=== Portfolio ===")
        portfolio = client.portfolio.get_portfolio()
        print(f"Total Value: ${portfolio.total_value:,.2f}")
        print(f"Cash Balance: ${portfolio.cash_balance:,.2f}")
        print(f"Daily P&L: ${portfolio.daily_pnl:,.2f}")
        print(f"Positions: {len(portfolio.positions)}")

        # Example 7: Create a backtest
        print("\n=== Backtest ===")
        from datetime import datetime, timedelta

        backtest_data = {
            "symbol": "0700.HK",
            "strategy": {
                "type": "RSI",
                "config": {
                    "rsi_period": 14,
                    "oversold": 30,
                    "overbought": 70,
                }
            },
            "start_date": (datetime.now() - timedelta(days=365)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "initial_capital": 10000.0,
        }

        backtest = client.backtests.create_backtest(backtest_data)
        print(f"Backtest created: ID {backtest.id}")
        print(f"Status: {backtest.status}")

        # Example 8: Webhook management
        print("\n=== Webhooks ===")
        webhooks = client.webhooks.get_webhooks()
        print(f"Active webhooks: {len(webhooks.data)}")

        print("\n✅ All examples completed successfully!")

    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("Please check your client credentials.")
    except CBSCAPIError as e:
        print(f"❌ API Error: {e}")
        if e.status_code:
            print(f"Status Code: {e.status_code}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        client.close()


if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("CBSC_CLIENT_ID") or not os.getenv("CBSC_CLIENT_SECRET"):
        print("⚠️  Warning: CBSC_CLIENT_ID and CBSC_CLIENT_SECRET environment variables not set.")
        print("   The SDK will attempt to authenticate, but may fail without proper credentials.")
        print("\n   To set them:")
        print("   export CBSC_CLIENT_ID='your_client_id'")
        print("   export CBSC_CLIENT_SECRET='your_client_secret'")
        print()

    main()