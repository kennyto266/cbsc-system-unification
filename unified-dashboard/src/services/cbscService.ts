/**
 * CBSC 数据服务
 * CBSC Data Service for fetching market data
 */

import axios from 'axios';
import {
  MarketSentiment,
  CBSCTopContracts,
  HistoricalDataPoint,
  CBSCDashboardData,
  HistoricalDataResponse,
  ApiResponse
} from '../types/cbsc';

// Re-export types that are used by components
export type {
  MarketSentiment,
  CBSCTopContracts,
  HistoricalDataPoint,
  CBSCDashboardData,
  HistoricalDataResponse
}

// API 基础 URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001';

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

/**
 * 获取市场情绪指标
 */
export const getMarketSentiment = async (): Promise<MarketSentiment> => {
  try {
    const response = await apiClient.get<ApiResponse<MarketSentiment>>('/api/cbsc/market-sentiment');
    return response.data.data;
  } catch (error) {
    console.error('Error fetching market sentiment:', error);
    throw error;
  }
};

/**
 * 获取牛熊证前十名
 */
export const getTopContracts = async (limit: number = 10): Promise<CBSCTopContracts> => {
  try {
    const response = await apiClient.get<ApiResponse<CBSCTopContracts>>(
      '/api/cbsc/top-contracts',
      { params: { limit } }
    );
    return response.data.data;
  } catch (error) {
    console.error('Error fetching top contracts:', error);
    throw error;
  }
};

/**
 * 获取历史数据
 */
export const getHistoricalData = async (
  days: number = 30,
  metric: string = 'all'
): Promise<HistoricalDataResponse> => {
  try {
    const response = await apiClient.get<ApiResponse<HistoricalDataResponse>>(
      '/api/cbsc/historical-data',
      { params: { days, metric } }
    );
    return response.data.data;
  } catch (error) {
    console.error('Error fetching historical data:', error);
    throw error;
  }
};

/**
 * 获取 Dashboard 综合数据
 */
export const getDashboardSummary = async (): Promise<CBSCDashboardData> => {
  try {
    const response = await apiClient.get<ApiResponse<CBSCDashboardData>>('/api/cbsc/dashboard-summary');
    return response.data.data;
  } catch (error) {
    console.error('Error fetching dashboard summary:', error);
    throw error;
  }
};

/**
 * 实时数据订阅 (使用 WebSocket)
 */
export class CBSCWebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(private onMessage: (data: any) => void) {}

  connect() {
    const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/ws/cbsc`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('CBSC WebSocket connected');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.onMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('CBSC WebSocket disconnected');
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('CBSC WebSocket error:', error);
      };
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      this.attemptReconnect();
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

      setTimeout(() => {
        this.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// 导出单例实例
let wsService: CBSCWebSocketService | null = null;

export const initWebSocketService = (onMessage: (data: any) => void) => {
  if (wsService) {
    wsService.disconnect();
  }
  wsService = new CBSCWebSocketService(onMessage);
  wsService.connect();
  return wsService;
};

export const disconnectWebSocketService = () => {
  if (wsService) {
    wsService.disconnect();
    wsService = null;
  }
};