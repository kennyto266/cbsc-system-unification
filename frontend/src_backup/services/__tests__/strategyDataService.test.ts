/**
 * Strategy Data Service Tests
 * API服務測試文件
 *
 * Task #002: API接口集成和數據獲取
 */

import {
  StrategyPerformance,
  StrategyConfig,
  StrategyDetail,
  PerformanceSummary,
  StrategyDataService,
  DataCache,
  HttpClient
} from '../strategyDataService';
import { validateStrategyPerformance, validateStrategyConfig } from '../../utils/dataValidation';

// Mock fetch for testing
global.fetch = jest.fn();

// Mock WebSocket
jest.mock('../../services/websocketService', () => ({
  getWebSocketService: jest.fn(() => ({
    on: jest.fn(),
    off: jest.fn(),
    subscribeToPerformance: jest.fn(),
    requestCurrentState: jest.fn(),
    disconnect: jest.fn()
  }))
}));

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

describe('DataCache', () => {
  let cache: DataCache;

  beforeEach(() => {
    cache = new DataCache();
  });

  test('should store and retrieve data', () => {
    const testData = { id: 1, name: 'Test' };
    cache.set('test-key', testData);

    const retrieved = cache.get('test-key');
    expect(retrieved).toEqual(testData);
  });

  test('should return null for expired data', (done) => {
    const testData = { id: 1, name: 'Test' };
    cache.set('test-key', testData, 100); // 100ms TTL

    setTimeout(() => {
      const retrieved = cache.get('test-key');
      expect(retrieved).toBeNull();
      done();
    }, 150);
  });

  test('should clear all data', () => {
    cache.set('key1', 'value1');
    cache.set('key2', 'value2');

    cache.clear();

    expect(cache.get('key1')).toBeNull();
    expect(cache.get('key2')).toBeNull();
  });
});

describe('HttpClient', () => {
  let httpClient: HttpClient;

  beforeEach(() => {
    httpClient = new HttpClient('http://test-api.com', 2, 100, 5000);
    jest.clearAllMocks();
  });

  test('should make successful GET request', async () => {
    const mockResponse = { data: 'test' };
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    });

    const result = await httpClient.get('/test');

    expect(fetch).toHaveBeenCalledWith(
      'http://test-api.com/test',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          'Content-Type': 'application/json'
        })
      })
    );
    expect(result).toEqual(mockResponse);
  });

  test('should handle HTTP error response', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found'
    });

    await expect(httpClient.get('/not-found')).rejects.toThrow();
  });

  test('should retry failed requests', async () => {
    (fetch as jest.Mock)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'success' })
      });

    const result = await httpClient.get('/test');

    expect(fetch).toHaveBeenCalledTimes(3);
    expect(result).toEqual({ data: 'success' });
  });

  test('should add authorization header when token is present', async () => {
    localStorageMock.getItem.mockReturnValue('test-token');

    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ data: 'test' })
    });

    await httpClient.get('/test');

    expect(fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': 'Bearer test-token'
        })
      })
    );
  });
});

