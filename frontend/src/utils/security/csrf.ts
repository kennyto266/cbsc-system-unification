/**
 * CSRF Protection Utilities
 * Implements Double Cookie Submit pattern for CSRF protection
 */

// CSRF token configuration
const CSRF_CONFIG = {
  TOKEN_LENGTH: 32,
  COOKIE_NAME: 'XSRF-TOKEN',
  HEADER_NAME: 'X-XSRF-TOKEN',
  TOKEN_EXPIRY: 24 * 60 * 60 * 1000, // 24 hours
  ROTATION_THRESHOLD: 60 * 60 * 1000 // 1 hour
};

/**
 * CSRF Protection class
 */
export class CSRFProtection {
  private static instance: CSRFProtection;
  private currentToken: string | null = null;
  private tokenGenerationTime: number = 0;
  private rotationTimer: NodeJS.Timeout | null = null;

  private constructor() {
    this.initializeToken();
    this.setupRotationTimer();
  }

  /**
   * Singleton instance getter
   */
  public static getInstance(): CSRFProtection {
    if (!CSRFProtection.instance) {
      CSRFProtection.instance = new CSRFProtection();
    }
    return CSRFProtection.instance;
  }

  /**
   * Initialize CSRF token from cookie or generate new one
   */
  private initializeToken(): void {
    const cookieToken = this.getCookie(CSRF_CONFIG.COOKIE_NAME);

    if (cookieToken && this.isValidToken(cookieToken)) {
      this.currentToken = cookieToken;
    } else {
      this.generateToken();
    }
  }

  /**
   * Generate cryptographically secure random token
   */
  private generateToken(): string {
    const array = new Uint8Array(CSRF_CONFIG.TOKEN_LENGTH);
    crypto.getRandomValues(array);

    const token = Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');

    this.currentToken = token;
    this.tokenGenerationTime = Date.now();
    this.setCookie(CSRF_CONFIG.COOKIE_NAME, token, CSRF_CONFIG.TOKEN_EXPIRY);

    return token;
  }

  /**
   * Validate token format
   */
  private isValidToken(token: string): boolean {
    return /^[a-f0-9]{64}$/.test(token);
  }

  /**
   * Get cookie value
   */
  private getCookie(name: string): string | null {
    const cookies = document.cookie.split(';');

    for (const cookie of cookies) {
      const [cookieName, cookieValue] = cookie.trim().split('=');
      if (cookieName === name) {
        return decodeURIComponent(cookieValue);
      }
    }

    return null;
  }

  /**
   * Set cookie value
   */
  private setCookie(name: string, value: string, maxAge: number): void {
    const secure = location.protocol === 'https:';
    const sameSite = secure ? 'Strict' : 'Lax';

    document.cookie = `${name}=${encodeURIComponent(value)}; ` +
      `max-age=${maxAge}; ` +
      `path=/; ` +
      `${sameSite ? `SameSite=${sameSite}; ` : ''}` +
      `${secure ? 'Secure; ' : ''}` +
      'HttpOnly';
  }

  /**
   * Setup automatic token rotation
   */
  private setupRotationTimer(): void {
    if (this.rotationTimer) {
      clearInterval(this.rotationTimer);
    }

    this.rotationTimer = setInterval(() => {
      this.rotateToken();
    }, CSRF_CONFIG.ROTATION_THRESHOLD);
  }

  /**
   * Rotate CSRF token
   */
  public rotateToken(): void {
    this.generateToken();
  }

  /**
   * Get current CSRF token
   */
  public getToken(): string {
    if (!this.currentToken) {
      this.generateToken();
    }

    return this.currentToken!;
  }

  /**
   * Validate CSRF token from request
   */
  public validateToken(token: string): boolean {
    if (!token || !this.currentToken) {
      return false;
    }

    return token === this.currentToken && this.isValidToken(token);
  }

  /**
   * Add CSRF token to headers
   */
  public addTokenToHeaders(headers: Record<string, string>): Record<string, string> {
    return {
      ...headers,
      [CSRF_CONFIG.HEADER_NAME]: this.getToken()
    };
  }

  /**
   * Add CSRF token to form data
   */
  public addTokenToFormData(formData: FormData): void {
    formData.append('_csrf', this.getToken());
  }

