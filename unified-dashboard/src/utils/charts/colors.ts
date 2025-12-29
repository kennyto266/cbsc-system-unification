// Chart color themes and utilities

export interface ChartColorTheme {
  name: string
  colors: string[]
  background: string
  text: string
  grid: string
  success: string
  warning: string
  error: string
  info: string
}

// Predefined color themes
export const chartThemes: Record<string, ChartColorTheme> = {
  // Default light theme
  light: {
    name: 'Light',
    colors: [
      '#3B82F6', // Blue
      '#10B981', // Green
      '#F59E0B', // Yellow
      '#EF4444', // Red
      '#8B5CF6', // Purple
      '#EC4899', // Pink
      '#14B8A6', // Teal
      '#F97316', // Orange
      '#6366F1', // Indigo
      '#84CC16', // Lime
    ],
    background: '#ffffff',
    text: '#374151',
    grid: 'rgba(0, 0, 0, 0.05)',
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
    info: '#3B82F6',
  },

  // Dark theme
  dark: {
    name: 'Dark',
    colors: [
      '#60A5FA', // Light Blue
      '#34D399', // Light Green
      '#FCD34D', // Light Yellow
      '#F87171', // Light Red
      '#A78BFA', // Light Purple
      '#F9A8D4', // Light Pink
      '#5EEAD4', // Light Teal
      '#FB923C', // Light Orange
      '#818CF8', // Light Indigo
      '#BEF264', // Light Lime
    ],
    background: '#1f2937',
    text: '#F9FAFB',
    grid: 'rgba(255, 255, 255, 0.05)',
    success: '#34D399',
    warning: '#FCD34D',
    error: '#F87171',
    info: '#60A5FA',
  },

  // CBSC theme
  cbsc: {
    name: 'CBSC',
    colors: [
      '#1E40AF', // Deep Blue
      '#059669', // Emerald
      '#D97706', // Amber
      '#DC2626', // Red
      '#7C3AED', // Violet
      '#BE185D', // Fuchsia
      '#0D9488', // Teal
      '#EA580C', // Orange
      '#4338CA', // Indigo
      '#65A30D', // Lime
    ],
    background: '#ffffff',
    text: '#1F2937',
    grid: 'rgba(0, 0, 0, 0.08)',
    success: '#059669',
    warning: '#D97706',
    error: '#DC2626',
    info: '#1E40AF',
  },

  // Professional theme (for financial charts)
  professional: {
    name: 'Professional',
    colors: [
      '#1f77b4', // Blue
      '#ff7f0e', // Orange
      '#2ca02c', // Green
      '#d62728', // Red
      '#9467bd', // Purple
      '#8c564b', // Brown
      '#e377c2', // Pink
      '#7f7f7f', // Gray
      '#bcbd22', // Olive
      '#17becf', // Cyan
    ],
    background: '#ffffff',
    text: '#333333',
    grid: 'rgba(0, 0, 0, 0.1)',
    success: '#2ca02c',
    warning: '#ff7f0e',
    error: '#d62728',
    info: '#1f77b4',
  },

  // Minimal theme
  minimal: {
    name: 'Minimal',
    colors: [
      '#000000', // Black
      '#666666', // Dark Gray
      '#999999', // Gray
      '#CCCCCC', // Light Gray
      '#E5E5E5', // Lighter Gray
      '#F0F0F0', // Very Light Gray
      '#333333', // Dark Gray
      '#777777', // Medium Gray
      '#BBBBBB', // Light Gray
      '#DDDDDD', // Very Light Gray
    ],
    background: '#ffffff',
    text: '#000000',
    grid: 'rgba(0, 0, 0, 0.03)',
    success: '#2ca02c',
    warning: '#ff7f0e',
    error: '#d62728',
    info: '#1f77b4',
  },
}

// Color generation utilities
export const generateColorPalette = (
  baseColor: string,
  count: number,
  variations: 'lightness' | 'saturation' | 'hue' = 'lightness'
): string[] => {
  const colors: string[] = []
  const baseHSL = hexToHSL(baseColor)

  for (let i = 0; i < count; i++) {
    let color: string

    switch (variations) {
      case 'lightness':
        const lightness = 20 + (60 * i) / (count - 1) // 20% to 80%
        color = HSLToHex(baseHSL.h, baseHSL.s, lightness)
        break
      case 'saturation':
        const saturation = 20 + (80 * i) / (count - 1) // 20% to 100%
        color = HSLToHex(baseHSL.h, saturation, baseHSL.l)
        break
      case 'hue':
        const hue = (baseHSL.h + (360 * i) / count) % 360
        color = HSLToHex(hue, baseHSL.s, baseHSL.l)
        break
      default:
        color = baseColor
    }

    colors.push(color)
  }

  return colors
}

