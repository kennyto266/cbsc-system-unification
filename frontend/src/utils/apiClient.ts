/**
 * API Client Utility
 * 統一的API客戶端工具，提供HTTP請求封裝和錯誤處理
 *
 * Task #002: API接口集成和數據獲取
 */

// API響應接口
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: string;
  pagination?: {
    page: number;
    pageSize: number;
    total: number;
    hasMore: boolean;
  };
}

// 請求配置接口
export interface RequestConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: any;
  timeout?: number;
  retries?: number;
  cache?: boolean;
  cacheTTL?: number;
}

// 錯誤類型枚舉
export enum ErrorType {
  NETWORK_ERROR = 'NETWORK_ERROR',
  HTTP_ERROR = 'HTTP_ERROR',
  TIMEOUT_ERROR = 'TIMEOUT_ERROR',
  PARSE_ERROR = 'PARSE_ERROR',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  AUTHENTICATION_ERROR = 'AUTHENTICATION_ERROR',
  AUTHORIZATION_ERROR = 'AUTHORIZATION_ERROR'
}

// 自定義錯誤類
export class ApiError extends Error {
  public type: ErrorType;
  public status?: number;
  public timestamp: string;

  constructor(
    message: string,
    type: ErrorType = ErrorType.NETWORK_ERROR,
    status?: number
  ) {
    super(message);
    this.name = 'ApiError';
    this.type = type;
    this.status = status;
    this.timestamp = new Date().toISOString();
  }
}

// 緩存項接口
interface CacheItem<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

// API客戶端類
export class ApiClient {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;
  private timeout: number;
  private retries: number;
  private cache: Map<string, CacheItem<any>>;

  constructor(baseUrl: string = 'http://localhost:3004') {
    this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
    this.timeout = 30000; // 30 seconds
    this.retries = 3;
    this.cache = new Map();

    // Setup periodic cache cleanup
    setInterval(() => this.cleanupCache(), 60000); // Every minute
  }

  /**
   * 設置默認請求頭
   */
  setDefaultHeader(key: string, value: string): void {
    this.defaultHeaders[key] = value;
  }

  /**
   * 移除默認請求頭
   */
  removeDefaultHeader(key: string): void {
    delete this.defaultHeaders[key];
  }

  /**
   * 設置認證token
   */
  setAuthToken(token: string): void {
    this.setDefaultHeader('Authorization', `Bearer ${token}`);
  }

  /**
   * 清除認證token
   */
  clearAuthToken(): void {
    this.removeDefaultHeader('Authorization');
  }

  /**
   * 從localStorage獲取並設置認證token
   */
  loadAuthToken(): void {
    const token = localStorage.getItem('auth_token');
    if (token) {
      this.setAuthToken(token);
    }
  }

  /**
   * 獲取完整的URL
   */
  private getUrl(endpoint: string): string {
    // Ensure endpoint starts with /
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    return `${this.baseUrl}${cleanEndpoint}`;
  }

  /**
   * 獲取緩存key
   */
  private getCacheKey(endpoint: string, config?: RequestConfig): string {
    const method = config?.method || 'GET';
    const body = config?.body ? JSON.stringify(config.body) : '';
    return `${method}:${endpoint}:${body}`;
  }

  /**
   * 獲取緩存數據
   */
  private getCacheData<T>(key: string): T | null {
    const item = this.cache.get(key);
    if (!item) return null;

    // Check if expired
    if (Date.now() - item.timestamp > item.ttl) {
      this.cache.delete(key);
      return null;
    }

    return item.data;
  }

