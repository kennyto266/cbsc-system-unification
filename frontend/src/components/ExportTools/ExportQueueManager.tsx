import React, { useState, useEffect } from 'react';
import {
  QueueListIcon,
  DocumentArrowDownIcon,
  XMarkIcon,
  ArrowPathIcon,
  TrashIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';
import { useExportQueue, ExportJob } from './utils/exportQueueManager';

interface ExportQueueManagerProps {
  isOpen: boolean;
  onClose: () => void;
}

const ExportQueueManager: React.FC<ExportQueueManagerProps> = ({ isOpen, onClose }) => {
  const {
    jobs,
    cancelJob,
    retryJob,
    clearCompleted,
    getStatistics,
    getEstimatedCompletionTime
  } = useExportQueue();

  const [showCompleted, setShowCompleted] = useState(true);
  const stats = getStatistics();
  const estimatedTime = getEstimatedCompletionTime();

  // Filter jobs based on status
  const activeJobs = jobs.filter(job => job.status === 'pending' || job.status === 'processing');
  const completedJobs = jobs.filter(job => job.status === 'completed' || job.status === 'failed');

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDuration = (ms: number): string => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  const getJobIcon = (status: ExportJob['status']) => {
    switch (status) {
      case 'pending':
        return ClockIcon;
      case 'processing':
        return QueueListIcon;
      case 'completed':
        return CheckCircleIcon;
      case 'failed':
        return XCircleIcon;
      default:
        return ExclamationCircleIcon;
    }
  };

  const getJobIconColor = (status: ExportJob['status']) => {
    switch (status) {
      case 'pending':
        return 'text-gray-400';
      case 'processing':
        return 'text-blue-500';
      case 'completed':
        return 'text-green-500';
      case 'failed':
        return 'text-red-500';
      default:
        return 'text-gray-400';
    }
  };

  const getStatusBadge = (status: ExportJob['status']) => {
    const styles = {
      pending: 'bg-gray-100 text-gray-800',
      processing: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800'
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status]}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-3">
            <QueueListIcon className="w-6 h-6 text-gray-600" />
            <h2 className="text-xl font-semibold text-gray-900">Export Queue</h2>
            {activeJobs.length > 0 && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                {activeJobs.length} active
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Statistics */}
        <div className="p-6 border-b bg-gray-50">
          <div className="grid grid-cols-5 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
              <p className="text-xs text-gray-500">Total</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-yellow-600">{stats.pending}</p>
              <p className="text-xs text-gray-500">Pending</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">{stats.processing}</p>
              <p className="text-xs text-gray-500">Processing</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">{stats.completed}</p>
              <p className="text-xs text-gray-500">Completed</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600">{stats.failed}</p>
              <p className="text-xs text-gray-500">Failed</p>
            </div>
          </div>

          {estimatedTime && (
            <div className="mt-4 text-sm text-gray-600">
              <ClockIcon className="w-4 h-4 inline mr-1" />
              Estimated completion: {estimatedTime.toLocaleTimeString()}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="px-6 py-3 border-b flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <label className="flex items-center text-sm">
              <input
                type="checkbox"
                checked={showCompleted}
                onChange={(e) => setShowCompleted(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mr-2"
              />
              Show completed jobs
            </label>
          </div>
          <button
            onClick={clearCompleted}
            disabled={completedJobs.length === 0}
            className={`flex items-center space-x-1 px-3 py-1.5 text-sm rounded-md transition-colors ${
              completedJobs.length === 0
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-red-50 text-red-600 hover:bg-red-100'
            }`}
          >
            <TrashIcon className="w-4 h-4" />
            <span>Clear Completed</span>
          </button>
        </div>

        {/* Jobs List */}
        <div className="max-h-96 overflow-y-auto">
          {/* Active Jobs */}
          {activeJobs.length > 0 && (
            <div className="p-4">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Active Jobs</h3>
              <div className="space-y-2">
                {activeJobs.map((job) => {
                  const Icon = getJobIcon(job.status);
                  return (
                    <div key={job.id} className="bg-white border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-3">
                          <Icon className={`w-5 h-5 ${getJobIconColor(job.status)}`} />
                          <div>
                            <p className="font-medium text-gray-900">{job.reportName}</p>
                            <p className="text-xs text-gray-500">
                              {job.type.toUpperCase()} • Template: {job.templateId}
                              {job.type === 'batch' && ` • ${job.reportCount} reports`}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          {getStatusBadge(job.status)}
                          {job.status === 'processing' && (
                            <button
                              onClick={() => cancelJob(job.id)}
                              className="p-1 hover:bg-gray-100 rounded transition-colors"
                            >
                              <XMarkIcon className="w-4 h-4 text-gray-500" />
                            </button>
                          )}
                        </div>
                      </div>

                      {job.status === 'processing' && (
                        <div className="mt-3">
                          <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                            <span>Progress</span>
                            <span>{job.progress}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                              style={{ width: `${job.progress}%` }}
                            />
                          </div>
                        </div>
                      )}

                      {job.error && (
                        <div className="mt-2 text-xs text-red-600">
                          Error: {job.error}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Completed Jobs */}
          {showCompleted && completedJobs.length > 0 && (
            <div className="p-4 border-t">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Completed Jobs</h3>
              <div className="space-y-2">
                {completedJobs.map((job) => {
                  const Icon = getJobIcon(job.status);
                  return (
                    <div key={job.id} className="bg-gray-50 border rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <Icon className={`w-5 h-5 ${getJobIconColor(job.status)}`} />
                          <div>
                            <p className="font-medium text-gray-900">{job.reportName}</p>
                            <p className="text-xs text-gray-500">
                              Completed {job.completedAt ? job.completedAt.toLocaleString() : ''}
                              {job.result && ` • ${formatFileSize(job.result.size)}`}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          {getStatusBadge(job.status)}
                          {job.result ? (
                            <a
                              href={job.result.url}
                              download={job.result.filename}
                              className="flex items-center space-x-1 p-1 hover:bg-gray-200 rounded transition-colors"
                            >
                              <DocumentArrowDownIcon className="w-4 h-4 text-gray-600" />
                            </a>
                          ) : job.status === 'failed' && (
                            <button
                              onClick={() => retryJob(job.id)}
                              className="flex items-center space-x-1 p-1 hover:bg-gray-200 rounded transition-colors"
                            >
                              <ArrowPathIcon className="w-4 h-4 text-gray-600" />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Empty State */}
          {activeJobs.length === 0 && (!showCompleted || completedJobs.length === 0) && (
            <div className="text-center py-12">
              <QueueListIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No active exports</h3>
              <p className="mt-1 text-sm text-gray-500">
                Export jobs will appear here when you generate reports.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ExportQueueManager;