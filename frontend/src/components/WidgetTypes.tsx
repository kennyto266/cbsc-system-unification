import React from 'react';
import { StrategyOverview } from './widgets/StrategyOverview';
import { PerformanceMetrics } from './widgets/PerformanceMetrics';
import { RealTimeMonitor } from './widgets/RealTimeMonitor';
import { QuickActions } from './widgets/QuickActions';

// Widget component registry
export const widgetRegistry = {
  'strategy-overview': {
    component: StrategyOverview,
    title: '策略概览',
    description: '显示系统策略的整体概况',
    icon: '📊',
    defaultConfig: {
      w: 6,
      h: 4,
      minW: 4,
      minH: 3,
    },
  },
  'performance-metrics': {
    component: PerformanceMetrics,
    title: '性能指标',
    description: '展示关键性能指标和收益数据',
    icon: '📈',
    defaultConfig: {
      w: 6,
      h: 4,
      minW: 4,
      minH: 3,
    },
  },
  'realtime-monitor': {
    component: RealTimeMonitor,
    title: '实时监控',
    description: '实时监控策略执行和市场数据',
    icon: '👁️',
    defaultConfig: {
      w: 6,
      h: 4,
      minW: 4,
      minH: 3,
    },
  },
  'quick-actions': {
    component: QuickActions,
    title: '快捷操作',
    description: '快速访问常用功能',
    icon: '⚡',
    defaultConfig: {
      w: 6,
      h: 4,
      minW: 4,
      minH: 3,
    },
  },
};
