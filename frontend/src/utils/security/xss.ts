/**
 * XSS Protection Utilities
 * Provides comprehensive XSS protection for the CBSC Dashboard
 */

import DOMPurify from 'dompurify';

// Default DOMPurify configuration for financial applications
const DEFAULT_CONFIG = {
  ALLOWED_TAGS: [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'strong', 'em', 'u', 'i', 'b',
    'ul', 'ol', 'li',
    'table', 'thead', 'tbody', 'tr', 'td', 'th',
    'div', 'span', 'section', 'article',
    'a', 'img',
    'code', 'pre',
    'blockquote'
  ],
  ALLOWED_ATTR: [
    'href', 'title', 'alt', 'src', 'class', 'id',
    'data-*', 'aria-*', 'role'
  ],
  ALLOW_DATA_ATTR: true,
  FORBID_ATTR: ['onclick', 'onload', 'onerror', 'onmouseover'],
  FORBID_TAGS: ['script', 'object', 'embed', 'iframe', 'form', 'input'],
  RETURN_DOM: true,
  RETURN_DOM_FRAGMENT: true,
  RETURN_DOM_IMPORT: true,
  SANITIZE_DOM: true,
  SAFE_FOR_TEMPLATES: true,
  WHOLE_DOCUMENT: true,
  CUSTOM_ELEMENT_HANDLING: {
    tagNameCheck: null,
    attributeNameCheck: null,
    allowCustomizedBuiltInElements: false
  }
};

/**
 * XSS Protection class providing multiple layers of defense
 */
export class XSSProtection {
  private static instance: XSSProtection;
  private purifyConfig: any;
  private urlWhitelist: Set<string>;
  private suspiciousPatterns: RegExp[];

