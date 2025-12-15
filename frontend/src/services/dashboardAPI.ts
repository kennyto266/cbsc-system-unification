import { apiClient } from './apiClient';
import {
  DashboardStats,
  Strategy,
  Trade,
  PerformanceData,
  RealTimePrice
} from '../types/dashboard';

// Dashboard API endpoints
export const dashboardAPI = {
  // Get dashboard statistics
  getStats: (): Promise<DashboardStats> =>
    apiClient.get('/dashboard/stats'),

  // Get strategies list
  getStrategies: (params?: {
    page?: number;
    limit?: number;
    status?: string;
    sortBy?: string;
    sortOrder?: 'asc' | 'desc';
  }): Promise<{ data: Strategy[]; total: number }> =>
    apiClient.get('/dashboard/strategies', { params }),

  // Get performance data
  getPerformance: (params?: {
    period?: string;
    strategyId?: string;
  }): Promise<PerformanceData[]> =>
    apiClient.get('/dashboard/performance', { params }),

  // Get recent trades
  getTrades: (params?: {
    page?: number;
    limit?: number;
    strategyId?: string;
  }): Promise<{ data: Trade[]; total: number }> =>
    apiClient.get('/dashboard/trades', { params }),

  // Get real-time prices
  getPrices: (symbols?: string[]): Promise<RealTimePrice[]> =>
    apiClient.get('/dashboard/prices', { params: { symbols } }),

  // Batch operations on strategies
  batchStartStrategies: (strategyIds: string[]): Promise<void> =>
    apiClient.post('/dashboard/strategies/batch-start', { strategyIds }),

  batchStopStrategies: (strategyIds: string[]): Promise<void> =>
    apiClient.post('/dashboard/strategies/batch-stop', { strategyIds }),

  batchDeleteStrategies: (strategyIds: string[]): Promise<void> =>
    apiClient.post('/dashboard/strategies/batch-delete', { strategyIds }),
};

// WebSocket service for real-time data
export class DashboardWebSocket {
  private ws: WebSocket | null = null;
  private subscribers: Map<string, Set<(data: any) => void>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect(url: string = 'ws://localhost:3004/ws/dashboard') {
    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('Dashboard WebSocket connected');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        const { type, data } = JSON.parse(event.data);
        const callbacks = this.subscribers.get(type);
        if (callbacks) {
          callbacks.forEach(callback => callback(data));
        }
      };

      this.ws.onclose = () => {
        console.log('Dashboard WebSocket disconnected');
        this.handleReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('Dashboard WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      this.handleReconnect();
    }
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        this.reconnectAttempts++;
        console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.connect();
      }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts));
    }
  }

  subscribe(type: string, callback: (data: any) => void) {
    if (!this.subscribers.has(type)) {
      this.subscribers.set(type, new Set());
    }
    this.subscribers.get(type)!.add(callback);
  }

  unsubscribe(type: string, callback: (data: any) => void) {
    const callbacks = this.subscribers.get(type);
    if (callbacks) {
      callbacks.delete(callback);
      if (callbacks.size === 0) {
        this.subscribers.delete(type);
      }
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.subscribers.clear();
  }
}

export const dashboardWS = new DashboardWebSocket();