/**
 * Content Security Policy (CSP) Configuration
 * Provides dynamic CSP management for the CBSC Dashboard
 */

// CSP directive configuration
interface CSPConfig {
  'default-src'?: string[];
  'script-src'?: string[];
  'style-src'?: string[];
  'img-src'?: string[];
  'font-src'?: string[];
  'connect-src'?: string[];
  'media-src'?: string[];
  'object-src'?: string[];
  'child-src'?: string[];
  'frame-src'?: string[];
  'worker-src'?: string[];
  'manifest-src'?: string[];
  'base-uri'?: string[];
  'form-action'?: string[];
  'frame-ancestors'?: string[];
  'report-to'?: string[];
  'report-uri'?: string[];
  'upgrade-insecure-requests'?: boolean;
  'block-all-mixed-content'?: boolean;
  'require-trusted-types-for'?: string[];
  'trusted-types'?: string[];
}

// Default CSP configuration for financial applications
const DEFAULT_CSP_CONFIG: CSPConfig = {
  'default-src': ["'self'"],
  'script-src': [
    "'self'",
    "'unsafe-eval'", // Only for development
    "'unsafe-inline'" // Only for development - remove in production
  ],
  'style-src': [
    "'self'",
    "'unsafe-inline'", // Required for CSS-in-JS libraries
    'https://fonts.googleapis.com'
  ],
  'img-src': [
    "'self'",
    'data:',
    'https:',
    'blob:'
  ],
  'font-src': [
    "'self'",
    'https://fonts.gstatic.com',
    'data:'
  ],
  'connect-src': [
    "'self'",
    'wss:',
    'ws:'
  ],
  'media-src': ["'self'"],
  'object-src': ["'none'"],
  'child-src': ["'none'"],
  'frame-src': ["'none'"],
  'worker-src': ["'self'"],
  'manifest-src': ["'self'"],
  'base-uri': ["'self'"],
  'form-action': ["'self'"],
  'frame-ancestors': ["'none'"],
  'upgrade-insecure-requests': true,
  'block-all-mixed-content': true
};

/**
 * CSP Configuration class
 */
export class CSPConfigManager {
  private static instance: CSPConfigManager;
  private config: CSPConfig;
  private reportEndpoint: string | null = null;
  private reportObserver: MutationObserver | null = null;
  private violationLog: CSPViolation[] = [];

  private constructor() {
    this.config = { ...DEFAULT_CSP_CONFIG };
    this.initialize();
  }

  /**
   * Singleton instance getter
   */
  public static getInstance(): CSPConfigManager {
    if (!CSPConfigManager.instance) {
      CSPConfigManager.instance = new CSPConfigManager();
    }
    return CSPConfigManager.instance;
  }

  /**
   * Initialize CSP
   */
  private initialize(): void {
    // Set up CSP violation reporting
    this.setupViolationReporting();

    // Generate and set CSP header
    const policy = this.generatePolicy();
    this.applyCSP(policy);

    // Set up CSP meta tag for browsers that don't support CSP headers
    this.applyCSPMetaTag(policy);
  }

  /**
   * Generate CSP policy string
   */
  private generatePolicy(): string {
    const directives: string[] = [];

    for (const [directive, sources] of Object.entries(this.config)) {
      if (Array.isArray(sources)) {
        directives.push(`${directive} ${sources.join(' ')}`);
      } else if (typeof sources === 'boolean') {
        if (sources) {
          directives.push(directive);
        }
      }
    }

    return directives.join('; ');
  }

  /**
   * Apply CSP via HTTP header (for client-side routing)
   */
  private applyCSP(policy: string): void {
    // Note: In a real application, CSP headers should be set server-side
    // This is for development and testing purposes
    console.info('CSP Policy:', policy);
  }

