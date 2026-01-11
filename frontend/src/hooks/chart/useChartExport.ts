/**
 * useChartExport Hook
 *
 * A comprehensive hook for exporting charts to various formats including PNG, JPG, SVG, CSV, and JSON.
 * Supports custom dimensions, quality settings, and multiple chart libraries.
 *
 * @example
 * ```tsx
 * const MyChart = () => {
 *   const chartRef = useRef<HTMLCanvasElement>(null);
 *   const { exportToPNG, exportToSVG, exportToCSV, isExporting } = useChartExport({
 *     chartRef,
 *     chartType: 'chartjs',
 *     filename: 'my-chart',
 *     data: chartData
 *   });
 *
 *   return (
 *     <div>
 *       <canvas ref={chartRef} />
 *       <button onClick={() => exportToPNG({ width: 1920, height: 1080 })}>
 *         Export as PNG
 *       </button>
 *     </div>
 *   );
 * };
 * ```
 */

import { useState, useRef, useCallback, useMemo } from 'react';
import { ChartDataPoint } from './useRealtimeChart';

// Types for the hook
export type ChartType = 'chartjs' | 'plotly' | 'recharts' | 'antd' | 'custom';

export type ExportFormat = 'png' | 'jpg' | 'jpeg' | 'svg' | 'csv' | 'json';

export interface ExportOptions {
  /** Export width in pixels */
  width?: number;
  /** Export height in pixels */
  height?: number;
  /** Quality for lossy formats (0-1) */
  quality?: number;
  /** Background color for image formats */
  backgroundColor?: string;
  /** Scale factor for high-DPI displays */
  scale?: number;
  /** Include chart legend */
  includeLegend?: boolean;
  /** Include chart title */
  includeTitle?: boolean;
  /** Custom filename without extension */
  filename?: string;
  /** Export data only (no chart visualization) */
  dataOnly?: boolean;
}

export interface ChartExportConfig {
  /** Reference to the chart element */
  chartRef: React.RefObject<HTMLElement>;
  /** Type of chart library being used */
  chartType?: ChartType;
  /** Chart data for CSV/JSON export */
  data?: any[] | ChartDataPoint[];
  /** Default filename for exports */
  filename?: string;
  /** Default export options */
  defaultOptions?: Partial<ExportOptions>;
  /** Custom export function for non-standard chart types */
  customExportFunction?: (format: ExportFormat, options: ExportOptions) => Promise<Blob | null>;
  /** Enable debug logging */
  enableDebug?: boolean;
}

export interface ChartExportState {
  /** Currently exporting format */
  isExporting: ExportFormat | null;
  /** Last export error */
  error: Error | null;
  /** Export history */
  exportHistory: Array<{
    format: ExportFormat;
    timestamp: number;
    filename: string;
    options: ExportOptions;
  }>;
}

export interface ChartExportActions {
  /** Export chart to PNG format */
  exportToPNG: (options?: ExportOptions) => Promise<void>;
  /** Export chart to JPG format */
  exportToJPG: (options?: ExportOptions) => Promise<void>;
  /** Export chart to SVG format */
  exportToSVG: (options?: ExportOptions) => Promise<void>;
  /** Export chart data to CSV format */
  exportToCSV: (options?: ExportOptions) => Promise<void>;
  /** Export chart data to JSON format */
  exportToJSON: (options?: ExportOptions) => Promise<void>;
  /** Export chart to specified format */
  export: (format: ExportFormat, options?: ExportOptions) => Promise<void>;
  /** Get chart as blob */
  getChartBlob: (format: ExportFormat, options?: ExportOptions) => Promise<Blob | null>;
  /** Clear export history */
  clearHistory: () => void;
}

export interface UseChartExportReturn extends ChartExportState, ChartExportActions {}

// Default configuration
const DEFAULT_CONFIG: Partial<ChartExportConfig> = {
  chartType: 'chartjs',
  filename: 'chart',
  defaultOptions: {
    width: 1920,
    height: 1080,
    quality: 0.9,
    backgroundColor: '#ffffff',
    scale: 2,
    includeLegend: true,
    includeTitle: true,
  },
  enableDebug: false,
};

// Utility functions
const generateFilename = (baseName: string, format: ExportFormat): string => {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
  const extension = format === 'jpeg' ? 'jpg' : format;
  return `${baseName}-${timestamp}.${extension}`;
};

const downloadBlob = (blob: Blob, filename: string): void => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

