/**
 * Security Utilities Index
 * Central export for all security-related utilities
 */

// XSS Protection
export {
  XSSProtection,
  xssProtection,
  sanitizeHTML,
  sanitizeURL,
  safeJSONParse,
  sanitizeInput,
  sanitizeCSS,
  containsDangerousPatterns
} from './xss';

// CSRF Protection
export {
  CSRFProtection,
  csrfProtection,
  getCSRFToken,
  validateCSRFToken,
  fetchWithCSRF
} from './csrf';

// CSP Configuration
export {
  CSPConfigManager,
  cspConfig,
  updateCSPConfig,
  addCSPTrustedDomain,
  getCSPNonce,
  enableCSPStrictMode,
  type CSPConfig,
  type CSPViolation,
  type CSPStatistics
} from './csp';

// Security Audit
export {
  SecurityAudit,
  securityAudit,
  runSecurityAudit,
  getSecurityReport,
  updateAuditConfig,
  type AuditResult,
  type SecurityStatistics
} from './audit';

// Input Validation
export {
  InputValidator,
  inputValidator,
  validateInput,
  validateSecure,
  validateFinancial,
  VALIDATION_PATTERNS,
  USER_SCHEMA,
  STRATEGY_SCHEMA,
  type ValidationRule,
  type ValidationSchema
} from './validation';

// Encryption
export {
  EncryptionUtil,
  encryption,
  encrypt,
  decrypt,
  encryptObject,
  decryptObject,
  secureHash,
  generateToken
} from './encryption';

/**
 * Security Manager class to coordinate all security features
 */
export class SecurityManager {
  private static instance: SecurityManager;
  private initialized = false;

  private constructor() {}

  public static getInstance(): SecurityManager {
    if (!SecurityManager.instance) {
      SecurityManager.instance = new SecurityManager();
    }
    return SecurityManager.instance;
  }

  /**
   * Initialize all security features
   */
  public async initialize(): Promise<void> {
    if (this.initialized) {
      return;
    }

    try {
      // Initialize CSRF protection
      csrfProtection.initialize();

      // Initialize CSP
      cspConfig.setReportEndpoint('/api/security/csp-report');

      // Initialize encryption
      await encryption.initialize();

      // Run initial security audit
      securityAudit.runFullAudit();

      // Set up global error handling for security
      this.setupGlobalSecurityHandlers();

      this.initialized = true;
      console.info('Security Manager initialized successfully');
    } catch (error) {
      console.error('Security Manager initialization failed:', error);
      throw error;
    }
  }

  /**
   * Enable production security mode
   */
  public enableProductionMode(): void {
    // Enable strict CSP
    cspConfig.enableStrictMode();

    // Update audit config for production
    securityAudit.updateConfig({
      enabledChecks: {
        xss: true,
        csp: true,
        dependencies: true,
        localStorage: true,
        sessionStorage: true,
        cookies: true,
        networkRequests: true,
        consoleLogs: false, // Disable in production
        domManipulation: true,
        errorHandling: true
      }
    });

    console.info('Security Manager: Production mode enabled');
  }

  /**
   * Enable development mode
   */
  public enableDevelopmentMode(): void {
    // Allow more permissive CSP for development
    cspConfig.updateConfig({
      'script-src': [
        "'self'",
        "'unsafe-eval'",
        "'unsafe-inline'",
        'http://localhost:*',
        'ws://localhost:*'
      ],
      'connect-src': [
        "'self'",
        'http://localhost:*',
        'ws://localhost:*',
        'wss://localhost:*'
      ]
    });

    // Add development domains to whitelist
    cspConfig.addTrustedDomain('script-src', 'http://localhost');
    cspConfig.addTrustedDomain('connect-src', 'http://localhost');

    console.info('Security Manager: Development mode enabled');
  }

  /**
   * Get comprehensive security status
   */
  public getSecurityStatus(): {
    initialized: boolean;
    cspStatistics: any;
    auditReport: any;
    csrfToken: string;
    encryptionStatus: boolean;
  } {
    return {
      initialized: this.initialized,
      cspStatistics: cspConfig.getStatistics(),
      auditReport: securityAudit.generateSecurityReport(),
      csrfToken: csrfProtection.getToken(),
      encryptionStatus: !!encryption.getKey()
    };
  }

  /**
   * Perform security health check
   */
  public async performHealthCheck(): Promise<{
    status: 'healthy' | 'warning' | 'critical';
    checks: Array<{
      name: string;
      status: 'pass' | 'fail' | 'warning';
      message: string;
    }>;
  }> {
    const checks = [];
    let hasFailures = false;
    let hasWarnings = false;

    // Check CSP
    const cspStats = cspConfig.getStatistics();
    checks.push({
      name: 'CSP Status',
      status: cspStats.totalViolations === 0 ? 'pass' :
               cspStats.totalViolations < 10 ? 'warning' : 'fail',
      message: `${cspStats.totalViolations} CSP violations detected`
    });
    if (cspStats.totalViolations > 0) hasWarnings = true;
    if (cspStats.totalViolations > 10) hasFailures = true;

    // Check security audit
    const auditReport = securityAudit.generateSecurityReport();
    checks.push({
      name: 'Security Audit',
      status: auditReport.overallScore >= 90 ? 'pass' :
               auditReport.overallScore >= 70 ? 'warning' : 'fail',
      message: `Security score: ${auditReport.overallScore}/100`
    });
    if (auditReport.overallScore < 90) hasWarnings = true;
    if (auditReport.overallScore < 70) hasFailures = true;

    // Check CSRF token
    const token = csrfProtection.getToken();
    checks.push({
      name: 'CSRF Protection',
      status: token ? 'pass' : 'fail',
      message: token ? 'CSRF token active' : 'CSRF token missing'
    });
    if (!token) hasFailures = true;

    // Check encryption
    const encKey = encryption.getKey();
    checks.push({
      name: 'Encryption',
      status: encKey ? 'pass' : 'fail',
      message: encKey ? 'Encryption initialized' : 'Encryption not initialized'
    });
    if (!encKey) hasFailures = true;

    // Determine overall status
    const status = hasFailures ? 'critical' : hasWarnings ? 'warning' : 'healthy';

    return { status, checks };
  }

  /**
   * Setup global security handlers
   */
  private setupGlobalSecurityHandlers(): void {
    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      console.error('Unhandled promise rejection:', event.reason);
      securityAudit.runFullAudit();
    });

    // Handle global errors
    window.addEventListener('error', (event) => {
      console.error('Global error:', event.error);
      // Run security audit on errors
      if (event.error && event.error.message) {
        securityAudit.runFullAudit();
      }
    });

    // Clear sensitive data on page unload
    window.addEventListener('beforeunload', () => {
      encryption.wipe();
    });
  }

  /**
   * Cleanup and destroy all security features
   */
  public destroy(): void {
    securityAudit.destroy();
    csrfProtection.destroy();
    encryption.wipe();
    this.initialized = false;
  }
}

// Export singleton instance
export const securityManager = SecurityManager.getInstance();

// Export initialization function
export const initializeSecurity = async (): Promise<void> => {
  await securityManager.initialize();
};