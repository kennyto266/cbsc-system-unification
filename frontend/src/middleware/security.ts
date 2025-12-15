/**
 * Security Middleware
 * Provides security middleware for API requests and responses
 */

import { initializeSecurity, securityManager } from '../utils/security';

// Security middleware configuration
interface SecurityMiddlewareConfig {
  enableCSP?: boolean;
  enableCSRF?: boolean;
  enableXSSProtection?: boolean;
  enableAudit?: boolean;
  trustedOrigins?: string[];
  excludedPaths?: string[];
}

// Default configuration
const DEFAULT_CONFIG: SecurityMiddlewareConfig = {
  enableCSP: true,
  enableCSRF: true,
  enableXSSProtection: true,
  enableAudit: true,
  trustedOrigins: ['https://cbsc.com', 'https://api.cbsc.com'],
  excludedPaths: ['/health', '/metrics']
};

/**
 * Initialize security middleware
 */
export const initSecurityMiddleware = async (config: Partial<SecurityMiddlewareConfig> = {}) => {
  const finalConfig = { ...DEFAULT_CONFIG, ...config };

  // Initialize security system
  await initializeSecurity();

  // Enable production mode if not in development
  if (process.env.NODE_ENV === 'production') {
    securityManager.enableProductionMode();
  } else {
    securityManager.enableDevelopmentMode();
  }

  return finalConfig;
};

/**
 * Fetch wrapper with security middleware
 */
export const secureFetch = async (
  input: RequestInfo | URL,
  init?: RequestInit & { securityConfig?: Partial<SecurityMiddlewareConfig> }
): Promise<Response> => {
  const { securityConfig = {}, ...fetchInit } = init || {};
  const config = { ...DEFAULT_CONFIG, ...securityConfig };

  // Check if path is excluded
  const url = typeof input === 'string' ? input : input.toString();
  const isExcluded = config.excludedPaths?.some(path => url.includes(path));

  // Add security headers
  const headers = new Headers(fetchInit.headers);

  if (config.enableCSRF && !isExcluded) {
    const token = await import('../utils/security').then(m => m.csrfProtection.getToken());
    headers.set('X-XSRF-TOKEN', token);
  }

  if (config.enableXSSProtection) {
    headers.set('X-Content-Type-Options', 'nosniff');
    headers.set('X-Frame-Options', 'DENY');
    headers.set('X-XSS-Protection', '1; mode=block');
  }

  // Add origin and referer headers for CORS
  if (typeof window !== 'undefined') {
    headers.set('Origin', window.location.origin);
    if (document.referrer) {
      headers.set('Referer', document.referrer);
    }
  }

  // Make request with modified headers
  const response = await fetch(input, {
    ...fetchInit,
    headers
  });

  // Check response security
  if (!isExcluded) {
    // Validate CORS headers
    const corsOrigin = response.headers.get('Access-Control-Allow-Origin');
    if (corsOrigin && corsOrigin !== '*' && !config.trustedOrigins?.includes(corsOrigin)) {
      console.warn('Suspicious CORS origin detected:', corsOrigin);
    }

    // Check for security headers in response
    const cspHeader = response.headers.get('Content-Security-Policy');
    if (config.enableCSP && !cspHeader) {
      console.warn('Missing CSP header in response');
    }
  }

  return response;
};

/**
 * WebSocket wrapper with security
 */
