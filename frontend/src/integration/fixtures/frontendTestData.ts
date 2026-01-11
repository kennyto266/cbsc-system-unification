/**
 * Test data fixtures for frontend integration tests
 */

import { Strategy, User, Portfolio, Trade } from '@/types';

export class FrontendTestDataGenerator {
  private static readonly HK_STOCKS = [
    '00700.HK', '00005.HK', '00003.HK', '00388.HK', '00291.HK',
    '00002.HK', '00027.HK', '01810.HK', '09988.HK', '03690.HK',
    '00941.HK', '01299.HK', '02020.HK', '01024.HK', '00011.HK'
  ];

  private static readonly US_STOCKS = [
    'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM',
    'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'BAC', 'XOM'
  ];

  // Generate test user
  static generateUser(overrides: Partial<User> = {}): User {
    return {
      id: 'user-test-123',
      username: 'testuser',
      email: 'test@example.com',
      role: 'user',
      is_active: true,
      is_superuser: false,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      last_login: '2024-01-01T00:00:00Z',
      preferences: {
        theme: 'light',
        language: 'en',
        timezone: 'UTC',
        notifications: {
          email: true,
          push: false,
          trade_alerts: true,
          daily_summary: false
        }
      },
      ...overrides
    };
  }

  // Generate test strategy
  static generateStrategy(overrides: Partial<Strategy> = {}): Strategy {
    const symbols = [...this.HK_STOCKS, ...this.US_STOCKS];
    const selectedSymbols = this.getRandomElements(symbols, 3);
    
    return {
      id: `strategy-test-${Date.now()}`,
      name: 'Test Momentum Strategy',
      description: 'A test strategy using momentum indicators',
      user_id: 'user-test-123',
      status: 'inactive',
      parameters: {
        symbols: selectedSymbols,
        timeframe: '1d',
        risk_level: 0.02,
        position_size: 0.1,
        stop_loss: 0.05,
        take_profit: 0.1,
        indicators: {
          rsi_period: 14,
          rsi_oversold: 30,
          rsi_overbought: 70,
          ma_short: 20,
          ma_long: 50
        }
      },
      performance_metrics: {
        total_return: 0.15,
        sharpe_ratio: 1.5,
        max_drawdown: -0.08,
        win_rate: 0.55,
        profit_factor: 1.8,
        calmar_ratio: 1.2,
        sortino_ratio: 2.1
      },
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      last_run: '2024-01-01T00:00:00Z',
      ...overrides
    };
  }

  // Generate test portfolio
  static generatePortfolio(overrides: Partial<Portfolio> = {}): Portfolio {
    const symbols = this.getRandomElements([...this.HK_STOCKS, ...this.US_STOCKS], 8);
    
    return {
      id: 'portfolio-test-123',
      name: 'Test Portfolio',
      user_id: 'user-test-123',
      total_value: 1000000,
      cash_balance: 50000,
      positions: symbols.map((symbol, index) => ({
        symbol,
        quantity: Math.floor(Math.random() * 1000) + 100,
        avg_cost: this.getRandomPrice(symbol),
        current_price: this.getRandomPrice(symbol),
        market_value: 0,
        unrealized_pnl: 0,
        unrealized_pnl_pct: 0
      })).map(pos => ({
        ...pos,
        market_value: pos.quantity * pos.current_price,
        unrealized_pnl: pos.quantity * (pos.current_price - pos.avg_cost),
        unrealized_pnl_pct: ((pos.current_price - pos.avg_cost) / pos.avg_cost) * 100
      })),
      transactions: [],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      ...overrides
    };
  }

  // Generate test trades
  static generateTrades(count: number = 10, overrides: Partial<Trade> = {}): Trade[] {
    const symbols = [...this.HK_STOCKS, ...this.US_STOCKS];
    const trades: Trade[] = [];
    
    for (let i = 0; i < count; i++) {
      const symbol = this.getRandomElements(symbols, 1)[0];
      const type = Math.random() > 0.5 ? 'buy' : 'sell';
      
      trades.push({
        id: `trade-test-${i + 1}`,
        user_id: 'user-test-123',
        strategy_id: 'strategy-test-123',
        portfolio_id: 'portfolio-test-123',
        symbol,
        type,
        quantity: Math.floor(Math.random() * 500) + 100,
        price: this.getRandomPrice(symbol),
        timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
        status: 'executed',
        fees: Math.random() * 10,
        commission: Math.random() * 5,
        notes: `Test trade ${i + 1}`,
        ...overrides
      });
    }
    
    return trades.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }

  // Generate market data
  static generateMarketData(
    symbol: string,
    days: number = 30,
    frequency: string = '1d'
  ) {
    const data = [];
    const basePrice = this.getRandomPrice(symbol);
    const now = Date.now();
    const interval = frequency === '1d' ? 24 * 60 * 60 * 1000 : 
                    frequency === '1h' ? 60 * 60 * 1000 : 60 * 1000;
    
    for (let i = days; i >= 0; i--) {
      const timestamp = new Date(now - i * interval);
      const open = basePrice * (1 + (Math.random() - 0.5) * 0.02);
      const close = open * (1 + (Math.random() - 0.5) * 0.02);
      const high = Math.max(open, close) * (1 + Math.random() * 0.01);
      const low = Math.min(open, close) * (1 - Math.random() * 0.01);
      const volume = Math.floor(Math.random() * 1000000) + 100000;
      
      data.push({
        timestamp: timestamp.toISOString(),
        symbol,
        open: parseFloat(open.toFixed(2)),
        high: parseFloat(high.toFixed(2)),
        low: parseFloat(low.toFixed(2)),
        close: parseFloat(close.toFixed(2)),
        volume,
        vwap: parseFloat(((high + low + close) / 3).toFixed(2)),
        num_trades: Math.floor(Math.random() * 1000) + 100
      });
    }
    
    return data;
  }

  // Helper methods
  private static getRandomElements<T>(array: T[], count: number): T[] {
    const shuffled = [...array].sort(() => Math.random() - 0.5);
    return shuffled.slice(0, count);
  }

  private static getRandomPrice(symbol?: string): number {
    const basePrice = symbol?.endsWith('.HK') ? 200 : 150;
    return parseFloat((basePrice * (1 + (Math.random() - 0.5) * 0.5)).toFixed(2));
  }
}

// Export for easy access in tests
export const testUtils = {
  user: FrontendTestDataGenerator.generateUser,
  strategy: FrontendTestDataGenerator.generateStrategy,
  portfolio: FrontendTestDataGenerator.generatePortfolio,
  trades: FrontendTestDataGenerator.generateTrades,
  marketData: FrontendTestDataGenerator.generateMarketData
};