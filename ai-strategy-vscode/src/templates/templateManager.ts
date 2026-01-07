/**
 * TemplateManager - Manages strategy notebook templates
 *
 * Provides built-in templates for common trading strategies
 */

import { NotebookTemplate } from './notebookTemplate';

export interface TemplateInfo {
  name: string;
  description: string;
}

export class TemplateManager {
  private templates: Map<string, NotebookTemplate>;

  constructor() {
    this.templates = new Map();
    this.initTemplates();
  }

  /**
   * Initialize built-in templates
   */
  private initTemplates(): void {
    this.createBreakoutTemplate();
    this.createMeanReversionTemplate();
  }

  /**
   * Create Breakout Strategy Template
   * Classic breakout strategy with moving average confirmation
   */
  private createBreakoutTemplate(): void {
    const breakout = new NotebookTemplate(
      'breakout',
      'Classic breakout strategy with moving average confirmation'
    );

    // Title cell
    breakout.addCell('markdown', '# Breakout Strategy\n\nTrend-following strategy using moving average crossovers and price breakouts.');

    // Configuration cell
    breakout.addCell('code', `import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration
SYMBOL = "AAPL"
START_DATE = "2023-01-01"
END_DATE = "2024-01-01"
SHORT_MA = 20
LONG_MA = 50
BREAKOUT_THRESHOLD = 0.02  # 2% breakout
INITIAL_CAPITAL = 100000`);

    // Data fetching cell
    breakout.addCell('code', `# Fetch data (placeholder - replace with actual data source)
def fetch_data(symbol: str, start: str, end: str):
    # TODO: Integrate with CBSC data service
    dates = pd.date_range(start=start, end=end, freq='D')
    np.random.seed(42)
    prices = np.random.randn(len(dates)).cumsum() + 100

    return pd.DataFrame({
        'date': dates,
        'open': prices,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, len(dates))
    }).set_index('date')

data = fetch_data(SYMBOL, START_DATE, END_DATE)
print(f"Loaded {len(data)} days of data for {SYMBOL}")`);

    // Signal generation cell
    breakout.addCell('code', `# Calculate indicators
data['ma_short'] = data['close'].rolling(window=SHORT_MA).mean()
data['ma_long'] = data['close'].rolling(window=LONG_MA).mean()

# Generate signals
data['signal'] = 0
data.loc[
    (data['ma_short'] > data['ma_long']) &
    (data['close'] > data['ma_short'] * (1 + BREAKOUT_THRESHOLD)),
    'signal'
] = 1

data.loc[
    (data['ma_short'] < data['ma_long']),
    'signal'
] = -1

print(f"Generated {data['signal'].abs().sum()} trading signals")`);

    // Backtesting cell
    breakout.addCell('code', `# Backtest
position = 0
cash = INITIAL_CAPITAL
portfolio_values = []

for i, row in data.iterrows():
    if row['signal'] == 1 and position == 0:
        # Buy
        position = cash / row['close']
        cash = 0
    elif row['signal'] == -1 and position > 0:
        # Sell
        cash = position * row['close']
        position = 0

    portfolio_values.append(cash + position * row['close'])

data['portfolio_value'] = portfolio_values
data['returns'] = data['portfolio_value'].pct_change()`);

    // Performance metrics cell
    breakout.addCell('code', `# Calculate performance metrics
total_return = (data['portfolio_value'].iloc[-1] / INITIAL_CAPITAL - 1) * 100
sharpe_ratio = data['returns'].mean() / data['returns'].std() * np.sqrt(252) if data['returns'].std() > 0 else 0
max_drawdown = (data['portfolio_value'].cummax() - data['portfolio_value']).max() / INITIAL_CAPITAL * 100

print(f"Total Return: {total_return:.2f}%")
print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
print(f"Max Drawdown: {max_drawdown:.2f}%")`);

    // Visualization cell
    breakout.addCell('code', `# Visualize results
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# Price and moving averages
ax1.plot(data.index, data['close'], label='Close', alpha=0.7)
ax1.plot(data.index, data['ma_short'], label=f'{SHORT_MA}-day MA', alpha=0.7)
ax1.plot(data.index, data['ma_long'], label=f'{LONG_MA}-day MA', alpha=0.7)
ax1.set_title(f'{SYMBOL} Breakout Strategy')
ax1.set_ylabel('Price')
ax1.legend()

# Portfolio value
ax2.plot(data.index, data['portfolio_value'], label='Portfolio', color='green')
ax2.set_title('Portfolio Performance')
ax2.set_ylabel('Portfolio Value ($)')
ax2.legend()

plt.tight_layout()
plt.show()`);

    this.templates.set('breakout', breakout);
  }

