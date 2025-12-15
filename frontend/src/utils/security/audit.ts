/**
 * Security Audit Utilities
 * Provides comprehensive security auditing for the CBSC Dashboard
 */

import { xssProtection } from './xss';
import { cspConfig, CSPViolation } from './csp';

// Security audit configuration
interface AuditConfig {
  enabledChecks: {
    xss: boolean;
    csp: boolean;
    dependencies: boolean;
    localStorage: boolean;
    sessionStorage: boolean;
    cookies: boolean;
    networkRequests: boolean;
    consoleLogs: boolean;
    domManipulation: boolean;
    errorHandling: boolean;
  };
  auditInterval: number;
  maxLogSize: number;
  reportEndpoint?: string;
}

// Default audit configuration
const DEFAULT_AUDIT_CONFIG: AuditConfig = {
  enabledChecks: {
    xss: true,
    csp: true,
    dependencies: true,
    localStorage: true,
    sessionStorage: true,
    cookies: true,
    networkRequests: true,
    consoleLogs: true,
    domManipulation: true,
    errorHandling: true
  },
  auditInterval: 60000, // 1 minute
  maxLogSize: 1000
};

/**
 * Security audit result
 */
export interface AuditResult {
  timestamp: number;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  details: any;
  recommendation?: string;
}

/**
 * Security statistics
 */
export interface SecurityStatistics {
  overallScore: number;
  auditResults: AuditResult[];
  vulnerabilities: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  recommendations: string[];
  lastAudit: number;
}

/**
 * Security Audit class
 */
export class SecurityAudit {
  private static instance: SecurityAudit;
  private config: AuditConfig;
  private auditLog: AuditResult[] = [];
  private auditTimer: NodeJS.Timeout | null = null;
  private observers: MutationObserver[] = [];
  private originalConsole: Console;
  private networkRequests: any[] = [];

  private constructor() {
    this.config = { ...DEFAULT_AUDIT_CONFIG };
    this.originalConsole = { ...console };
    this.initialize();
  }

  /**
   * Singleton instance getter
   */
  public static getInstance(): SecurityAudit {
    if (!SecurityAudit.instance) {
      SecurityAudit.instance = new SecurityAudit();
    }
    return SecurityAudit.instance;
  }

  /**
   * Initialize security audit
   */
  private initialize(): void {
    // Set up monitoring if checks are enabled
    if (this.config.enabledChecks.domManipulation) {
      this.setupDOMObserver();
    }

    if (this.config.enabledChecks.networkRequests) {
      this.setupNetworkObserver();
    }

    if (this.config.enabledChecks.consoleLogs) {
      this.setupConsoleObserver();
    }

    // Start periodic audit
    this.startAuditTimer();

    // Run initial audit
    this.runFullAudit();
  }

