// Widget type definitions
export interface Widget {
  id: string;
  type: WidgetType;
  title: string;
  data?: any;
  isCollapsed?: boolean;
  config?: WidgetConfig;
}

export type WidgetType =
  | 'strategy-overview'
  | 'performance-chart'
  | 'market-monitor'
  | 'trading-list'
  | 'notification-center'
  | 'custom';

export interface WidgetConfig {
  color?: string;
  refreshInterval?: number;
  dataSource?: string;
  filters?: Record<string, any>;
}

// Layout definitions for react-grid-layout
export interface LayoutItem {
  i: string;
  x: number;
  y: number;
  w: number;
  h: number;
  minW?: number;
  minH?: number;
  maxW?: number;
  maxH?: number;
}

export interface Breakpoint {
  lg: number;
  md: number;
  sm: number;
  xs: number;
  xxs: number;
}

export interface Layouts {
  lg: LayoutItem[];
  md: LayoutItem[];
  sm: LayoutItem[];
  xs: LayoutItem[];
  xxs: LayoutItem[];
}

// Widget position and size for each breakpoint
export interface WidgetLayout {
  [widgetId: string]: {
    lg?: Partial<LayoutItem>;
    md?: Partial<LayoutItem>;
    sm?: Partial<LayoutItem>;
    xs?: Partial<LayoutItem>;
    xxs?: Partial<LayoutItem>;
  };
}

// Grid configuration
export interface GridConfig {
  cols: Breakpoint;
  rowHeight: number;
  margin: [number, number];
  containerPadding: [number, number];
  isDraggable: boolean;
  isResizable: boolean;
  compactType: 'vertical' | 'horizontal' | null;
}

// Widget registry
export interface WidgetRegistry {
  [key: string]: {
    type: WidgetType;
    title: string;
    defaultSize: {
      w: number;
      h: number;
    };
    minSize?: {
      w: number;
      h: number;
    };
    maxSize?: {
      w: number;
      h: number;
    };
    icon?: string;
    category?: string;
  };
}