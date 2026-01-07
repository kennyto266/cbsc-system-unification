import { Strategy, PerformanceMetrics, WebSocketMessage } from '../types/index';
import { getWebSocketService } from './websocketService';

// Real-time data update configuration
interface RealtimeConfig {
  updateInterval: number; // 10 seconds by default
  maxRetries: number;
  retryDelay: number;
  enableWebSocket: boolean;
  enablePeriodicRefresh: boolean;
}

// Network status interface
interface NetworkStatus {
  isOnline: boolean;
  connectionType: string;
  effectiveType: string;
  downlink: number;
  rtt: number;
}

// Data hash for change detection
interface DataHash {
  strategies: string;
  performance: string;
  timestamp: number;
}

// Real-time event callbacks
interface RealtimeCallbacks {
  onStrategyUpdate?: (strategies: Strategy[]) => void;
  onPerformanceUpdate?: (performance: PerformanceMetrics[]) => void;
  onError?: (error: Error, context: string) => void;
  onNetworkChange?: (status: NetworkStatus) => void;
  onSyncStart?: () => void;
  onSyncComplete?: (duration: number) => void;
}

export class RealtimeManager {
  private config: RealtimeConfig;
  private callbacks: RealtimeCallbacks = {};
  private _wsService: any = null; // Lazy initialization

  // Getter for wsService to allow lazy initialization
  private get wsService(): any {
    if (!this._wsService) {
      try {
        this._wsService = getWebSocketService();
      } catch (error) {
        console.warn('[RealtimeManager] WebSocket service not available:', error);
        // Return a minimal no-op mock if service is not available
        this._wsService = {
          connect: () => Promise.resolve(),
          disconnect: () => {},
          send: () => {},
          on: () => {},
          off: () => {},
          subscribeToStrategy: () => {},
          subscribeToPerformance: () => {},
          subscribeToSignals: () => {}
        };
      }
    }
    return this._wsService;
  }

  // Timer management
  private updateTimer: NodeJS.Timeout | null = null;
  private retryTimer: NodeJS.Timeout | null = null;

  // State tracking
  private isActive = false;
  private isPaused = false;
  private retryCount = 0;
  private lastDataHash: DataHash | null = null;
  private lastSyncTime: Date | null = null;
  private networkStatus: NetworkStatus;

  // Performance tracking
  private syncStartTime: number = 0;
  private updateCount = 0;
  private errorCount = 0;

  // Data cache
  private strategyCache: Map<string, Strategy> = new Map();
  private performanceCache: Map<string, PerformanceMetrics> = new Map();

  constructor(config: Partial<RealtimeConfig> = {}) {
    this.config = {
      updateInterval: 10000, // 10 seconds
      maxRetries: 3,
      retryDelay: 2000,
      enableWebSocket: true,
      enablePeriodicRefresh: true,
      ...config
    };

    this.networkStatus = this.getNetworkStatus();
    this.setupNetworkMonitoring();
    this.setupWebSocketListeners();
  }

  // Initialize real-time updates
  async initialize(callbacks: RealtimeCallbacks = {}): Promise<void> {
    this.callbacks = { ...this.callbacks, ...callbacks };

    try {
      // Check network status
      if (!this.networkStatus.isOnline) {
        throw new Error('Network is offline');
      }

      // Start WebSocket connection if enabled
      if (this.config.enableWebSocket) {
        await this.connectWebSocket();
      }

      // Start periodic refresh if enabled
      if (this.config.enablePeriodicRefresh) {
        this.startPeriodicRefresh();
      }

      this.isActive = true;
      console.log('RealtimeManager initialized successfully');

    } catch (error) {
      console.error('Failed to initialize RealtimeManager:', error);
      this.handleError(error as Error, 'initialization');
      throw error;
    }
  }

  // Start real-time updates
  start(): void {
    if (this.isActive) {
      console.warn('RealtimeManager is already active');
      return;
    }

    this.isPaused = false;
    this.retryCount = 0;

    if (this.config.enablePeriodicRefresh) {
      this.startPeriodicRefresh();
    }

    if (this.config.enableWebSocket) {
      this.connectWebSocket();
    }

    this.isActive = true;
    console.log('RealtimeManager started');
  }

  // Stop real-time updates
  stop(): void {
    this.isActive = false;
    this.isPaused = false;

    this.stopPeriodicRefresh();
    this.stopRetryTimer();

    if (this.wsService) {
      this.wsService.disconnect();
    }

    console.log('RealtimeManager stopped');
  }

  // Pause updates (e.g., when page is hidden)
  pause(): void {
    this.isPaused = true;
    this.stopPeriodicRefresh();
    console.log('RealtimeManager paused');
  }

  // Resume updates
  resume(): void {
    if (!this.isActive) {
      this.start();
      return;
    }

    this.isPaused = false;

    if (this.config.enablePeriodicRefresh) {
      this.startPeriodicRefresh();
    }

    console.log('RealtimeManager resumed');
  }

