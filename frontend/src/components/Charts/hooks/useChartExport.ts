import { useRef, useState } from 'react';
import html2canvas from 'html2canvas';
import { useToast } from '../../hooks/useToast';

// 导出配置接口
interface ExportConfig {
  filename?: string;
  format?: 'png' | 'svg' | 'csv' | 'json';
  quality?: number;
  scale?: number;
}

// 返回类型
interface UseChartExportReturn {
  isExporting: boolean;
  exportChart: (config?: ExportConfig) => Promise<void>;
  exportData: (data: any[], config?: ExportConfig) => Promise<void>;
}

export const useChartExport = (chartRef?: React.RefObject<HTMLElement>): UseChartExportReturn => {
  const [isExporting, setIsExporting] = useState(false);
  const { addToast } = useToast();

  // 导出图表为图片
  const exportChart = async (config: ExportConfig = {}) => {
    if (!chartRef?.current) {
      addToast({
        type: 'error',
        message: '图表引用不存在'
      });
      return;
    }

    setIsExporting(true);

    try {
      const {
        filename = `chart-${Date.now()}`,
        format = 'png',
        quality = 0.95,
        scale = 2
      } = config;

      if (format === 'png' || format === 'jpeg') {
        // 导出为PNG/JPEG
        const canvas = await html2canvas(chartRef.current, {
          backgroundColor: '#ffffff',
          scale: scale,
          logging: false,
          useCORS: true,
          allowTaint: true
        });

        const link = document.createElement('a');
        link.download = `${filename}.${format}`;
        link.href = canvas.toDataURL(`image/${format}`, quality);
        link.click();
      } else if (format === 'svg') {
        // 如果是SVG格式，需要查找SVG元素
        const svgElement = chartRef.current.querySelector('svg');
        if (svgElement) {
          const svgData = new XMLSerializer().serializeToString(svgElement);
          const blob = new Blob([svgData], { type: 'image/svg+xml' });
          const url = URL.createObjectURL(blob);

          const link = document.createElement('a');
          link.download = `${filename}.svg`;
          link.href = url;
          link.click();

          URL.revokeObjectURL(url);
        } else {
          throw new Error('未找到SVG元素');
        }
      }

      addToast({
        type: 'success',
        message: `图表已导出为 ${format.toUpperCase()} 格式`
      });
    } catch (error) {
      console.error('Export error:', error);
      addToast({
        type: 'error',
        message: '导出失败，请重试'
      });
    } finally {
      setIsExporting(false);
    }
  };

  // 导出数据为CSV或JSON
  const exportData = async (data: any[], config: ExportConfig = {}) => {
    setIsExporting(true);

    try {
      const {
        filename = `data-${Date.now()}`,
        format = 'csv'
      } = config;

      if (format === 'csv') {
        // 导出为CSV
        if (data.length === 0) {
          throw new Error('没有数据可导出');
        }

        // 获取所有列名
        const columns = Object.keys(data[0]);

        // 构建CSV内容
        const header = columns.join(',');
        const rows = data.map(item => {
          return columns.map(col => {
            const value = item[col];
            // 处理包含逗号或引号的值
            if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
              return `"${value.replace(/"/g, '""')}"`;
            }
            return value;
          }).join(',');
        });

        const csvContent = [header, ...rows].join('\n');

        // 添加BOM以支持中文
        const BOM = '\uFEFF';
        const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8' });
        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.download = `${filename}.csv`;
        link.href = url;
        link.click();

        URL.revokeObjectURL(url);
      } else if (format === 'json') {
        // 导出为JSON
        const jsonContent = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonContent], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.download = `${filename}.json`;
        link.href = url;
        link.click();

        URL.revokeObjectURL(url);
      }

      addToast({
        type: 'success',
        message: `数据已导出为 ${format.toUpperCase()} 格式`
      });
    } catch (error) {
      console.error('Export error:', error);
      addToast({
        type: 'error',
        message: error instanceof Error ? error.message : '导出失败，请重试'
      });
    } finally {
      setIsExporting(false);
    }
  };

  return {
    isExporting,
    exportChart,
    exportData
  };
};