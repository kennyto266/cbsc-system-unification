/**
 * Export Service
 * 導出服務 - 支持數據導出、草稿保存和分享功能
 */

import { Strategy, StrategyExecution, BacktestResult, PerformanceReport } from '../types/strategyTypes';

// Draft Types
export interface Draft {
  id: string;
  name: string;
  step: number;
  data: any;
  timestamp: string;
  type: 'strategy' | 'backtest' | 'configuration';
}

// Export Types
export type ExportFormat = 'csv' | 'json' | 'pdf' | 'png';

export interface ExportOptions {
  format: ExportFormat;
  includeMetadata?: boolean;
  includeTimestamp?: boolean;
  includeSource?: boolean;
  compression?: boolean;
  template?: string;
}

export interface ShareOptions {
  expiresAt?: Date;
  password?: string;
  allowDownload?: boolean;
  allowEdit?: boolean;
  maxViews?: number;
}

// Report Template Types
export interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  sections: ReportSection[];
  isDefault: boolean;
}

interface ReportSection {
  id: string;
  title: string;
  type: 'summary' | 'chart' | 'table' | 'text';
  config: Record<string, any>;
  order: number;
}

class ExportService {
  private readonly DRAFTS_KEY = 'cbsc_strategy_drafts';
  private readonly TEMPLATES_KEY = 'cbsc_report_templates';

  // Draft Management
  async saveDraft(draft: Partial<Draft>): Promise<Draft> {
    const drafts = this.getDrafts();
    const id = draft.id || this.generateId();
    const timestamp = new Date().toISOString();

    const newDraft: Draft = {
      id,
      name: draft.name || '未命名草稿',
      step: draft.step || 1,
      data: draft.data || {},
      timestamp: draft.timestamp || timestamp,
      type: draft.type || 'strategy'
    };

    // Update existing or add new
    const existingIndex = drafts.findIndex(d => d.id === id);
    if (existingIndex >= 0) {
      drafts[existingIndex] = newDraft;
    } else {
      drafts.push(newDraft);
    }

    // Keep only last 50 drafts
    if (drafts.length > 50) {
      drafts.splice(0, drafts.length - 50);
    }

    localStorage.setItem(this.DRAFTS_KEY, JSON.stringify(drafts));
    return newDraft;
  }

  async loadDraft(id: string): Promise<Draft | null> {
    const drafts = this.getDrafts();
    return drafts.find(d => d.id === id) || null;
  }

  async deleteDraft(id: string): Promise<boolean> {
    const drafts = this.getDrafts();
    const filtered = drafts.filter(d => d.id !== id);
    localStorage.setItem(this.DRAFTS_KEY, JSON.stringify(filtered));
    return true;
  }