  // Manual refresh trigger
  async triggerManualRefresh(): Promise<void> {
    if (this.isPaused) {
      console.warn('Cannot refresh while paused');
      return;
    }

    console.log('Manual refresh triggered');
    await this.performDataSync(true);
  }

  // WebSocket connection setup
  private async connectWebSocket(): Promise<void> {
    try {
      await this.wsService.connect();

      // Subscribe to relevant channels
      this.wsService.subscribeToStrategy();
      this.wsService.subscribeToPerformance();
      this.wsService.subscribeToSignals();

      console.log('WebSocket connected and subscribed');
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      throw error;
    }
  }

  // WebSocket event listeners
  private setupWebSocketListeners(): void {
    this.wsService.on('message', (message) => {
      this.handleWebSocketMessage(message);
    });

    this.wsService.on('connect', () => {
      console.log('WebSocket connected');
      this.retryCount = 0;
    });

    this.wsService.on('disconnect', () => {
      console.log('WebSocket disconnected');
      this.handleWebSocketDisconnect();
    });

    this.wsService.on('error', (error) => {
      console.error('WebSocket error:', error);
      this.handleError(error.error || new Error('WebSocket error'), 'websocket');
    });
  }

  // Handle WebSocket messages
  private handleWebSocketMessage(message: any): void {
    if (this.isPaused) return;

    try {
      switch (message.type) {
        case 'strategy_update':
          this.handleStrategyUpdate(message.data);
          break;
        case 'performance_update':
          this.handlePerformanceUpdate(message.data);
          break;
        case 'signals_update':
          this.handleSignalsUpdate(message.data);
          break;
        default:
          console.log('Unknown WebSocket message type:', message.type);
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
      this.handleError(error as Error, 'websocket_message');
    }
  }

  // Handle strategy updates
  private handleStrategyUpdate(strategyData: any): void {
    const strategy: Strategy = {
      id: strategyData.id,
      name: strategyData.name,
      type: strategyData.type,
      category: strategyData.category,
      status: strategyData.status,
      performance: strategyData.performance,
      parameters: strategyData.parameters,
      latestSignal: strategyData.latestSignal,
      description: strategyData.description
    };

    // Update cache
    this.strategyCache.set(strategy.id, strategy);

    // Trigger callback
    this.callbacks.onStrategyUpdate?.([strategy]);
    this.updateCount++;
  }

  // Handle performance updates
  private handlePerformanceUpdate(performanceData: any): void {
    const performance: PerformanceMetrics = {
      strategyId: performanceData.strategy_id,
      totalReturn: performanceData.total_return,
      sharpeRatio: performanceData.sharpe_ratio,
      maxDrawdown: performanceData.max_drawdown,
      volatility: performanceData.volatility,
      winRate: performanceData.win_rate,
      profitFactor: performanceData.profit_factor,
      calmarRatio: performanceData.calmar_ratio,
      var95: performanceData.var_95,
      cvar95: performanceData.cvar_95,
      lastUpdated: new Date(performanceData.last_updated)
    };

    // Update cache
    this.performanceCache.set(performance.strategyId, performance);

    // Trigger callback
    this.callbacks.onPerformanceUpdate?.([performance]);
    this.updateCount++;
  }

  // Handle signals updates
  private handleSignalsUpdate(signalsData: any): void {
    console.log('Received signals update:', signalsData);
    // Handle signals as needed
  }

  // Handle WebSocket disconnect
  private handleWebSocketDisconnect(): void {
    if (this.retryCount < this.config.maxRetries) {
      this.retryCount++;
      const delay = this.config.retryDelay * Math.pow(2, this.retryCount - 1);

      this.retryTimer = setTimeout(() => {
        console.log(`Attempting WebSocket reconnection... (${this.retryCount}/${this.config.maxRetries})`);
        this.connectWebSocket();
      }, delay);
    } else {
      console.error('Max WebSocket reconnection attempts reached');
      this.handleError(new Error('WebSocket connection failed'), 'websocket_reconnect');
    }
  }

  // Start periodic data refresh
  private startPeriodicRefresh(): void {
    this.stopPeriodicRefresh(); // Clear any existing timer

    this.updateTimer = setInterval(() => {
      if (!this.isPaused && this.networkStatus.isOnline) {
        this.performDataSync(false);
      }
    }, this.config.updateInterval);

    console.log(`Periodic refresh started with ${this.config.updateInterval}ms interval`);
  }

  // Stop periodic data refresh
  private stopPeriodicRefresh(): void {
    if (this.updateTimer) {
      clearInterval(this.updateTimer);
      this.updateTimer = null;
    }
  }

  // Stop retry timer
  private stopRetryTimer(): void {
    if (this.retryTimer) {
      clearTimeout(this.retryTimer);
      this.retryTimer = null;
    }
  }

  // Perform data synchronization
  private async performDataSync(isManual: boolean = false): Promise<void> {
    this.syncStartTime = Date.now();
    this.callbacks.onSyncStart?.();

    try {
      // Fetch latest data
      const [strategies, performance] = await Promise.all([
        this.fetchStrategies(),
        this.fetchPerformance()
      ]);

      // Check if data has changed
      const newDataHash = this.calculateDataHash(strategies, performance);

      if (this.hasDataChanged(newDataHash) || isManual) {
        // Update caches
        strategies.forEach(strategy => {
          this.strategyCache.set(strategy.id, strategy);
        });

        performance.forEach(perf => {
          this.performanceCache.set(perf.strategyId, perf);
        });

        // Trigger callbacks
        this.callbacks.onStrategyUpdate?.(strategies);
        this.callbacks.onPerformanceUpdate?.(performance);

        this.lastDataHash = newDataHash;

        // Increment update count when data is actually updated
        this.updateCount++;
      }

      this.lastSyncTime = new Date();

      // Calculate sync duration
      const duration = Date.now() - this.syncStartTime;
      this.callbacks.onSyncComplete?.(duration);

      // Reset retry count on success
      this.retryCount = 0;

    } catch (error) {
      console.error('Data sync failed:', error);
      this.handleError(error as Error, 'data_sync');
      this.errorCount++;
    }
  }

  // Fetch strategies from API
  private async fetchStrategies(): Promise<Strategy[]> {
    const response = await fetch('/api/strategies');
    if (!response.ok) {
      throw new Error(`Failed to fetch strategies: ${response.status}`);
    }
    const data = await response.json();
    return data.strategies || [];
  }

  // Fetch performance data from API
  private async fetchPerformance(): Promise<PerformanceMetrics[]> {
    const response = await fetch('/api/performance');
    if (!response.ok) {
      throw new Error(`Failed to fetch performance: ${response.status}`);
    }
    const data = await response.json();
    return data.performance || [];
  }

  // Calculate data hash for change detection
  private calculateDataHash(strategies: Strategy[], performance: PerformanceMetrics[]): DataHash {
    const strategiesHash = this.hashObject(strategies);
    const performanceHash = this.hashObject(performance);

    return {
      strategies: strategiesHash,
      performance: performanceHash,
      timestamp: Date.now()
    };
  }

  // Simple hash function for objects
  private hashObject(obj: any): string {
    const str = JSON.stringify(obj);
    let hash = 0;

    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }

    return hash.toString();
  }

