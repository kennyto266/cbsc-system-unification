/**
 * Chart Hooks Index
 *
 * Central export point for all chart-related hooks.
 * This file provides a clean interface for importing chart utilities.
 *
 * @example
 * ```tsx
 * // Import all chart hooks
 * import {
 *   useRealtimeChart,
 *   useChartResize,
 *   useChartExport
 * } from '@/hooks/chart';
 *
 * // Or import specific hooks
 * import { useRealtimeChart } from '@/hooks/chart/useRealtimeChart';
 * ```
 */

// Main hooks
export { useRealtimeChart } from './useRealtimeChart';
export { useChartResize } from './useChartResize';
export { useChartExport } from './useChartExport';

// Types for useRealtimeChart
export type {
  ChartDataPoint,
  RealtimeChartConfig,
  RealtimeChartState,
  RealtimeChartActions,
  UseRealtimeChartReturn
} from './useRealtimeChart';

// Types for useChartResize
export type {
  ChartSize,
  ChartBreakpoints,
  ChartResizeConfig,
  ChartResizeState,
  ChartResizeActions,
  UseChartResizeReturn
} from './useChartResize';

// Types for useChartExport
export type {
  ChartType,
  ExportFormat,
  ExportOptions,
  ChartExportConfig,
  ChartExportState,
  ChartExportActions,
  UseChartExportReturn
} from './useChartExport';

// Re-export WebSocket types for convenience
export type {
  WSMessage,
  ChannelType,
  MessageType,
  ConnectionState
} from '../../types/websocket';

// Utility exports
export const ChartHooks = {
  useRealtimeChart,
  useChartResize,
  useChartExport,
} as const;

// Default export containing all hooks
export default ChartHooks;