"""
Basic usage example for CBSC Trading API Python SDK
"""

import os
from datetime import datetime, timedelta
from cbsc_trading_api import CBSCClient
from cbsc_trading_api.exceptions import CBSCAPIError, AuthenticationError

def main():
    """Basic SDK usage example"""

    # Initialize client (you can get these from environment variables or config)
    client = CBSCClient(
        base_url="http://localhost:3005",  # Use local backend for testing
        client_id="test_client_id",
        client_secret="test_client_secret"
    )

    try:
        print("=== CBSC Trading API SDK Example ===\n")

        # 1. Get access token
        print("1. Getting access token...")
        token = client.auth.get_token()
        print(f"   Access token: {token.access_token[:20]}...")
        print(f"   Expires in: {token.expires_in} seconds\n")

        # 2. Get users list
        print("2. Getting users list...")
        users_response = client.users.get_users(limit=5)
        print(f"   Total users: {users_response.total}")
        if users_response.data:
            print(f"   First user: {users_response.data[0].username}")
        print()

        # 3. Get strategies
        print("3. Getting strategies...")
        strategies_response = client.strategies.get_strategies(limit=5)
        print(f"   Total strategies: {strategies_response.total}")
        if strategies_response.data:
            print(f"   First strategy: {strategies_response.data[0].name}")
        print()

        # 4. Get market data
        print("4. Getting market symbols...")
        symbols_response = client.market_data.get_symbols(limit=5)
        print(f"   Total symbols: {symbols_response.total}")
        if symbols_response.data:
            print(f"   First symbol: {symbols_response.data[0].symbol} - {symbols_response.data[0].name}")
        print()

        # 5. Get portfolio
        print("5. Getting portfolio...")
        try:
            portfolio = client.portfolio.get_portfolio()
            print(f"   Total value: ${portfolio.total_value:,.2f}")
            print(f"   Cash balance: ${portfolio.cash_balance:,.2f}")
            print(f"   Positions: {len(portfolio.positions)}")
        except Exception as e:
            print(f"   Portfolio error: {e}")
        print()

        # 6. Get webhooks
        print("6. Getting webhooks...")
        try:
            webhooks_response = client.webhooks.get_webhooks()
            print(f"   Total webhooks: {webhooks_response.total}")
        except Exception as e:
            print(f"   Webhooks error: {e}")
        print()

        print("=== Example completed successfully! ===")

    except AuthenticationError as e:
        print(f"Authentication failed: {e}")
    except CBSCAPIError as e:
        print(f"API error: {e.message}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()