export const interpolateColors = (
  startColor: string,
  endColor: string,
  steps: number
): string[] => {
  const start = hexToRGB(startColor)
  const end = hexToRGB(endColor)

  if (!start || !end) return [startColor, endColor]

  const colors: string[] = []

  for (let i = 0; i < steps; i++) {
    const ratio = i / (steps - 1)
    const r = Math.round(start.r + (end.r - start.r) * ratio)
    const g = Math.round(start.g + (end.g - start.g) * ratio)
    const b = Math.round(start.b + (end.b - start.b) * ratio)
    colors.push(`#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`)
  }

  return colors
}

export const getContrastColor = (backgroundColor: string): '#000000' | '#FFFFFF' => {
  const rgb = hexToRGB(backgroundColor)
  if (!rgb) return '#000000'

  // Calculate relative luminance
  const luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255
  return luminance > 0.5 ? '#000000' : '#FFFFFF'
}

export const adjustColorBrightness = (
  color: string,
  factor: number // 0 to 1, where < 0.5 darkens, > 0.5 lightens
): string => {
  const rgb = hexToRGB(color)
  if (!rgb) return color

  const adjustment = factor < 0.5
    ? -0.5 + factor // Darken
    : factor - 0.5 // Lighten

  const r = Math.max(0, Math.min(255, rgb.r + adjustment * 255))
  const g = Math.max(0, Math.min(255, rgb.g + adjustment * 255))
  const b = Math.max(0, Math.min(255, rgb.b + adjustment * 255))

  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`
}

export const setOpacity = (color: string, opacity: number): string => {
  const rgb = hexToRGB(color)
  if (!rgb) return color

  return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${Math.max(0, Math.min(1, opacity))})`
}

// Color space conversion utilities
export const hexToRGB = (hex: string): { r: number; g: number; b: number } | null => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : null
}

export const hexToHSL = (hex: string): { h: number; s: number; l: number } => {
  const rgb = hexToRGB(hex)
  if (!rgb) return { h: 0, s: 0, l: 0 }

  const r = rgb.r / 255
  const g = rgb.g / 255
  const b = rgb.b / 255

  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  let h = 0
  let s = 0
  const l = (max + min) / 2

  if (max !== min) {
    const d = max - min
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min)

    switch (max) {
      case r:
        h = ((g - b) / d + (g < b ? 6 : 0)) / 6
        break
      case g:
        h = ((b - r) / d + 2) / 6
        break
      case b:
        h = ((r - g) / d + 4) / 6
        break
    }
  }

  return {
    h: Math.round(h * 360),
    s: Math.round(s * 100),
    l: Math.round(l * 100),
  }
}

export const HSLToHex = (h: number, s: number, l: number): string => {
  h = h / 360
  s = s / 100
  l = l / 100

  let r, g, b

  if (s === 0) {
    r = g = b = l
  } else {
    const hue2rgb = (p: number, q: number, t: number) => {
      if (t < 0) t += 1
      if (t > 1) t -= 1
      if (t < 1 / 6) return p + (q - p) * 6 * t
      if (t < 1 / 2) return q
      if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6
      return p
    }

    const q = l < 0.5 ? l * (1 + s) : l + s - l * s
    const p = 2 * l - q
    r = hue2rgb(p, q, h + 1 / 3)
    g = hue2rgb(p, q, h)
    b = hue2rgb(p, q, h - 1 / 3)
  }

  const toHex = (x: number) => {
    const hex = Math.round(x * 255).toString(16)
    return hex.length === 1 ? '0' + hex : hex
  }

  return `#${toHex(r)}${toHex(g)}${toHex(b)}`
}

// Financial chart specific colors
export const financialChartColors = {
  bullish: '#10B981', // Green
  bearish: '#EF4444', // Red
  neutral: '#6B7280', // Gray
  volume: '#3B82F6', // Blue
  maShort: '#F59E0B', // Yellow
  maLong: '#8B5CF6', // Purple
  upperBand: '#EF4444', // Red
  lowerBand: '#10B981', // Green
  support: '#059669', // Dark Green
  resistance: '#DC2626', // Dark Red
  grid: 'rgba(0, 0, 0, 0.05)',
  crosshair: 'rgba(0, 0, 0, 0.3)',
}

// Get chart theme based on name
export const getChartTheme = (themeName: string): ChartColorTheme => {
  return chartThemes[themeName] || chartThemes.light
}

// Create custom gradient
export const createGradient = (
  ctx: CanvasRenderingContext2D,
  colors: string[],
  direction: 'horizontal' | 'vertical' | 'diagonal' = 'vertical'
): CanvasGradient => {
  const { width, height } = ctx.canvas

  let gradient: CanvasGradient

  switch (direction) {
    case 'horizontal':
      gradient = ctx.createLinearGradient(0, 0, width, 0)
      break
    case 'diagonal':
      gradient = ctx.createLinearGradient(0, 0, width, height)
      break
    case 'vertical':
    default:
      gradient = ctx.createLinearGradient(0, 0, 0, height)
      break
  }

  colors.forEach((color, index) => {
    gradient.addColorStop(index / (colors.length - 1), color)
  })

  return gradient
}