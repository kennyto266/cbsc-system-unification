/**
 * AlertHistory Component
 * Display and search through alert history with advanced filtering
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState, AppDispatch } from '../../store';
import {
  Alert,
  AlertAggregation,
  AlertHistoryFilters,
  AlertStatistics,
  AlertPriority
} from '../../services/alertService';
import {
  selectAlertHistory,
  selectHistoryLoading,
  selectHistoryError,
  selectAlertFilters,
  loadAlertHistory,
  updateFilters,
  resetFilters,
  resolveAlert,
  openAlertDetailsModal
} from '../../store/slices/alertsSlice';

interface AlertHistoryProps {
  className?: string;
  showStatistics?: boolean;
  showFilters?: boolean;
  allowExport?: boolean;
  maxRecordsPerPage?: number;
}

const AlertHistory: React.FC<AlertHistoryProps> = ({
  className = '',
  showStatistics = true,
  showFilters = true,
  allowExport = true,
  maxRecordsPerPage = 100
}) => {
  const dispatch = useDispatch<AppDispatch>();

  // Selectors
  const history = useSelector(selectAlertHistory);
  const isLoading = useSelector(selectHistoryLoading);
  const error = useSelector(selectHistoryError);
  const filters = useSelector(selectAlertFilters);

  // Local state
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [expandedAggregations, setExpandedAggregations] = useState<Set<string>>(new Set());
  const [showExportModal, setShowExportModal] = useState(false);

  // Load history when filters change
  useEffect(() => {
    dispatch(loadAlertHistory(filters));
  }, [dispatch, filters]);

  // Calculate pagination
  const totalRecords = history?.alerts.length || 0;
  const totalPages = Math.ceil(totalRecords / maxRecordsPerPage);
  const startIndex = (currentPage - 1) * maxRecordsPerPage;
  const endIndex = startIndex + maxRecordsPerPage;
  const paginatedAlerts = history?.alerts.slice(startIndex, endIndex) || [];

  // Priority order for sorting
  const priorityOrder: Record<AlertPriority, number> = {
    critical: 4,
    high: 3,
    medium: 2,
    low: 1
  };

  // Event handlers
  const handleFilterChange = useCallback((newFilters: Partial<AlertHistoryFilters>) => {
    dispatch(updateFilters(newFilters));
    setCurrentPage(1); // Reset to first page when filters change
  }, [dispatch]);

  const handleDateRangeChange = useCallback((start: string, end: string) => {
    handleFilterChange({
      dateRange: { start, end }
    });
  }, [handleFilterChange]);

  const handlePriorityFilter = useCallback((priority: AlertPriority, checked: boolean) => {
    const currentPriorities = filters.priorities || [];
    const newPriorities = checked
      ? [...currentPriorities, priority]
      : currentPriorities.filter(p => p !== priority);

    handleFilterChange({ priorities: newPriorities });
  }, [filters.priorities, handleFilterChange]);

  const handleStatusFilter = useCallback((status: Alert['status'], checked: boolean) => {
    const currentStatuses = filters.status || [];
    const newStatuses = checked
      ? [...currentStatuses, status]
      : currentStatuses.filter(s => s !== status);

    handleFilterChange({ status: newStatuses });
  }, [filters.status, handleFilterChange]);

  const handleSearchChange = useCallback((search: string) => {
    handleFilterChange({ search });
  }, [handleFilterChange]);

  const handleResetFilters = useCallback(() => {
    dispatch(resetFilters());
    setCurrentPage(1);
  }, [dispatch]);

  const handleResolveAlert = useCallback(async (alertId: string) => {
    await dispatch(resolveAlert(alertId));
  }, [dispatch]);

  const handleAlertClick = useCallback((alert: Alert) => {
    setSelectedAlert(alert);
    dispatch(openAlertDetailsModal(alert));
  }, [dispatch]);

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

  const handleExport = useCallback(() => {
    setShowExportModal(true);
  }, []);

  const handleExportConfirm = useCallback((format: 'csv' | 'json') => {
    if (!history) return;

    let content: string;
    let filename: string;
    let mimeType: string;

    if (format === 'csv') {
      // CSV export
      const headers = ['ID', 'Title', 'Message', 'Type', 'Source', 'Priority', 'Status', 'Triggered At'];
      const rows = history.alerts.map(alert => [
        alert.id,
        alert.title,
        alert.message,
        alert.type,
        alert.source,
        alert.priority,
        alert.status,
        alert.triggeredAt
      ]);

      content = [headers, ...rows].map(row => row.join(',')).join('\n');
      filename = `alerts_${new Date().toISOString().split('T')[0]}.csv`;
      mimeType = 'text/csv';
    } else {
      // JSON export
      content = JSON.stringify(history.alerts, null, 2);
      filename = `alerts_${new Date().toISOString().split('T')[0]}.json`;
      mimeType = 'application/json';
    }

    // Download file
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    setShowExportModal(false);
  }, [history]);

  // Render helpers
  const getPriorityBadgeColor = (priority: AlertPriority): string => {
    switch (priority) {
      case 'critical':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusBadgeColor = (status: Alert['status']): string => {
    switch (status) {
      case 'active':
        return 'bg-red-100 text-red-800';
      case 'acknowledged':
        return 'bg-yellow-100 text-yellow-800';
      case 'resolved':
        return 'bg-green-100 text-green-800';
      case 'suppressed':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatTime = (timestamp: string): string => {
    return new Date(timestamp).toLocaleString();
  };

  const formatDuration = (start: string, end?: string): string => {
    const startTime = new Date(start).getTime();
    const endTime = end ? new Date(end).getTime() : Date.now();
    const duration = endTime - startTime;

    const hours = Math.floor(duration / (1000 * 60 * 60));
    const minutes = Math.floor((duration % (1000 * 60 * 60)) / (1000 * 60));

    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  // Render statistics panel
  const renderStatistics = () => {
    if (!showStatistics || !history?.statistics) return null;

    const stats = history.statistics;

    return (
      <div className="bg-white rounded-lg shadow p-4 mb-4">
        <h3 className="text-lg font-semibold mb-3">Alert Statistics</h3>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-800">{stats.total}</div>
            <div className="text-sm text-gray-600">Total</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{stats.active}</div>
            <div className="text-sm text-gray-600">Active</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{stats.acknowledged}</div>
            <div className="text-sm text-gray-600">Acknowledged</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{stats.resolved}</div>
            <div className="text-sm text-gray-600">Resolved</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-600">{stats.suppressed}</div>
            <div className="text-sm text-gray-600">Suppressed</div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="bg-gray-50 p-3 rounded">
            <div className="font-medium text-gray-700">Priority Distribution</div>
            <div className="mt-1">
              <span className="text-red-600">Critical: {stats.byPriority.critical || 0}</span>
              {' | '}
              <span className="text-orange-600">High: {stats.byPriority.high || 0}</span>
              {' | '}
              <span className="text-yellow-600">Medium: {stats.byPriority.medium || 0}</span>
              {' | '}
              <span className="text-blue-600">Low: {stats.byPriority.low || 0}</span>
            </div>
          </div>
          <div className="bg-gray-50 p-3 rounded">
            <div className="font-medium text-gray-700">Trigger Rate</div>
            <div className="mt-1">
              {stats.triggerRate.toFixed(2)} alerts/hour (last 24h)
            </div>
          </div>
          <div className="bg-gray-50 p-3 rounded">
            <div className="font-medium text-gray-700">Avg Resolution Time</div>
            <div className="mt-1">
              {stats.resolutionTime.toFixed(1)} hours
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Render filters panel
  const renderFilters = () => {
    if (!showFilters) return null;

    const quickDateRanges = [
      { label: 'Last 24h', hours: 24 },
      { label: 'Last 7d', hours: 24 * 7 },
      { label: 'Last 30d', hours: 24 * 30 },
      { label: 'Last 90d', hours: 24 * 90 }
    ];

    return (
      <div className="bg-white rounded-lg shadow p-4 mb-4">
        <h3 className="text-lg font-semibold mb-3">Filters</h3>

        <div className="space-y-4">
          {/* Search */}
          <div>
            <input
              type="text"
              placeholder="Search alerts..."
              value={filters.search || ''}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Quick date ranges */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Quick Date Range</label>
            <div className="flex flex-wrap gap-2">
              {quickDateRanges.map(range => (
                <button
                  key={range.label}
                  onClick={() => {
                    const end = new Date();
                    const start = new Date(end.getTime() - range.hours * 60 * 60 * 1000);
                    handleDateRangeChange(start.toISOString(), end.toISOString());
                  }}
                  className="px-3 py-1 text-sm bg-gray-100 rounded hover:bg-gray-200"
                >
                  {range.label}
                </button>
              ))}
            </div>
          </div>

          {/* Priority filters */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Priority</label>
            <div className="flex flex-wrap gap-2">
              {(['critical', 'high', 'medium', 'low'] as AlertPriority[]).map(priority => {
                const isChecked = filters.priorities?.includes(priority);
                return (
                  <label key={priority} className="flex items-center gap-1">
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={(e) => handlePriorityFilter(priority, e.target.checked)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="text-sm capitalize">{priority}</span>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Status filters */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <div className="flex flex-wrap gap-2">
              {(['active', 'acknowledged', 'resolved', 'suppressed'] as Alert['status'][]).map(status => {
                const isChecked = filters.status?.includes(status);
                return (
                  <label key={status} className="flex items-center gap-1">
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={(e) => handleStatusFilter(status, e.target.checked)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="text-sm capitalize">{status}</span>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-between items-center pt-2">
            <button
              onClick={handleResetFilters}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Reset Filters
            </button>
            {allowExport && (
              <button
                onClick={handleExport}
                className="px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600"
              >
                Export
              </button>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Render alert item
  const renderAlert = (alert: Alert) => {
    return (
      <div
        key={alert.id}
        className="bg-white rounded-lg shadow p-4 mb-2 cursor-pointer hover:shadow-md transition-shadow"
        onClick={() => handleAlertClick(alert)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h4 className="font-semibold">{alert.title}</h4>
              <span className={`px-2 py-1 text-xs rounded-full ${getPriorityBadgeColor(alert.priority)}`}>
                {alert.priority}
              </span>
              <span className={`px-2 py-1 text-xs rounded-full ${getStatusBadgeColor(alert.status)}`}>
                {alert.status}
              </span>
            </div>

            <p className="text-sm text-gray-600 mb-2">{alert.message}</p>

            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span>Type: {alert.type}</span>
              <span>Source: {alert.source}</span>
              <span>Rule: {alert.ruleName}</span>
              <span>Triggered: {formatTime(alert.triggeredAt)}</span>
              {alert.acknowledgedAt && (
                <span>Ack: {formatTime(alert.acknowledgedAt)}</span>
              )}
              {alert.resolvedAt && (
                <span>Resolved: {formatTime(alert.resolvedAt)}</span>
              )}
              {!alert.resolvedAt && (
                <span>Duration: {formatDuration(alert.triggeredAt)}</span>
              )}
            </div>
          </div>

          {alert.status === 'active' && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleResolveAlert(alert.id);
              }}
              className="ml-4 px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600"
            >
              Resolve
            </button>
          )}
        </div>
      </div>
    );
  };

  // Render aggregation
  const renderAggregation = (aggregation: AlertAggregation) => {
    const isExpanded = expandedAggregations.has(aggregation.id);

    return (
      <div key={aggregation.id} className="bg-white rounded-lg shadow mb-2">
        <div
          className="p-4 cursor-pointer hover:bg-gray-50"
          onClick={() => handleToggleAggregation(aggregation.id)}
        >
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold">{aggregation.title}</h4>
              <p className="text-sm text-gray-600">{aggregation.summary}</p>
              <div className="flex items-center gap-4 text-xs text-gray-500 mt-1">
                <span>Count: {aggregation.count}</span>
                <span>Type: {aggregation.type}</span>
                <span>Source: {aggregation.source}</span>
                <span>{formatTime(aggregation.createdAt)}</span>
              </div>
            </div>
            <div className="text-gray-400">
              {isExpanded ? '▼' : '▶'}
            </div>
          </div>
        </div>

        {isExpanded && (
          <div className="px-4 pb-4">
            {aggregation.alerts.map(alert => renderAlert(alert))}
          </div>
        )}
      </div>
    );
  };

  // Render pagination
  const renderPagination = () => {
    if (totalPages <= 1) return null;

    return (
      <div className="flex justify-center items-center gap-2 mt-4">
        <button
          onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
          disabled={currentPage === 1}
          className="px-3 py-1 text-sm bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50"
        >
          Previous
        </button>

        <span className="text-sm text-gray-600">
          Page {currentPage} of {totalPages}
        </span>

        <button
          onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
          disabled={currentPage === totalPages}
          className="px-3 py-1 text-sm bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50"
        >
          Next
        </button>
      </div>
    );
  };

  // Render export modal
  const renderExportModal = () => {
    if (!showExportModal) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Export Alert History</h3>
          <p className="text-sm text-gray-600 mb-4">
            Choose export format for {totalRecords} alerts
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => handleExportConfirm('csv')}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Export as CSV
            </button>
            <button
              onClick={() => handleExportConfirm('json')}
              className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            >
              Export as JSON
            </button>
            <button
              onClick={() => setShowExportModal(false)}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className={`alert-history ${className}`}>
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-4 mb-4">
        <h2 className="text-xl font-bold">Alert History</h2>
        <p className="text-sm text-gray-600 mt-1">
          {totalRecords} alerts found
        </p>
      </div>

      {/* Statistics */}
      {renderStatistics()}

      {/* Filters */}
      {renderFilters()}

      {/* Loading state */}
      {isLoading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
          <p className="text-sm text-gray-600 mt-2">Loading alert history...</p>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <p className="text-red-600">Error loading alert history: {error}</p>
        </div>
      )}

      {/* Alerts list */}
      {!isLoading && !error && (
        <>
          <div className="space-y-2">
            {paginatedAlerts.length > 0 ? (
              paginatedAlerts.map(alert => renderAlert(alert))
            ) : (
              <div className="text-center py-8 text-gray-500">
                No alerts found matching the current filters
              </div>
            )}
          </div>

          {/* Aggregations */}
          {history?.aggregations && history.aggregations.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-3">Alert Aggregations</h3>
              {history.aggregations.map(renderAggregation)}
            </div>
          )}

          {/* Pagination */}
          {renderPagination()}
        </>
      )}

      {/* Export modal */}
      {renderExportModal()}
    </div>
  );
};

export default AlertHistory;