import { ReactNode } from 'react';

// Grid布局相关类型定义
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
  isDraggable?: boolean;
  isResizable?: boolean;
  isStatic?: boolean;
}

export interface ResponsiveLayout {
  lg?: LayoutItem[];
  md?: LayoutItem[];
  sm?: LayoutItem[];
  xs?: LayoutItem[];
  xxs?: LayoutItem[];
}

export interface Breakpoint {
  lg: number;
  md: number;
  sm: number;
  xs: number;
  xxs: number;
}

export interface GridProps {
  className?: string;
  style?: React.CSSProperties;
  width?: number;
  autoSize?: boolean;
  cols?: number | Breakpoint;
  draggableHandle?: string;
  compactType?: 'vertical' | 'horizontal' | null;
  preventCollision?: boolean;
  rowHeight?: number;
  margin?: [number, number];
  containerPadding?: [number, number];
  onDragStart?: (layout: LayoutItem[], oldItem: LayoutItem, newItem: LayoutItem, placeholder: LayoutItem, e: MouseEvent, element: HTMLElement) => void;
  onDrag?: (layout: LayoutItem[], oldItem: LayoutItem, newItem: LayoutItem, placeholder: LayoutItem, e: MouseEvent, element: HTMLElement) => void;
  onDragEnd?: (layout: LayoutItem[], oldItem: LayoutItem, newItem: LayoutItem, placeholder: LayoutItem, e: MouseEvent, element: HTMLElement) => void;
}

// Widget注册接口
export interface WidgetConfig {
  id: string;
  type: string;
  title: string;
  component: React.ComponentType<any>;
  defaultSize: {
    w: number;
    h: number;
    minW?: number;
    minH?: number;
    maxW?: number;
    maxH?: number;
  };
  config?: Record<string, any>;
  category?: string;
  icon?: ReactNode;
}

export interface WidgetRegistry {
  widgets: Map<string, WidgetConfig>;
  categories: string[];

  register(widget: WidgetConfig): void;
  unregister(id: string): void;
  get(id: string): WidgetConfig | undefined;
  getAll(): WidgetConfig[];
  getByCategory(category: string): WidgetConfig[];
}

export interface GridLayoutState {
  layout: ResponsiveLayout;
  breakpoints: Breakpoint;
  cols: number | Breakpoint;
  compactType: 'vertical' | 'horizontal' | null;
  preventCollision: boolean;
  rowHeight: number;
  margin: [number, number];
  containerPadding: [number, number];
  isDragging: boolean;
  isResizing: boolean;
  activeWidget: string | null;
}