const convertCanvasToBlob = (
  canvas: HTMLCanvasElement,
  format: 'png' | 'jpeg' | 'jpg',
  quality?: number
): Promise<Blob | null> => {
  return new Promise((resolve) => {
    canvas.toBlob(
      (blob) => resolve(blob),
      `image/${format}`,
      quality
    );
  });
};

const createSVGElement = (element: HTMLElement): string => {
  const svgElement = element.querySelector('svg');
  if (!svgElement) return '';

  const serializer = new XMLSerializer();
  let svgString = serializer.serializeToString(svgElement);

  // Add XML declaration and namespace if not present
  if (!svgString.startsWith('<?xml')) {
    svgString = '<?xml version="1.0" encoding="UTF-8"?>' + svgString;
  }

  // Make sure xmlns is present
  if (!svgString.includes('xmlns="http://www.w3.org/2000/svg"')) {
    svgString = svgString.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"');
  }

  return svgString;
};

const exportDataToCSV = (data: any[] | ChartDataPoint[]): string => {
  if (!data || data.length === 0) return '';

  // Get headers from first object
  const firstItem = data[0];
  const headers = Object.keys(firstItem);

  // Create CSV content
  const csvContent = [
    headers.join(','),
    ...data.map(item =>
      headers.map(header => {
        const value = item[header];
        // Handle nested objects and arrays
        if (typeof value === 'object' && value !== null) {
          return `"${JSON.stringify(value).replace(/"/g, '""')}"`;
        }
        // Handle strings with commas
        if (typeof value === 'string' && value.includes(',')) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
      }).join(',')
    )
  ].join('\n');

  return csvContent;
};

const exportDataToJSON = (data: any[] | ChartDataPoint[], pretty: boolean = true): string => {
  return JSON.stringify(data, null, pretty ? 2 : 0);
};

const applyScaleToCanvas = (
  canvas: HTMLCanvasElement,
  scale: number
): HTMLCanvasElement => {
  const scaledCanvas = document.createElement('canvas');
  const ctx = scaledCanvas.getContext('2d')!;

  scaledCanvas.width = canvas.width * scale;
  scaledCanvas.height = canvas.height * scale;

  ctx.scale(scale, scale);
  ctx.drawImage(canvas, 0, 0);

  return scaledCanvas;
};

/**
 * useChartExport Hook
 *
 * @param config - Configuration object for chart export functionality
 * @returns Hook state and actions
 */
