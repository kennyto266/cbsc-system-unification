/**
 * Strategy Data Service
 * 提供與後端策略管理API的集成服務
 * 實現策略數據獲取、性能指標、詳細信息等核心功能
 *
 * Task #002: API接口集成和數據獲取
 */

import { API_BASE_URL, API_ENDPOINTS, REQUEST_CONFIG, CACHE_CONFIG, ERROR_MESSAGES } from './config';
import { getWebSocketService } from './websocketService';

// Type definitions
export interface StrategyPerformance {
  name: string;
  sharpe_ratio: number;
  max_drawdown: number;
  total_return: number;
  win_rate: number;
  status: 'enabled' | 'disabled';
  daily_pnl?: number;
  volatility?: number;
  calmar_ratio?: number;
  profit_factor?: number;
  last_updated: string;
}

export interface StrategyConfig {
  name: string;
  enabled: boolean;
  description: string;
  parameters: Record<string, any>;
  strategy_type: string;
  risk_level: string;
  created_at: string;
  updated_at: string;
}

export interface StrategyDetail {
  name: string;
  config: StrategyConfig;
  performance: StrategyPerformance;
  last_signal?: {
    type: 'buy' | 'sell' | 'hold';
    strength: number;
    timestamp: string;
    price?: number;
    reason?: string;
  };
  positions?: Array<{
    symbol: string;
    size: number;
    entry_price: number;
    current_price: number;
    unrealized_pnl: number;
  }>;
  recent_signals?: Array<{
    type: 'buy' | 'sell' | 'hold';
    strength: number;
    timestamp: string;
    executed: boolean;
  }>;
}

export interface StrategyListResponse {
  strategies: StrategyConfig[];
  total_count: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface PerformanceSummary {
  total_strategies: number;
  active_strategies: number;
  total_return: number;
  daily_pnl: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  best_strategy: StrategyPerformance;
  worst_strategy: StrategyPerformance;
}

// Cache implementation
class DataCache {
  private cache: Map<string, { data: any; timestamp: number; ttl: number }> = new Map();

  set(key: string, data: any, ttl: number = CACHE_CONFIG.STRATEGY_DATA_TTL): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }

  get(key: string): any | null {
    const item = this.cache.get(key);
    if (!item) return null;

    if (Date.now() - item.timestamp > item.ttl) {
      this.cache.delete(key);
      return null;
    }

    return item.data;
  }

  clear(): void {
    this.cache.clear();
  }

  delete(key: string): void {
    this.cache.delete(key);
  }

  // Clean expired entries
  cleanup(): void {
    const now = Date.now();
    for (const [key, item] of this.cache.entries()) {
      if (now - item.timestamp > item.ttl) {
        this.cache.delete(key);
      }
    }
  }
}

// HTTP Client with error handling and retry logic
class HttpClient {
  private baseUrl: string;
  private retryAttempts: number;
  private retryDelay: number;
  private timeout: number;

  constructor(
    baseUrl: string = API_BASE_URL,
    retryAttempts: number = REQUEST_CONFIG.RETRY_ATTEMPTS,
    retryDelay: number = REQUEST_CONFIG.RETRY_DELAY,
    timeout: number = REQUEST_CONFIG.TIMEOUT
  ) {
    this.baseUrl = baseUrl;
    this.retryAttempts = retryAttempts;
    this.retryDelay = retryDelay;
    this.timeout = timeout;
  }

