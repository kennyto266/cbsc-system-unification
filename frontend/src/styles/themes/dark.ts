/**
 * CBSC Design System - Dark Theme
 * 暗色主题配置
 */

import { baseTheme } from '../tokens'

// Dark theme configuration - 暗色主题
export const darkTheme = {
  ...baseTheme,

  // Theme name - 主题名称
  name: 'dark',

  // Color palette - 色彩方案
  colors: {
    ...baseTheme.colors,

    // Background colors - 背景色
    background: {
      primary: '#0f172a',      // 主背景 - 深蓝黑
      secondary: '#1e293b',    // 次级背景 - 深灰蓝
      tertiary: '#334155',     // 三级背景 - 灰蓝
      quaternary: '#475569',   // 四级背景
      disabled: '#1e293b',     // 禁用背景
      inverse: '#ffffff',      // 反色背景 - 纯白
      overlay: 'rgba(0, 0, 0, 0.75)',       // 遮罩层
      overlayLight: 'rgba(0, 0, 0, 0.25)',  // 轻遮罩
      accent: '#1e3a8a',       // 强调背景
      success: '#14532d',      // 成功背景
      warning: '#78350f',      // 警告背景
      error: '#7f1d1d',        // 错误背景
      info: '#1e3a8a',         // 信息背景
    },

    // Text colors - 文本色
    text: {
      primary: '#f8fafc',      // 主文本 - 浅灰白
      secondary: '#cbd5e1',    // 次级文本 - 中浅灰
      tertiary: '#94a3b8',     // 三级文本 - 浅灰
      quaternary: '#64748b',   // 四级文本
      disabled: '#475569',     // 禁用文本
      inverse: '#0f172a',      // 反色文本 - 深蓝黑
      link: '#7dd3fc',         // 链接色 - 浅蓝
      linkHover: '#bae6fd',    // 链接悬停
      onPrimary: '#ffffff',    // 主色上的文本
      onSecondary: '#f8fafc',  // 次色上的文本
      onAccent: '#7dd3fc',     // 强调色上的文本
    },

    // Border colors - 边框色
    border: {
      primary: '#334155',      // 主边框 - 灰蓝
      secondary: '#475569',    // 次边框
      tertiary: '#1e293b',     // 三级边框
      focus: '#7dd3fc',        // 焦点边框
      error: '#f87171',        // 错误边框
      success: '#4ade80',      // 成功边框
      warning: '#fbbf24',      // 警告边框
      info: '#60a5fa',         // 信息边框
      disabled: '#334155',     // 禁用边框
      inverse: '#0f172a',      // 反色边框
    },

    // Icon colors - 图标色
    icon: {
      primary: '#cbd5e1',      // 主图标
      secondary: '#94a3b8',    // 次级图标
      tertiary: '#64748b',     // 三级图标
      disabled: '#475569',     // 禁用图标
      inverse: '#0f172a',      // 反色图标
      accent: '#7dd3fc',       // 强调图标
      success: '#4ade80',      // 成功图标
      warning: '#fbbf24',      // 警告图标
      error: '#f87171',        // 错误图标
      info: '#60a5fa',         // 信息图标
    },
  },

  // Component specific colors - 组件特定色彩
  components: {
    // Button colors - 按钮色彩
    button: {
      primary: {
        background: '#0284c7',
        backgroundHover: '#0369a1',
        text: '#ffffff',
        border: '#0284c7',
        borderHover: '#0369a1',
        shadow: '0 4px 6px rgba(2, 132, 199, 0.25)',
      },
      secondary: {
        background: '#1e293b',
        backgroundHover: '#334155',
        text: '#f8fafc',
        border: '#475569',
        borderHover: '#64748b',
        shadow: '0 1px 3px rgba(0, 0, 0, 0.3)',
      },
      outline: {
        background: 'transparent',
        backgroundHover: '#1e3a8a',
        text: '#7dd3fc',
        border: '#7dd3fc',
        borderHover: '#bae6fd',
        shadow: 'none',
      },
      ghost: {
        background: 'transparent',
        backgroundHover: '#334155',
        text: '#cbd5e1',
        border: 'transparent',
        borderHover: 'transparent',
        shadow: 'none',
      },
      danger: {
        background: '#ef4444',
        backgroundHover: '#dc2626',
        text: '#ffffff',
        border: '#ef4444',
        borderHover: '#dc2626',
        shadow: '0 4px 6px rgba(239, 68, 68, 0.25)',
      },
    },

    // Card colors - 卡片色彩
    card: {
      background: '#1e293b',
      backgroundHover: '#334155',
      border: '#334155',
      shadow: '0 1px 3px rgba(0, 0, 0, 0.3), 0 1px 2px rgba(0, 0, 0, 0.2)',
      shadowHover: '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2)',
    },

    // Input colors - 输入框色彩
    input: {
      background: '#1e293b',
      backgroundDisabled: '#334155',
      text: '#f8fafc',
      placeholder: '#64748b',
      border: '#475569',
      borderFocus: '#7dd3fc',
      borderError: '#f87171',
      shadow: '0 0 0 0 transparent',
      shadowFocus: '0 0 0 3px rgba(125, 211, 252, 0.1)',
      ring: '#7dd3fc',
      ringError: '#f87171',
    },

    // Modal colors - 模态框色彩
    modal: {
      background: '#1e293b',
      overlay: 'rgba(0, 0, 0, 0.75)',
      border: '#334155',
      shadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
    },

    // Table colors - 表格色彩
    table: {
      background: '#1e293b',
      backgroundHover: '#334155',
      backgroundSelected: '#1e3a8a',
      header: {
        background: '#0f172a',
        text: '#f8fafc',
        border: '#334155',
      },
      row: {
        border: '#334155',
        text: '#f8fafc',
        textSecondary: '#cbd5e1',
      },
      striped: '#0f172a',
    },

    // Sidebar colors - 侧边栏色彩
    sidebar: {
      background: '#0f172a',
      backgroundHover: '#1e293b',
      backgroundActive: '#1e3a8a',
      border: '#334155',
      text: '#f8fafc',
      textHover: '#f8fafc',
      textActive: '#7dd3fc',
      icon: '#94a3b8',
      iconHover: '#f8fafc',
      iconActive: '#7dd3fc',
    },

    // Top navigation - 顶部导航色彩
    topbar: {
      background: '#1e293b',
      border: '#334155',
      text: '#f8fafc',
      icon: '#94a3b8',
      shadow: '0 1px 3px rgba(0, 0, 0, 0.3)',
    },
  },

  // Status colors - 状态色
  status: {
    online: '#4ade80',      // 在线
    offline: '#64748b',     // 离线
    busy: '#fbbf24',        // 忙碌
    away: '#94a3b8',        // 离开
    error: '#f87171',       // 错误
    warning: '#fbbf24',     // 警告
    success: '#4ade80',     // 成功
    info: '#60a5fa',        // 信息
  },

  // Chart colors - 图表色彩（针对暗色背景优化）
  chart: {
    primary: ['#7dd3fc', '#bae6fd', '#e0f2fe', '#38bdf8', '#0ea5e9'],
    secondary: ['#64748b', '#94a3b8', '#cbd5e1', '#e2e8f0', '#f1f5f9'],
    success: ['#4ade80', '#86efac', '#bbf7d0', '#dcfce7', '#f0fdf4'],
    warning: ['#fbbf24', '#fcd34d', '#fde68a', '#fef3c7', '#fffbeb'],
    error: ['#f87171', '#fca5a5', '#fecaca', '#fee2e2', '#fef2f2'],
    info: ['#60a5fa', '#93c5fd', '#bfdbfe', '#dbeafe', '#eff6ff'],
    neutral: ['#475569', '#64748b', '#94a3b8', '#cbd5e1', '#e2e8f0'],
  },
}

// Export dark theme
export default darkTheme