export const useChartExport = (config: ChartExportConfig): UseChartExportReturn => {
  const finalConfig = { ...DEFAULT_CONFIG, ...config };

  // State management
  const [isExporting, setIsExporting] = useState<ExportFormat | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [exportHistory, setExportHistory] = useState<Array<{
    format: ExportFormat;
    timestamp: number;
    filename: string;
    options: ExportOptions;
  }>>([]);

  // Track export state
  const isExportingRef = useRef(false);

  // Internal export function
  const performExport = useCallback(async (
    format: ExportFormat,
    options: ExportOptions = {}
  ): Promise<Blob | null> => {
    if (!config.chartRef.current) {
      throw new Error('Chart reference is null. Make sure the chart is mounted.');
    }

    if (isExportingRef.current) {
      throw new Error('Export already in progress. Please wait for the current export to complete.');
    }

    // Merge with default options
    const finalOptions = { ...finalConfig.defaultOptions, ...options };

    setIsExporting(format);
    isExportingRef.current = true;
    setError(null);

    try {
      let blob: Blob | null = null;

      // Use custom export function if provided
      if (finalConfig.customExportFunction) {
        blob = await finalConfig.customExportFunction(format, finalOptions);
      } else {
        // Default export logic based on chart type and format
        const chartElement = finalConfig.chartRef.current;

        switch (finalConfig.chartType) {
          case 'chartjs':
            blob = await exportChartJS(chartElement, format, finalOptions);
            break;
          case 'plotly':
            blob = await exportPlotly(chartElement, format, finalOptions);
            break;
          case 'recharts':
            blob = await exportRecharts(chartElement, format, finalOptions);
            break;
          case 'antd':
            blob = await exportAntd(chartElement, format, finalOptions);
            break;
          default:
            throw new Error(`Unsupported chart type: ${finalConfig.chartType}`);
        }
      }

      // Handle data-only exports
      if (finalOptions.dataOnly && (format === 'csv' || format === 'json')) {
        if (!finalConfig.data) {
          throw new Error('No data available for export');
        }

        const content = format === 'csv'
          ? exportDataToCSV(finalConfig.data)
          : exportDataToJSON(finalConfig.data);

        blob = new Blob([content], { type: format === 'csv' ? 'text/csv' : 'application/json' });
      }

      // Add to history
      const filename = finalOptions.filename
        ? generateFilename(finalOptions.filename, format)
        : generateFilename(finalConfig.filename || 'chart', format);

      setExportHistory(prev => [...prev, {
        format,
        timestamp: Date.now(),
        filename,
        options: finalOptions
      }]);

      finalConfig.enableDebug &&
        console.log(`[useChartExport] Exported to ${format}:`, { filename, options: finalOptions });

      return blob;

    } catch (err) {
      const error = err as Error;
      setError(error);
      finalConfig.enableDebug && console.error(`[useChartExport] Export failed:`, error);
      throw error;
    } finally {
      setIsExporting(null);
      isExportingRef.current = false;
    }
  }, [config, finalConfig]);

  // Chart library-specific export functions
  const exportChartJS = async (
    element: HTMLElement,
    format: ExportFormat,
    options: ExportOptions
  ): Promise<Blob | null> => {
    const canvas = element as HTMLCanvasElement;

    if (format === 'svg') {
      // Chart.js doesn't natively support SVG export
      throw new Error('SVG export is not supported for Chart.js. Consider using a third-party library.');
    }

    let exportCanvas = canvas;

    // Apply scaling if needed
    if (options.scale && options.scale !== 1) {
      exportCanvas = applyScaleToCanvas(canvas, options.scale);
    }

    const imageFormat = format === 'jpg' || format === 'jpeg' ? 'jpeg' : 'png';
    const blob = await convertCanvasToBlob(exportCanvas, imageFormat, options.quality);

    // Cleanup scaled canvas
    if (exportCanvas !== canvas) {
      exportCanvas.remove();
    }

    return blob;
  };

  const exportPlotly = async (
    element: HTMLElement,
    format: ExportFormat,
    options: ExportOptions
  ): Promise<Blob | null> => {
    // Plotly export requires the plotly.js library to be available
    if (typeof (window as any).Plotly === 'undefined') {
      throw new Error('Plotly library not found. Make sure plotly.js is loaded.');
    }

    const plotlyElement = element;
    const width = options.width || plotlyElement.offsetWidth;
    const height = options.height || plotlyElement.offsetHeight;

    switch (format) {
      case 'png':
        return (window as any).Plotly.toImage(plotlyElement, {
          format: 'png',
          width,
          height,
          scale: options.scale || 1,
        }).then((dataUrl: string) => {
          const response = fetch(dataUrl);
          return response.then(r => r.blob());
        });

      case 'jpg':
      case 'jpeg':
        return (window as any).Plotly.toImage(plotlyElement, {
          format: 'jpeg',
          width,
          height,
          scale: options.scale || 1,
        }).then((dataUrl: string) => {
          const response = fetch(dataUrl);
          return response.then(r => r.blob());
        });

      case 'svg':
        return (window as any).Plotly.toSVG(plotlyElement, {
          width,
          height,
        }).then((svgString: string) => {
          return new Blob([svgString], { type: 'image/svg+xml' });
        });

      default:
        throw new Error(`Unsupported export format for Plotly: ${format}`);
    }
  };

  const exportRecharts = async (
    element: HTMLElement,
    format: ExportFormat,
    options: ExportOptions
  ): Promise<Blob | null> => {
    // Recharts renders to SVG, so we can export SVG directly
    if (format === 'svg') {
      const svgString = createSVGElement(element);
      return new Blob([svgString], { type: 'image/svg+xml' });
    }

    // For raster formats, we need to convert SVG to canvas
    const svgString = createSVGElement(element);
    const img = new Image();
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d')!;

    canvas.width = options.width || element.offsetWidth;
    canvas.height = options.height || element.offsetHeight;

    return new Promise((resolve, reject) => {
      img.onload = () => {
        // Fill background if specified
        if (options.backgroundColor) {
          ctx.fillStyle = options.backgroundColor;
          ctx.fillRect(0, 0, canvas.width, canvas.height);
        }

        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

        const imageFormat = format === 'jpg' || format === 'jpeg' ? 'jpeg' : 'png';
        canvas.toBlob(
          (blob) => resolve(blob),
          `image/${imageFormat}`,
          options.quality
        );
      };

      img.onerror = () => reject(new Error('Failed to load SVG'));
      img.src = 'data:image/svg+xml;base64,' + btoa(svgString);
    });
  };

  const exportAntd = async (
    element: HTMLElement,
    format: ExportFormat,
    options: ExportOptions
  ): Promise<Blob | null> => {
    // Ant Design charts are built on G2, which renders to canvas
    const canvas = element.querySelector('canvas');

    if (!canvas) {
      // If no canvas found, try to find SVG
      const svgString = createSVGElement(element);
      if (svgString && format === 'svg') {
        return new Blob([svgString], { type: 'image/svg+xml' });
      }
      throw new Error('Could not find canvas or SVG element in Ant Design chart');
    }

    let exportCanvas = canvas as HTMLCanvasElement;

    // Apply scaling if needed
    if (options.scale && options.scale !== 1) {
      exportCanvas = applyScaleToCanvas(canvas, options.scale);
    }

    const imageFormat = format === 'jpg' || format === 'jpeg' ? 'jpeg' : 'png';
    const blob = await convertCanvasToBlob(exportCanvas, imageFormat, options.quality);

    // Cleanup scaled canvas
    if (exportCanvas !== canvas) {
      exportCanvas.remove();
    }

    return blob;
  };

  // Public actions
  const exportToPNG = useCallback(async (options?: ExportOptions) => {
    const blob = await performExport('png', options);
    if (blob) {
      const filename = generateFilename(options?.filename || finalConfig.filename || 'chart', 'png');
      downloadBlob(blob, filename);
    }
  }, [performExport, finalConfig.filename]);

  const exportToJPG = useCallback(async (options?: ExportOptions) => {
    const blob = await performExport('jpg', options);
    if (blob) {
      const filename = generateFilename(options?.filename || finalConfig.filename || 'chart', 'jpg');
      downloadBlob(blob, filename);
    }
  }, [performExport, finalConfig.filename]);

  const exportToSVG = useCallback(async (options?: ExportOptions) => {
    const blob = await performExport('svg', options);
    if (blob) {
      const filename = generateFilename(options?.filename || finalConfig.filename || 'chart', 'svg');
      downloadBlob(blob, filename);
    }
  }, [performExport, finalConfig.filename]);

  const exportToCSV = useCallback(async (options?: ExportOptions) => {
    const blob = await performExport('csv', { ...options, dataOnly: true });
    if (blob) {
      const filename = generateFilename(options?.filename || finalConfig.filename || 'chart', 'csv');
      downloadBlob(blob, filename);
    }
  }, [performExport, finalConfig.filename]);

  const exportToJSON = useCallback(async (options?: ExportOptions) => {
    const blob = await performExport('json', { ...options, dataOnly: true });
    if (blob) {
      const filename = generateFilename(options?.filename || finalConfig.filename || 'chart', 'json');
      downloadBlob(blob, filename);
    }
  }, [performExport, finalConfig.filename]);

  const export = useCallback(async (format: ExportFormat, options?: ExportOptions) => {
    switch (format) {
      case 'png':
        return exportToPNG(options);
      case 'jpg':
      case 'jpeg':
        return exportToJPG(options);
      case 'svg':
        return exportToSVG(options);
      case 'csv':
        return exportToCSV(options);
      case 'json':
        return exportToJSON(options);
      default:
        throw new Error(`Unsupported export format: ${format}`);
    }
  }, [exportToPNG, exportToJPG, exportToSVG, exportToCSV, exportToJSON]);

  const getChartBlob = useCallback(async (format: ExportFormat, options?: ExportOptions) => {
    return performExport(format, options);
  }, [performExport]);

  const clearHistory = useCallback(() => {
    setExportHistory([]);
  }, []);

  // Memoized return value
  const returnValue = useMemo<UseChartExportReturn>(() => ({
    // State
    isExporting,
    error,
    exportHistory,

    // Actions
    exportToPNG,
    exportToJPG,
    exportToSVG,
    exportToCSV,
    exportToJSON,
    export,
    getChartBlob,
    clearHistory,
  }), [
    isExporting,
    error,
    exportHistory,
    exportToPNG,
    exportToJPG,
    exportToSVG,
    exportToCSV,
    exportToJSON,
    export,
    getChartBlob,
    clearHistory,
  ]);

  return returnValue;
};

// Export types for external use
export type {
  ExportFormat,
  ExportOptions,
  ChartExportConfig,
  ChartExportState,
  ChartExportActions,
  UseChartExportReturn
};