  private async sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private async requestWithTimeout(url: string, options: RequestInit): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      throw error;
    }
  }

  private async request(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const url = `${this.baseUrl}${endpoint}`;

    // Set default headers
    const defaultHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      defaultHeaders['Authorization'] = `Bearer ${token}`;
    }

    const requestOptions: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    let lastError: Error | null = null;

    // Retry logic
    for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
      try {
        const response = await this.requestWithTimeout(url, requestOptions);

        if (!response.ok) {
          const errorMessage = ERROR_MESSAGES[response.status] || `HTTP ${response.status}`;
          throw new Error(`${errorMessage}: ${response.statusText}`);
        }

        return response;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');

        // Don't retry on client errors (4xx)
        if (lastError.message.includes('HTTP 4')) {
          break;
        }

        // Log retry attempt
        console.warn(`Request failed (attempt ${attempt}/${this.retryAttempts}):`, lastError.message);

        // Don't sleep after last attempt
        if (attempt < this.retryAttempts) {
          await this.sleep(this.retryDelay * attempt); // Exponential backoff
        }
      }
    }

    throw lastError || new Error('Request failed');
  }

  async get(endpoint: string): Promise<any> {
    const response = await this.request(endpoint, { method: 'GET' });
    return response.json();
  }

  async post(endpoint: string, data?: any): Promise<any> {
    const response = await this.request(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
    return response.json();
  }

  async put(endpoint: string, data?: any): Promise<any> {
    const response = await this.request(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
    return response.json();
  }

  async delete(endpoint: string): Promise<any> {
    const response = await this.request(endpoint, { method: 'DELETE' });
    return response.json();
  }
}

// Main Strategy Data Service
class StrategyDataService {
  private httpClient: HttpClient;
  private cache: DataCache;
  private wsService: any;
  private refreshIntervals: Map<string, NodeJS.Timeout> = new Map();

  constructor() {
    this.httpClient = new HttpClient();
    this.cache = new DataCache();
    this.wsService = getWebSocketService();

    // Setup WebSocket listeners for real-time updates
    this.setupWebSocketListeners();

    // Periodically clean cache
    setInterval(() => this.cache.cleanup(), 60000); // Clean every minute
  }

  private setupWebSocketListeners(): void {
    // Listen for strategy updates
    this.wsService.on('message', (data: any) => {
      switch (data.type) {
        case 'strategy_update':
          // Invalidate cache for updated strategy
          this.cache.delete(`strategy_detail_${data.data.name}`);
          this.cache.delete('strategy_list');
          this.cache.delete('performance_summary');
          break;
        case 'performance_update':
          // Invalidate performance cache
          this.cache.delete(`performance_${data.data.strategy_name}`);
          this.cache.delete('performance_summary');
          break;
      }
    });
  }

  /**
   * Get strategy performance data
   */
  async getStrategyPerformance(strategyName?: string): Promise<StrategyPerformance[]> {
    const cacheKey = strategyName ? `performance_${strategyName}` : 'all_performance';

    // Check cache first
    const cached = this.cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    try {
      const endpoint = strategyName
        ? `/strategies/${strategyName}/performance`
        : '/strategies/performance';

      const data = await this.httpClient.get(endpoint);

      // Transform data if needed
      const performances = Array.isArray(data) ? data : [data];
      const transformedPerformances = performances.map((p: any) => ({
        ...p,
        last_updated: p.last_updated || new Date().toISOString()
      }));

      // Cache the result
      this.cache.set(cacheKey, transformedPerformances);

      return transformedPerformances;
    } catch (error) {
      console.error('Failed to fetch strategy performance:', error);
      throw error;
    }
  }

  /**
   * Get strategy list
   */
  async getStrategyList(page: number = 1, pageSize: number = 50): Promise<StrategyListResponse> {
    const cacheKey = `strategy_list_${page}_${pageSize}`;

    // Check cache first
    const cached = this.cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    try {
      const data = await this.httpClient.get(
        `/strategies/list?page=${page}&page_size=${pageSize}`
      );

      // Transform and validate data
      const response: StrategyListResponse = {
        strategies: Array.isArray(data) ? data : (data.strategies || []),
        total_count: data.total_count || data.length || 0,
        page: data.page || page,
        page_size: data.page_size || pageSize,
        has_more: data.has_more || false
      };

      // Cache the result
      this.cache.set(cacheKey, response);

      return response;
    } catch (error) {
      console.error('Failed to fetch strategy list:', error);
      throw error;
    }
  }

  /**
   * Get strategy details
   */
  async getStrategyDetail(strategyName: string): Promise<StrategyDetail> {
    const cacheKey = `strategy_detail_${strategyName}`;

    // Check cache first
    const cached = this.cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    try {
      const [config, performance, lastSignal] = await Promise.all([
        this.httpClient.get(`/strategies/${strategyName}/details`),
        this.httpClient.get(`/strategies/${strategyName}/performance`),
        this.httpClient.get(`/strategies/${strategyName}/last-signal`).catch(() => null)
      ]);

      const detail: StrategyDetail = {
        name: strategyName,
        config: config,
        performance: performance,
        last_signal: lastSignal
      };

      // Cache the result
      this.cache.set(cacheKey, detail);

      return detail;
    } catch (error) {
      console.error(`Failed to fetch strategy details for ${strategyName}:`, error);
      throw error;
    }
  }

  /**
   * Toggle strategy status (enable/disable)
   */
  async toggleStrategy(strategyName: string, enabled: boolean): Promise<any> {
    try {
      const data = await this.httpClient.post(
        `/strategies/${strategyName}/toggle`,
        { enabled }
      );

      // Invalidate relevant cache entries
      this.cache.delete(`strategy_detail_${strategyName}`);
      this.cache.delete('strategy_list');
      this.cache.delete(`performance_${strategyName}`);

      return data;
    } catch (error) {
      console.error(`Failed to toggle strategy ${strategyName}:`, error);
      throw error;
    }
  }

  /**
   * Get performance summary
   */
  async getPerformanceSummary(): Promise<PerformanceSummary> {
    const cacheKey = 'performance_summary';

    // Check cache first
    const cached = this.cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    try {
      const data = await this.httpClient.get('/strategies/performance-summary');

      // Transform and validate data
      const summary: PerformanceSummary = {
        total_strategies: data.total_strategies || 0,
        active_strategies: data.active_strategies || 0,
        total_return: data.total_return || 0,
        daily_pnl: data.daily_pnl || 0,
        sharpe_ratio: data.sharpe_ratio || 0,
        max_drawdown: data.max_drawdown || 0,
        win_rate: data.win_rate || 0,
        best_strategy: data.best_strategy || null,
        worst_strategy: data.worst_strategy || null
      };

      // Cache the result (shorter TTL for summary data)
      this.cache.set(cacheKey, summary, CACHE_CONFIG.METRICS_DATA_TTL);

      return summary;
    } catch (error) {
      console.error('Failed to fetch performance summary:', error);
      throw error;
    }
  }

  /**
   * Setup auto-refresh for specific data
   */
  setupAutoRefresh(key: string, callback: () => void, interval: number = 10000): void {
    // Clear existing interval for this key
    if (this.refreshIntervals.has(key)) {
      clearInterval(this.refreshIntervals.get(key)!);
    }

    // Setup new interval
    const intervalId = setInterval(callback, interval);
    this.refreshIntervals.set(key, intervalId);
  }

  /**
   * Stop auto-refresh for specific data
   */
  stopAutoRefresh(key: string): void {
    if (this.refreshIntervals.has(key)) {
      clearInterval(this.refreshIntervals.get(key)!);
      this.refreshIntervals.delete(key);
    }
  }

  /**
   * Clear all cache
   */
  clearCache(): void {
    this.cache.clear();
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): { size: number; keys: string[] } {
    const keys = Array.from((this.cache as any).cache.keys());
    return {
      size: keys.length,
      keys
    };
  }

  /**
   * Health check for API connectivity
   */
  async healthCheck(): Promise<boolean> {
    try {
      await this.httpClient.get('/health');
      return true;
    } catch (error) {
      console.error('API health check failed:', error);
      return false;
    }
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    // Clear all refresh intervals
    for (const interval of this.refreshIntervals.values()) {
      clearInterval(interval);
    }
    this.refreshIntervals.clear();

    // Clear cache
    this.cache.clear();

    // Disconnect WebSocket
    if (this.wsService) {
      this.wsService.disconnect();
    }
  }
}

// Create and export singleton instance
const strategyDataService = new StrategyDataService();

export default strategyDataService;
export { StrategyDataService, DataCache, HttpClient };