  // Check if data has changed
  private hasDataChanged(newHash: DataHash): boolean {
    if (!this.lastDataHash) return true;

    return (
      newHash.strategies !== this.lastDataHash.strategies ||
      newHash.performance !== this.lastDataHash.performance
    );
  }

  // Setup network monitoring
  private setupNetworkMonitoring(): void {
    // Listen for online/offline events
    window.addEventListener('online', () => {
      console.log('Network connection restored');
      this.updateNetworkStatus();

      // Resume updates if previously paused due to offline status
      if (this.isActive && this.isPaused) {
        this.resume();
      }
    });

    window.addEventListener('offline', () => {
      console.log('Network connection lost');
      this.updateNetworkStatus();

      // Pause updates when offline
      if (this.isActive && !this.isPaused) {
        this.pause();
      }
    });

    // Monitor connection changes
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      connection.addEventListener('change', () => {
        this.updateNetworkStatus();
        this.callbacks.onNetworkChange?.(this.networkStatus);
      });
    }
  }

  // Update network status
  private updateNetworkStatus(): void {
    this.networkStatus = this.getNetworkStatus();
  }

  // Get current network status
  private getNetworkStatus(): NetworkStatus {
    const connection = (navigator as any).connection;

    return {
      isOnline: navigator.onLine,
      connectionType: connection?.type || 'unknown',
      effectiveType: connection?.effectiveType || 'unknown',
      downlink: connection?.downlink || 0,
      rtt: connection?.rtt || 0
    };
  }

  // Handle errors
  private handleError(error: Error, context: string): void {
    console.error(`Error in ${context}:`, error);
    this.callbacks.onError?.(error, context);
  }

  // Get statistics
  getStats(): {
    updateCount: number;
    errorCount: number;
    lastSyncTime: Date | null;
    networkStatus: NetworkStatus;
    isActive: boolean;
    isPaused: boolean;
  } {
    return {
      updateCount: this.updateCount,
      errorCount: this.errorCount,
      lastSyncTime: this.lastSyncTime,
      networkStatus: this.networkStatus,
      isActive: this.isActive,
      isPaused: this.isPaused
    };
  }

  // Get cached data
  getCachedData(): {
    strategies: Strategy[];
    performance: PerformanceMetrics[];
  } {
    return {
      strategies: Array.from(this.strategyCache.values()),
      performance: Array.from(this.performanceCache.values())
    };
  }

  // Cleanup
  destroy(): void {
    this.stop();
    this.strategyCache.clear();
    this.performanceCache.clear();
    this.lastDataHash = null;
    console.log('RealtimeManager destroyed');
  }
}

// Export singleton instance
let realtimeManager: RealtimeManager | null = null;

export const getRealtimeManager = (config?: Partial<RealtimeConfig>): RealtimeManager => {
  if (!realtimeManager) {
    realtimeManager = new RealtimeManager(config);
  }
  return realtimeManager;
};

export default RealtimeManager;