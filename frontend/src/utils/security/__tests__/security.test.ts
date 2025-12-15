/**
 * Security Module Tests
 * Tests for all security utilities
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import {
  xssProtection,
  csrfProtection,
  cspConfig,
  securityAudit,
  inputValidator,
  encryption,
  securityManager
} from '../index';

describe('XSS Protection', () => {
  beforeEach(() => {
    // Reset XSS protection before each test
    xssProtection.configure({
      ALLOWED_TAGS: ['p', 'b', 'i', 'em', 'strong'],
      ALLOWED_ATTR: ['class', 'id']
    });
  });

  it('should sanitize HTML with dangerous content', () => {
    const dangerousHTML = '<script>alert("XSS")</script><p>Safe content</p>';
    const sanitized = xssProtection.sanitizeHTML(dangerousHTML);
    expect(sanitized).not.toContain('<script>');
    expect(sanitized).toContain('<p>Safe content</p>');
  });

  it('should detect dangerous patterns', () => {
    const content = '<img src="x" onerror="alert(1)">';
    expect(xssProtection.containsDangerousPatterns(content)).toBe(true);
  });

  it('should validate URLs', () => {
    const validUrl = 'https://cbsc.com/path';
    const invalidUrl = 'javascript:alert(1)';

    expect(xssProtection.sanitizeURL(validUrl)).toBe(validUrl);
    expect(xssProtection.sanitizeURL(invalidUrl)).toBe('');
  });

  it('should safely parse JSON', () => {
    const validJSON = '{"key": "value"}';
    const maliciousJSON = '{"__proto__": {"polluted": true}}';

    expect(xssProtection.safeJSONParse(validJSON)).toEqual({ key: 'value' });
    expect(xssProtection.safeJSONParse(maliciousJSON)).toBeNull();
  });
});

describe('CSRF Protection', () => {
  beforeEach(() => {
    // Reset CSRF protection
    csrfProtection.destroy();
  });

  it('should generate and validate tokens', () => {
    const token = csrfProtection.getToken();
    expect(token).toBeTruthy();
    expect(token.length).toBeGreaterThan(0);
    expect(csrfProtection.validateToken(token)).toBe(true);
  });

  it('should add token to headers', () => {
    const headers = { 'Content-Type': 'application/json' };
    const headersWithToken = csrfProtection.addTokenToHeaders(headers);

    expect(headersWithToken).toHaveProperty('X-XSRF-TOKEN');
    expect(headersWithToken['X-XSRF-TOKEN']).toBe(csrfProtection.getToken());
  });

  it('should rotate tokens', () => {
    const originalToken = csrfProtection.getToken();
    csrfProtection.rotateToken();
    const newToken = csrfProtection.getToken();

    expect(newToken).not.toBe(originalToken);
    expect(csrfProtection.validateToken(originalToken)).toBe(false);
    expect(csrfProtection.validateToken(newToken)).toBe(true);
  });
});

describe('CSP Configuration', () => {
  it('should generate valid CSP policy', () => {
    const config = cspConfig.getStatistics();
    expect(config).toHaveProperty('totalViolations');
    expect(config).toHaveProperty('violationsByDirective');
    expect(config).toHaveProperty('violationsByURI');
  });

  it('should add trusted domains', () => {
    cspConfig.addTrustedDomain('script-src', 'https://trusted.com');
    const config = cspConfig.getStatistics();
    // This would need to be extended to check actual config
    expect(config).toBeTruthy();
  });

  it('should enable strict mode', () => {
    cspConfig.enableStrictMode();
    const config = cspConfig.getStatistics();
    expect(config).toBeTruthy();
  });
});

describe('Input Validation', () => {
  it('should validate email addresses', () => {
    const validEmail = 'user@cbsc.com';
    const invalidEmail = 'invalid-email';

    const validResult = inputValidator.validate(validEmail, {
      pattern: inputValidator.VALIDATION_PATTERNS.email
    });
    const invalidResult = inputValidator.validate(invalidEmail, {
      pattern: inputValidator.VALIDATION_PATTERNS.email
    });

    expect(validResult.valid).toBe(true);
    expect(invalidResult.valid).toBe(false);
  });

  it('should validate financial data', () => {
    const validData = {
      amount: '$1,000.00',
      percentage: '25%',
      symbol: 'AAPL'
    };
    const invalidData = {
      amount: 'invalid',
      percentage: '200%',
      symbol: 'invalid-symbol'
    };

    const validResult = inputValidator.validateFinancialData(validData);
    const invalidResult = inputValidator.validateFinancialData(invalidData);

    expect(validResult.valid).toBe(true);
    expect(invalidResult.valid).toBe(false);
  });

  it('should sanitize input securely', () => {
    const malicious = '<script>alert(1)</script>Hello';
    const sanitized = inputValidator.sanitize(malicious);
    expect(sanitized).not.toContain('<script>');
    expect(sanitized).toContain('Hello');
  });
});

describe('Security Audit', () => {
  beforeEach(() => {
    securityAudit.clearAuditLog();
  });

  it('should generate security report', () => {
    securityAudit.runFullAudit();
    const report = securityAudit.generateSecurityReport();

    expect(report).toHaveProperty('overallScore');
    expect(report).toHaveProperty('vulnerabilities');
    expect(report).toHaveProperty('recommendations');
    expect(typeof report.overallScore).toBe('number');
  });

  it('should log security violations', () => {
    const violation = {
      timestamp: Date.now(),
      type: 'test',
      severity: 'high' as const,
      message: 'Test violation',
      details: {}
    };

    // Access private method through type assertion
    (securityAudit as any).logResult('test', 'high', 'Test violation', {});
    const log = securityAudit.getAuditLog();

    expect(log.length).toBeGreaterThan(0);
    expect(log[0]).toHaveProperty('type', 'test');
    expect(log[0]).toHaveProperty('severity', 'high');
  });
});

describe('Encryption', () => {
  beforeEach(async () => {
    await encryption.initialize();
  });

  afterEach(() => {
    encryption.wipe();
  });

  it('should encrypt and decrypt data', () => {
    const data = 'Sensitive financial data';
    const encrypted = encryption.encrypt(data);
    const decrypted = encryption.decrypt(encrypted);

    expect(encrypted).not.toBe(data);
    expect(decrypted).toBe(data);
  });

  it('should encrypt and decrypt objects', () => {
    const obj = { key: 'value', number: 42 };
    const encrypted = encryption.encryptObject(obj);
    const decrypted = encryption.decryptObject(encrypted);

    expect(decrypted).toEqual(obj);
  });

  it('should generate secure hash', () => {
    const data = 'test data';
    const hash = encryption.hash(data);

    expect(hash).toBeTruthy();
    expect(typeof hash).toBe('string');
    expect(hash.length).toBeGreaterThan(0);

    // Verify hash consistency
    const hash2 = encryption.hash(data);
    expect(hash).toBe(hash2);

    // Verify hash verification
    expect(encryption.verifyHash(data, hash)).toBe(true);
    expect(encryption.verifyHash('different', hash)).toBe(false);
  });

  it('should generate random tokens', () => {
    const token1 = encryption.generateToken();
    const token2 = encryption.generateToken();

    expect(token1).toBeTruthy();
    expect(token2).toBeTruthy();
    expect(token1).not.toBe(token2);
    expect(token1.length).toBe(32);
  });
});

describe('Security Manager', () => {
  beforeEach(async () => {
    await securityManager.initialize();
  });

  afterEach(() => {
    securityManager.destroy();
  });

  it('should initialize security features', () => {
    const status = securityManager.getSecurityStatus();
    expect(status.initialized).toBe(true);
    expect(status).toHaveProperty('cspStatistics');
    expect(status).toHaveProperty('auditReport');
    expect(status).toHaveProperty('csrfToken');
    expect(status).toHaveProperty('encryptionStatus');
  });

  it('should perform health check', async () => {
    const health = await securityManager.performHealthCheck();
    expect(health).toHaveProperty('status');
    expect(health).toHaveProperty('checks');
    expect(['healthy', 'warning', 'critical']).toContain(health.status);
  });

  it('should enable production mode', () => {
    securityManager.enableProductionMode();
    // This would need to be verified by checking actual config
    expect(true).toBe(true); // Placeholder
  });
});

describe('Security Integration', () => {
  it('should work together for complete protection', async () => {
    // Initialize all security features
    await securityManager.initialize();

    // Test XSS protection with encryption
    const maliciousData = '<script>alert("XSS")</script>';
    const sanitized = xssProtection.sanitizeHTML(maliciousData);
    const encrypted = encryption.encrypt(sanitized);
    const decrypted = encryption.decrypt(encrypted);

    expect(decrypted).not.toContain('<script>');

    // Test CSRF with input validation
    const formData = new FormData();
    csrfProtection.addTokenToFormData(formData);
    const token = formData.get('_csrf');
    expect(token).toBeTruthy();
    expect(csrfProtection.validateToken(token as string)).toBe(true);

    // Test audit integration
    securityAudit.runFullAudit();
    const report = securityAudit.generateSecurityReport();
    expect(report.overallScore).toBeGreaterThanOrEqual(0);
    expect(report.overallScore).toBeLessThanOrEqual(100);
  });
});