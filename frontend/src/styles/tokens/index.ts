/**
 * CBSC Design System - Design Tokens Index
 * 设计令牌导出文件
 */

export * from './colors'
export * from './typography'
export * from './spacing'
export * from './effects'

// Import all token types
import { colors } from './colors'
import { typography } from './typography'
import { spacingTokens } from './spacing'
import { effects } from './effects'

// Base theme definition - 基础主题定义
export const baseTheme = {
  // Colors
  ...colors,

  // Typography
  ...typography,

  // Spacing & Layout
  ...spacingTokens,

  // Effects
  ...effects,

  // Breakpoints - 响应式断点
  breakpoints: {
    mobile: '0px',
    tablet: '768px',
    desktop: '1024px',
    wide: '1280px',
    ultrawide: '1536px',
  },

  // Z-index scale
  zIndex: {
    base: 0,
    overlay: 1000,
    modal: 1050,
    notification: 1100,
    tooltip: 1200,
  },

  // Other design tokens
  opacity: {
    invisible: 0,
    semiTransparent: 0.5,
    transparent: 1,
  },
}

// Export theme type
export type Theme = typeof baseTheme

// Export default theme
export default baseTheme