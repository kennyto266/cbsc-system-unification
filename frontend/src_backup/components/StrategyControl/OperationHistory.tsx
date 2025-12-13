import React, { useState, useEffect } from 'react';
import { OperationHistoryResponse } from '../../services/strategyControlService';

interface OperationHistoryProps {
  strategyId: string;
  strategyName: string;
  isVisible: boolean;
  onClose: () => void;
}

interface FormattedLog {
  id: string;
  action: string;
  actionText: string;
  description: string;
  timestamp: string;
  status: 'success' | 'failed';
  reason?: string;
}

export const OperationHistory: React.FC<OperationHistoryProps> = ({
  strategyId,
  strategyName,
  isVisible,
  onClose
}) => {
  const [logs, setLogs] = useState<FormattedLog[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 加载操作历史
  const loadOperationHistory = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // 这里应该调用API服务获取操作历史
      // const response = await strategyControlService.getOperationHistory(strategyId, 50);

      // 模拟数据
      const mockLogs: FormattedLog[] = [
        {
          id: '1',
          action: 'enable',
          actionText: '启用',
          description: '启用策略: 已停止 → 运行中',
          timestamp: '2025-12-10 15:30:00',
          status: 'success',
          reason: '市场条件良好，适合启动策略'
        },
        {
          id: '2',
          action: 'pause',
          actionText: '暂停',
          description: '暂停策略: 运行中 → 已停止',
          timestamp: '2025-12-10 14:25:00',
          status: 'success',
          reason: '即将进行系统维护'
        },
        {
          id: '3',
          action: 'batch_disable',
          actionText: '批量禁用',
          description: '批量禁用: 运行中 → 已停止',
          timestamp: '2025-12-10 13:15:00',
          status: 'success',
          reason: '风险控制，降低整体风险敞口'
        },
        {
          id: '4',
          action: 'stop',
          actionText: '停止',
          description: '停止策略: 运行中 → 已停止',
          timestamp: '2025-12-10 12:00:00',
          status: 'failed',
          reason: '紧急风险控制'
        },
        {
          id: '5',
          action: 'start',
          actionText: '启动',
          description: '启动策略: 已停止 → 运行中',
          timestamp: '2025-12-10 10:30:00',
          status: 'success'
        }
      ];

      setLogs(mockLogs);
    } catch (err) {
      console.error('加载操作历史失败:', err);
      setError(err instanceof Error ? err.message : '加载操作历史失败');
    } finally {
      setIsLoading(false);
    }
  };

  // 组件显示时加载历史
  useEffect(() => {
    if (isVisible && strategyId) {
      loadOperationHistory();
    }
  }, [isVisible, strategyId]);

  // 获取操作图标
  const getActionIcon = (action: string) => {
    switch (action) {
      case 'enable':
      case 'start':
        return (
          <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        );
      case 'disable':
      case 'stop':
        return (
          <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10h6v4H9z" />
            </svg>
          </div>
        );
      case 'pause':
        return (
          <div className="w-8 h-8 rounded-full bg-yellow-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6" />
            </svg>
          </div>
        );
      case 'batch_enable':
      case 'batch_start':
        return (
          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        );
      case 'batch_disable':
      case 'batch_stop':
        return (
          <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </div>
        );
      default:
        return (
          <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        );
    }
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-3xl w-full max-h-[80vh] mx-4 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">操作历史</h2>
              <p className="text-sm text-gray-500 mt-1">策略: {strategyName}</p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-3 text-gray-600">加载操作历史中...</span>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="text-red-600 mb-4">
                  <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.314 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">加载失败</h3>
                <p className="text-gray-600 mb-4">{error}</p>
                <button
                  onClick={loadOperationHistory}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  重新加载
                </button>
              </div>
            </div>
          ) : logs.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-400 mb-4">
                <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">暂无操作记录</h3>
              <p className="text-gray-600">该策略还没有执行过任何操作</p>
            </div>
          ) : (
            <div className="space-y-4">
              {logs.map((log) => (
                <div key={log.id} className="flex space-x-4 p-4 bg-gray-50 rounded-lg">
                  {/* Action Icon */}
                  <div className="flex-shrink-0 mt-0.5">
                    {getActionIcon(log.action)}
                  </div>

                  {/* Log Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {log.actionText}
                          {log.action.startsWith('batch_') && (
                            <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                              批量操作
                            </span>
                          )}
                        </p>
                        <p className="text-sm text-gray-600 mt-1">{log.description}</p>
                        {log.reason && (
                          <p className="text-xs text-gray-500 mt-2">
                            原因: {log.reason}
                          </p>
                        )}
                      </div>
                      <div className="flex flex-col items-end space-y-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          log.status === 'success'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {log.status === 'success' ? '成功' : '失败'}
                        </span>
                        <span className="text-xs text-gray-500">
                          {log.timestamp}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-600">
              共 {logs.length} 条操作记录
            </p>
            <div className="flex space-x-3">
              <button
                onClick={() => {
                  // 导出功能
                  const csvContent = [
                    ['时间', '操作', '描述', '状态', '原因'],
                    ...logs.map(log => [
                      log.timestamp,
                      log.actionText,
                      log.description,
                      log.status === 'success' ? '成功' : '失败',
                      log.reason || ''
                    ])
                  ].map(row => row.join(',')).join('\n');

                  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                  const link = document.createElement('a');
                  link.href = URL.createObjectURL(blob);
                  link.download = `${strategyName}_操作历史_${new Date().toISOString().split('T')[0]}.csv`;
                  link.click();
                }}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors text-sm font-medium"
              >
                导出CSV
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OperationHistory;