describe('Strategy Data Validation', () => {
  test('should validate valid strategy performance data', () => {
    const validData: StrategyPerformance = {
      name: 'TestStrategy',
      sharpe_ratio: 1.5,
      max_drawdown: -0.15,
      total_return: 0.25,
      win_rate: 0.65,
      status: 'enabled',
      last_updated: new Date().toISOString()
    };

    const result = validateStrategyPerformance(validData);

    expect(result.isValid).toBe(true);
    expect(result.errors).toHaveLength(0);
    expect(result.data).toEqual(validData);
  });

  test('should reject invalid strategy performance data', () => {
    const invalidData = {
      name: '',
      sharpe_ratio: 'invalid',
      max_drawdown: 0.5, // Should be negative
      total_return: null,
      win_rate: 1.5, // Should be <= 1
      status: 'invalid'
    };

    const result = validateStrategyPerformance(invalidData);

    expect(result.isValid).toBe(false);
    expect(result.errors.length).toBeGreaterThan(0);
  });

  test('should validate valid strategy config data', () => {
    const validData: StrategyConfig = {
      name: 'TestStrategy',
      enabled: true,
      description: 'Test strategy description',
      parameters: { rsi_period: 14 },
      strategy_type: 'RSI',
      risk_level: 'medium',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    const result = validateStrategyConfig(validData);

    expect(result.isValid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  test('should reject missing required fields', () => {
    const invalidData = {
      name: 'TestStrategy',
      enabled: true
      // Missing description, strategy_type, etc.
    };

    const result = validateStrategyConfig(invalidData);

    expect(result.isValid).toBe(false);
    expect(result.errors.some(e => e.includes('缺少必需字段'))).toBe(true);
  });
});

describe('StrategyDataService Integration', () => {
  let service: StrategyDataService;

  beforeEach(() => {
    service = new StrategyDataService();
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  test('should fetch strategy performance data', async () => {
    const mockPerformanceData: StrategyPerformance[] = [
      {
        name: 'Strategy1',
        sharpe_ratio: 1.5,
        max_drawdown: -0.15,
        total_return: 0.25,
        win_rate: 0.65,
        status: 'enabled',
        last_updated: new Date().toISOString()
      }
    ];

    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockPerformanceData
    });

    const result = await service.getStrategyPerformance();

    expect(result).toEqual(mockPerformanceData);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/strategies/performance'),
      expect.any(Object)
    );
  });

  test('should cache fetched data', async () => {
    const mockData = [{ name: 'Test' }];
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    });

    // First call
    await service.getStrategyPerformance();

    // Second call should use cache
    const result = await service.getStrategyPerformance();

    expect(result).toEqual(mockData);
    expect(fetch).toHaveBeenCalledTimes(1); // Should only be called once
  });

  test('should toggle strategy status', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true })
    });

    await service.toggleStrategy('TestStrategy', true);

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/strategies/TestStrategy/toggle'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ enabled: true })
      })
    );
  });

  test('should handle API errors gracefully', async () => {
    (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    await expect(service.getStrategyPerformance()).rejects.toThrow();

    // Service should still be functional
    expect(service.healthCheck()).resolves.toBe(false);
  });

  test('should setup auto-refresh correctly', async () => {
    jest.useFakeTimers();

    const mockData = [{ name: 'Test' }];
    (fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => mockData
    });

    service.setupAutoRefresh('test', jest.fn(), 1000);

    // Fast-forward time
    jest.advanceTimersByTime(1000);

    expect(fetch).toHaveBeenCalled();

    jest.useRealTimers();
  });

  test('should cleanup resources on destroy', () => {
    const clearIntervalSpy = jest.spyOn(global, 'clearInterval');

    service.destroy();

    expect(clearIntervalSpy).toHaveBeenCalled();
    expect(service.getCacheStats().size).toBe(0);

    clearIntervalSpy.mockRestore();
  });
});

describe('Performance Summary Tests', () => {
  test('should validate performance summary structure', () => {
    const validSummary: PerformanceSummary = {
      total_strategies: 10,
      active_strategies: 7,
      total_return: 0.15,
      daily_pnl: 1500,
      sharpe_ratio: 1.2,
      max_drawdown: -0.1,
      win_rate: 0.6,
      best_strategy: {
        name: 'BestStrategy',
        sharpe_ratio: 2.5,
        max_drawdown: -0.05,
        total_return: 0.3,
        win_rate: 0.7,
        status: 'enabled',
        last_updated: new Date().toISOString()
      },
      worst_strategy: {
        name: 'WorstStrategy',
        sharpe_ratio: 0.5,
        max_drawdown: -0.2,
        total_return: 0.05,
        win_rate: 0.45,
        status: 'enabled',
        last_updated: new Date().toISOString()
      }
    };

    const { validatePerformanceSummary } = require('../../utils/dataValidation');
    const result = validatePerformanceSummary(validSummary);

    expect(result.isValid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  test('should detect logical inconsistencies', () => {
    const invalidSummary = {
      total_strategies: 5,
      active_strategies: 10, // More active than total
      total_return: -0.5,
      sharpe_ratio: -2,
      max_drawdown: 0.3, // Should be negative
      win_rate: 1.5 // Should be <= 1
    };

    const { validatePerformanceSummary } = require('../../utils/dataValidation');
    const result = validatePerformanceSummary(invalidSummary);

    expect(result.isValid).toBe(false);
    expect(result.errors.length).toBeGreaterThan(0);
    expect(result.warnings.length).toBeGreaterThan(0);
  });
});

describe('Error Handling', () => {
  let service: StrategyDataService;

  beforeEach(() => {
    service = new StrategyDataService();
    jest.clearAllMocks();
  });

  test('should handle timeout errors', async () => {
    // Mock timeout
    (fetch as jest.Mock).mockImplementationOnce(() =>
      new Promise((_, reject) => {
        setTimeout(() => reject(new DOMException('AbortError', 'AbortError')), 100);
      })
    );

    await expect(service.getStrategyPerformance()).rejects.toThrow('Request timeout');
  });

  test('should handle parse errors', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => {
        throw new Error('Invalid JSON');
      }
    });

    await expect(service.getStrategyPerformance()).rejects.toThrow();
  });

  test('should provide meaningful error messages', async () => {
    const testCases = [
      { status: 400, expectedError: '請求參數錯誤' },
      { status: 401, expectedError: '未授權' },
      { status: 403, expectedError: '禁止訪問' },
      { status: 404, expectedError: '不存在' },
      { status: 500, expectedError: '服務器內部錯誤' }
    ];

    for (const testCase of testCases) {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: testCase.status,
        statusText: 'Error'
      });

      try {
        await service.getStrategyPerformance();
      } catch (error) {
        expect((error as Error).message).toContain(testCase.expectedError);
      }
    }
  });
});