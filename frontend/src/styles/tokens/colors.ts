/**
 * CBSC Design System - Color Tokens
 * 企业级色彩系统设计令牌
 */

// Primary Color Palette - 主色调
export const primaryColors = {
  50: '#e0f2fe',
  100: '#bae6fd',
  200: '#7dd3fc',
  300: '#38bdf8',
  400: '#0ea5e9',
  500: '#0284c7', // Primary brand color - 品牌主色
  600: '#0369a1',
  700: '#075985',
  800: '#0c4a6e',
  900: '#164e63', // Deep blue - 深蓝色（主色调）
}

// Secondary Color Palette - 辅助色（灰色系）
export const neutralColors = {
  0: '#ffffff',
  50: '#f8fafc',
  100: '#f1f5f9',
  200: '#e2e8f0',
  300: '#cbd5e1',
  400: '#94a3b8',
  500: '#64748b',
  600: '#475569',
  700: '#334155',
  800: '#1e293b',
  900: '#0f172a',
  950: '#020617',
}

// Semantic Colors - 语义色彩
export const semanticColors = {
  success: {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e', // Success primary - 成功色
    600: '#16a34a',
    700: '#15803d',
    800: '#166534',
    900: '#14532d',
  },
  warning: {
    50: '#fffbeb',
    100: '#fef3c7',
    200: '#fde68a',
    300: '#fcd34d',
    400: '#fbbf24',
    500: '#f59e0b', // Warning primary - 警告色
    600: '#d97706',
    700: '#b45309',
    800: '#92400e',
    900: '#78350f',
  },
  error: {
    50: '#fef2f2',
    100: '#fee2e2',
    200: '#fecaca',
    300: '#fca5a5',
    400: '#f87171',
    500: '#ef4444', // Error primary - 错误色
    600: '#dc2626',
    700: '#b91c1c',
    800: '#991b1b',
    900: '#7f1d1d',
  },
  info: {
    50: '#eff6ff',
    100: '#dbeafe',
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6', // Info primary - 信息色
    600: '#2563eb',
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a',
  }
}

// Background Colors - 背景色
export const backgroundColors = {
  primary: neutralColors.white,
  secondary: neutralColors[50],
  tertiary: neutralColors[100],
  inverse: neutralColors[900],
  disabled: neutralColors[100],
  overlay: 'rgba(0, 0, 0, 0.5)',
  overlayLight: 'rgba(0, 0, 0, 0.1)',
}

// Text Colors - 文本色
export const textColors = {
  primary: neutralColors[900],
  secondary: neutralColors[600],
  tertiary: neutralColors[400],
  inverse: neutralColors.white,
  disabled: neutralColors[400],
  link: primaryColors[600],
  linkHover: primaryColors[700],
}

// Border Colors - 边框色
export const borderColors = {
  primary: neutralColors[200],
  secondary: neutralColors[300],
  focus: primaryColors[500],
  error: semanticColors.error[500],
  success: semanticColors.success[500],
  warning: semanticColors.warning[500],
}

// Shadow Colors - 阴影色
export const shadowColors = {
  sm: `0 1px 2px 0 ${neutralColors[200]}80`,
  base: `0 1px 3px 0 ${neutralColors[200]}80, 0 1px 2px 0 ${neutralColors[300]}80`,
  md: `0 4px 6px -1px ${neutralColors[200]}80, 0 2px 4px -1px ${neutralColors[300]}80`,
  lg: `0 10px 15px -3px ${neutralColors[200]}80, 0 4px 6px -2px ${neutralColors[300]}80`,
  xl: `0 20px 25px -5px ${neutralColors[200]}80, 0 10px 10px -5px ${neutralColors[300]}80`,
  '2xl': `0 25px 50px -12px ${neutralColors[200]}80`,
  inner: `inset 0 2px 4px 0 ${neutralColors[200]}80`,
  glow: `0 0 20px ${primaryColors[400]}40`,
  glowError: `0 0 20px ${semanticColors.error[500]}40`,
  glowSuccess: `0 0 20px ${semanticColors.success[500]}40`,
  glowWarning: `0 0 20px ${semanticColors.warning[500]}40`,
}

// Special Colors - 特殊色彩
export const specialColors = {
  gradient: {
    primary: `linear-gradient(135deg, ${primaryColors[500]}, ${primaryColors[700]})`,
    success: `linear-gradient(135deg, ${semanticColors.success[400]}, ${semanticColors.success[600]})`,
    warning: `linear-gradient(135deg, ${semanticColors.warning[400]}, ${semanticColors.warning[600]})`,
    error: `linear-gradient(135deg, ${semanticColors.error[400]}, ${semanticColors.error[600]})`,
    sunset: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    ocean: 'linear-gradient(135deg, #667eea 0%, #0ea5e9 100%)',
    forest: 'linear-gradient(135deg, #22c55e 0%, #15803d 100%)',
  },
  chart: {
    blue: primaryColors[500],
    green: semanticColors.success[500],
    yellow: semanticColors.warning[500],
    red: semanticColors.error[500],
    purple: '#a855f7',
    orange: '#f97316',
    teal: '#14b8a6',
    pink: '#ec4899',
  }
}

// Export all color tokens
export const colors = {
  primary: primaryColors,
  neutral: neutralColors,
  semantic: semanticColors,
  background: backgroundColors,
  text: textColors,
  border: borderColors,
  shadow: shadowColors,
  special: specialColors,
}