/**
 * API Service
 * 统一管理所有后端API调用
 * Integration with CBSC Backend System
 */

// API基础配置 - 使用 Vite 环境变量
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3003';
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:3007';

// Request interceptor - 添加认证token
const getAuthHeaders = () => {
  const token = localStorage.getItem('auth_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

// 通用请求函数
const apiRequest = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);

    // Handle 401 Unauthorized
    if (response.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API Request Error:', error);
    throw error;
  }
};

// 用户管理API
export const userAPI = {
  // 获取用户列表
  getUsers: async (page = 1, pageSize = 20) => {
    return apiRequest(`/api/strategies/users?page=${page}&page_size=${pageSize}`);
  },

  // 获取用户详情
  getUser: async (userId) => {
    return apiRequest(`/api/strategies/users/${userId}`);
  },

  // 创建用户
  createUser: async (userData) => {
    return apiRequest('/api/strategies/users', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  },

  // 更新用户
  updateUser: async (userId, userData) => {
    return apiRequest(`/api/strategies/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
  },

  // 删除用户
  deleteUser: async (userId) => {
    return apiRequest(`/api/strategies/users/${userId}`, {
      method: 'DELETE',
    });
  },

  // 用户认证
  login: async (credentials) => {
    const response = await apiRequest('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });

    // 保存token
    if (response.access_token) {
      localStorage.setItem('auth_token', response.access_token);
    }

    return response;
  },

  // 登出
  logout: async () => {
    localStorage.removeItem('auth_token');
    return apiRequest('/api/auth/logout', { method: 'POST' });
  },
};

// 策略管理API
export const strategyAPI = {
  // 获取策略列表
  getStrategies: async (page = 1, pageSize = 20, filters = {}) => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
      ...filters,
    });
    return apiRequest(`/api/strategies?${params}`);
  },

  // 获取策略详情
  getStrategy: async (strategyId) => {
    return apiRequest(`/api/strategies/${strategyId}`);
  },

  // 创建策略
  createStrategy: async (strategyData) => {
    return apiRequest('/api/strategies', {
      method: 'POST',
      body: JSON.stringify(strategyData),
    });
  },

  // 更新策略
  updateStrategy: async (strategyId, strategyData) => {
    return apiRequest(`/api/strategies/${strategyId}`, {
      method: 'PUT',
      body: JSON.stringify(strategyData),
    });
  },

  // 删除策略
  deleteStrategy: async (strategyId) => {
    return apiRequest(`/api/strategies/${strategyId}`, {
      method: 'DELETE',
    });
  },

  // 获取策略模板
  getStrategyTemplates: async () => {
    return apiRequest('/api/strategies/templates');
  },

  // 执行策略
  executeStrategy: async (strategyId, params) => {
    return apiRequest(`/api/strategies/${strategyId}/execute`, {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },
};

// WebSocket连接管理
export class WebSocketManager {
  constructor() {
    this.ws = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect(userId) {
    const wsUrl = `${WS_URL}/ws/${userId}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.reconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  subscribe(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  unsubscribe(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  handleMessage(data) {
    const { event, payload } = data;
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => callback(payload));
    }
  }

  reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
      setTimeout(() => {
        this.connect();
      }, 1000 * this.reconnectAttempts);
    }
  }
}

// 创建WebSocket管理器实例
export const wsManager = new WebSocketManager();

// Export API base URL for other modules
export { API_BASE_URL };

// Generic API client for economicStrategyApi
export const api = {
  get: async (endpoint, options = {}) => {
    return apiRequest(endpoint, { method: 'GET', ...options });
  },
  post: async (endpoint, data, options = {}) => {
    return apiRequest(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
      ...options
    });
  },
  put: async (endpoint, data, options = {}) => {
    return apiRequest(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
      ...options
    });
  },
  delete: async (endpoint, options = {}) => {
    return apiRequest(endpoint, { method: 'DELETE', ...options });
  },
};