  /**
   * Fetch wrapper with CSRF protection
   */
  public async fetchWithCSRF(url: string, options: RequestInit = {}): Promise<Response> {
    // Only add token to state-changing methods
    const needsToken = ['POST', 'PUT', 'DELETE', 'PATCH'].includes(
      options.method?.toUpperCase() || 'GET'
    );

    if (needsToken) {
      const headers = new Headers(options.headers);
      headers.set(CSRF_CONFIG.HEADER_NAME, this.getToken());

      options.headers = headers;
    }

    const response = await fetch(url, options);

    // Check for token refresh header
    const newToken = response.headers.get('X-New-CSRF-Token');
    if (newToken && this.isValidToken(newToken)) {
      this.currentToken = newToken;
      this.tokenGenerationTime = Date.now();
      this.setCookie(CSRF_CONFIG.COOKIE_NAME, newToken, CSRF_CONFIG.TOKEN_EXPIRY);
    }

    return response;
  }

  /**
   * Setup global fetch interceptor
   */
  public setupFetchInterceptor(): void {
    const originalFetch = window.fetch;

    window.fetch = async (url, options = {}) => {
      // Skip external requests
      if (typeof url === 'string' && url.startsWith('http')) {
        const urlObj = new URL(url);
        if (urlObj.hostname !== window.location.hostname) {
          return originalFetch(url, options);
        }
      }

      return this.fetchWithCSRF(url, options);
    };
  }

  /**
   * Setup XMLHttpRequest interceptor
   */
  public setupXHRInterceptor(): void {
    const originalOpen = XMLHttpRequest.prototype.open;
    const originalSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function(method: string, url: string | URL) {
      (this as any)._method = method;
      (this as any)._url = url;
      return originalOpen.call(this, method, url);
    };

    XMLHttpRequest.prototype.send = function(body?: Document | BodyInit | null) {
      const needsToken = ['POST', 'PUT', 'DELETE', 'PATCH'].includes(
        (this as any)._method?.toUpperCase() || 'GET'
      );

      if (needsToken && !this.getResponseHeader(CSRF_CONFIG.HEADER_NAME)) {
        this.setRequestHeader(CSRF_CONFIG.HEADER_NAME, csrfProtection.getToken());
      }

      return originalSend.call(this, body);
    };
  }

  /**
   * Protect all forms on the page
   */
  public protectForms(): void {
    const forms = document.querySelectorAll('form');

    forms.forEach(form => {
      // Check if form already has CSRF token
      if (form.querySelector(`input[name="_csrf"]`)) {
        return;
      }

      // Create hidden input for CSRF token
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = '_csrf';
      input.value = this.getToken();

      form.appendChild(input);
    });
  }

  /**
   * Initialize all CSRF protections
   */
  public initialize(): void {
    this.setupFetchInterceptor();
    this.setupXHRInterceptor();

    // Protect forms when DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        this.protectForms();
      });
    } else {
      this.protectForms();
    }

    // Protect dynamically added forms
    const observer = new MutationObserver((mutations) => {
      mutations.forEach(mutation => {
        mutation.addedNodes.forEach(node => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            const element = node as Element;
            if (element.tagName === 'FORM') {
              this.protectSingleForm(element);
            } else {
              // Check for forms within added elements
              const forms = element.querySelectorAll('form');
              forms.forEach(form => this.protectSingleForm(form));
            }
          }
        });
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  /**
   * Protect a single form
   */
  private protectSingleForm(form: HTMLFormElement): void {
    if (form.querySelector(`input[name="_csrf"]`)) {
      return;
    }

    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = '_csrf';
    input.value = this.getToken();

    form.appendChild(input);
  }

  /**
   * Cleanup resources
   */
  public destroy(): void {
    if (this.rotationTimer) {
      clearInterval(this.rotationTimer);
      this.rotationTimer = null;
    }
  }
}

// Export singleton instance
export const csrfProtection = CSRFProtection.getInstance();

// Convenience functions
export const getCSRFToken = (): string => csrfProtection.getToken();
export const validateCSRFToken = (token: string): boolean => csrfProtection.validateToken(token);
export const fetchWithCSRF = (url: string, options?: RequestInit): Promise<Response> =>
  csrfProtection.fetchWithCSRF(url, options);