  /**
   * Apply CSP via meta tag
   */
  private applyCSPMetaTag(policy: string): void {
    // Remove existing CSP meta tags
    const existingMeta = document.querySelectorAll('meta[http-equiv="Content-Security-Policy"]');
    existingMeta.forEach(meta => meta.remove());

    // Add new CSP meta tag
    const meta = document.createElement('meta');
    meta.httpEquiv = 'Content-Security-Policy';
    meta.content = policy;
    document.head.appendChild(meta);
  }

  /**
   * Setup CSP violation reporting
   */
  private setupViolationReporting(): void {
    // Listen for CSP violation reports
    document.addEventListener('securitypolicyviolation', (event) => {
      const violation: CSPViolation = {
        blockedURI: event.blockedURI,
        documentURI: event.documentURI,
        effectiveDirective: event.effectiveDirective,
        originalPolicy: event.originalPolicy,
        referrer: event.referrer,
        sourceFile: event.sourceFile,
        statusCode: event.statusCode,
        violatedDirective: event.violatedDirective,
        timeStamp: event.timeStamp,
        isReportOnly: event.isReportOnly,
        disposition: event.disposition,
        sample: event.sample
      };

      this.logViolation(violation);
      this.reportViolation(violation);
    });

    // Set up CSP report-only meta tag for development
    if (process.env.NODE_ENV === 'development') {
      const reportOnlyMeta = document.createElement('meta');
      reportOnlyMeta.httpEquiv = 'Content-Security-Policy-Report-Only';
      reportOnlyMeta.content = this.generatePolicy();
      document.head.appendChild(reportOnlyMeta);
    }
  }

  /**
   * Log CSP violation
   */
  private logViolation(violation: CSPViolation): void {
    this.violationLog.push(violation);

    // Keep only last 100 violations
    if (this.violationLog.length > 100) {
      this.violationLog.shift();
    }

    console.warn('CSP Violation:', violation);
  }