  private constructor() {
    this.purifyConfig = { ...DEFAULT_CONFIG };
    this.urlWhitelist = new Set([
      'https://cbsc.com',
      'https://api.cbsc.com',
      'https://cdn.cbsc.com',
      'https://fonts.googleapis.com',
      'https://fonts.gstatic.com'
    ]);
    this.suspiciousPatterns = [
      /javascript:/gi,
      /data:text\/html/gi,
      /vbscript:/gi,
      /on\w+\s*=/gi,
      /expression\s*\(/gi,
      /@import/gi,
      /binding\s*:/gi
    ];
  }

  /**
   * Singleton instance getter
   */
  public static getInstance(): XSSProtection {
    if (!XSSProtection.instance) {
      XSSProtection.instance = new XSSProtection();
    }
    return XSSProtection.instance;
  }

  /**
   * Sanitize HTML content
   */
  public sanitizeHTML(dirty: string): string {
    if (!dirty || typeof dirty !== 'string') {
      return '';
    }

    try {
      const clean = DOMPurify.sanitize(dirty, this.purifyConfig);
      return clean;
    } catch (error) {
      console.error('XSS Protection: Failed to sanitize HTML', error);
      return '';
    }
  }

  /**
   * Sanitize and validate URLs
   */
  public sanitizeURL(url: string): string {
    if (!url || typeof url !== 'string') {
      return '';
    }

    try {
      // Decode URL to detect encoded attacks
      const decodedUrl = decodeURIComponent(url);

      // Check for suspicious patterns
      for (const pattern of this.suspiciousPatterns) {
        if (pattern.test(decodedUrl)) {
          console.warn('XSS Protection: Suspicious URL pattern detected', { url, pattern });
          return '';
        }
      }

      // Parse and validate URL
      const parsedUrl = new URL(url);

      // Only allow HTTPS and HTTP
      if (!['https:', 'http:'].includes(parsedUrl.protocol)) {
        return '';
      }

      // Check against whitelist
      const isWhitelisted = Array.from(this.urlWhitelist).some(domain =>
        parsedUrl.hostname === domain || parsedUrl.hostname.endsWith(`.${domain}`)
      );

      if (!isWhitelisted) {
        console.warn('XSS Protection: URL not in whitelist', { url, domain: parsedUrl.hostname });
        return '';
      }

      return url;
    } catch (error) {
      console.error('XSS Protection: Invalid URL', { url, error });
      return '';
    }
  }

  /**
   * Safely parse JSON with protection against prototype pollution
   */
  public safeJSONParse<T = any>(json: string, fallback?: T): T | null {
    if (!json || typeof json !== 'string') {
      return fallback || null;
    }

    try {
      // Remove potential XSS vectors
      const sanitized = json.replace(/[\u0000-\u001F\u007F-\u009F]/g, '');

      // Parse with protection
      const parsed = JSON.parse(sanitized);

      // Check for prototype pollution
      if (this.hasPrototypePollution(parsed)) {
        console.error('XSS Protection: Prototype pollution detected');
        return fallback || null;
      }

      return parsed;
    } catch (error) {
      console.error('XSS Protection: Failed to parse JSON', error);
      return fallback || null;
    }
  }

  /**
   * Sanitize user input for display
   */
  public sanitizeInput(input: string): string {
    if (!input || typeof input !== 'string') {
      return '';
    }

    // HTML entity encoding
    const entityMap: { [key: string]: string } = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#x27;',
      '/': '&#x2F;'
    };

    return input.replace(/[&<>"'/]/g, (s) => entityMap[s]);
  }

  /**
   * Validate and sanitize CSS values
   */
  public sanitizeCSS(value: string): string {
    if (!value || typeof value !== 'string') {
      return '';
    }

    // Remove dangerous CSS constructs
    const sanitized = value
      .replace(/javascript:/gi, '')
      .replace(/expression\s*\(/gi, '')
      .replace(/@import/gi, '')
      .replace(/binding\s*:/gi, '')
      .replace(/behavior\s*:/gi, '')
      .replace(/url\s*\(\s*['"]*javascript:/gi, '')
      .replace(/url\s*\(\s*['"]*data:/gi, '');

    return sanitized.trim();
  }

  /**
   * Check for dangerous DOM patterns
   */
  public containsDangerousPatterns(content: string): boolean {
    if (!content || typeof content !== 'string') {
      return false;
    }

    const dangerousPatterns = [
      /<script[^>]*>.*?<\/script>/gi,
      /<iframe[^>]*>.*?<\/iframe>/gi,
      /<object[^>]*>.*?<\/object>/gi,
      /<embed[^>]*>/gi,
      /<link[^>]*stylesheet/gi,
      /@import/gi,
      /javascript:/gi,
      /vbscript:/gi,
      /on\w+\s*=/gi,
      /expression\s*\(/gi
    ];

    return dangerousPatterns.some(pattern => pattern.test(content));
  }

  /**
   * Configure custom sanitization rules
   */
  public configure(config: Partial<typeof DEFAULT_CONFIG>): void {
    this.purifyConfig = { ...this.purifyConfig, ...config };
  }

  /**
   * Add URL to whitelist
   */
  public addToWhitelist(domain: string): void {
    this.urlWhitelist.add(domain);
  }

  /**
   * Remove URL from whitelist
   */
  public removeFromWhitelist(domain: string): void {
    this.urlWhitelist.delete(domain);
  }

  /**
   * Get current whitelist
   */
  public getWhitelist(): string[] {
    return Array.from(this.urlWhitelist);
  }

  /**
   * Check for prototype pollution in parsed object
   */
  private hasPrototypePollution(obj: any): boolean {
    if (typeof obj !== 'object' || obj === null) {
      return false;
    }

    // Check __proto__ property
    if (obj.hasOwnProperty('__proto__')) {
      return true;
    }

    // Check prototype property
    if (obj.hasOwnProperty('prototype')) {
      return true;
    }

    // Check constructor property
    if (obj.hasOwnProperty('constructor')) {
      return true;
    }

    // Recursively check nested objects
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        if (this.hasPrototypePollution(obj[key])) {
          return true;
        }
      }
    }

    return false;
  }
}

// Export singleton instance
export const xssProtection = XSSProtection.getInstance();

// Convenience functions
export const sanitizeHTML = (html: string): string => xssProtection.sanitizeHTML(html);
export const sanitizeURL = (url: string): string => xssProtection.sanitizeURL(url);
export const safeJSONParse = <T = any>(json: string, fallback?: T): T | null =>
  xssProtection.safeJSONParse<T>(json, fallback);
export const sanitizeInput = (input: string): string => xssProtection.sanitizeInput(input);
export const sanitizeCSS = (css: string): string => xssProtection.sanitizeCSS(css);
export const containsDangerousPatterns = (content: string): boolean =>
  xssProtection.containsDangerousPatterns(content);