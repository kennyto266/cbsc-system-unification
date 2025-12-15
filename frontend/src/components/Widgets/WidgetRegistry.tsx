import { WidgetRegistry } from '../../types/widget';

// Registry of all available widget types
export const widgetRegistry: WidgetRegistry = {
  'strategy-overview': {
    type: 'strategy-overview',
    title: '策略概覽',
    defaultSize: { w: 4, h: 3 },
    minSize: { w: 2, h: 2 },
    icon: '📊',
    category: '策略',
  },
  'performance-chart': {
    type: 'performance-chart',
    title: '性能圖表',
    defaultSize: { w: 8, h: 4 },
    minSize: { w: 4, h: 3 },
    icon: '📈',
    category: '分析',
  },
  'market-monitor': {
    type: 'market-monitor',
    title: '市場監控',
    defaultSize: { w: 6, h: 4 },
    minSize: { w: 4, h: 3 },
    icon: '🏢',
    category: '市場',
  },
  'trading-list': {
    type: 'trading-list',
    title: '交易列表',
    defaultSize: { w: 6, h: 5 },
    minSize: { w: 4, h: 3 },
    icon: '💹',
    category: '交易',
  },
  'notification-center': {
    type: 'notification-center',
    title: '通知中心',
    defaultSize: { w: 4, h: 3 },
    minSize: { w: 2, h: 2 },
    icon: '🔔',
    category: '系統',
  },
};

// Get widget categories
export function getWidgetCategories(): string[] {
  const categories = new Set<string>();
  Object.values(widgetRegistry).forEach(widget => {
    if (widget.category) {
      categories.add(widget.category);
    }
  });
  return Array.from(categories);
}

// Get widgets by category
export function getWidgetsByCategory(category?: string): WidgetRegistry {
  if (!category) return widgetRegistry;

  const filtered: WidgetRegistry = {};
  Object.entries(widgetRegistry).forEach(([key, widget]) => {
    if (widget.category === category) {
      filtered[key] = widget;
    }
  });
  return filtered;
}