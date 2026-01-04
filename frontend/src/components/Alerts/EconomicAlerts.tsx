/**
 * EconomicAlerts Component
 * Displays real-time economic alerts with filtering and management capabilities
 */

import React, { useEffect, useState, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  Alert,
  AlertRule,
  AlertAggregation,
  AlertPriority
} from '../../services/alertService';
import {
  selectAlerts,
  selectAggregations,
  selectUnreadAlertsCount,
  selectCriticalAlerts,
  selectActiveAlerts,
  selectShowAggregatedView,
  selectAlertStatistics,
  toggleAggregatedView,
  openAlertDetailsModal,
  markAllAlertsAsRead,
  bulkAcknowledgeAlerts,
  bulkResolveAlerts
} from '../../store/slices/alertsSlice';
import { RootState, AppDispatch } from '../../store';

interface EconomicAlertsProps {
  className?: string;
  maxDisplayCount?: number;
  showStatistics?: boolean;
  showBulkActions?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const EconomicAlerts: React.FC<EconomicAlertsProps> = ({
  className = '',
  maxDisplayCount = 50,
  showStatistics = true,
  showBulkActions = true,
  autoRefresh = true,
  refreshInterval = 30000 // 30 seconds
}) => {
  const dispatch = useDispatch<AppDispatch>();

  // Selectors
  const alerts = useSelector(selectAlerts);
  const aggregations = useSelector(selectAggregations);
  const unreadCount = useSelector(selectUnreadAlertsCount);
  const criticalAlerts = useSelector(selectCriticalAlerts);
  const activeAlerts = useSelector(selectActiveAlerts);
  const showAggregated = useSelector(selectShowAggregatedView);
  const statistics = useSelector(selectAlertStatistics);

  // Local state
  const [selectedAlerts, setSelectedAlerts] = useState<Set<string>>(new Set());
  const [expandedAggregations, setExpandedAggregations] = useState<Set<string>>(new Set());
  const [refreshTimer, setRefreshTimer] = useState<NodeJS.Timeout | null>(null);

  // Priority order for sorting
  const priorityOrder: Record<AlertPriority, number> = {
    critical: 4,
    high: 3,
    medium: 2,
    low: 1
  };

  // Sort alerts by priority and time
  const sortedAlerts = [...alerts].sort((a, b) => {
    // First sort by priority
    const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
    if (priorityDiff !== 0) return priorityDiff;

    // Then by time (newest first)
    return new Date(b.triggeredAt).getTime() - new Date(a.triggeredAt).getTime();
  }).slice(0, maxDisplayCount);

  // Sort aggregations similarly
  const sortedAggregations = [...aggregations].sort((a, b) => {
    const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
    if (priorityDiff !== 0) return priorityDiff;

    return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
  });

  // Auto-refresh effect
  useEffect(() => {
    if (autoRefresh) {
      const timer = setInterval(() => {
        // Refresh logic here - would typically dispatch an action
      }, refreshInterval);

      setRefreshTimer(timer);

      return () => {
        if (timer) clearInterval(timer);
      };
    }
  }, [autoRefresh, refreshInterval]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (refreshTimer) clearInterval(refreshTimer);
    };
  }, [refreshTimer]);

  // Event handlers
  const handleAlertClick = useCallback((alert: Alert) => {
    dispatch(openAlertDetailsModal(alert));
    // Mark as read logic here
  }, [dispatch]);

  const handleToggleAggregatedView = useCallback(() => {
    dispatch(toggleAggregatedView());
  }, [dispatch]);

  const handleMarkAllAsRead = useCallback(() => {
    dispatch(markAllAlertsAsRead());
  }, [dispatch]);

  const handleSelectAlert = useCallback((alertId: string, selected: boolean) => {
    setSelectedAlerts(prev => {
      const newSet = new Set(prev);
      if (selected) {
        newSet.add(alertId);
      } else {
        newSet.delete(alertId);
      }
      return newSet;
    });
  }, []);

  const handleSelectAllAlerts = useCallback(() => {
    const currentAlerts = showAggregated
      ? sortedAggregations.flatMap(agg => agg.alerts.map(a => a.id))
      : sortedAlerts.map(a => a.id);

    if (selectedAlerts.size === currentAlerts.length) {
      setSelectedAlerts(new Set());
    } else {
      setSelectedAlerts(new Set(currentAlerts));
    }
  }, [showAggregated, sortedAlerts, sortedAggregations]);

  const handleBulkAcknowledge = useCallback(() => {
    if (selectedAlerts.size > 0) {
      dispatch(bulkAcknowledgeAlerts(Array.from(selectedAlerts)));
      setSelectedAlerts(new Set());
    }
  }, [dispatch, selectedAlerts]);

  const handleBulkResolve = useCallback(() => {
    if (selectedAlerts.size > 0) {
      dispatch(bulkResolveAlerts(Array.from(selectedAlerts)));
      setSelectedAlerts(new Set());
    }
  }, [dispatch, selectedAlerts]);

  const handleToggleAggregation = useCallback((aggregationId: string) => {
    setExpandedAggregations(prev => {
      const newSet = new Set(prev);
      if (newSet.has(aggregationId)) {
        newSet.delete(aggregationId);
      } else {
        newSet.add(aggregationId);
      }
      return newSet;
    });
  }, []);

  // Render helpers
  const getPriorityColor = (priority: AlertPriority): string => {
    switch (priority) {
      case 'critical':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'high':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getPriorityIcon = (priority: AlertPriority): string => {
    switch (priority) {
      case 'critical':
        return '⚠️';
      case 'high':
        return '🔴';
      case 'medium':
        return '🟡';
      case 'low':
        return '🔵';
      default:
        return 'ℹ️';
    }
  };

  const formatTime = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;

    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  // Render statistics panel
  const renderStatistics = () => {
    if (!showStatistics || !statistics) return null;

    return (
      <div className="bg-white rounded-lg shadow p-4 mb-4">
        <h3 className="text-lg font-semibold mb-3">Alert Statistics</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-800">{statistics.total}</div>
            <div className="text-sm text-gray-600">Total Alerts</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{statistics.active}</div>
            <div className="text-sm text-gray-600">Active</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{statistics.acknowledged}</div>
            <div className="text-sm text-gray-600">Acknowledged</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{statistics.resolved}</div>
            <div className="text-sm text-gray-600">Resolved</div>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="font-medium">Trigger Rate:</span> {statistics.triggerRate.toFixed(2)}/hour
          </div>
          <div>
            <span className="font-medium">Avg Resolution:</span> {statistics.resolutionTime.toFixed(1)}h
          </div>
          <div>
            <span className="font-medium">Critical:</span> {statistics.byPriority.critical || 0}
          </div>
        </div>
      </div>
    );
  };

  // Render alert item
  const renderAlert = (alert: Alert, isAggregated: boolean = false) => {
    const isSelected = selectedAlerts.has(alert.id);
    const priorityClass = getPriorityColor(alert.priority);
    const priorityIcon = getPriorityIcon(alert.priority);

    return (
      <div
        key={alert.id}
        className={`
          border rounded-lg p-4 mb-2 cursor-pointer transition-all hover:shadow-md
          ${priorityClass}
          ${isSelected ? 'ring-2 ring-blue-500' : ''}
          ${isAggregated ? 'ml-4 border-l-4' : ''}
        `}
        onClick={() => handleAlertClick(alert)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg">{priorityIcon}</span>
              <h4 className="font-semibold">{alert.title}</h4>
              {isAggregated && (
                <span className="text-xs bg-gray-200 px-2 py-1 rounded">
                  Aggregated
                </span>
              )}
            </div>
            <p className="text-sm text-gray-700 mb-2">{alert.message}</p>
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span>Source: {alert.source}</span>
              <span>Type: {alert.type}</span>
              <span>{formatTime(alert.triggeredAt)}</span>
              <span className={`px-2 py-1 rounded ${priorityClass}`}>
                {alert.priority}
              </span>
            </div>
          </div>

          {showBulkActions && (
            <div className="ml-2" onClick={(e) => e.stopPropagation()}>
              <input
                type="checkbox"
                checked={isSelected}
                onChange={(e) => handleSelectAlert(alert.id, e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
            </div>
          )}
        </div>
      </div>
    );
  };

  // Render aggregation
  const renderAggregation = (aggregation: AlertAggregation) => {
    const isExpanded = expandedAggregations.has(aggregation.id);
    const priorityClass = getPriorityColor(aggregation.priority);
    const priorityIcon = getPriorityIcon(aggregation.priority);

    return (
      <div key={aggregation.id} className="mb-4">
        <div
          className={`
            border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md
            ${priorityClass}
          `}
          onClick={() => handleToggleAggregation(aggregation.id)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-xl">{priorityIcon}</span>
              <div>
                <h4 className="font-semibold">{aggregation.title}</h4>
                <p className="text-sm text-gray-700">{aggregation.summary}</p>
                <div className="flex items-center gap-4 text-xs text-gray-500 mt-1">
                  <span>Count: {aggregation.count}</span>
                  <span>Source: {aggregation.source}</span>
                  <span>{formatTime(aggregation.createdAt)}</span>
                </div>
              </div>
            </div>
            <div className="text-gray-400">
              {isExpanded ? '▼' : '▶'}
            </div>
          </div>
        </div>

        {isExpanded && (
          <div className="mt-2">
            {aggregation.alerts.map(alert => renderAlert(alert, true))}
          </div>
        )}
      </div>
    );
  };

  // Render bulk actions
  const renderBulkActions = () => {
    if (!showBulkActions || selectedAlerts.size === 0) return null;

    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-blue-800">
            {selectedAlerts.size} alert{selectedAlerts.size > 1 ? 's' : ''} selected
          </span>
          <div className="flex gap-2">
            <button
              onClick={handleBulkAcknowledge}
              className="px-3 py-1 text-sm bg-yellow-500 text-white rounded hover:bg-yellow-600"
            >
              Acknowledge
            </button>
            <button
              onClick={handleBulkResolve}
              className="px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600"
            >
              Resolve
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className={`economic-alerts ${className}`}>
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-4 mb-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xl font-bold flex items-center gap-2">
            Economic Alerts
            {unreadCount > 0 && (
              <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                {unreadCount}
              </span>
            )}
          </h2>
          <div className="flex gap-2">
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllAsRead}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Mark all as read
              </button>
            )}
            <button
              onClick={handleToggleAggregatedView}
              className={`px-3 py-1 text-sm rounded ${
                showAggregated
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {showAggregated ? 'Show Individual' : 'Show Aggregated'}
            </button>
          </div>
        </div>

        {/* Quick stats */}
        <div className="flex gap-4 text-sm">
          <span className="text-red-600 font-medium">
            {criticalAlerts.length} Critical
          </span>
          <span className="text-gray-600">
            {activeAlerts.length} Active
          </span>
          <span className="text-gray-600">
            {sortedAlerts.length + sortedAggregations.length} Total
          </span>
        </div>
      </div>

      {/* Statistics */}
      {renderStatistics()}

      {/* Bulk actions */}
      {renderBulkActions()}

      {/* Select all checkbox */}
      {showBulkActions && (showAggregated ? sortedAggregations.length > 0 : sortedAlerts.length > 0) && (
        <div className="mb-3">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={
                selectedAlerts.size ===
                (showAggregated
                  ? sortedAggregations.flatMap(agg => agg.alerts.map(a => a.id)).length
                  : sortedAlerts.length)
              }
              onChange={handleSelectAllAlerts}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            Select all
          </label>
        </div>
      )}

      {/* Alerts list */}
      <div className="space-y-2">
        {showAggregated ? (
          <>
            {sortedAggregations.length > 0 ? (
              sortedAggregations.map(renderAggregation)
            ) : (
              <div className="text-center py-8 text-gray-500">
                No alert aggregations found
              </div>
            )}
          </>
        ) : (
          <>
            {sortedAlerts.length > 0 ? (
              sortedAlerts.map(alert => renderAlert(alert))
            ) : (
              <div className="text-center py-8 text-gray-500">
                No active alerts
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default EconomicAlerts;