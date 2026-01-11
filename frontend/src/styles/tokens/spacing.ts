/**
 * CBSC Design System - Spacing Tokens
 * 间距系统设计令牌 - 基于8px网格系统
 */

// Base spacing unit - 基础间距单位（8px）
export const baseUnit = 8

// Spacing scale - 间距比例
export const spacing = {
  0: '0',
  px: '1px',
  0.5: `${baseUnit * 0.5}px`,  // 4px
  1: `${baseUnit}px`,          // 8px
  1.5: `${baseUnit * 1.5}px`,  // 12px
  2: `${baseUnit * 2}px`,      // 16px
  2.5: `${baseUnit * 2.5}px`,  // 20px
  3: `${baseUnit * 3}px`,      // 24px
  3.5: `${baseUnit * 3.5}px`,  // 28px
  4: `${baseUnit * 4}px`,      // 32px
  5: `${baseUnit * 5}px`,      // 40px
  6: `${baseUnit * 6}px`,      // 48px
  7: `${baseUnit * 7}px`,      // 56px
  8: `${baseUnit * 8}px`,      // 64px
  9: `${baseUnit * 9}px`,      // 72px
  10: `${baseUnit * 10}px`,    // 80px
  12: `${baseUnit * 12}px`,    // 96px
  14: `${baseUnit * 14}px`,    // 112px
  16: `${baseUnit * 16}px`,    // 128px
  20: `${baseUnit * 20}px`,    // 160px
  24: `${baseUnit * 24}px`,    // 192px
  28: `${baseUnit * 28}px`,    // 224px
  32: `${baseUnit * 32}px`,    // 256px
  36: `${baseUnit * 36}px`,    // 288px
  40: `${baseUnit * 40}px`,    // 320px
  44: `${baseUnit * 44}px`,    // 352px
  48: `${baseUnit * 48}px`,    // 384px
  52: `${baseUnit * 52}px`,    // 416px
  56: `${baseUnit * 56}px`,    // 448px
  60: `${baseUnit * 60}px`,    // 480px
  64: `${baseUnit * 64}px`,    // 512px
  72: `${baseUnit * 72}px`,    // 576px
  80: `${baseUnit * 80}px`,    // 640px
  96: `${baseUnit * 96}px`,    // 768px
}

// Common spacing values - 常用间距
export const commonSpacing = {
  none: spacing[0],
  xs: spacing[1],      // 8px - 微小间距
  sm: spacing[2],      // 16px - 小间距
  md: spacing[4],      // 32px - 中等间距
  lg: spacing[6],      // 48px - 大间距
  xl: spacing[8],      // 64px - 超大间距
  '2xl': spacing[12],  // 96px - 极大间距
  '3xl': spacing[16],  // 128px - 最大间距
}

// Component spacing presets - 组件间距预设
export const componentSpacing = {
  // Button padding
  button: {
    sm: { x: spacing[3], y: spacing[1.5] },   // 24px 12px
    md: { x: spacing[4], y: spacing[2] },     // 32px 16px
    lg: { x: spacing[6], y: spacing[3] },     // 48px 24px
    xl: { x: spacing[8], y: spacing[4] },     // 64px 32px
  },

  // Card padding
  card: {
    sm: spacing[4],     // 32px
    md: spacing[6],     // 48px
    lg: spacing[8],     // 64px
  },

  // Form field spacing
  form: {
    labelBottom: spacing[1],     // 8px
    fieldBottom: spacing[4],     // 32px
    groupBottom: spacing[6],     // 48px
  },

  // Modal spacing
  modal: {
    padding: spacing[6],         // 48px
    headerBottom: spacing[4],    // 32px
    footerTop: spacing[6],       // 48px
  },

  // List spacing
  list: {
    itemPadding: spacing[3],     // 24px
    itemGap: spacing[2],         // 16px
  },

  // Table spacing
  table: {
    cellPadding: `${spacing[3]} ${spacing[4]}`,  // 24px 32px
    headerBottom: spacing[2],    // 16px
  },

  // Layout spacing
  layout: {
    container: {
      sm: spacing[4],     // 32px
      md: spacing[6],     // 48px
      lg: spacing[8],     // 64px
      xl: spacing[12],    // 96px
    },
    section: spacing[16],        // 128px
    subsection: spacing[12],     // 96px
  },

  // Navigation spacing
  navigation: {
    itemPadding: spacing[3],     // 24px
    itemGap: spacing[2],         // 16px
    brandPadding: spacing[4],    // 32px
  },
}

// Grid system - 网格系统
export const grid = {
  // Grid columns
  columns: 12,

  // Grid gaps
  gap: {
    none: spacing[0],
    sm: spacing[2],     // 16px
    md: spacing[4],     // 32px
    lg: spacing[6],     // 48px
    xl: spacing[8],     // 64px
  },

  // Container max widths
  container: {
    sm: '640px',       // Small screens
    md: '768px',       // Medium screens
    lg: '1024px',      // Large screens
    xl: '1280px',      // Extra large screens
    '2xl': '1536px',   // 2X large screens
  },

  // Breakpoints
  breakpoints: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
}

// Border radius - 圆角
export const borderRadius = {
  none: '0',
  sm: `${baseUnit * 0.5}px`,    // 4px - 小圆角
  base: `${baseUnit}px`,        // 8px - 基础圆角
  md: `${baseUnit * 1.5}px`,    // 12px - 中等圆角
  lg: `${baseUnit * 2}px`,      // 16px - 大圆角
  xl: `${baseUnit * 3}px`,      // 24px - 超大圆角
  '2xl': `${baseUnit * 4}px`,   // 32px - 极大圆角
  '3xl': `${baseUnit * 6}px`,   // 48px
  full: '9999px',
}

// Component specific border radius
export const componentRadius = {
  button: {
    sm: borderRadius.sm,
    md: borderRadius.base,
    lg: borderRadius.md,
    xl: borderRadius.lg,
  },
  card: borderRadius.lg,
  input: borderRadius.base,
  modal: borderRadius.lg,
  dropdown: borderRadius.base,
  tag: borderRadius.full,
  avatar: borderRadius.full,
  chip: borderRadius.full,
  alert: borderRadius.base,
  badge: borderRadius.full,
  tooltip: borderRadius.base,
  popover: borderRadius.lg,
}

// Z-index scale - 层级
export const zIndex = {
  hide: -1,
  auto: 'auto',
  base: 0,
  docked: 10,
  dropdown: 1000,
  sticky: 1100,
  banner: 1200,
  overlay: 1300,
  modal: 1400,
  popover: 1500,
  skipLink: 1600,
  toast: 1700,
  tooltip: 1800,
  menu: 1900,
  focus: 9999,
}

// Export all spacing tokens
export const spacingTokens = {
  baseUnit,
  spacing,
  commonSpacing,
  componentSpacing,
  grid,
  borderRadius,
  componentRadius,
  zIndex,
}