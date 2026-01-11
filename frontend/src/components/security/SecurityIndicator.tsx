/**
 * SecurityIndicator Component
 * Visual indicators for security status and alerts
 */

import React, { useState, useEffect } from 'react';
import { securityManager } from '../../utils/security';

interface SecurityIndicatorProps {
  mode?: 'status' | 'detailed' | 'compact';
  showLabel?: boolean;
  className?: string;
  onClick?: () => void;
}

export const SecurityIndicator: React.FC<SecurityIndicatorProps> = ({
  mode = 'status',
  showLabel = true,
  className,
  onClick
}) => {
  const [status, setStatus] = useState<{
    overall: 'healthy' | 'warning' | 'critical';
    checks: Array<{ name: string; status: string; message: string }>;
  }>({ overall: 'healthy', checks: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkSecurityStatus();
    // Check every 30 seconds
    const interval = setInterval(checkSecurityStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkSecurityStatus = async () => {
    try {
      const healthCheck = await securityManager.performHealthCheck();
      setStatus(healthCheck);
    } catch (error) {
      console.error('Security status check failed:', error);
      setStatus({
        overall: 'critical',
        checks: [{ name: 'System', status: 'fail', message: 'Status check failed' }]
      });
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = () => {
    switch (status.overall) {
      case 'healthy': return 'bg-green-500';
      case 'warning': return 'bg-yellow-500';
      case 'critical': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    switch (status.overall) {
      case 'healthy': return 'Security: Good';
      case 'warning': return 'Security: Warning';
      case 'critical': return 'Security: Issues';
      default: return 'Security: Unknown';
    }
  };

  const getIcon = () => {
    switch (status.overall) {
      case 'healthy':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'warning':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'critical':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  if (loading) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <div className="animate-pulse rounded-full bg-gray-300 w-3 h-3"></div>
        {showLabel && <span className="text-sm text-gray-600">Checking...</span>}
      </div>
    );
  }

  if (mode === 'compact') {
    return (
      <div
        className={`flex items-center space-x-1 cursor-pointer ${className}`}
        onClick={onClick}
        title={getStatusText()}
      >
        <div className={`rounded-full ${getStatusColor()} w-2 h-2`} />
      </div>
    );
  }

  if (mode === 'status') {
    return (
      <div
        className={`flex items-center space-x-2 cursor-pointer ${className}`}
        onClick={onClick}
      >
        <div className={`rounded-full ${getStatusColor()} w-3 h-3`} />
        {showLabel && (
          <span className="text-sm font-medium text-gray-700">{getStatusText()}</span>
        )}
      </div>
    );
  }

  // Detailed mode
  return (
    <div className={`bg-white rounded-lg shadow p-4 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className={`rounded-full ${getStatusColor()} w-4 h-4`} />
          <h3 className="font-semibold text-gray-900">{getStatusText()}</h3>
        </div>
        <button
          onClick={checkSecurityStatus}
          className="text-gray-400 hover:text-gray-600"
          title="Refresh"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>

      <div className="space-y-2">
        {status.checks.map((check, index) => (
          <div key={index} className="flex items-center justify-between text-sm">
            <span className="text-gray-600">{check.name}</span>
            <span className={`font-medium ${
              check.status === 'pass' ? 'text-green-600' :
              check.status === 'warning' ? 'text-yellow-600' :
              'text-red-600'
            }`}>
              {check.message}
            </span>
          </div>
        ))}
      </div>

      <button
        onClick={onClick}
        className="mt-4 text-sm text-blue-600 hover:text-blue-800 font-medium"
      >
        View Full Security Report →
      </button>
    </div>
  );
};

// Security badge component
export const SecurityBadge: React.FC<{
  type: 'xss' | 'csrf' | 'csp' | 'audit' | 'encryption';
  status?: 'active' | 'inactive' | 'warning';
  className?: string;
}> = ({ type, status = 'active', className }) => {
  const getConfig = () => {
    switch (type) {
      case 'xss':
        return { label: 'XSS Protection', icon: '🛡️' };
      case 'csrf':
        return { label: 'CSRF Protection', icon: '🔐' };
      case 'csp':
        return { label: 'CSP', icon: '🔒' };
      case 'audit':
        return { label: 'Security Audit', icon: '🔍' };
      case 'encryption':
        return { label: 'Encryption', icon: '🔑' };
      default:
        return { label: 'Security', icon: '🔒' };
    }
  };

  const { label, icon } = getConfig();

  const getStatusColor = () => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'inactive': return 'bg-gray-100 text-gray-800';
      case 'warning': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor()} ${className}`}>
      <span className="mr-1">{icon}</span>
      {label}
    </span>
  );
};

// Quick security actions component
export const SecurityActions: React.FC<{
  onAudit?: () => void;
  onSettings?: () => void;
  className?: string;
}> = ({ onAudit, onSettings, className }) => {
  const [isRunning, setIsRunning] = useState(false);

  const handleRunAudit = async () => {
    setIsRunning(true);
    try {
      await onAudit?.();
    } finally {
      setTimeout(() => setIsRunning(false), 1000);
    }
  };

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <button
        onClick={handleRunAudit}
        disabled={isRunning}
        className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
          isRunning
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
            : 'bg-blue-50 text-blue-700 hover:bg-blue-100'
        }`}
      >
        {isRunning ? 'Running...' : 'Run Audit'}
      </button>
      <button
        onClick={onSettings}
        className="px-3 py-1.5 rounded text-sm font-medium bg-gray-50 text-gray-700 hover:bg-gray-100 transition-colors"
      >
        Security Settings
      </button>
    </div>
  );
};

export default SecurityIndicator;