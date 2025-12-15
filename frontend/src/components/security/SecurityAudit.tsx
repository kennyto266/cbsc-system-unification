/**
 * SecurityAudit Component
 * Displays comprehensive security audit reports
 */

import React, { useState, useEffect } from 'react';
import { securityAudit, SecurityStatistics, AuditResult } from '../../utils/security';

interface SecurityAuditProps {
  className?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
  showDetails?: boolean;
  onIssueClick?: (issue: AuditResult) => void;
}

export const SecurityAudit: React.FC<SecurityAuditProps> = ({
  className,
  autoRefresh = false,
  refreshInterval = 60000,
  showDetails = false,
  onIssueClick
}) => {
  const [report, setReport] = useState<SecurityStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedIssues, setExpandedIssues] = useState<Set<number>>(new Set());

  // Load initial report
  useEffect(() => {
    loadReport();
  }, []);

  // Set up auto-refresh
  useEffect(() => {
    if (autoRefresh) {
      const timer = setInterval(loadReport, refreshInterval);
      return () => clearInterval(timer);
    }
  }, [autoRefresh, refreshInterval]);

  const loadReport = async () => {
    setLoading(true);
    try {
      const newReport = securityAudit.generateSecurityReport();
      setReport(newReport);
    } catch (error) {
      console.error('Failed to load security report:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAudit = () => {
    securityAudit.runFullAudit();
    loadReport();
  };

  const toggleIssueExpansion = (index: number) => {
    const newExpanded = new Set(expandedIssues);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedIssues(newExpanded);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-blue-600 bg-blue-50 border-blue-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading && !report) {
    return (
      <div className={`p-6 bg-white rounded-lg shadow ${className}`}>
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className={`p-6 bg-white rounded-lg shadow ${className}`}>
        <p className="text-gray-500">Failed to load security report</p>
      </div>
    );
  }

  return (
    <div className={`p-6 bg-white rounded-lg shadow ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Security Audit Report</h2>
        <div className="flex items-center space-x-2">
          <span className={`text-lg font-semibold ${getScoreColor(report.overallScore)}`}>
            Score: {report.overallScore}/100
          </span>
          <button
            onClick={handleRunAudit}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            Run Audit
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white border rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-500">Critical</h3>
          <p className="text-2xl font-bold text-red-600">{report.vulnerabilities.critical}</p>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-500">High</h3>
          <p className="text-2xl font-bold text-orange-600">{report.vulnerabilities.high}</p>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-500">Medium</h3>
          <p className="text-2xl font-bold text-yellow-600">{report.vulnerabilities.medium}</p>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-500">Low</h3>
          <p className="text-2xl font-bold text-blue-600">{report.vulnerabilities.low}</p>
        </div>
      </div>

      {/* Vulnerability List */}
      {showDetails && report.auditResults.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Security Issues</h3>
          <div className="space-y-2">
            {report.auditResults.map((issue, index) => (
              <div
                key={index}
                className={`border rounded-lg p-4 cursor-pointer transition-colors hover:bg-gray-50 ${getSeverityColor(issue.severity)}`}
                onClick={() => {
                  toggleIssueExpansion(index);
                  onIssueClick?.(issue);
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className={`text-xs font-medium uppercase px-2 py-1 rounded ${getSeverityColor(issue.severity)}`}>
                        {issue.severity}
                      </span>
                      <span className="text-sm text-gray-500">
                        {new Date(issue.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <h4 className="font-medium text-gray-900 mt-1">{issue.message}</h4>
                  </div>
                  <svg
                    className={`w-5 h-5 text-gray-400 transform transition-transform ${expandedIssues.has(index) ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>

                {expandedIssues.has(index) && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h5 className="font-medium text-gray-700 mb-2">Type</h5>
                        <p className="text-sm text-gray-600">{issue.type}</p>
                      </div>
                      {issue.recommendation && (
                        <div>
                          <h5 className="font-medium text-gray-700 mb-2">Recommendation</h5>
                          <p className="text-sm text-gray-600">{issue.recommendation}</p>
                        </div>
                      )}
                    </div>

                    {issue.details && Object.keys(issue.details).length > 0 && (
                      <div className="mt-4">
                        <h5 className="font-medium text-gray-700 mb-2">Details</h5>
                        <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                          {JSON.stringify(issue.details, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {report.recommendations.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Security Recommendations</h3>
          <ul className="space-y-2">
            {report.recommendations.map((recommendation, index) => (
              <li key={index} className="flex items-start">
                <svg
                  className="w-5 h-5 text-yellow-500 mt-0.5 mr-2"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <span className="text-sm text-gray-600">{recommendation}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

// Security indicator component for dashboard
export const SecurityIndicator: React.FC<{
  score?: number;
  showScore?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}> = ({ score, showScore = true, size = 'md', className }) => {
  const [currentScore, setCurrentScore] = useState<number | null>(null);

  useEffect(() => {
    if (score !== undefined) {
      setCurrentScore(score);
    } else {
      // Get latest security score
      const report = securityAudit.generateSecurityReport();
      setCurrentScore(report.overallScore);
    }
  }, [score]);

  if (currentScore === null) {
    return null;
  }

  const getStatusColor = () => {
    if (currentScore >= 90) return 'bg-green-500';
    if (currentScore >= 70) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getSizeClasses = () => {
    switch (size) {
      case 'sm': return 'w-2 h-2';
      case 'md': return 'w-3 h-3';
      case 'lg': return 'w-4 h-4';
    }
  };

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <div className={`rounded-full ${getStatusColor()} ${getSizeClasses()}`} />
      {showScore && (
        <span className="text-sm font-medium text-gray-700">
          {currentScore}/100
        </span>
      )}
    </div>
  );
};

export default SecurityAudit;