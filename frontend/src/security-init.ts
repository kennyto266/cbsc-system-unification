/**
 * Security Initialization
 * Initializes all security features when the application starts
 */

import { securityManager } from './utils/security';

/**
 * Initialize security features
 */
export const initializeSecurity = async () => {
  try {
    console.info('Initializing security features...');

    // Initialize the security manager
    await securityManager.initialize();

    // Set up global error handlers
    setupGlobalErrorHandlers();

    // Set up security event listeners
    setupSecurityEventListeners();

    // Perform initial security audit
    await performInitialAudit();

    console.info('Security features initialized successfully');
    return true;
  } catch (error) {
    console.error('Failed to initialize security features:', error);
    return false;
  }
};

/**
 * Setup global error handlers
 */
const setupGlobalErrorHandlers = () => {
  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);

    // Log security event if it appears to be a security-related error
    if (isSecurityError(event.reason)) {
      logSecurityEvent('unhandled_rejection', event.reason);
    }
  });

  // Handle global errors
  window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);

    // Log security event if it appears to be a security-related error
    if (isSecurityError(event.error)) {
      logSecurityEvent('global_error', event.error);
    }
  });
};

/**
 * Check if error is security-related
 */
const isSecurityError = (error: any): boolean => {
  if (!error) return false;

  const errorString = error.toString().toLowerCase();
  const securityKeywords = [
    'csrf',
    'xss',
    'csp',
    'security',
    'unauthorized',
    'forbidden',
    'unsafe',
    'injection',
    'validation'
  ];

  return securityKeywords.some(keyword => errorString.includes(keyword));
};

/**
 * Log security event
 */
const logSecurityEvent = (type: string, details: any) => {
  const securityEvent = {
    timestamp: Date.now(),
    type,
    url: window.location.href,
    userAgent: navigator.userAgent,
    details: details instanceof Error ? {
      message: details.message,
      stack: details.stack
    } : details
  };

  // Store in sessionStorage for debugging
  try {
    const existingEvents = JSON.parse(sessionStorage.getItem('security_events') || '[]');
    existingEvents.push(securityEvent);

    // Keep only last 100 events
    if (existingEvents.length > 100) {
      existingEvents.shift();
    }

    sessionStorage.setItem('security_events', JSON.stringify(existingEvents));
  } catch (error) {
    console.warn('Failed to store security event:', error);
  }
};

/**
 * Setup security event listeners
 */
const setupSecurityEventListeners = () => {
  // Monitor for CSP violations
  document.addEventListener('securitypolicyviolation', (event) => {
    console.warn('CSP Violation:', event);
    logSecurityEvent('csp_violation', {
      blockedURI: event.blockedURI,
      violatedDirective: event.violatedDirective,
      originalPolicy: event.originalPolicy
    });
  });

  // Monitor for console warnings (development only)
  if (process.env.NODE_ENV === 'development') {
    const originalWarn = console.warn;
    console.warn = (...args: any[]) => {
      originalWarn.apply(console, args);

      // Check for security-related warnings
      const message = args.join(' ');
      if (isSecurityError(message)) {
        logSecurityEvent('security_warning', { message });
      }
    };
  }

  // Monitor for DOM mutations that might be XSS attempts
  if (typeof MutationObserver !== 'undefined') {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach(mutation => {
        if (mutation.type === 'childList') {
          mutation.addedNodes.forEach(node => {
            if (node.nodeType === Node.ELEMENT_NODE) {
              const element = node as Element;

              // Check for suspicious elements
              if (element.tagName === 'SCRIPT') {
                const src = element.getAttribute('src');
                const content = element.textContent;

                if (src && !isTrustedSource(src)) {
                  logSecurityEvent('suspicious_script', { src });
                }

                if (content && containsSuspiciousContent(content)) {
                  logSecurityEvent('suspicious_script_content', {
                    content: content.substring(0, 200)
                  });
                }
              }
            }
          });
        }
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }
};

/**
 * Check if source is trusted
 */
const isTrustedSource = (src: string): boolean => {
  try {
    const url = new URL(src, window.location.origin);
    const trustedDomains = [
      window.location.hostname,
      'localhost',
      'cbsc.com',
      'api.cbsc.com',
      'cdn.cbsc.com',
      'fonts.googleapis.com',
      'fonts.gstatic.com'
    ];

    return trustedDomains.some(domain =>
      url.hostname === domain || url.hostname.endsWith(`.${domain}`)
    );
  } catch {
    return false;
  }
};

/**
 * Check if content contains suspicious patterns
 */
const containsSuspiciousContent = (content: string): boolean => {
  const suspiciousPatterns = [
    /eval\s*\(/gi,
    /Function\s*\(/gi,
    /document\.write/gi,
    /innerHTML\s*=/gi,
    /outerHTML\s*=/gi,
    /insertAdjacentHTML/gi,
    /javascript:/gi,
    /on\w+\s*=/gi
  ];

  return suspiciousPatterns.some(pattern => pattern.test(content));
};

/**
 * Perform initial security audit
 */
const performInitialAudit = async () => {
  try {
    const { securityAudit } = await import('./utils/security');
    securityAudit.runFullAudit();

    // Log initial audit results
    const report = securityAudit.generateSecurityReport();
    console.info('Initial security audit completed:', {
      score: report.overallScore,
      vulnerabilities: report.vulnerabilities
    });
  } catch (error) {
    console.error('Failed to perform initial security audit:', error);
  }
};

/**
 * Get security events for debugging
 */
export const getSecurityEvents = () => {
  try {
    return JSON.parse(sessionStorage.getItem('security_events') || '[]');
  } catch {
    return [];
  }
};

/**
 * Clear security events
 */
export const clearSecurityEvents = () => {
  sessionStorage.removeItem('security_events');
};

/**
 * Export security utilities for global access
 */
export const securityUtils = {
  initializeSecurity,
  getSecurityEvents,
  clearSecurityEvents,
  securityManager
};

// Auto-initialize if this module is imported
if (typeof window !== 'undefined') {
  // Add to global scope for debugging
  (window as any).securityUtils = securityUtils;
}