  /**
   * 設置緩存數據
   */
  private setCacheData<T>(key: string, data: T, ttl: number = 300000): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }

  /**
   * 清理過期緩存
   */
  private cleanupCache(): void {
    const now = Date.now();
    for (const [key, item] of this.cache.entries()) {
      if (now - item.timestamp > item.ttl) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * 睡眠函數
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 處理HTTP錯誤響應
   */
  private handleHttpError(response: Response): ApiError {
    let type = ErrorType.HTTP_ERROR;

    if (response.status === 401) {
      type = ErrorType.AUTHENTICATION_ERROR;
    } else if (response.status === 403) {
      type = ErrorType.AUTHORIZATION_ERROR;
    } else if (response.status >= 400 && response.status < 500) {
      type = ErrorType.VALIDATION_ERROR;
    } else if (response.status >= 500) {
      type = ErrorType.NETWORK_ERROR;
    }

    return new ApiError(
      `HTTP ${response.status}: ${response.statusText}`,
      type,
      response.status
    );
  }

  /**
   * 處理網絡錯誤
   */
  private handleNetworkError(error: any): ApiError {
    if (error.name === 'AbortError') {
      return new ApiError('Request timeout', ErrorType.TIMEOUT_ERROR);
    }

    if (error instanceof ApiError) {
      return error;
    }

    return new ApiError(
      error.message || 'Network error',
      ErrorType.NETWORK_ERROR
    );
  }

  /**
   * 解析響應數據
   */
  private async parseResponse<T>(response: Response): Promise<T> {
    const contentType = response.headers.get('content-type');

    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    }

    // Handle non-JSON responses
    const text = await response.text();
    try {
      return JSON.parse(text) as T;
    } catch {
      return text as unknown as T;
    }
  }

  /**
   * 執行HTTP請求
   */
  private async request<T>(
    endpoint: string,
    config: RequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const {
      method = 'GET',
      headers = {},
      body,
      timeout = this.timeout,
      retries = this.retries,
      cache = false,
      cacheTTL = 300000 // 5 minutes default
    } = config;

    // Check cache for GET requests
    if (method === 'GET' && cache) {
      const cacheKey = this.getCacheKey(endpoint, config);
      const cachedData = this.getCacheData<ApiResponse<T>>(cacheKey);
      if (cachedData) {
        return cachedData;
      }
    }

    const url = this.getUrl(endpoint);
    const requestHeaders = { ...this.defaultHeaders, ...headers };

    // Prepare request body
    let requestBody: string | undefined;
    if (body) {
      if (typeof body === 'string') {
        requestBody = body;
      } else if (body instanceof FormData || body instanceof URLSearchParams) {
        requestBody = body as unknown as string;
        // Remove content-type header for FormData
        if (body instanceof FormData) {
          delete requestHeaders['Content-Type'];
        }
      } else {
        requestBody = JSON.stringify(body);
      }
    }

    let lastError: Error | null = null;

    // Retry logic
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        // Create abort controller for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        const response = await fetch(url, {
          method,
          headers: requestHeaders,
          body: requestBody,
          signal: controller.signal
        });

        clearTimeout(timeoutId);

        // Handle HTTP errors
        if (!response.ok) {
          throw this.handleHttpError(response);
        }

        // Parse response
        const data = await this.parseResponse<T>(response);

        // Create success response
        const apiResponse: ApiResponse<T> = {
          success: true,
          data,
          timestamp: new Date().toISOString()
        };

        // Cache successful GET requests
        if (method === 'GET' && cache) {
          const cacheKey = this.getCacheKey(endpoint, config);
          this.setCacheData(cacheKey, apiResponse, cacheTTL);
        }

        return apiResponse;

      } catch (error) {
        lastError = this.handleNetworkError(error);

        // Don't retry on client errors (4xx) except 429 (Too Many Requests)
        if (lastError.type === ErrorType.VALIDATION_ERROR &&
            !(lastError.status === 429)) {
          break;
        }

        // Don't retry on authentication errors
        if (lastError.type === ErrorType.AUTHENTICATION_ERROR) {
          break;
        }

        // Log retry attempt
        if (attempt < retries) {
          console.warn(`Request failed (attempt ${attempt}/${retries}):`, lastError.message);
          await this.sleep(Math.min(1000 * Math.pow(2, attempt - 1), 5000)); // Exponential backoff, max 5s
        }
      }
    }

    // Return error response
    return {
      success: false,
      error: lastError?.message || 'Request failed',
      timestamp: new Date().toISOString()
    };
  }

  /**
   * GET請求
   */
  async get<T>(
    endpoint: string,
    config: Omit<RequestConfig, 'method'> = {}
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'GET' });
  }

  /**
   * POST請求
   */
  async post<T>(
    endpoint: string,
    data?: any,
    config: Omit<RequestConfig, 'method' | 'body'> = {}
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'POST', body: data });
  }

  /**
   * PUT請求
   */
  async put<T>(
    endpoint: string,
    data?: any,
    config: Omit<RequestConfig, 'method' | 'body'> = {}
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'PUT', body: data });
  }

  /**
   * PATCH請求
   */
  async patch<T>(
    endpoint: string,
    data?: any,
    config: Omit<RequestConfig, 'method' | 'body'> = {}
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'PATCH', body: data });
  }

  /**
   * DELETE請求
   */
  async delete<T>(
    endpoint: string,
    config: Omit<RequestConfig, 'method'> = {}
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'DELETE' });
  }

  /**
   * 上傳文件
   */
  async upload<T>(
    endpoint: string,
    file: File,
    additionalData?: Record<string, any>,
    config: Omit<RequestConfig, 'method' | 'body' | 'headers'> = {}
  ): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

    // Add additional data
    if (additionalData) {
      for (const [key, value] of Object.entries(additionalData)) {
        formData.append(key, String(value));
      }
    }

    return this.request<T>(endpoint, {
      ...config,
      method: 'POST',
      body: formData,
      headers: {} // Let browser set content-type for FormData
    });
  }

  /**
   * 清除所有緩存
   */
  clearCache(): void {
    this.cache.clear();
  }

  /**
   * 獲取緩存統計
   */
  getCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys())
    };
  }

  /**
   * 批量請求
   */
  async batch<T>(
    requests: Array<{ endpoint: string; config?: RequestConfig }>
  ): Promise<ApiResponse<T>[]> {
    const promises = requests.map(({ endpoint, config }) =>
      this.request<T>(endpoint, config)
    );

    return Promise.all(promises);
  }
}

// 創建並導出默認實例
const apiClient = new ApiClient();

// 自動加載認證token
apiClient.loadAuthToken();

// 監聽storage變化以更新token
window.addEventListener('storage', (e) => {
  if (e.key === 'auth_token') {
    if (e.newValue) {
      apiClient.setAuthToken(e.newValue);
    } else {
      apiClient.clearAuthToken();
    }
  }
});

export default apiClient;