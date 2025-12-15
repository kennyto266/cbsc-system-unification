/**
 * useSecurityAudit Hook
 * React hook for security auditing
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { securityAudit, SecurityStatistics, AuditResult } from '../utils/security';

interface SecurityAuditState {
  report: SecurityStatistics | null;
  isRunning: boolean;
  lastRun: number | null;
  autoRefresh: boolean;
  refreshInterval: number;
}

export const useSecurityAudit = (options?: {
  autoRun?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
}) => {
  const {
    autoRun = true,
    autoRefresh = false,
    refreshInterval = 60000 // 1 minute
  } = options || {};

  const [state, setState] = useState<SecurityAuditState>({
    report: null,
    isRunning: false,
    lastRun: null,
    autoRefresh,
    refreshInterval
  });

  const refreshTimerRef = useRef<NodeJS.Timeout>();

  // Run initial audit
  useEffect(() => {
    if (autoRun) {
      runAudit();
    }
  }, [autoRun]);

  // Set up auto-refresh
  useEffect(() => {
    if (state.autoRefresh) {
      refreshTimerRef.current = setInterval(() => {
        runAudit();
      }, state.refreshInterval);
    } else {
      if (refreshTimerRef.current) {
        clearInterval(refreshTimerRef.current);
      }
    }

    return () => {
      if (refreshTimerRef.current) {
        clearInterval(refreshTimerRef.current);
      }
    };
  }, [state.autoRefresh, state.refreshInterval]);

  const runAudit = useCallback(async () => {
    setState(prev => ({ ...prev, isRunning: true }));

    try {
      const report = securityAudit.generateSecurityReport();
      setState(prev => ({
        ...prev,
        report,
        isRunning: false,
        lastRun: Date.now()
      }));
    } catch (error) {
      console.error('Security audit failed:', error);
      setState(prev => ({ ...prev, isRunning: false }));
    }
  }, []);

  const getReport = useCallback(() => {
    return securityAudit.generateSecurityReport();
  }, []);

  const enableAutoRefresh = useCallback(() => {
    setState(prev => ({ ...prev, autoRefresh: true }));
  }, []);

  const disableAutoRefresh = useCallback(() => {
    setState(prev => ({ ...prev, autoRefresh: false }));
  }, []);

  const setRefreshInterval = useCallback((interval: number) => {
    setState(prev => ({ ...prev, refreshInterval: interval }));
  }, []);

  return {
    ...state,
    runAudit,
    getReport,
    enableAutoRefresh,
    disableAutoRefresh,
    setRefreshInterval
  };
};

// Hook for monitoring security violations
export const useSecurityMonitor = (options?: {
  onViolation?: (violation: AuditResult) => void;
  maxViolations?: number;
}) => {
  const { onViolation, maxViolations = 100 } = options || {};
  const [violations, setViolations] = useState<AuditResult[]>([]);
  const [thresholds, setThresholds] = useState({
    critical: 0,
    high: 0,
    medium: 0,
    low: 0
  });

  // Check for new violations periodically
  useEffect(() => {
    const checkViolations = () => {
      const report = securityAudit.generateSecurityReport();
      const newViolations = report.auditResults.slice(0, maxViolations);

      setViolations(newViolations);

      // Update thresholds
      const newThresholds = {
        critical: 0,
        high: 0,
        medium: 0,
        low: 0
      };

      newViolations.forEach(violation => {
        newThresholds[violation.severity]++;
      });

      setThresholds(newThresholds);

      // Notify about critical violations
      const criticalViolations = newViolations.filter(v => v.severity === 'critical');
      criticalViolations.forEach(violation => {
        onViolation?.(violation);
      });
    };

    // Initial check
    checkViolations();

    // Set up periodic checking
    const timer = setInterval(checkViolations, 30000); // 30 seconds

    return () => clearInterval(timer);
  }, [onViolation, maxViolations]);

  const getSecurityHealth = useCallback((): {
    status: 'healthy' | 'warning' | 'critical';
    score: number;
    issues: number;
  } => {
    const totalIssues = Object.values(thresholds).reduce((a, b) => a + b, 0);
    const criticalScore = thresholds.critical * 25;
    const highScore = thresholds.high * 10;
    const mediumScore = thresholds.medium * 5;
    const lowScore = thresholds.low * 1;
    const deduction = criticalScore + highScore + mediumScore + lowScore;
    const score = Math.max(0, 100 - deduction);

    let status: 'healthy' | 'warning' | 'critical';
    if (thresholds.critical > 0 || thresholds.high > 5) {
      status = 'critical';
    } else if (thresholds.high > 0 || thresholds.medium > 10) {
      status = 'warning';
    } else {
      status = 'healthy';
    }

    return {
      status,
      score,
      issues: totalIssues
    };
  }, [thresholds]);

  return {
    violations,
    thresholds,
    getSecurityHealth
  };
};

// Hook for security recommendations
export const useSecurityRecommendations = () => {
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [implemented, setImplemented] = useState<Set<string>>(new Set());

  useEffect(() => {
    const updateRecommendations = () => {
      const report = securityAudit.generateSecurityReport();
      setRecommendations(report.recommendations);
    };

    // Initial update
    updateRecommendations();

    // Update every 5 minutes
    const timer = setInterval(updateRecommendations, 300000);

    return () => clearInterval(timer);
  }, []);

  const markAsImplemented = useCallback((recommendation: string) => {
    setImplemented(prev => new Set(prev).add(recommendation));
  }, []);

  const markAsNotImplemented = useCallback((recommendation: string) => {
    setImplemented(prev => {
      const newSet = new Set(prev);
      newSet.delete(recommendation);
      return newSet;
    });
  }, []);

  const getPendingRecommendations = useCallback(() => {
    return recommendations.filter(r => !implemented.has(r));
  }, [recommendations, implemented]);

  const getImplementationRate = useCallback(() => {
    if (recommendations.length === 0) return 100;
    return (implemented.size / recommendations.length) * 100;
  }, [recommendations, implemented]);

  return {
    recommendations,
    implemented,
    markAsImplemented,
    markAsNotImplemented,
    getPendingRecommendations,
    getImplementationRate
  };
};

// Hook for security health check
export const useSecurityHealthCheck = () => {
  const [health, setHealth] = useState<{
    status: 'healthy' | 'warning' | 'critical';
    checks: Array<{
      name: string;
      status: 'pass' | 'fail' | 'warning';
      message: string;
    }>;
    lastCheck: number | null;
  }>({ status: 'healthy', checks: [], lastCheck: null });

  const performCheck = useCallback(async () => {
    // This would typically call securityManager.performHealthCheck()
    // For now, using a simplified version
    try {
      const report = securityAudit.generateSecurityReport();
      const checks = [
        {
          name: 'XSS Protection',
          status: report.vulnerabilities.critical === 0 ? 'pass' as const : 'fail' as const,
          message: `${report.vulnerabilities.critical} critical issues found`
        },
        {
          name: 'Security Score',
          status: report.overallScore >= 80 ? 'pass' as const :
                 report.overallScore >= 60 ? 'warning' as const : 'fail' as const,
          message: `Score: ${report.overallScore}/100`
        },
        {
          name: 'Recent Activity',
          status: report.auditResults.length < 10 ? 'pass' as const : 'warning' as const,
          message: `${report.auditResults.length} recent issues`
        }
      ];

      const status = checks.some(c => c.status === 'fail') ? 'critical' :
                     checks.some(c => c.status === 'warning') ? 'warning' : 'healthy';

      setHealth({
        status,
        checks,
        lastCheck: Date.now()
      });
    } catch (error) {
      setHealth({
        status: 'critical',
        checks: [{
          name: 'Health Check',
          status: 'fail',
          message: 'Failed to perform health check'
        }],
        lastCheck: Date.now()
      });
    }
  }, []);

  // Perform initial check
  useEffect(() => {
    performCheck();
  }, [performCheck]);

  // Set up periodic checks
  useEffect(() => {
    const timer = setInterval(performCheck, 60000); // 1 minute
    return () => clearInterval(timer);
  }, [performCheck]);

  return {
    ...health,
    performCheck
  };
};

export default useSecurityAudit;