import { RealtimeManager, getRealtimeManager } from '../realtimeManager';
import { WebSocketService, getWebSocketService } from '../websocketService';

// Mock WebSocket service
jest.mock('../websocketService');

// Mock fetch
global.fetch = jest.fn();

describe('RealtimeManager', () => {
  let realtimeManager: RealtimeManager;
  let mockWebSocketService: jest.Mocked<ReturnType<typeof WebSocketService>>;

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();

    // Create mock WebSocket service
    mockWebSocketService = {
      connect: jest.fn().mockResolvedValue(undefined),
      disconnect: jest.fn(),
      send: jest.fn(),
      on: jest.fn(),
      off: jest.fn(),
      subscribeToStrategy: jest.fn(),
      subscribeToPerformance: jest.fn(),
      subscribeToSignals: jest.fn(),
      unsubscribe: jest.fn(),
      requestCurrentState: jest.fn(),
      getConnectionStatus: jest.fn().mockReturnValue('connected')
    } as any;

    (WebSocketService as jest.Mock).mockImplementation(() => mockWebSocketService);
    (getWebSocketService as jest.Mock).mockReturnValue(mockWebSocketService);

    // Create new instance
    realtimeManager = new RealtimeManager({
      updateInterval: 1000, // Short interval for testing
      enableWebSocket: true,
      enablePeriodicRefresh: true
    });
  });

  afterEach(() => {
    realtimeManager.destroy();
  });

  describe('initialization', () => {
    it('should initialize with default configuration', () => {
      const manager = new RealtimeManager();
      expect(manager).toBeInstanceOf(RealtimeManager);
      manager.destroy();
    });

    it('should initialize with custom configuration', () => {
      const manager = new RealtimeManager({
        updateInterval: 5000,
        maxRetries: 5,
        enableWebSocket: false
      });

      expect(manager).toBeInstanceOf(RealtimeManager);
      manager.destroy();
    });

    it('should setup network monitoring', () => {
      expect(typeof window.addEventListener).toBe('function');
    });
  });

  describe('lifecycle management', () => {
    it('should start and stop updates', async () => {
      const callbacks = {
        onStrategyUpdate: jest.fn(),
        onPerformanceUpdate: jest.fn(),
        onError: jest.fn()
      };

      // Mock successful fetch responses
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          strategies: [],
          performance: []
        })
      });

      await realtimeManager.initialize(callbacks);
      realtimeManager.start();

      expect(mockWebSocketService.connect).toHaveBeenCalled();
      expect(mockWebSocketService.subscribeToStrategy).toHaveBeenCalled();
      expect(mockWebSocketService.subscribeToPerformance).toHaveBeenCalled();

      realtimeManager.stop();
      realtimeManager.destroy();
    });

    it('should pause and resume updates', async () => {
      const callbacks = { onStrategyUpdate: jest.fn() };

      await realtimeManager.initialize(callbacks);
      realtimeManager.start();

      realtimeManager.pause();
      expect(realtimeManager.getStats().isPaused).toBe(true);

      realtimeManager.resume();
      expect(realtimeManager.getStats().isPaused).toBe(false);

      realtimeManager.destroy();
    });
  });

  describe('manual refresh', () => {
    it('should trigger manual refresh', async () => {
      const callbacks = { onStrategyUpdate: jest.fn() };

      // Mock successful fetch responses
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          strategies: [{ id: 'test', name: 'Test Strategy' }],
          performance: []
        })
      });

      await realtimeManager.initialize(callbacks);

      await realtimeManager.triggerManualRefresh();

      expect(fetch).toHaveBeenCalledWith('/api/strategies');
      expect(fetch).toHaveBeenCalledWith('/api/performance');

      realtimeManager.destroy();
    });

    it('should handle fetch errors during refresh', async () => {
      const callbacks = {
        onStrategyUpdate: jest.fn(),
        onError: jest.fn()
      };

      // Mock fetch failure
      (fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      await realtimeManager.initialize(callbacks);

      await realtimeManager.triggerManualRefresh();

      expect(callbacks.onError).toHaveBeenCalledWith(
        expect.any(Error),
        'data_sync'
      );

      realtimeManager.destroy();
    });
  });

  describe('data change detection', () => {
    it('should detect data changes', () => {
      const strategies1 = [{ id: '1', name: 'Strategy 1' }];
      const strategies2 = [{ id: '1', name: 'Strategy 1', status: 'active' }];
      const performance = [];

      // Access private method through prototype for testing
      const calculateHash = (realtimeManager as any).calculateDataHash.bind(realtimeManager);

      const hash1 = calculateHash(strategies1, performance);
      const hash2 = calculateHash(strategies2, performance);

      expect(hash1.strategies).not.toBe(hash2.strategies);
    });

    it('should not trigger updates for unchanged data', async () => {
      const callbacks = { onStrategyUpdate: jest.fn() };

      // Mock same data response
      const mockData = {
        strategies: [{ id: '1', name: 'Strategy 1' }],
        performance: []
      };

      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockData)
      });

      await realtimeManager.initialize(callbacks);

      // First refresh should trigger update
      await realtimeManager.triggerManualRefresh();
      expect(callbacks.onStrategyUpdate).toHaveBeenCalledTimes(1);

      // Second refresh with same data should not trigger update
      await realtimeManager.triggerManualRefresh();
      expect(callbacks.onStrategyUpdate).toHaveBeenCalledTimes(1);

      realtimeManager.destroy();
    });
  });

  describe('WebSocket integration', () => {
    it('should handle WebSocket messages', async () => {
      const callbacks = {
        onStrategyUpdate: jest.fn(),
        onPerformanceUpdate: jest.fn()
      };

      await realtimeManager.initialize(callbacks);

      // Simulate WebSocket message
      const messageHandlers = (mockWebSocketService.on as jest.Mock).mock.calls;
      const messageHandler = messageHandlers.find(call => call[0] === 'message')?.[1];

      if (messageHandler) {
        // Test strategy update
        messageHandler({
          type: 'strategy_update',
          data: { id: '1', name: 'Updated Strategy' }
        });

        expect(callbacks.onStrategyUpdate).toHaveBeenCalledWith([
          { id: '1', name: 'Updated Strategy' }
        ]);

        // Test performance update
        messageHandler({
          type: 'performance_update',
          data: {
            strategy_id: '1',
            totalReturn: 0.15,
            sharpeRatio: 1.2
          }
        });

        expect(callbacks.onPerformanceUpdate).toHaveBeenCalledWith([
          {
            strategyId: '1',
            totalReturn: 0.15,
            sharpeRatio: 1.2
          }
        ]);
      }

      realtimeManager.destroy();
    });

    it('should handle WebSocket disconnection', async () => {
      const callbacks = {
        onError: jest.fn(),
        onStrategyUpdate: jest.fn()
      };

      await realtimeManager.initialize(callbacks);

      // Simulate WebSocket disconnect
      const disconnectHandlers = (mockWebSocketService.on as jest.Mock).mock.calls;
      const disconnectHandler = disconnectHandlers.find(call => call[0] === 'disconnect')?.[1];

      if (disconnectHandler) {
        disconnectHandler({ status: 'disconnected' });
      }

      // Should attempt reconnection
      expect(setTimeout).toHaveBeenCalled();

      realtimeManager.destroy();
    });
  });

  describe('network monitoring', () => {
    it('should handle network status changes', () => {
      // Mock navigator online/offline
      const originalOnline = navigator.onLine;
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false
      });

      // Trigger offline event
      window.dispatchEvent(new Event('offline'));

      // Restore online status
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: true
      });

      // Trigger online event
      window.dispatchEvent(new Event('online'));

      // Reset
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: originalOnline
      });
    });
  });

  describe('statistics', () => {
    it('should track update statistics', async () => {
      const callbacks = { onStrategyUpdate: jest.fn() };

      // Mock successful fetch responses
      (fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          strategies: [{ id: '1', name: 'Strategy 1' }],
          performance: []
        })
      });

      await realtimeManager.initialize(callbacks);

      // Check initial stats
      let stats = realtimeManager.getStats();
      expect(stats.updateCount).toBe(0);
      expect(stats.errorCount).toBe(0);

      // Trigger refresh
      await realtimeManager.triggerManualRefresh();

      // Check updated stats
      stats = realtimeManager.getStats();
      expect(stats.updateCount).toBe(1);
      expect(stats.lastSyncTime).toBeInstanceOf(Date);

      realtimeManager.destroy();
    });
  });

  describe('singleton pattern', () => {
    it('should return same instance', () => {
      const manager1 = getRealtimeManager();
      const manager2 = getRealtimeManager();

      expect(manager1).toBe(manager2);

      // Cleanup
      manager1.destroy();
    });
  });

  describe('cleanup', () => {
    it('should clean up resources on destroy', () => {
      realtimeManager.destroy();

      const stats = realtimeManager.getStats();
      expect(stats.isActive).toBe(false);
    });
  });
});