export class SecureWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private protocols?: string[];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private securityConfig: SecurityMiddlewareConfig;

  constructor(
    url: string,
    protocols?: string[],
    securityConfig?: Partial<SecurityMiddlewareConfig>
  ) {
    this.url = url;
    this.protocols = protocols;
    this.securityConfig = { ...DEFAULT_CONFIG, ...securityConfig };
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // Validate URL
        const wsUrl = new URL(this.url);
        if (!['ws:', 'wss:'].includes(wsUrl.protocol)) {
          throw new Error('Invalid WebSocket protocol');
        }

        // Create WebSocket
        this.ws = new WebSocket(this.url, this.protocols);

        this.ws.onopen = () => {
          console.log('Secure WebSocket connected');
          resolve();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket closed');
          this.attemptReconnect();
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

      setTimeout(() => {
        this.connect().catch(error => {
          console.error('Reconnection failed:', error);
        });
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  send(data: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      // Sanitize data if XSS protection is enabled
      if (this.securityConfig.enableXSSProtection) {
        const { validateSecure } = require('../utils/security');
        const { valid, sanitized, threats } = validateSecure(data, 'text');

        if (!valid) {
          console.warn('WebSocket data contains threats:', threats);
        }

        this.ws.send(sanitized);
      } else {
        this.ws.send(data);
      }
    } else {
      console.error('WebSocket is not connected');
    }
  }

  close(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnection
  }

  onmessage(handler: (event: MessageEvent) => void): void {
    if (this.ws) {
      this.ws.onmessage = (event) => {
        // Validate incoming data
        if (this.securityConfig.enableXSSProtection) {
          const { validateSecure } = require('../utils/security');
          const { valid, threats } = validateSecure(event.data, 'text');

          if (!valid) {
            console.warn('Received WebSocket data contains threats:', threats);
            return;
          }
        }

        handler(event);
      };
    }
  }

  onopen(handler: (event: Event) => void): void {
    if (this.ws) {
      this.ws.onopen = handler;
    }
  }

  onerror(handler: (event: Event) => void): void {
    if (this.ws) {
      this.ws.onerror = handler;
    }
  }

  onclose(handler: (event: CloseEvent) => void): void {
    if (this.ws) {
      this.ws.onclose = handler;
    }
  }
}

/**
 * Request interceptor for axios
 */
export const createSecurityInterceptor = (axios: any) => {
  // Request interceptor
  axios.interceptors.request.use(
    (config: any) => {
      // Add CSRF token
      const { csrfProtection } = require('../utils/security');
      const token = csrfProtection.getToken();
      if (token) {
        config.headers['X-XSRF-TOKEN'] = token;
      }

      // Add security headers
      config.headers['X-Requested-With'] = 'XMLHttpRequest';

      // Validate request data
      if (config.data && typeof config.data === 'object') {
        const { validateFinancial } = require('../utils/security');
        if (config.url?.includes('/strategy') || config.url?.includes('/portfolio')) {
          const validation = validateFinancial(config.data);
          if (!validation.valid) {
            console.warn('Invalid financial data:', validation.errors);
          }
        }
      }

      return config;
    },
    (error: any) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor
  axios.interceptors.response.use(
    (response: any) => {
      // Validate response data
      if (response.data) {
        const { safeJSONParse } = require('../utils/security');
        const data = safeJSONParse(JSON.stringify(response.data));
        if (data === null) {
          console.warn('Invalid JSON in response');
        }
      }

      return response;
    },
    (error: any) => {
      // Handle security-related errors
      if (error.response?.status === 403) {
        console.error('Request blocked by CSRF protection');
      } else if (error.response?.status === 419) {
        console.error('CSRF token mismatch');
      }

      return Promise.reject(error);
    }
  );
};

/**
 * Content Security Policy middleware
 */
export const CSPMiddleware = {
  // Generate nonce for inline scripts
  generateNonce: (): string => {
    const { cspConfig } = require('../utils/security');
    return cspConfig.getNonce();
  },

  // Validate script content
  validateScript: (content: string): boolean => {
    const { xssProtection } = require('../utils/security');
    return !xssProtection.containsDangerousPatterns(content);
  },

  // Add CSP header to response
  addCSPHeader: (response: Response, policy: string): void => {
    response.headers.set('Content-Security-Policy', policy);
  }
};

export default {
  initSecurityMiddleware,
  secureFetch,
  SecureWebSocket,
  createSecurityInterceptor,
  CSPMiddleware
};