  getDrafts(): Draft[] {
    try {
      const stored = localStorage.getItem(this.DRAFTS_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  }

  // Export Functions
  async exportData(
    data: any,
    format: ExportFormat,
    options: ExportOptions = {}
  ): Promise<Blob> {
    const timestamp = new Date().toISOString();
    const metadata = options.includeMetadata ? {
      exported_at: timestamp,
      exported_by: 'CBSC System',
      version: '1.0.0'
    } : {};

    switch (format) {
      case 'csv':
        return this.exportToCSV(data, { ...options, metadata });
      case 'json':
        return this.exportToJSON(data, { ...options, metadata });
      case 'pdf':
        return this.exportToPDF(data, { ...options, metadata });
      case 'png':
        return this.exportToPNG(data, { ...options, metadata });
      default:
        throw new Error(`Unsupported export format: ${format}`);
    }
  }

  private async exportToCSV(data: any, options: any): Promise<Blob> {
    // Convert data to CSV format
    let csv = '';

    // Add metadata header if enabled
    if (options.metadata) {
      csv += '# CBSC Strategy Export\n';
      csv += `# Exported at: ${options.metadata.exported_at}\n`;
      csv += `# Version: ${options.metadata.version}\n\n`;
    }

    // Process different data types
    if (Array.isArray(data)) {
      if (data.length > 0) {
        // Header row
        const headers = Object.keys(data[0]);
        csv += headers.join(',') + '\n';

        // Data rows
        data.forEach(item => {
          const row = headers.map(header => {
            const value = item[header];
            if (typeof value === 'string' && value.includes(',')) {
              return `"${value}"`;
            }
            return value;
          });
          csv += row.join(',') + '\n';
        });
      }
    } else if (typeof data === 'object') {
      // Single object - convert to key-value pairs
      Object.entries(data).forEach(([key, value]) => {
        csv += `${key},${value}\n`;
      });
    }

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    return options.compression ? this.compressBlob(blob) : blob;
  }

  private async exportToJSON(data: any, options: any): Promise<Blob> {
    const json = JSON.stringify({
      ...(options.metadata && { metadata: options.metadata }),
      data
    }, null, 2);

    const blob = new Blob([json], { type: 'application/json;charset=utf-8;' });
    return options.compression ? this.compressBlob(blob) : blob;
  }

  private async exportToPDF(data: any, options: any): Promise<Blob> {
    // This would typically use a library like jsPDF or PDFKit
    // For now, we'll create a simple HTML to PDF conversion
    const html = this.generateReportHTML(data, options);

    // In a real implementation, this would use a PDF generation service
    // For demonstration, we'll create a simple text representation
    let pdf = 'CBSC Strategy Report\n';
    pdf += '=' .repeat(50) + '\n\n';

    if (options.metadata) {
      pdf += `Generated: ${options.metadata.exported_at}\n`;
      pdf += `Version: ${options.metadata.version}\n\n`;
    }

    pdf += JSON.stringify(data, null, 2);

    const blob = new Blob([pdf], { type: 'application/pdf' });
    return blob;
  }

  private async exportToPNG(data: any, options: any): Promise<Blob> {
    // For chart/data visualization export
    // This would typically use html2canvas or similar library
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    if (!ctx) {
      throw new Error('Cannot export to PNG: Canvas not supported');
    }

    // Set canvas size
    canvas.width = 800;
    canvas.height = 600;

    // Simple text-based visualization
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = '#000000';
    ctx.font = '16px Arial';

    let y = 50;
    if (options.metadata) {
      ctx.fillText(`CBSC Report - ${options.metadata.exported_at}`, 50, y);
      y += 40;
    }

    // Add data content
    const content = JSON.stringify(data, null, 2).substring(0, 500);
    ctx.font = '12px monospace';
    ctx.fillText(content, 50, y);

    return new Promise((resolve) => {
      canvas.toBlob((blob) => {
        if (blob) {
          resolve(blob);
        } else {
          throw new Error('Failed to generate PNG');
        }
      }, 'image/png');
    });
  }

  // Share Functions
  async generateShareLink(
    strategyId: string,
    options: ShareOptions = {}
  ): Promise<string> {
    // Generate a unique share token
    const token = this.generateId();

    // Store share configuration
    const shareData = {
      strategyId,
      token,
      createdAt: new Date().toISOString(),
      expiresAt: options.expiresAt?.toISOString(),
      password: options.password ? btoa(options.password) : undefined,
      allowDownload: options.allowDownload ?? true,
      allowEdit: options.allowEdit ?? false,
      maxViews: options.maxViews,
      viewCount: 0
    };

    // In a real implementation, this would be stored in a backend service
    const shares = this.getShares();
    shares[token] = shareData;
    localStorage.setItem('cbsc_strategy_shares', JSON.stringify(shares));

    // Generate share URL
    const baseUrl = window.location.origin;
    return `${baseUrl}/shared/strategy/${token}`;
  }

  private getShares(): Record<string, any> {
    try {
      const stored = localStorage.getItem('cbsc_strategy_shares');
      return stored ? JSON.parse(stored) : {};
    } catch {
      return {};
    }
  }

  // Report Template Management
  async saveTemplate(template: ReportTemplate): Promise<void> {
    const templates = this.getTemplates();

    const existingIndex = templates.findIndex(t => t.id === template.id);
    if (existingIndex >= 0) {
      templates[existingIndex] = template;
    } else {
      templates.push(template);
    }

    localStorage.setItem(this.TEMPLATES_KEY, JSON.stringify(templates));
  }

  getTemplates(): ReportTemplate[] {
    try {
      const stored = localStorage.getItem(this.TEMPLATES_KEY);
      return stored ? JSON.parse(stored) : this.getDefaultTemplates();
    } catch {
      return this.getDefaultTemplates();
    }
  }

  private getDefaultTemplates(): ReportTemplate[] {
    return [
      {
        id: 'default-summary',
        name: '標準摘要報告',
        description: '包含策略基本資訊和性能指標的標準報告',
        isDefault: true,
        sections: [
          {
            id: 'overview',
            title: '策略概述',
            type: 'summary',
            config: { includeBasicInfo: true, includePerformance: true },
            order: 1
          },
          {
            id: 'performance',
            title: '性能指標',
            type: 'table',
            config: { includeMetrics: ['sharpe', 'sortino', 'max_drawdown', 'win_rate'] },
            order: 2
          },
          {
            id: 'equity',
            title: '權益曲線',
            type: 'chart',
            config: { chartType: 'equity_curve' },
            order: 3
          }
        ]
      },
      {
        id: 'detailed-analysis',
        name: '詳細分析報告',
        description: '包含深入分析和可視化的詳細報告',
        isDefault: false,
        sections: [
          {
            id: 'executive-summary',
            title: '執行摘要',
            type: 'text',
            config: { includeAiInsights: true },
            order: 1
          },
          {
            id: 'risk-analysis',
            title: '風險分析',
            type: 'chart',
            config: { includeVaR: true, includeDrawdownChart: true },
            order: 2
          },
          {
            id: 'trade-analysis',
            title: '交易分析',
            type: 'table',
            config: { includeTradeHistory: true, includeStatistics: true },
            order: 3
          }
        ]
      }
    ];
  }

  // Utility Functions
  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  private async compressBlob(blob: Blob): Promise<Blob> {
    // In a real implementation, this would use compression library
    // For now, just return the original blob
    return blob;
  }

  private generateReportHTML(data: any, options: any): string {
    return `
      <!DOCTYPE html>
      <html>
      <head>
        <title>CBSC Strategy Report</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 20px; }
          .header { border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }
          .section { margin-bottom: 30px; }
          table { border-collapse: collapse; width: 100%; }
          th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
          th { background-color: #f5f5f5; }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>CBSC Strategy Report</h1>
          ${options.metadata ? `<p>Generated: ${options.metadata.exported_at}</p>` : ''}
        </div>
        <div class="content">
          <pre>${JSON.stringify(data, null, 2)}</pre>
        </div>
      </body>
      </html>
    `;
  }
}

// Export singleton instance
export const exportService = new ExportService();

// Helper function to download files
export const downloadFile = async (
  blob: Blob,
  filename: string,
  format: ExportFormat
): Promise<void> => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${filename}.${format}`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

// Export batch data with progress tracking
export const exportBatchData = async (
  items: any[],
  format: ExportFormat,
  options: ExportOptions & { batchSize?: number },
  onProgress?: (progress: number) => void
): Promise<Blob> => {
  const batchSize = options.batchSize || 1000;
  const total = items.length;
  let processed = 0;
  const results: string[] = [];

  for (let i = 0; i < total; i += batchSize) {
    const batch = items.slice(i, i + batchSize);
    const batchBlob = await exportService.exportData(batch, format, options);
    const batchText = await batchBlob.text();
    results.push(batchText);

    processed += batch.length;
    if (onProgress) {
      onProgress(Math.round((processed / total) * 100));
    }
  }

  // Combine all batch results
  const combined = results.join('\n');
  return new Blob([combined], { type: batchToMimeType(format) });
};

function batchToMimeType(format: ExportFormat): string {
  switch (format) {
    case 'csv': return 'text/csv';
    case 'json': return 'application/json';
    case 'pdf': return 'application/pdf';
    case 'png': return 'image/png';
    default: return 'text/plain';
  }
}