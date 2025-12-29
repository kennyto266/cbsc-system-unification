/**
 * CBSC主題提供者
 * 管理全局主題狀態和切換
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { cbscTheme, CBSCTheme, UseCBSCThemeReturn } from './cbsc-theme'

interface ThemeContextType extends UseCBSCThemeReturn {
  updateTheme: (updates: Partial<CBSCTheme>) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

interface ThemeProviderProps {
  children: ReactNode
  defaultTheme?: 'light' | 'dark'
  storageKey?: string
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  defaultTheme = 'light',
  storageKey = 'cbsc-theme',
}) => {
  const [isDark, setIsDark] = useState(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(storageKey)
      return stored === 'dark' || (!stored && defaultTheme === 'dark')
    }
    return defaultTheme === 'dark'
  })

  const [customTheme, setCustomTheme] = useState<CBSCTheme>(cbscTheme)

  // 主題切換函數
  const toggleTheme = () => {
    const newTheme = !isDark ? 'dark' : 'light'
    setIsDark(newTheme)
    if (typeof window !== 'undefined') {
      localStorage.setItem(storageKey, newTheme)
    }
  }

  const setTheme = (theme: 'light' | 'dark') => {
    setIsDark(theme === 'dark')
    if (typeof window !== 'undefined') {
      localStorage.setItem(storageKey, theme)
    }
  }

  const updateTheme = (updates: Partial<CBSCTheme>) => {
    setCustomTheme(prev => ({
      ...prev,
      ...updates,
    }))
  }

  // 獲取顏色值
  const getColor = (colorPath: string): string => {
    const keys = colorPath.split('.')
    let value: any = customTheme.colors

    for (const key of keys) {
      value = value?.[key]
    }

    return value || '#000000'
  }

  // 應用深色模式
  useEffect(() => {
    if (typeof document !== 'undefined') {
      const root = document.documentElement

      if (isDark) {
        root.classList.add('dark')
        // 更新深色模式色彩
        updateTheme({
          colors: {
            ...customTheme.colors,
            primary: {
              ...customTheme.colors.primary,
              50: '#1e3a8a',
              100: '#1e40af',
              500: '#60a5fa', // 深色模式下的主色
              900: '#eff6ff',
            },
            gray: {
              ...customTheme.colors.gray,
              50: '#111827',
              100: '#1f2937',
              500: '#9ca3af',
              900: '#f9fafb',
            },
          },
        })
      } else {
        root.classList.remove('dark')
        // 恢復淺色模式
        updateTheme({
          colors: cbscTheme.colors,
        })
      }
    }
  }, [isDark])

  const value: ThemeContextType = {
    theme: customTheme,
    isDark,
    toggleTheme,
    setTheme,
    updateTheme,
    colors: customTheme.colors,
    getColor,
  }

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  )
}

// 主題Hook
export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

// 主題樣式Hook
export const useThemeStyles = () => {
  const { theme, isDark } = useTheme()

  const getChartColors = () => ({
    background: isDark ? theme.colors.gray[900] : theme.colors.gray[50],
    grid: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
    text: isDark ? theme.colors.gray[300] : theme.colors.gray[700],
    ...theme.chart?.line,
  })

  const getStatusColor = (status: 'running' | 'stopped' | 'error' | 'warning' | 'success') => {
    return theme.status?.[status] || theme.colors.gray[500]
  }

  const getProfitColor = (value: number) => {
    return value >= 0 ? theme.colors.success[500] : theme.colors.danger[500]
  }

  const getProgressColor = (percentage: number) => {
    if (percentage >= 80) return theme.colors.success[500]
    if (percentage >= 60) return theme.colors.primary[500]
    if (percentage >= 40) return theme.colors.warning[500]
    return theme.colors.danger[500]
  }

  return {
    getChartColors,
    getStatusColor,
    getProfitColor,
    getProgressColor,
  }
}

// 主題工具函數
export const themeUtils = {
  // 混合顏色
  mixColors: (color1: string, color2: string, ratio: number = 0.5): string => {
    const hex2rgb = (hex: string) => {
      const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
      return result
        ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16),
          }
        : { r: 0, g: 0, b: 0 }
    }

    const rgb1 = hex2rgb(color1)
    const rgb2 = hex2rgb(color2)

    const r = Math.round(rgb1.r * (1 - ratio) + rgb2.r * ratio)
    const g = Math.round(rgb1.g * (1 - ratio) + rgb2.g * ratio)
    const b = Math.round(rgb1.b * (1 - ratio) + rgb2.b * ratio)

    return `rgb(${r}, ${g}, ${b})`
  },

  // 調整顏色亮度
  adjustBrightness: (color: string, amount: number): string => {
    const hex2rgb = (hex: string) => {
      const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
      return result
        ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16),
          }
        : { r: 0, g: 0, b: 0 }
    }

    const rgb = hex2rgb(color)
    const r = Math.min(255, Math.max(0, rgb.r + amount))
    const g = Math.min(255, Math.max(0, rgb.g + amount))
    const b = Math.min(255, Math.max(0, rgb.b + amount))

    return `rgb(${r}, ${g}, ${b})`
  },

  // 生成漸變
  createGradient: (
    direction: 'horizontal' | 'vertical' | 'diagonal',
    colors: string[]
  ): string => {
    const directionMap = {
      horizontal: 'to right',
      vertical: 'to bottom',
      diagonal: 'to bottom right',
    }

    return `linear-gradient(${directionMap[direction]}, ${colors.join(', ')})`
  },
}

export default ThemeProvider