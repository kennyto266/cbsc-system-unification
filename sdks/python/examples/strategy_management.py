"""
Strategy management example for CBSC Trading API Python SDK
"""

from datetime import datetime, timedelta
from cbsc_trading_api import CBSCClient
from cbsc_trading_api.models import StrategyCreate, StrategyType

def main():
    """Strategy management example"""

    client = CBSCClient(
        base_url="http://localhost:3005",
        client_id="test_client_id",
        client_secret="test_client_secret"
    )

    try:
        print("=== Strategy Management Example ===\n")

        # 1. Create a new strategy
        print("1. Creating new strategy...")
        strategy_data = StrategyCreate(
            name="RSI Mean Reversion Strategy",
            type=StrategyType.RSI,
            description="A strategy that uses RSI indicator for mean reversion",
            config={
                "rsi_period": 14,
                "oversold_threshold": 30,
                "overbought_threshold": 70,
                "position_size": 0.1
            },
            risk_level=6
        )

        try:
            new_strategy = client.strategies.create_strategy(strategy_data)
            print(f"   Created strategy: {new_strategy.name} (ID: {new_strategy.id})")
            strategy_id = new_strategy.id
        except Exception as e:
            print(f"   Error creating strategy: {e}")
            # Use existing strategy for demo
            strategies = client.strategies.get_strategies(limit=1)
            if strategies.data:
                strategy_id = strategies.data[0].id
                print(f"   Using existing strategy ID: {strategy_id}")
            else:
                print("   No strategies available")
                return

        print()

        # 2. Get strategy details
        print("2. Getting strategy details...")
        strategy = client.strategies.get_strategy(strategy_id)
        print(f"   Strategy name: {strategy.name}")
        print(f"   Strategy type: {strategy.type}")
        print(f"   Risk level: {strategy.risk_level}")
        print(f"   Active: {strategy.is_active}")
        if strategy.performance:
            print(f"   Performance: {strategy.performance}")
        print()

        # 3. Update strategy
        print("3. Updating strategy...")
        update_data = {
            "description": "Updated strategy description",
            "config": {
                "rsi_period": 21,  # Updated RSI period
                "oversold_threshold": 25,
                "overbought_threshold": 75,
                "position_size": 0.15
            }
        }

        try:
            updated_strategy = client.strategies.update_strategy(strategy_id, update_data)
            print(f"   Updated strategy description: {updated_strategy.description}")
            print(f"   Updated RSI period: {updated_strategy.config['rsi_period']}")
        except Exception as e:
            print(f"   Error updating strategy: {e}")
        print()

        # 4. Run backtest
        print("4. Running strategy backtest...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        try:
            backtest = client.strategies.backtest_strategy(
                strategy_id=strategy_id,
                symbol="0700.HK",
                start_date=start_date,
                end_date=end_date,
                initial_capital=100000.0
            )
            print(f"   Backtest ID: {backtest.id}")
            print(f"   Symbol: {backtest.symbol}")
            print(f"   Initial capital: ${backtest.initial_capital:,.2f}")
            print(f"   Final capital: ${backtest.final_capital:,.2f}")
            print(f"   Total return: {backtest.total_return:.2%}")
            print(f"   Sharpe ratio: {backtest.sharpe_ratio}")
            print(f"   Max drawdown: {backtest.max_drawdown:.2%}")
            print(f"   Win rate: {backtest.win_rate:.2%}")
        except Exception as e:
            print(f"   Error running backtest: {e}")
        print()

        # 5. Get strategy performance
        print("5. Getting strategy performance...")
        try:
            performance = client.strategies.get_strategy_performance(strategy_id)
            print(f"   Performance metrics: {performance}")
        except Exception as e:
            print(f"   Error getting performance: {e}")
        print()

        print("=== Strategy Management Example Completed ===")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()