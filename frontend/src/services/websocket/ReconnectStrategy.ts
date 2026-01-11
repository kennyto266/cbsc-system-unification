/**
 * WebSocket Reconnection Strategy
 * Implements various reconnection strategies with exponential backoff and jitter
 */

import { ReconnectStrategy } from '../../types/websocket';

export class ReconnectionStrategy {
  private strategy: ReconnectStrategy;
  private attemptCount = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private isActive = false;
  private lastReconnectTime = 0;

  constructor(strategy: Partial<ReconnectStrategy> = {}) {
    this.strategy = {
      maxAttempts: 5,
      baseDelay: 1000,
      maxDelay: 30000,
      backoffFactor: 2,
      jitter: true,
      ...strategy
    };
  }

  /**
   * Start reconnection process
   */
  start(reconnectFn: () => Promise<void>): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.isActive) {
        reject(new Error('Reconnection already in progress'));
        return;
      }

      this.isActive = true;
      this.attemptCount = 0;

      this.attemptReconnect(reconnectFn, resolve, reject);
    });
  }

  /**
   * Stop reconnection process
   */
  stop(): void {
    this.isActive = false;
    this.attemptCount = 0;

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Reset reconnection state
   */
  reset(): void {
    this.attemptCount = 0;
    this.lastReconnectTime = 0;
  }

  /**
   * Get current attempt count
   */
  getAttemptCount(): number {
    return this.attemptCount;
  }

  /**
   * Check if reconnection is active
   */
  isReconnecting(): boolean {
    return this.isActive;
  }

  /**
   * Get next reconnection delay
   */
  getNextDelay(): number {
    // Calculate base delay with exponential backoff
    let delay = this.strategy.baseDelay * Math.pow(this.strategy.backoffFactor, this.attemptCount);

    // Apply maximum delay limit
    delay = Math.min(delay, this.strategy.maxDelay);

    // Add jitter if enabled
    if (this.strategy.jitter) {
      // Add random jitter between -25% and +25%
      const jitterAmount = delay * 0.25;
      delay += (Math.random() * 2 - 1) * jitterAmount;
    }

    // Ensure minimum delay of 100ms
    delay = Math.max(100, delay);

    return Math.floor(delay);
  }

  /**
   * Get reconnection statistics
   */
  getStats() {
    return {
      attemptCount: this.attemptCount,
      maxAttempts: this.strategy.maxAttempts,
      isActive: this.isActive,
      lastReconnectTime: this.lastReconnectTime,
      nextDelay: this.isActive ? this.getNextDelay() : 0
    };
  }

  /**
   * Attempt to reconnect
   */
  private attemptReconnect(
    reconnectFn: () => Promise<void>,
    resolve: () => void,
    reject: (error: Error) => void
  ): void {
    if (!this.isActive) {
      reject(new Error('Reconnection stopped'));
      return;
    }

    if (this.attemptCount >= this.strategy.maxAttempts) {
      this.isActive = false;
      const error = new Error(`Max reconnection attempts (${this.strategy.maxAttempts}) reached`);

      if (this.strategy.onFailed) {
        this.strategy.onFailed();
      }

      reject(error);
      return;
    }

    this.attemptCount++;
    const delay = this.getNextDelay();

    // Notify about reconnection attempt
    if (this.strategy.onReconnecting) {
      this.strategy.onReconnecting(this.attemptCount, delay);
    }

    // Schedule reconnection attempt
    this.reconnectTimer = setTimeout(async () => {
      if (!this.isActive) {
        reject(new Error('Reconnection stopped'));
        return;
      }

      try {
        this.lastReconnectTime = Date.now();
        await reconnectFn();

        // Successful reconnection
        this.isActive = false;
        this.attemptCount = 0;
        resolve();
      } catch (error) {
        console.error(`Reconnection attempt ${this.attemptCount} failed:`, error);

        // Continue with next attempt
        this.attemptReconnect(reconnectFn, resolve, reject);
      }
    }, delay);
  }
}

/**
 * Predefined reconnection strategies
 */
export const ReconnectionStrategies = {
  /**
   * Conservative strategy - longer delays, fewer attempts
   */
  conservative: () => ({
    maxAttempts: 3,
    baseDelay: 2000,
    maxDelay: 30000,
    backoffFactor: 2.5,
    jitter: true
  } as Partial<ReconnectStrategy>),

  /**
   * Aggressive strategy - shorter delays, more attempts
   */
  aggressive: () => ({
    maxAttempts: 10,
    baseDelay: 500,
    maxDelay: 10000,
    backoffFactor: 1.5,
    jitter: true
  } as Partial<ReconnectStrategy>),

  /**
   * Balanced strategy - moderate settings
   */
  balanced: () => ({
    maxAttempts: 5,
    baseDelay: 1000,
    maxDelay: 20000,
    backoffFactor: 2,
    jitter: true
  } as Partial<ReconnectStrategy>),

  /**
   * Custom strategy with exponential backoff
   */
  exponential: (options: {
    maxAttempts?: number;
    baseDelay?: number;
    maxDelay?: number;
  }) => ({
    maxAttempts: options.maxAttempts || 5,
    baseDelay: options.baseDelay || 1000,
    maxDelay: options.maxDelay || 30000,
    backoffFactor: 2,
    jitter: true
  }),

  /**
   * Linear backoff strategy
   */
  linear: (options: {
    maxAttempts?: number;
    baseDelay?: number;
    increment?: number;
  }) => ({
    maxAttempts: options.maxAttempts || 5,
    baseDelay: options.baseDelay || 1000,
    maxDelay: 10000,
    backoffFactor: 1,
    jitter: false,
    onReconnecting: (attempt: number) => {
      // Custom linear delay calculation
      const delay = (options.baseDelay || 1000) + (attempt - 1) * (options.increment || 500);
      console.log(`Linear reconnect attempt ${attempt}, next delay: ${delay}ms`);
    }
  })
};

