"""
Simple client example for CBSC Trading API Python SDK

This is a minimal example showing how to use the SDK.
"""

from cbsc_trading_api import CBSCClient


def main():
    # Create a client instance
    # For development, you can use without authentication
    client = CBSCClient(base_url="https://api.cbsc.com")

    print("CBSC Trading API Python SDK")
    print("=" * 40)

    # Print available resources
    print("\nAvailable API resources:")
    print("- auth: Authentication and token management")
    print("- users: User management")
    print("- strategies: Strategy operations")
    print("- portfolio: Portfolio and positions")
    print("- market_data: Market data and quotes")
    print("- backtests: Backtesting operations")
    print("- webhooks: Webhook management")

    # Example: Try to get public market data (no auth required)
    try:
        print("\nFetching market symbols...")
        symbols = client.market_data.get_symbols()
        print(f"Found {len(symbols.data)} symbols")

        if symbols.data:
            print("\nFirst 5 symbols:")
            for symbol in symbols.data[:5]:
                print(f"  {symbol.symbol} - {symbol.name}")

    except Exception as e:
        print(f"Error fetching market data: {e}")

    print("\nSDK initialized successfully!")
    print("To use authenticated endpoints, provide client credentials:")
    print("  client = CBSCClient(client_id='your_id', client_secret='your_secret')")


if __name__ == "__main__":
    main()