  /**
   * Report CSP violation to endpoint
   */
  private async reportViolation(violation: CSPViolation): Promise<void> {
    if (!this.reportEndpoint) {
      return;
    }

    try {
      await fetch(this.reportEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          csp_report: {
            'document-uri': violation.documentURI,
            'referrer': violation.referrer,
            'violated-directive': violation.violatedDirective,
            'effective-directive': violation.effectiveDirective,
            'original-policy': violation.originalPolicy,
            'disposition': violation.disposition,
            'blocked-uri': violation.blockedURI,
            'line-number': violation.sourceFile ? violation.lineNumber : null,
            'column-number': violation.sourceFile ? violation.columnNumber : null,
            'source-file': violation.sourceFile,
            'status-code': violation.statusCode,
            'script-sample': violation.sample
          }
        })
      });
    } catch (error) {
      console.error('Failed to report CSP violation:', error);
    }
  }

  /**
   * Update CSP configuration
   */
  public updateConfig(newConfig: Partial<CSPConfig>): void {
    this.config = { ...this.config, ...newConfig };
    const policy = this.generatePolicy();
    this.applyCSP(policy);
    this.applyCSPMetaTag(policy);
  }

  /**
   * Add trusted domain to specific directive
   */
  public addTrustedDomain(directive: keyof CSPConfig, domain: string): void {
    const sources = this.config[directive] as string[] || [];
    if (!sources.includes(domain)) {
      sources.push(domain);
      this.config[directive] = sources;
      this.updateConfig(this.config);
    }
  }

  /**
   * Remove trusted domain from specific directive
   */
  public removeTrustedDomain(directive: keyof CSPConfig, domain: string): void {
    const sources = this.config[directive] as string[] || [];
    const index = sources.indexOf(domain);
    if (index > -1) {
      sources.splice(index, 1);
      this.config[directive] = sources;
      this.updateConfig(this.config);
    }
  }

  /**
   * Enable nonce-based CSP for scripts
   */
  public enableNonceForScripts(): void {
    // Generate random nonce
    const nonce = this.generateNonce();

    // Update script-src directive
    this.config['script-src'] = [
      "'self'",
      `'nonce-${nonce}'`
    ];

    // Apply new policy
    this.updateConfig(this.config);

    // Store nonce for use in script tags
    (window as any).__CSP_NONCE = nonce;
  }

  /**
   * Generate cryptographically secure nonce
   */
  private generateNonce(): string {
    const array = new Uint8Array(16);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }

  /**
   * Get current nonce for inline scripts
   */
  public getNonce(): string {
    return (window as any).__CSP_NONCE || '';
  }

  /**
   * Set CSP violation report endpoint
   */
  public setReportEndpoint(endpoint: string): void {
    this.reportEndpoint = endpoint;

    if (endpoint) {
      this.updateConfig({
        'report-to': 'csp-endpoint',
        'report-uri': endpoint
      });

      // Set up report-to directive
      const reportGroup = document.createElement('meta');
      reportGroup.httpEquiv = 'Report-To';
      reportGroup.content = JSON.stringify({
        'group': 'csp-endpoint',
        'max_age': 10886400,
        'endpoints': [{ 'url': endpoint }]
      });
      document.head.appendChild(reportGroup);
    }
  }

  /**
   * Get CSP violation log
   */
  public getViolationLog(): CSPViolation[] {
    return [...this.violationLog];
  }

  /**
   * Clear CSP violation log
   */
  public clearViolationLog(): void {
    this.violationLog = [];
  }

  /**
   * Get CSP statistics
   */
  public getStatistics(): CSPStatistics {
    const stats: CSPStatistics = {
      totalViolations: this.violationLog.length,
      violationsByDirective: {},
      violationsByURI: {},
      recentViolations: this.violationLog.slice(-10)
    };

    this.violationLog.forEach(violation => {
      stats.violationsByDirective[violation.violatedDirective] =
        (stats.violationsByDirective[violation.violatedDirective] || 0) + 1;

      stats.violationsByURI[violation.blockedURI] =
        (stats.violationsByURI[violation.blockedURI] || 0) + 1;
    });

    return stats;
  }

  /**
   * Enable strict CSP for production
   */
  public enableStrictMode(): void {
    this.config = {
      'default-src': ["'self'"],
      'script-src': ["'self'"],
      'style-src': ["'self'", 'https://fonts.googleapis.com'],
      'img-src': ["'self'", 'data:', 'https:'],
      'font-src': ["'self'", 'https://fonts.gstatic.com'],
      'connect-src': ["'self'"],
      'media-src': ["'self'"],
      'object-src': ["'none'"],
      'child-src': ["'none'"],
      'frame-src': ["'none'"],
      'worker-src': ["'self'"],
      'manifest-src': ["'self'"],
      'base-uri': ["'self'"],
      'form-action': ["'self'"],
      'frame-ancestors': ["'none'"],
      'upgrade-insecure-requests': true,
      'block-all-mixed-content': true
    };

    this.updateConfig(this.config);
  }
}

// Type definitions
export interface CSPViolation {
  blockedURI: string;
  documentURI: string;
  effectiveDirective: string;
  originalPolicy: string;
  referrer: string;
  sourceFile: string | null;
  statusCode: number | null;
  violatedDirective: string;
  timeStamp: number;
  isReportOnly: boolean;
  disposition: string;
  sample: string;
  lineNumber?: number;
  columnNumber?: number;
}

export interface CSPStatistics {
  totalViolations: number;
  violationsByDirective: { [directive: string]: number };
  violationsByURI: { [uri: string]: number };
  recentViolations: CSPViolation[];
}

// Export singleton instance
export const cspConfig = CSPConfigManager.getInstance();

// Convenience functions
export const updateCSPConfig = (config: Partial<CSPConfig>): void =>
  cspConfig.updateConfig(config);
export const addCSPTrustedDomain = (directive: keyof CSPConfig, domain: string): void =>
  cspConfig.addTrustedDomain(directive, domain);
export const getCSPNonce = (): string => cspConfig.getNonce();
export const enableCSPStrictMode = (): void => cspConfig.enableStrictMode();