  /**
   * Create Mean Reversion Strategy Template
   * Mean reversion strategy using Bollinger Bands
   */
  private createMeanReversionTemplate(): void {
    const meanReversion = new NotebookTemplate(
      'mean_reversion',
      'Mean reversion strategy using Bollinger Bands'
    );

    // Title cell
    meanReversion.addCell('markdown', '# Mean Reversion Strategy\n\nCounter-trend strategy using Bollinger Bands to identify overbought/oversold conditions.');

    // Configuration cell
    meanReversion.addCell('code', `import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration
SYMBOL = "AAPL"
START_DATE = "2023-01-01"
END_DATE = "2024-01-01"
LOOKBACK = 20
STD_DEV = 2
ENTRY_THRESHOLD = 2.0  # Enter when price is 2 std dev from mean
INITIAL_CAPITAL = 100000`);

    // Data fetching cell
    meanReversion.addCell('code', `# Fetch data (placeholder)
def fetch_data(symbol: str, start: str, end: str):
    dates = pd.date_range(start=start, end=end, freq='D')
    np.random.seed(42)
    prices = np.random.randn(len(dates)).cumsum() + 100

    return pd.DataFrame({
        'date': dates,
        'close': prices
    }).set_index('date')

data = fetch_data(SYMBOL, START_DATE, END_DATE)
print(f"Loaded {len(data)} days of data")`);

    // Bollinger Bands calculation cell
    meanReversion.addCell('code', `# Calculate Bollinger Bands
data['mean'] = data['close'].rolling(window=LOOKBACK).mean()
data['std'] = data['close'].rolling(window=LOOKBACK).std()
data['upper_band'] = data['mean'] + STD_DEV * data['std']
data['lower_band'] = data['mean'] - STD_DEV * data['std']

# Generate signals
data['z_score'] = (data['close'] - data['mean']) / data['std']
data['signal'] = 0

# Buy when price is below lower band (oversold)
data.loc[data['z_score'] < -ENTRY_THRESHOLD, 'signal'] = 1

# Sell when price is above upper band (overbought)
data.loc[data['z_score'] > ENTRY_THRESHOLD, 'signal'] = -1

print(f"Generated {data['signal'].abs().sum()} trading signals")`);

    // Backtesting cell
    meanReversion.addCell('code', `# Backtest
position = 0
cash = INITIAL_CAPITAL
portfolio_values = []

for i, row in data.iterrows():
    if row['signal'] == 1 and position == 0:
        # Buy (oversold)
        position = cash / row['close']
        cash = 0
    elif row['signal'] == -1 and position > 0:
        # Sell (overbought)
        cash = position * row['close']
        position = 0

    portfolio_values.append(cash + position * row['close'])

data['portfolio_value'] = portfolio_values
data['returns'] = data['portfolio_value'].pct_change()`);

    // Performance metrics cell
    meanReversion.addCell('code', `# Calculate performance metrics
total_return = (data['portfolio_value'].iloc[-1] / INITIAL_CAPITAL - 1) * 100
sharpe_ratio = data['returns'].mean() / data['returns'].std() * np.sqrt(252) if data['returns'].std() > 0 else 0
win_rate = (data['returns'] > 0).sum() / (data['returns'] != 0).sum() * 100

print(f"Total Return: {total_return:.2f}%")
print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
print(f"Win Rate: {win_rate:.2f}%")`);

    // Visualization cell
    meanReversion.addCell('code', `# Visualize results
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# Price and Bollinger Bands
ax1.plot(data.index, data['close'], label='Close', alpha=0.7)
ax1.plot(data.index, data['upper_band'], label='Upper Band', linestyle='--', alpha=0.5)
ax1.plot(data.index, data['lower_band'], label='Lower Band', linestyle='--', alpha=0.5)
ax1.fill_between(data.index, data['lower_band'], data['upper_band'], alpha=0.1)
ax1.set_title(f'{SYMBOL} Mean Reversion Strategy')
ax1.set_ylabel('Price')
ax1.legend()

# Portfolio value
ax2.plot(data.index, data['portfolio_value'], label='Portfolio', color='green')
ax2.set_title('Portfolio Performance')
ax2.set_ylabel('Portfolio Value ($)')
ax2.legend()

plt.tight_layout()
plt.show()`);

    this.templates.set('mean_reversion', meanReversion);
  }

  /**
   * Get a template by name
   * @param name - Template name
   * @returns Template or undefined if not found
   */
  public getTemplate(name: string): NotebookTemplate | undefined {
    return this.templates.get(name);
  }

  /**
   * List all available templates
   * @returns Array of template info
   */
  public listTemplates(): TemplateInfo[] {
    return Array.from(this.templates.values()).map(template => ({
      name: template.name,
      description: template.description
    }));
  }

  /**
   * Check if a template exists
   * @param name - Template name
   * @returns True if template exists
   */
  public hasTemplate(name: string): boolean {
    return this.templates.has(name);
  }
}
