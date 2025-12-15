/**
 * CBSC Design System - Light Theme
 * 亮色主题配置
 */

import { baseTheme } from '../tokens'

// Light theme configuration - 亮色主题
export const lightTheme = {
  ...baseTheme,

  // Theme name - 主题名称
  name: 'light',

  // Color palette - 色彩方案
  colors: {
    ...baseTheme.colors,

    // Background colors - 背景色
    background: {
      primary: '#ffffff',      // 主背景 - 纯白
      secondary: '#f8fafc',    // 次级背景 - 极浅灰
      tertiary: '#f1f5f9',     // 三级背景 - 浅灰
      quaternary: '#e2e8f0',   // 四级背景
      disabled: '#f8fafc',     // 禁用背景
      inverse: '#0f172a',      // 反色背景 - 深蓝黑
      overlay: 'rgba(0, 0, 0, 0.5)',        // 遮罩层
      overlayLight: 'rgba(0, 0, 0, 0.1)',   // 轻遮罩
      accent: '#eff6ff',       // 强调背景
      success: '#f0fdf4',      // 成功背景
      warning: '#fffbeb',      // 警告背景
      error: '#fef2f2',        // 错误背景
      info: '#eff6ff',         // 信息背景
    },

    // Text colors - 文本色
    text: {
      primary: '#0f172a',      // 主文本 - 深蓝黑
      secondary: '#475569',    // 次级文本 - 中灰
      tertiary: '#94a3b8',     // 三级文本 - 浅灰
      quaternary: '#cbd5e1',   // 四级文本
      disabled: '#cbd5e1',     // 禁用文本
      inverse: '#ffffff',      // 反色文本
      link: '#0284c7',         // 链接色 - 品牌蓝
      linkHover: '#0369a1',    // 链接悬停
      onPrimary: '#ffffff',    // 主色上的文本
      onSecondary: '#0f172a',  // 次色上的文本
      onAccent: '#0284c7',     // 强调色上的文本
    },

    // Border colors - 边框色
    border: {
      primary: '#e2e8f0',      // 主边框 - 浅灰
      secondary: '#cbd5e1',    // 次边框
      tertiary: '#f1f5f9',     // 三级边框
      focus: '#0284c7',        // 焦点边框
      error: '#ef4444',        // 错误边框
      success: '#22c55e',      // 成功边框
      warning: '#f59e0b',      // 警告边框
      info: '#3b82f6',         // 信息边框
      disabled: '#f1f5f9',     // 禁用边框
      inverse: '#ffffff',      // 反色边框
    },

    // Icon colors - 图标色
    icon: {
      primary: '#475569',      // 主图标
      secondary: '#64748b',    // 次级图标
      tertiary: '#94a3b8',     // 三级图标
      disabled: '#cbd5e1',     // 禁用图标
      inverse: '#ffffff',      // 反色图标
      accent: '#0284c7',       // 强调图标
      success: '#22c55e',      // 成功图标
      warning: '#f59e0b',      // 警告图标
      error: '#ef4444',        // 错误图标
      info: '#3b82f6',         // 信息图标
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
        background: '#ffffff',
        backgroundHover: '#f1f5f9',
        text: '#0f172a',
        border: '#e2e8f0',
        borderHover: '#cbd5e1',
        shadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      },
      outline: {
        background: 'transparent',
        backgroundHover: '#eff6ff',
        text: '#0284c7',
        border: '#0284c7',
        borderHover: '#0369a1',
        shadow: 'none',
      },
      ghost: {
        background: 'transparent',
        backgroundHover: '#f1f5f9',
        text: '#475569',
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
      background: '#ffffff',
      backgroundHover: '#f8fafc',
      border: '#e2e8f0',
      shadow: '0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06)',
      shadowHover: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    },

    // Input colors - 输入框色彩
    input: {
      background: '#ffffff',
      backgroundDisabled: '#f8fafc',
      text: '#0f172a',
      placeholder: '#94a3b8',
      border: '#e2e8f0',
      borderFocus: '#0284c7',
      borderError: '#ef4444',
      shadow: '0 0 0 0 transparent',
      shadowFocus: '0 0 0 3px rgba(2, 132, 199, 0.1)',
      ring: '#0284c7',
      ringError: '#ef4444',
    },

    // Modal colors - 模态框色彩
    modal: {
      background: '#ffffff',
      overlay: 'rgba(0, 0, 0, 0.5)',
      border: '#e2e8f0',
      shadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    },

    // Table colors - 表格色彩
    table: {
      background: '#ffffff',
      backgroundHover: '#f8fafc',
      backgroundSelected: '#eff6ff',
      header: {
        background: '#f8fafc',
        text: '#0f172a',
        border: '#e2e8f0',
      },
      row: {
        border: '#e2e8f0',
        text: '#0f172a',
        textSecondary: '#64748b',
      },
      striped: '#f8fafc',
    },

    // Sidebar colors - 侧边栏色彩
    sidebar: {
      background: '#ffffff',
      backgroundHover: '#f8fafc',
      backgroundActive: '#eff6ff',
      border: '#e2e8f0',
      text: '#0f172a',
      textHover: '#0f172a',
      textActive: '#0284c7',
      icon: '#64748b',
      iconHover: '#0f172a',
      iconActive: '#0284c7',
    },

    // Top navigation - 顶部导航色彩
    topbar: {
      background: '#ffffff',
      border: '#e2e8f0',
      text: '#0f172a',
      icon: '#64748b',
      shadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
    },
  },

  // Status colors - 状态色
  status: {
    online: '#22c55e',      // 在线
    offline: '#94a3b8',     // 离线
    busy: '#f59e0b',        // 忙碌
    away: '#64748b',        // 离开
    error: '#ef4444',       // 错误
    warning: '#f59e0b',     // 警告
    success: '#22c55e',     // 成功
    info: '#3b82f6',        // 信息
  },

  // Chart colors - 图表色彩
  chart: {
    primary: ['#0284c7', '#0ea5e9', '#38bdf8', '#7dd3fc', '#bae6fd'],
    secondary: ['#64748b', '#94a3b8', '#cbd5e1', '#e2e8f0', '#f1f5f9'],
    success: ['#22c55e', '#4ade80', '#86efac', '#bbf7d0', '#dcfce7'],
    warning: ['#f59e0b', '#fbbf24', '#fcd34d', '#fde68a', '#fef3c7'],
    error: ['#ef4444', '#f87171', '#fca5a5', '#fecaca', '#fee2e2'],
    info: ['#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#dbeafe'],
    neutral: ['#475569', '#64748b', '#94a3b8', '#cbd5e1', '#e2e8f0'],
  },
}

// Export light theme
export default lightTheme