  /**
   * Set up DOM manipulation observer
   */
  private setupDOMObserver(): void {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach(mutation => {
        if (mutation.type === 'childList') {
          mutation.addedNodes.forEach(node => {
            if (node.nodeType === Node.ELEMENT_NODE) {
              const element = node as Element;
              this.checkElementSecurity(element);
            }
          });
        }
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    this.observers.push(observer);
  }

  /**
   * Check element for security issues
   */
  private checkElementSecurity(element: Element): void {
    // Check for inline scripts
    if (element.tagName === 'SCRIPT') {
      const src = element.getAttribute('src');
      const content = element.textContent;

      if (src && !this.isTrustedSource(src)) {
        this.logResult('xss', 'high', 'Untrusted script source', { src });
      }

      if (content && xssProtection.containsDangerousPatterns(content)) {
        this.logResult('xss', 'critical', 'Dangerous script content detected', { content });
      }
    }

    // Check for inline event handlers
    Array.from(element.attributes).forEach(attr => {
      if (attr.name.startsWith('on')) {
        this.logResult('xss', 'high', 'Inline event handler detected', {
          element: element.tagName,
          attribute: attr.name,
          value: attr.value
        });
      }
    });

    // Check for dangerous attributes
    const dangerousAttrs = ['href', 'src', 'action', 'formaction'];
    dangerousAttrs.forEach(attr => {
      const value = element.getAttribute(attr);
      if (value && xssProtection.containsDangerousPatterns(value)) {
        this.logResult('xss', 'medium', `Dangerous ${attr} attribute`, {
          element: element.tagName,
          attribute: attr,
          value
        });
      }
    });
  }

  /**
   * Check if source is trusted
   */
  private isTrustedSource(src: string): boolean {
    try {
      const url = new URL(src, window.location.origin);
      return url.hostname === window.location.hostname ||
             url.hostname === 'localhost' ||
             url.hostname.endsWith('.cbsc.com');
    } catch {
      return false;
    }
  }

  /**
   * Set up network request observer
   */
  private setupNetworkObserver(): void {
    const originalFetch = window.fetch;
    const originalXHROpen = XMLHttpRequest.prototype.open;
    const originalXHRSend = XMLHttpRequest.prototype.send;

    // Observe fetch requests
    window.fetch = async (input, init) => {
      const startTime = Date.now();
      const url = typeof input === 'string' ? input : input.url;

      try {
        const response = await originalFetch(input, init);
        this.logNetworkRequest({
          type: 'fetch',
          url,
          method: init?.method || 'GET',
          status: response.status,
          duration: Date.now() - startTime
        });
        return response;
      } catch (error) {
        this.logNetworkRequest({
          type: 'fetch',
          url,
          method: init?.method || 'GET',
          error: error.message,
          duration: Date.now() - startTime
        });
        throw error;
      }
    };

    // Observe XMLHttpRequest
    XMLHttpRequest.prototype.open = function(method: string, url: string | URL) {
      (this as any)._audit = {
        type: 'xhr',
        url: url.toString(),
        method,
        startTime: Date.now()
      };
      return originalXHROpen.call(this, method, url);
    };

    XMLHttpRequest.prototype.send = function(body) {
      const self = this;
      const audit = (self as any)._audit;

      this.addEventListener('loadend', () => {
        if (audit) {
          audit.status = self.status;
          audit.duration = Date.now() - audit.startTime;
          SecurityAudit.getInstance().logNetworkRequest(audit);
        }
      });

      return originalXHRSend.call(this, body);
    };
  }

  /**
   * Log network request
   */
  private logNetworkRequest(request: any): void {
    this.networkRequests.push(request);

    // Keep only last 1000 requests
    if (this.networkRequests.length > 1000) {
      this.networkRequests.shift();
    }

    // Check for suspicious requests
    if (request.url.includes('javascript:') ||
        request.url.includes('data:text/html')) {
      this.logResult('network', 'high', 'Suspicious network request detected', request);
    }
  }

  /**
   * Set up console observer
   */
  private setupConsoleObserver(): void {
    const logLevels = ['log', 'warn', 'error', 'info', 'debug'];

    logLevels.forEach(level => {
      const original = console[level];
      console[level] = (...args: any[]) => {
        original.apply(console, args);

        // Check for sensitive information in logs
        const message = args.join(' ');
        if (this.containsSensitiveData(message)) {
          this.logResult('data', 'medium', 'Sensitive data logged to console', {
            level,
            message: message.substring(0, 100)
          });
        }
      };
    });
  }

  /**
   * Check for sensitive data patterns
   */
  private containsSensitiveData(message: string): boolean {
    const sensitivePatterns = [
      /password/i,
      /token/i,
      /secret/i,
      /api[_-]?key/i,
      /credential/i,
      /authorization/i,
      /bearer/i,
      /\b\d{16}\b/, // Credit card numbers
      /\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b/ // Formatted credit card
    ];

    return sensitivePatterns.some(pattern => pattern.test(message));
  }

  /**
   * Start periodic audit timer
   */
  private startAuditTimer(): void {
    if (this.auditTimer) {
      clearInterval(this.auditTimer);
    }

    this.auditTimer = setInterval(() => {
      this.runPeriodicAudit();
    }, this.config.auditInterval);
  }

  /**
   * Run full security audit
   */
  public runFullAudit(): void {
    if (this.config.enabledChecks.xss) {
      this.auditXSS();
    }

    if (this.config.enabledChecks.csp) {
      this.auditCSP();
    }

    if (this.config.enabledChecks.dependencies) {
      this.auditDependencies();
    }

    if (this.config.enabledChecks.localStorage) {
      this.auditLocalStorage();
    }

    if (this.config.enabledChecks.sessionStorage) {
      this.auditSessionStorage();
    }

    if (this.config.enabledChecks.cookies) {
      this.auditCookies();
    }

    if (this.config.enabledChecks.errorHandling) {
      this.auditErrorHandling();
    }

    this.generateSecurityReport();
  }

  /**
   * Run periodic audit checks
   */
  private runPeriodicAudit(): void {
    // Check for new vulnerabilities
    this.auditRecentActivity();

    // Check memory usage
    this.auditMemoryUsage();

    // Check performance impact
    this.auditPerformance();
  }

  /**
   * Audit XSS vulnerabilities
   */
  private auditXSS(): void {
    // Check for dangerous patterns in scripts
    const scripts = document.querySelectorAll('script');
    scripts.forEach(script => {
      if (script.textContent) {
        if (xssProtection.containsDangerousPatterns(script.textContent)) {
          this.logResult('xss', 'critical', 'Dangerous script content found', {
            element: 'script',
            content: script.textContent.substring(0, 100)
          });
        }
      }
    });

    // Check for unsafe eval usage
    const evalPattern = /eval\s*\(|Function\s*\(|setTimeout\s*\(\s*["']/;
    if (evalPattern.test(document.body.innerHTML)) {
      this.logResult('xss', 'high', 'Unsafe dynamic code execution detected', {
        pattern: 'eval/Function/setTimeout with string'
      });
    }
  }

  /**
   * Audit CSP violations
   */
  private auditCSP(): void {
    const violations = cspConfig.getViolationLog();
    const recentViolations = violations.filter(v =>
      Date.now() - v.timeStamp < 60000 // Last minute
    );

    if (recentViolations.length > 0) {
      this.logResult('csp', 'medium', 'CSP violations detected', {
        count: recentViolations.length,
        violations: recentViolations.slice(0, 5)
      });
    }
  }

  /**
   * Audit dependencies for known vulnerabilities
   */
  private auditDependencies(): void {
    // Check package.json if available
    const packageJson = (window as any).__PACKAGE_JSON__;
    if (packageJson) {
      // This would typically be done server-side
      // For client-side, we check for known vulnerable versions
      this.checkVulnerableDependencies(packageJson);
    }
  }

  /**
   * Check for vulnerable dependencies
   */
  private checkVulnerableDependencies(packageJson: any): void {
    // Known vulnerable package patterns
    const vulnerablePackages = [
      { name: 'lodash', vulnerableVersions: '<4.17.21' },
      { name: 'axios', vulnerableVersions: '<0.21.1' },
      { name: 'react', vulnerableVersions: '<16.13.0' },
      { name: 'react-dom', vulnerableVersions: '<16.13.0' }
    ];

    Object.entries(packageJson.dependencies || {}).forEach(([name, version]: [string, any]) => {
      const vulnerable = vulnerablePackages.find(pkg => pkg.name === name);
      if (vulnerable) {
        this.logResult('dependency', 'high', `Vulnerable dependency detected`, {
          name,
          version,
          recommendation: `Update to latest version`
        });
      }
    });
  }

  /**
   * Audit localStorage usage
   */
  private auditLocalStorage(): void {
    try {
      const keys = Object.keys(localStorage);
      let sensitiveCount = 0;

      keys.forEach(key => {
        const value = localStorage.getItem(key);
        if (value && this.containsSensitiveData(value)) {
          sensitiveCount++;
        }
      });

      if (sensitiveCount > 0) {
        this.logResult('storage', 'medium', 'Sensitive data stored in localStorage', {
          sensitiveItems: sensitiveCount,
          totalItems: keys.length
        });
      }
    } catch (error) {
      this.logResult('storage', 'low', 'localStorage access error', { error: error.message });
    }
  }

  /**
   * Audit sessionStorage usage
   */
  private auditSessionStorage(): void {
    try {
      const keys = Object.keys(sessionStorage);
      let sensitiveCount = 0;

      keys.forEach(key => {
        const value = sessionStorage.getItem(key);
        if (value && this.containsSensitiveData(value)) {
          sensitiveCount++;
        }
      });

      if (sensitiveCount > 0) {
        this.logResult('storage', 'medium', 'Sensitive data stored in sessionStorage', {
          sensitiveItems: sensitiveCount,
          totalItems: keys.length
        });
      }
    } catch (error) {
      this.logResult('storage', 'low', 'sessionStorage access error', { error: error.message });
    }
  }

  /**
   * Audit cookies
   */
  private auditCookies(): void {
    const cookies = document.cookie.split(';');
    let insecureCount = 0;

    cookies.forEach(cookie => {
      const [name] = cookie.trim().split('=');
      if (!name.startsWith('__Host-') && !name.startsWith('__Secure-')) {
        insecureCount++;
      }
    });

    if (insecureCount > 0) {
      this.logResult('storage', 'medium', 'Insecure cookies detected', {
        insecureCount,
        totalCookies: cookies.length
      });
    }
  }

  /**
   * Audit error handling
   */
  private auditErrorHandling(): void {
    // Check for global error handlers
    if (!window.onerror && !window.addEventListener('error')) {
      this.logResult('error', 'medium', 'Missing global error handler', {
        recommendation: 'Implement global error handling'
      });
    }

    if (!window.onunhandledrejection) {
      this.logResult('error', 'medium', 'Missing unhandled promise rejection handler', {
        recommendation: 'Implement unhandled rejection handling'
      });
    }
  }

  /**
   * Audit recent activity
   */
  private auditRecentActivity(): void {
    const recentResults = this.auditLog.filter(r =>
      Date.now() - r.timestamp < 300000 // Last 5 minutes
    );

    if (recentResults.length > 10) {
      this.logResult('activity', 'medium', 'High security alert volume', {
        count: recentResults.length,
        timeframe: '5 minutes'
      });
    }
  }

  /**
   * Audit memory usage
   */
  private auditMemoryUsage(): void {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      const usedMB = Math.round(memory.usedJSHeapSize / 1048576);

      if (usedMB > 100) { // 100MB threshold
        this.logResult('performance', 'low', 'High memory usage detected', {
          usedMB,
          recommendation: 'Consider memory optimization'
        });
      }
    }
  }

  /**
   * Audit performance
   */
  private auditPerformance(): void {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    const loadTime = navigation.loadEventEnd - navigation.loadEventStart;

    if (loadTime > 3000) { // 3 seconds
      this.logResult('performance', 'low', 'Slow page load detected', {
        loadTime: Math.round(loadTime),
        recommendation: 'Optimize page load performance'
      });
    }
  }

  /**
   * Log audit result
   */
  private logResult(type: string, severity: 'low' | 'medium' | 'high' | 'critical',
                   message: string, details?: any, recommendation?: string): void {
    const result: AuditResult = {
      timestamp: Date.now(),
      type,
      severity,
      message,
      details,
      recommendation
    };

    this.auditLog.push(result);

    // Keep log size within limit
    if (this.auditLog.length > this.config.maxLogSize) {
      this.auditLog.shift();
    }
  }

  /**
   * Generate security report
   */
  public generateSecurityReport(): SecurityStatistics {
    const vulnerabilities = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0
    };

    const recommendations = new Set<string>();

    this.auditLog.forEach(result => {
      vulnerabilities[result.severity]++;
      if (result.recommendation) {
        recommendations.add(result.recommendation);
      }
    });

    // Calculate security score (0-100)
    const weights = { critical: 25, high: 10, medium: 5, low: 1 };
    const deduction = vulnerabilities.critical * weights.critical +
                      vulnerabilities.high * weights.high +
                      vulnerabilities.medium * weights.medium +
                      vulnerabilities.low * weights.low;

    const overallScore = Math.max(0, 100 - deduction);

    return {
      overallScore,
      auditResults: [...this.auditLog],
      vulnerabilities,
      recommendations: Array.from(recommendations),
      lastAudit: Date.now()
    };
  }

  /**
   * Get audit configuration
   */
  public getConfig(): AuditConfig {
    return { ...this.config };
  }

  /**
   * Update audit configuration
   */
  public updateConfig(newConfig: Partial<AuditConfig>): void {
    this.config = { ...this.config, ...newConfig };
    this.initialize();
  }

  /**
   * Get audit log
   */
  public getAuditLog(): AuditResult[] {
    return [...this.auditLog];
  }

  /**
   * Clear audit log
   */
  public clearAuditLog(): void {
    this.auditLog = [];
  }

  /**
   * Export audit results
   */
  public exportResults(): string {
    const report = this.generateSecurityReport();
    return JSON.stringify(report, null, 2);
  }

  /**
   * Cleanup resources
   */
  public destroy(): void {
    if (this.auditTimer) {
      clearInterval(this.auditTimer);
      this.auditTimer = null;
    }

    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];

    // Restore original console
    Object.keys(this.originalConsole).forEach(key => {
      console[key] = this.originalConsole[key];
    });
  }
}

// Export singleton instance
export const securityAudit = SecurityAudit.getInstance();

// Convenience functions
export const runSecurityAudit = (): void => securityAudit.runFullAudit();
export const getSecurityReport = (): SecurityStatistics => securityAudit.generateSecurityReport();
export const updateAuditConfig = (config: Partial<AuditConfig>): void =>
  securityAudit.updateConfig(config);