/**
 * Network-aware reconnection strategy
 * Adapts based on network conditions
 */
export class NetworkAwareReconnectionStrategy extends ReconnectionStrategy {
  private networkQuality: 'excellent' | 'good' | 'fair' | 'poor' = 'good';
  private lastNetworkCheck = 0;
  private networkCheckInterval = 30000; // 30 seconds

  constructor(strategy: Partial<ReconnectStrategy> = {}) {
    super(strategy);
    this.monitorNetwork();
  }

  /**
   * Get adjusted delay based on network quality
   */
  getNextDelay(): number {
    const baseDelay = super.getNextDelay();

    // Adjust delay based on network quality
    switch (this.networkQuality) {
      case 'excellent':
        return Math.floor(baseDelay * 0.5);
      case 'good':
        return baseDelay;
      case 'fair':
        return Math.floor(baseDelay * 1.5);
      case 'poor':
        return Math.floor(baseDelay * 2);
      default:
        return baseDelay;
    }
  }

  /**
   * Monitor network quality
   */
  private monitorNetwork(): void {
    if (typeof window === 'undefined' || !('connection' in navigator)) {
      return;
    }

    const checkNetworkQuality = () => {
      const connection = (navigator as any).connection;

      if (connection) {
        const { effectiveType, downlink, rtt } = connection;

        // Determine network quality based on metrics
        if (effectiveType === '4g' && downlink > 5 && rtt < 100) {
          this.networkQuality = 'excellent';
        } else if (effectiveType === '4g' || downlink > 2) {
          this.networkQuality = 'good';
        } else if (effectiveType === '3g' || downlink > 0.5) {
          this.networkQuality = 'fair';
        } else {
          this.networkQuality = 'poor';
        }
      } else {
        // Fallback to navigator.onLine
        this.networkQuality = navigator.onLine ? 'good' : 'poor';
      }

      this.lastNetworkCheck = Date.now();
    };

    // Initial check
    checkNetworkQuality();

    // Set up periodic checks
    setInterval(checkNetworkQuality, this.networkCheckInterval);

    // Listen for network changes
    window.addEventListener('online', checkNetworkQuality);
    window.addEventListener('offline', checkNetworkQuality);
  }

  /**
   * Get current network quality
   */
  getNetworkQuality(): 'excellent' | 'good' | 'fair' | 'poor' {
    return this.networkQuality;
  }
}

/**
 * Adaptive reconnection strategy
 * Learns from previous reconnection patterns
 */
export class AdaptiveReconnectionStrategy extends ReconnectionStrategy {
  private connectionHistory: Array<{
    timestamp: number;
    success: boolean;
    duration: number;
  }> = [];
  private maxHistorySize = 50;
  private averageConnectionTime = 0;

  constructor(strategy: Partial<ReconnectStrategy> = {}) {
    super(strategy);
  }

  /**
   * Record connection attempt result
   */
  recordConnectionResult(success: boolean, duration: number): void {
    this.connectionHistory.push({
      timestamp: Date.now(),
      success,
      duration
    });

    // Limit history size
    if (this.connectionHistory.length > this.maxHistorySize) {
      this.connectionHistory.shift();
    }

    // Update average connection time
    if (success) {
      const successfulConnections = this.connectionHistory.filter(h => h.success);
      if (successfulConnections.length > 0) {
        this.averageConnectionTime = successfulConnections.reduce((sum, h) => sum + h.duration, 0) / successfulConnections.length;
      }
    }
  }

  /**
   * Get adaptive delay based on history
   */
  getNextDelay(): number {
    const baseDelay = super.getNextDelay();

    // Analyze recent failures
    const recentFailures = this.connectionHistory
      .filter(h => !h.success && Date.now() - h.timestamp < 300000) // Last 5 minutes
      .length;

    // Increase delay if many recent failures
    if (recentFailures > 3) {
      return Math.floor(baseDelay * 2);
    }

    // Reduce delay if connections are usually fast
    if (this.averageConnectionTime > 0 && this.averageConnectionTime < 1000) {
      return Math.floor(baseDelay * 0.75);
    }

    return baseDelay;
  }

  /**
   * Get connection statistics
   */
  getConnectionStats() {
    const totalConnections = this.connectionHistory.length;
    const successfulConnections = this.connectionHistory.filter(h => h.success).length;
    const successRate = totalConnections > 0 ? successfulConnections / totalConnections : 0;

    return {
      totalConnections,
      successfulConnections,
      successRate,
      averageConnectionTime: this.averageConnectionTime,
      recentFailures: this.connectionHistory
        .filter(h => !h.success && Date.now() - h.timestamp < 300000)
        .length
    };
  }
}