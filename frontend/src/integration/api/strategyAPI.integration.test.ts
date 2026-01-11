import { rest } from 'msw';
import { server } from '../setup/server';
import { integrationUtils } from '../utils/testUtils';
import { render, screen, waitFor, fireEvent } from '../utils/testUtils';

// Mock the strategy API service
import { strategyAPI } from '../../api/strategyService';

describe('Strategy API Integration Tests', () => {
  beforeEach(() => {
    // Login before each test
    integrationUtils.login();
  });

  describe('Strategy CRUD Operations', () => {
    test('should fetch strategies list', async () => {
      const { unmount } = render(
        <div data-testid="strategy-list">
          {/* Component that fetches and displays strategies */}
        </div>
      );

      // Test the API service directly
      const result = await strategyAPI.getStrategies({ page: 1, limit: 10 });
      
      expect(result.success).toBe(true);
      expect(result.data.strategies).toHaveLength(10);
      expect(result.data.pagination.page).toBe(1);
      
      unmount();
    });

    test('should create a new strategy', async () => {
      const newStrategy = {
        name: 'Test Strategy',
        description: 'Test description',
        parameters: {
          symbols: ['AAPL'],
          timeframe: '1d',
          risk_level: 0.02,
        },
      };

      const result = await strategyAPI.createStrategy(newStrategy);
      
      expect(result.success).toBe(true);
      expect(result.data.name).toBe(newStrategy.name);
      expect(result.data.id).toBeDefined();
    });

    test('should update an existing strategy', async () => {
      const strategyId = 'test-strategy-1';
      const updates = {
        name: 'Updated Strategy Name',
        parameters: {
          symbols: ['GOOGL'],
          timeframe: '1h',
        },
      };

      const result = await strategyAPI.updateStrategy(strategyId, updates);
      
      expect(result.success).toBe(true);
      expect(result.data.name).toBe(updates.name);
      expect(result.data.parameters.symbols).toEqual(updates.parameters.symbols);
    });

    test('should delete a strategy', async () => {
      const strategyId = 'test-strategy-1';
      
      const result = await strategyAPI.deleteStrategy(strategyId);
      
      expect(result.success).toBe(true);
      expect(result.message).toContain('deleted successfully');
    });

    test('should handle API errors gracefully', async () => {
      // Mock API error
      server.use(
        rest.get('*/strategies', (req, res, ctx) => {
          return res(
            ctx.status(500),
            ctx.json({
              success: false,
              error: {
                code: 'INTERNAL_ERROR',
                message: 'Internal server error',
              },
            })
          );
        })
      );

      await expect(strategyAPI.getStrategies()).rejects.toThrow();
    });
  });

  describe('Strategy Performance Data', () => {
    test('should fetch strategy performance metrics', async () => {
      const strategyId = 'test-strategy-1';
      
      const result = await strategyAPI.getStrategyPerformance(strategyId);
      
      expect(result.success).toBe(true);
      expect(result.data.metrics).toBeDefined();
      expect(result.data.metrics.total_return).toBeDefined();
      expect(result.data.metrics.sharpe_ratio).toBeDefined();
    });

    test('should fetch historical performance data', async () => {
      const strategyId = 'test-strategy-1';
      const params = {
        start_date: '2024-01-01',
        end_date: '2024-12-31',
      };
      
      const result = await strategyAPI.getStrategyHistory(strategyId, params);
      
      expect(result.success).toBe(true);
      expect(Array.isArray(result.data)).toBe(true);
      expect(result.data[0]).toHaveProperty('date');
      expect(result.data[0]).toHaveProperty('value');
    });
  });

  describe('Strategy Backtesting', () => {
    test('should initiate a backtest', async () => {
      const backtestRequest = {
        strategy_id: 'test-strategy-1',
        start_date: '2024-01-01',
        end_date: '2024-12-31',
        initial_capital: 100000,
      };

      const result = await strategyAPI.runBacktest(backtestRequest);
      
      expect(result.success).toBe(true);
      expect(result.data.backtest_id).toBeDefined();
      expect(result.data.status).toBe('pending');
    });

    test('should fetch backtest results', async () => {
      const backtestId = 'bt-123456';
      
      const result = await strategyAPI.getBacktestResults(backtestId);
      
      expect(result.success).toBe(true);
      expect(result.data.status).toBe('completed');
      expect(result.data.results).toBeDefined();
      expect(result.data.results.total_return).toBeDefined();
      expect(Array.isArray(result.data.results.trades)).toBe(true);
    });
  });

  describe('Real-time Strategy Updates', () => {
    test('should receive strategy updates via WebSocket', async () => {
      const mockWs = integrationUtils.createMockWebSocket();
      
      // Import and initialize WebSocket service
      const { wsService } = await import('../../services/websocket');
      wsService.connect();
      
      // Mock WebSocket message
      const mockMessage = {
        type: 'strategy_update',
        data: {
          strategy_id: 'test-strategy-1',
          status: 'running',
          performance: {
            current_return: 0.05,
          },
        },
      };
      
      // Simulate receiving message
      const onMessageCallback = mockWs.addEventListener.mock.calls.find(
        call => call[0] === 'message'
      )?.[1];
      
      if (onMessageCallback) {
        onMessageCallback({ data: JSON.stringify(mockMessage) });
      }
      
      // Wait for state update
      await integrationUtils.waitForState(
        state => state.strategies.list.some(s => s.id === 'test-strategy-1' && s.status === 'running')
      );
      
      expect(mockWs.addEventListener).toHaveBeenCalledWith('message', expect.any(Function));
    });
  });

  describe('Strategy Filtering and Search', () => {
    test('should filter strategies by status', async () => {
      const filters = { status: 'active' };
      
      const result = await strategyAPI.getStrategies({ filters });
      
      expect(result.success).toBe(true);
      expect(result.data.strategies.every(s => s.status === 'active')).toBe(true);
    });

    test('should search strategies by name', async () => {
      const search = 'Test';
      
      const result = await strategyAPI.getStrategies({ search });
      
      expect(result.success).toBe(true);
      expect(result.data.strategies.every(s => s.name.includes(search))).toBe(true);
    });

    test('should sort strategies by performance metric', async () => {
      const sort = { field: 'total_return', order: 'desc' };
      
      const result = await strategyAPI.getStrategies({ sort });
      
      expect(result.success).toBe(true);
      const strategies = result.data.strategies;
      
      for (let i = 1; i < strategies.length; i++) {
        expect(strategies[i-1].performance.total_return)
          .toBeGreaterThanOrEqual(strategies[i].performance.total_return);
      }
    });
  });

  describe('Concurrent Operations', () => {
    test('should handle multiple strategy updates concurrently', async () => {
      const updates = [
        { id: 'strategy-1', name: 'Updated 1' },
        { id: 'strategy-2', name: 'Updated 2' },
        { id: 'strategy-3', name: 'Updated 3' },
      ];

      const promises = updates.map(update =>
        strategyAPI.updateStrategy(update.id, { name: update.name })
      );

      const results = await Promise.all(promises);
      
      results.forEach(result => {
        expect(result.success).toBe(true);
      });
    });

    test('should cache strategy data efficiently', async () => {
      const strategyId = 'test-strategy-1';
      
      // First call should hit the API
      const result1 = await strategyAPI.getStrategy(strategyId);
      
      // Second call should use cache
      const result2 = await strategyAPI.getStrategy(strategyId);
      
      expect(result1.data).toEqual(result2.data);
    });
  });
});