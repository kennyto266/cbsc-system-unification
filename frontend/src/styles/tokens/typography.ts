/**
 * CBSC Design System - Typography Tokens
 * 字体系统设计令牌
 */

// Font Families - 字体族
export const fontFamilies = {
  // Primary font family - Inter字体族，支持中英文
  sans: [
    'Inter',
    '-apple-system',
    'BlinkMacSystemFont',
    '"Segoe UI"',
    'Roboto',
    '"Helvetica Neue"',
    'Arial',
    '"Noto Sans"',
    'sans-serif',
    '"Apple Color Emoji"',
    '"Segoe UI Emoji"',
    '"Segoe UI Symbol"',
    '"Noto Color Emoji"',
  ].join(', '),

  // Monospace font family - 等宽字体
  mono: [
    '"JetBrains Mono"',
    '"Fira Code"',
    'Menlo',
    'Monaco',
    'Consolas',
    '"Liberation Mono"',
    '"Courier New"',
    'monospace',
  ].join(', '),

  // Chinese font fallback - 中文字体后备
  chinese: [
    'Inter',
    'PingFang SC',
    'Hiragino Sans GB',
    'Microsoft YaHei',
    '微软雅黑',
    'STHeiti',
    'SimSun',
    'sans-serif',
  ].join(', '),
}

// Font Sizes - 字体大小
export const fontSizes = {
  xs: ['0.75rem', { lineHeight: '1rem' }],    // 12px
  sm: ['0.875rem', { lineHeight: '1.25rem' }], // 14px
  base: ['1rem', { lineHeight: '1.5rem' }],    // 16px
  lg: ['1.125rem', { lineHeight: '1.75rem' }], // 18px
  xl: ['1.25rem', { lineHeight: '1.75rem' }],  // 20px
  '2xl': ['1.5rem', { lineHeight: '2rem' }],   // 24px
  '3xl': ['1.875rem', { lineHeight: '2.25rem' }], // 30px
  '4xl': ['2.25rem', { lineHeight: '2.5rem' }],  // 36px
  '5xl': ['3rem', { lineHeight: '1' }],           // 48px
  '6xl': ['3.75rem', { lineHeight: '1' }],        // 60px
  '7xl': ['4.5rem', { lineHeight: '1' }],         // 72px
  '8xl': ['6rem', { lineHeight: '1' }],           // 96px
  '9xl': ['8rem', { lineHeight: '1' }],           // 128px
}

// Font Weights - 字重
export const fontWeights = {
  thin: '100',
  extralight: '200',
  light: '300',
  normal: '400',
  medium: '500',
  semibold: '600',
  bold: '700',
  extrabold: '800',
  black: '900',
}

// Letter Spacing - 字间距
export const letterSpacing = {
  tighter: '-0.05em',
  tight: '-0.025em',
  normal: '0em',
  wide: '0.025em',
  wider: '0.05em',
  widest: '0.1em',
}

// Line Heights - 行高
export const lineHeights = {
  none: '1',
  tight: '1.25',
  snug: '1.375',
  normal: '1.5',
  relaxed: '1.625',
  loose: '2',
}

// Text Styles - 文本样式预设
export const textStyles = {
  // Headings - 标题层级
  h1: {
    fontFamily: fontFamilies.sans,
    fontSize: fontSizes['4xl'][0],
    fontWeight: fontWeights.bold,
    lineHeight: lineHeights.tight,
    letterSpacing: letterSpacing.tighter,
  },
  h2: {
    fontFamily: fontFamilies.sans,
    fontSize: fontSizes['3xl'][0],
    fontWeight: fontWeights.semibold,
    lineHeight: lineHeights.tight,
    letterSpacing: letterSpacing.tight,
  },
  h3: {
    fontFamily: fontFamilies.sans,
    fontSize: fontSizes['2xl'][0],
    fontWeight: fontWeights.semibold,
    lineHeight: lineHeights.snug,
  },
  h4: {
    fontFamily: fontFamilies.sans,
    fontSize: fontSizes.xl[0],
    fontWeight: fontWeights.semibold,
    lineHeight: lineHeights.snug,
  },
  h5: {
    fontFamily: fontFamilies.sans,
    fontSize: fontSizes.lg[0],
    fontWeight: fontWeights.medium,
    lineHeight: lineHeights.normal,
  },
  h6: {
    fontFamily: fontFamilies.sans,
    fontSize: fontSizes.base[0],
    fontWeight: fontWeights.medium,
    lineHeight: lineHeights.normal,
  },

  // Body text - 正文
  body: {
    fontFamily: fontFamilies.sans,
    fontSize: fontSizes.base[0],
    fontWeight: fontWeights.normal,
    lineHeight: lineHeights.normal,
  },
  bodyLarge: {
    fontFamily: fontFamilies.sans,
    fontSize: fontSizes.lg[0],
    fontWeight: fontWeights.normal,
    lineHeight: lineHeights.relaxed,
  },
  bodySmall: {
    fontFamily: fontFamilies.sans,
    fontSize: fontSizes.sm[0],
    fontWeight: fontWeights.normal,
    lineHeight: lineHeights.normal,
  },

  // UI elements - UI元素
  caption: {
    fontFamily: fontFamilies.sans,
    fontSize: fontSizes.xs[0],
    fontWeight: fontWeights.normal,
    lineHeight: lineHeights.normal,
  },
  overline: {
    fontFamily: fontFamilies.sans,
    fontSize: fontSizes.xs[0],
    fontWeight: fontWeights.medium,
    lineHeight: lineHeights.normal,
    letterSpacing: letterSpacing.wide,
    textTransform: 'uppercase',
  },

  // Code - 代码
  code: {
    fontFamily: fontFamilies.mono,
    fontSize: fontSizes.sm[0],
    fontWeight: fontWeights.normal,
  },
  codeInline: {
    fontFamily: fontFamilies.mono,
    fontSize: fontSizes.sm[0],
    fontWeight: fontWeights.normal,
    backgroundColor: 'var(--color-bg-tertiary)',
    padding: '0.125rem 0.375rem',
    borderRadius: '0.25rem',
  },

  // Links - 链接
  link: {
    fontFamily: fontFamilies.sans,
    fontSize: fontSizes.base[0],
    fontWeight: fontWeights.medium,
    color: 'var(--color-primary)',
    textDecoration: 'none',
    transition: 'all 0.2s ease',
  },
  linkHover: {
    color: 'var(--color-primary-hover)',
    textDecoration: 'underline',
  },
}

// Responsive text sizes - 响应式字体大小
export const responsiveTextSizes = {
  h1: {
    sm: fontSizes['3xl'][0],
    md: fontSizes['4xl'][0],
    lg: fontSizes['5xl'][0],
    xl: fontSizes['6xl'][0],
  },
  h2: {
    sm: fontSizes['2xl'][0],
    md: fontSizes['3xl'][0],
    lg: fontSizes['4xl'][0],
    xl: fontSizes['5xl'][0],
  },
  h3: {
    sm: fontSizes.xl[0],
    md: fontSizes['2xl'][0],
    lg: fontSizes['3xl'][0],
    xl: fontSizes['4xl'][0],
  },
  body: {
    sm: fontSizes.sm[0],
    md: fontSizes.base[0],
    lg: fontSizes.lg[0],
    xl: fontSizes.xl[0],
  },
}

// Export all typography tokens
export const typography = {
  fontFamilies,
  fontSizes,
  fontWeights,
  letterSpacing,
  lineHeights,
  textStyles,
  responsiveTextSizes,
}