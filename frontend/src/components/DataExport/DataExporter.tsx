/**
 * Data Exporter Component
 * 數據導出組件
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Alert } from '../ui/Alert';
import { Loading } from '../ui/Loading';
import { CustomTabs, TabPanel } from '../ui/CustomTabs';
import {
  ArrowDownTrayIcon,
  ShareIcon,
  DocumentIcon,
  TableIcon,
  PhotoIcon,
  ClipboardDocumentIcon,
  ClockIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';
import {
  exportService,
  downloadFile,
  exportBatchData,
  ExportFormat,
  ExportOptions,
  ShareOptions,
  ReportTemplate
} from '../../services/exportService';

interface DataExporterProps {
  isOpen: boolean;
  onClose: () => void;
  data: any;
  title: string;
  type?: 'strategy' | 'backtest' | 'portfolio' | 'report';
  onExportComplete?: (filename: string) => void;
}

interface ExportState {
  format: ExportFormat;
  filename: string;
  includeMetadata: boolean;
  includeTimestamp: boolean;
  includeSource: boolean;
  compression: boolean;
  template?: string;
  isExporting: boolean;
  exportProgress: number;
  error?: string;
}

interface ShareState {
  link?: string;
  expiresAt: Date | null;
  password: string;
  allowDownload: boolean;
  allowEdit: boolean;
  maxViews: number;
  isGenerating: boolean;
  copied: boolean;
}

const DEFAULT_EXPORT_STATE: ExportState = {
  format: 'csv',
  filename: '',
  includeMetadata: true,
  includeTimestamp: true,
  includeSource: true,
  compression: false,
  template: undefined,
  isExporting: false,
  exportProgress: 0
};

const DEFAULT_SHARE_STATE: ShareState = {
  link: undefined,
  expiresAt: null,
  password: '',
  allowDownload: true,
  allowEdit: false,
  maxViews: 0,
  isGenerating: false,
  copied: false
};

export const DataExporter: React.FC<DataExporterProps> = ({
  isOpen,
  onClose,
  data,
  title,
  type = 'strategy',
  onExportComplete
}) => {
  const [activeTab, setActiveTab] = useState<'export' | 'share'>('export');
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [exportState, setExportState] = useState<ExportState>(DEFAULT_EXPORT_STATE);
  const [shareState, setShareState] = useState<ShareState>(DEFAULT_SHARE_STATE);

  // Load templates on mount
  useEffect(() => {
    if (isOpen) {
      const availableTemplates = exportService.getTemplates();
      setTemplates(availableTemplates);

      // Set default filename
      const timestamp = new Date().toISOString().slice(0, 10);
      setExportState(prev => ({
        ...prev,
        filename: `${title}_${timestamp}`
      }));

      // Reset states
      setExportState(DEFAULT_EXPORT_STATE);
      setShareState(DEFAULT_SHARE_STATE);
    }
  }, [isOpen, title]);

  // Check if data is large enough for batch processing
  const isLargeDataset = useCallback(() => {
    if (Array.isArray(data)) {
      return data.length > 1000;
    }
    if (data.trades && Array.isArray(data.trades)) {
      return data.trades.length > 1000;
    }
    if (data.equity_curve && Array.isArray(data.equity_curve)) {
      return data.equity_curve.length > 1000;
    }
    return false;
  }, [data]);

  // Handle format change
  const handleFormatChange = (format: ExportFormat) => {
    setExportState(prev => ({
      ...prev,
      format,
      // Reset template when format changes
      template: format === 'pdf' ? templates.find(t => t.isDefault)?.id : undefined
    }));
  };

  // Validate export options
  const validateExport = (): string | null => {
    if (!exportState.filename.trim()) {
      return '文件名稱不能為空';
    }

    // Check for invalid characters
    const invalidChars = /[<>:"/\\|?*]/;
    if (invalidChars.test(exportState.filename)) {
      return '文件名稱包含無效字符';
    }

    return null;
  };

  // Handle export
  const handleExport = async () => {
    const error = validateExport();
    if (error) {
      setExportState(prev => ({ ...prev, error }));
      return;
    }

    setExportState(prev => ({ ...prev, isExporting: true, error: undefined }));

    try {
      const options: ExportOptions = {
        format: exportState.format,
        includeMetadata: exportState.includeMetadata,
        includeTimestamp: exportState.includeTimestamp,
        includeSource: exportState.includeSource,
        compression: exportState.compression,
        template: exportState.template
      };

      let blob: Blob;

      if (isLargeDataset()) {
        // Use batch export for large datasets
        const dataset = Array.isArray(data) ? data : data.trades || data.equity_curve || [];
        blob = await exportBatchData(
          dataset,
          exportState.format,
          options,
          (progress) => {
            setExportState(prev => ({ ...prev, exportProgress: progress }));
          }
        );
      } else {
        // Standard export
        blob = await exportService.exportData(data, exportState.format, options);
      }

      // Download the file
      await downloadFile(blob, exportState.filename, exportState.format);

      // Success
      onExportComplete?.(exportState.filename);
      onClose();
    } catch (err) {
      console.error('Export failed:', err);
      setExportState(prev => ({
        ...prev,
        error: err instanceof Error ? err.message : '導出失敗',
        isExporting: false
      }));
    }
  };

  // Handle share link generation
  const handleGenerateShareLink = async () => {
    setShareState(prev => ({ ...prev, isGenerating: true }));

    try {
      const options: ShareOptions = {
        expiresAt: shareState.expiresAt || undefined,
        password: shareState.password || undefined,
        allowDownload: shareState.allowDownload,
        allowEdit: shareState.allowEdit,
        maxViews: shareState.maxViews || undefined
      };

      const strategyId = data.id || data.strategy_id || 'unknown';
      const link = await exportService.generateShareLink(strategyId, options);

      setShareState(prev => ({
        ...prev,
        link,
        isGenerating: false
      }));
    } catch (err) {
      console.error('Failed to generate share link:', err);
      setShareState(prev => ({
        ...prev,
        isGenerating: false,
        error: err instanceof Error ? err.message : '生成分享鏈接失敗'
      }));
    }
  };

  // Handle copy to clipboard
  const handleCopyLink = async () => {
    if (!shareState.link) return;

    try {
      await navigator.clipboard.writeText(shareState.link);
      setShareState(prev => ({ ...prev, copied: true }));
      setTimeout(() => {
        setShareState(prev => ({ ...prev, copied: false }));
      }, 2000);
    } catch (err) {
      console.error('Failed to copy link:', err);
    }
  };

  // Calculate expiration date
  const getExpirationDate = (days: number): Date => {
    const date = new Date();
    date.setDate(date.getDate() + days);
    return date;
  };

  // Get format icon
  const getFormatIcon = (format: ExportFormat) => {
    switch (format) {
      case 'csv':
        return TableIcon;
      case 'json':
        return DocumentIcon;
      case 'pdf':
        return DocumentIcon;
      case 'png':
        return PhotoIcon;
      default:
        return DocumentIcon;
    }
  };

  // Get format description
  const getFormatDescription = (format: ExportFormat) => {
    switch (format) {
      case 'csv':
        return '適合在 Excel 或其他電子表格軟件中打開';
      case 'json':
        return '結構化數據格式，適合程序化處理';
      case 'pdf':
        return '專業報告格式，適合分享和打印';
      case 'png':
        return '圖片格式，適合截圖和展示';
      default:
        return '';
    }
  };

  if (!isOpen) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="數據導出與分享"
      size="lg"
    >
      <CustomTabs
        tabs={[
          { id: 'export', label: '導出', icon: ArrowDownTrayIcon },
          { id: 'share', label: '分享', icon: ShareIcon }
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      {/* Export Tab */}
      {activeTab === 'export' && (
        <div className="space-y-6">
          {/* Format Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              選擇導出格式
            </label>
            <div className="grid grid-cols-2 gap-4">
              {(['csv', 'json', 'pdf', 'png'] as ExportFormat[]).map((format) => {
                const Icon = getFormatIcon(format);
                return (
                  <label
                    key={format}
                    className={`
                      relative flex items-center p-4 border-2 rounded-lg cursor-pointer transition-colors
                      ${exportState.format === format
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                      }
                    `}
                  >
                    <input
                      type="radio"
                      name="format"
                      value={format}
                      checked={exportState.format === format}
                      onChange={() => handleFormatChange(format)}
                      className="sr-only"
                    />
                    <Icon className="w-6 h-6 text-gray-600 dark:text-gray-400 mr-3" />
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white uppercase">
                        {format}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {getFormatDescription(format)}
                      </p>
                    </div>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Filename Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              文件名稱 <span className="text-red-500">*</span>
            </label>
            <Input
              value={exportState.filename}
              onChange={(e) => setExportState(prev => ({ ...prev, filename: e.target.value }))}
              placeholder="輸入文件名稱"
              error={exportState.error}
            />
          </div>

          {/* Export Options */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              導出選項
            </label>
            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={exportState.includeMetadata}
                  onChange={(e) => setExportState(prev => ({ ...prev, includeMetadata: e.target.checked }))}
                  className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  包含元數據（導出時間、版本等）
                </span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={exportState.includeTimestamp}
                  onChange={(e) => setExportState(prev => ({ ...prev, includeTimestamp: e.target.checked }))}
                  className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  包含時間戳
                </span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={exportState.includeSource}
                  onChange={(e) => setExportState(prev => ({ ...prev, includeSource: e.target.checked }))}
                  className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  包含數據源信息
                </span>
              </label>

              {isLargeDataset() && (
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={exportState.compression}
                    onChange={(e) => setExportState(prev => ({ ...prev, compression: e.target.checked }))}
                    className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                    壓縮文件（推薦用於大型數據集）
                  </span>
                </label>
              )}
            </div>
          </div>

          {/* PDF Template Selection */}
          {exportState.format === 'pdf' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                選擇模板
              </label>
              <select
                className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                value={exportState.template || ''}
                onChange={(e) => setExportState(prev => ({ ...prev, template: e.target.value }))}
              >
                <option value="">默認模板</option>
                {templates.map((template) => (
                  <option key={template.id} value={template.id}>
                    {template.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Large Dataset Warning */}
          {isLargeDataset() && (
            <Alert
              variant="warning"
              title="大型數據集"
              description="數據量較大，將分批處理。導出可能需要一些時間。"
            />
          )}

          {/* Export Progress */}
          {exportState.isExporting && exportState.exportProgress > 0 && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  導出進度
                </span>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {exportState.exportProgress}%
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-600 dark:bg-blue-400 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${exportState.exportProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Export Actions */}
          <div className="flex justify-end space-x-3">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={exportState.isExporting}
            >
              取消
            </Button>
            <Button
              variant="primary"
              icon={ArrowDownTrayIcon}
              onClick={handleExport}
              disabled={exportState.isExporting}
              loading={exportState.isExporting}
            >
              {exportState.isExporting ? '導出中...' : '導出'}
            </Button>
          </div>
        </div>
      )}

      {/* Share Tab */}
      {activeTab === 'share' && (
        <div className="space-y-6">
          {/* Share Options */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              分享設置
            </label>
            <div className="space-y-4">
              {/* Expiration */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  鏈接有效期
                </label>
                <select
                  className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  value={shareState.expiresAt ? getExpirationDate(7).toISOString().slice(0, 10) : ''}
                  onChange={(e) => {
                    const days = parseInt(e.target.value);
                    setShareState(prev => ({
                      ...prev,
                      expiresAt: days > 0 ? getExpirationDate(days) : null
                    }));
                  }}
                >
                  <option value="">永不過期</option>
                  <option value="1">1 天</option>
                  <option value="7">7 天</option>
                  <option value="30">30 天</option>
                  <option value="90">90 天</option>
                </select>
              </div>

              {/* Password Protection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  密碼保護（可選）
                </label>
                <Input
                  type="password"
                  value={shareState.password}
                  onChange={(e) => setShareState(prev => ({ ...prev, password: e.target.value }))}
                  placeholder="輸入密碼以保護分享鏈接"
                />
              </div>

              {/* Permissions */}
              <div className="space-y-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={shareState.allowDownload}
                    onChange={(e) => setShareState(prev => ({ ...prev, allowDownload: e.target.checked }))}
                    className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                    允許下載原始數據
                  </span>
                </label>

                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={shareState.allowEdit}
                    onChange={(e) => setShareState(prev => ({ ...prev, allowEdit: e.target.checked }))}
                    className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                    允許編輯策略配置
                  </span>
                </label>
              </div>

              {/* View Limit */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  最大瀏覽次數（可選）
                </label>
                <Input
                  type="number"
                  min="0"
                  value={shareState.maxViews}
                  onChange={(e) => setShareState(prev => ({ ...prev, maxViews: parseInt(e.target.value) || 0 }))}
                  placeholder="0 表示無限制"
                />
              </div>
            </div>
          </div>

          {/* Generate Share Link */}
          {!shareState.link ? (
            <div className="flex justify-end">
              <Button
                variant="primary"
                icon={ShareIcon}
                onClick={handleGenerateShareLink}
                disabled={shareState.isGenerating}
                loading={shareState.isGenerating}
              >
                {shareState.isGenerating ? '生成中...' : '生成分享鏈接'}
              </Button>
            </div>
          ) : (
            /* Share Link Display */
            <div className="space-y-4">
              <Alert
                variant="success"
                title="分享鏈接已生成"
                description="使用以下鏈接分享您的策略數據"
              />

              <div className="flex items-center space-x-2">
                <Input
                  value={shareState.link}
                  readOnly
                  className="flex-1"
                />
                <Button
                  variant="outline"
                  size="sm"
                  icon={shareState.copied ? ClipboardDocumentIcon : ClipboardDocumentIcon}
                  onClick={handleCopyLink}
                  className={shareState.copied ? 'text-green-600' : ''}
                >
                  {shareState.copied ? '已複製' : '複製'}
                </Button>
              </div>

              {/* Share Info */}
              <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <ShieldCheckIcon className="w-5 h-5 text-green-600 dark:text-green-400 mt-0.5" />
                  <div className="text-sm text-gray-700 dark:text-gray-300">
                    <p className="font-medium mb-1">安全設置</p>
                    <ul className="space-y-1 text-xs">
                      {shareState.expiresAt && (
                        <li>• 鏈接將於 {shareState.expiresAt.toLocaleDateString()} 過期</li>
                      )}
                      {shareState.password && (
                        <li>• 已設置密碼保護</li>
                      )}
                      <li>• 訪問日誌已記錄</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end space-x-3">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShareState(DEFAULT_SHARE_STATE);
                    setActiveTab('export');
                  }}
                >
                  創建新鏈接
                </Button>
                <Button variant="primary" onClick={onClose}>
                  完成
                </Button>
              </div>
            </div>
          )}

          {shareState.error && (
            <Alert
              variant="error"
              title="錯誤"
              description={shareState.error}
            />
          )}
        </div>
      )}
    </Modal>
  );
};