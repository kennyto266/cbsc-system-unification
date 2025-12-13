/**
 * CBSC Design System - Themes Index
 * 主题系统导出文件
 */

import lightTheme from './light'
import darkTheme from './dark'

// Theme type definition - 主题类型定义
export interface Theme {
  name: string
  colors: {
    background: Record<string, string>
    text: Record<string, string>
    border: Record<string, string>
    icon: Record<string, string>
  }
  components: {
    button: Record<string, any>
    card: Record<string, any>
    input: Record<string, any>
    modal: Record<string, any>
    table: Record<string, any>
    sidebar: Record<string, any>
    topbar: Record<string, any>
  }
  status: Record<string, string>
  chart: Record<string, string[]>
}

// Available themes - 可用主题
export const themes = {
  light: lightTheme,
  dark: darkTheme,
}

// Theme names - 主题名称列表
export const themeNames = Object.keys(themes) as Array<keyof typeof themes>

// Default theme - 默认主题
export const defaultTheme = 'light'

// Export themes
export { lightTheme, darkTheme }

// Theme utilities - 主题工具
export class ThemeManager {
  private static instance: ThemeManager
  private currentTheme: string = defaultTheme
  private storageKey = 'cbsc-theme'

  private constructor() {
    this.loadTheme()
  }

  static getInstance(): ThemeManager {
    if (!ThemeManager.instance) {
      ThemeManager.instance = new ThemeManager()
    }
    return ThemeManager.instance
  }

  // Get current theme - 获取当前主题
  getCurrentTheme(): string {
    return this.currentTheme
  }

  // Get theme object - 获取主题对象
  getTheme(themeName?: string): Theme {
    const name = themeName || this.currentTheme
    return themes[name as keyof typeof themes] || lightTheme
  }

  // Set theme - 设置主题
  setTheme(themeName: string): void {
    if (!themeNames.includes(themeName as keyof typeof themes)) {
      console.warn(`Theme "${themeName}" not found. Using default theme.`)
      return
    }

    this.currentTheme = themeName
    this.applyTheme(themeName)
    this.saveTheme(themeName)
    this.notifyThemeChange(themeName)
  }

  // Toggle theme - 切换主题
  toggleTheme(): void {
    const newTheme = this.currentTheme === 'light' ? 'dark' : 'light'
    this.setTheme(newTheme)
  }

  // Apply theme to DOM - 应用主题到DOM
  private applyTheme(themeName: string): void {
    const theme = this.getTheme(themeName)
    const root = document.documentElement

    // Set data-theme attribute - 设置data-theme属性
    root.setAttribute('data-theme', themeName)

    // Apply CSS variables - 应用CSS变量
    this.applyCSSVariables(theme, root)
  }

  // Apply CSS custom properties - 应用CSS自定义属性
  private applyCSSVariables(theme: Theme, element: HTMLElement): void {
    // Background colors
    Object.entries(theme.colors.background).forEach(([key, value]) => {
      element.style.setProperty(`--color-bg-${key}`, value)
    })

    // Text colors
    Object.entries(theme.colors.text).forEach(([key, value]) => {
      element.style.setProperty(`--color-text-${key}`, value)
    })

    // Border colors
    Object.entries(theme.colors.border).forEach(([key, value]) => {
      element.style.setProperty(`--color-border-${key}`, value)
    })

    // Icon colors
    Object.entries(theme.colors.icon).forEach(([key, value]) => {
      element.style.setProperty(`--color-icon-${key}`, value)
    })

    // Component colors
    Object.entries(theme.components.button).forEach(([variant, colors]: [string, any]) => {
      Object.entries(colors).forEach(([prop, value]) => {
        element.style.setProperty(`--color-btn-${variant}-${prop}`, value)
      })
    })

    // Status colors
    Object.entries(theme.status).forEach(([key, value]) => {
      element.style.setProperty(`--color-status-${key}`, value)
    })

    // Chart colors
    Object.entries(theme.chart).forEach(([type, colors]) => {
      colors.forEach((color: string, index: number) => {
        element.style.setProperty(`--color-chart-${type}-${index}`, color)
      })
    })
  }

  // Save theme to localStorage - 保存主题到本地存储
  private saveTheme(themeName: string): void {
    try {
      localStorage.setItem(this.storageKey, themeName)
    } catch (error) {
      console.warn('Failed to save theme preference:', error)
    }
  }

  // Load theme from localStorage - 从本地存储加载主题
  private loadTheme(): void {
    try {
      const savedTheme = localStorage.getItem(this.storageKey)
      if (savedTheme && themeNames.includes(savedTheme as keyof typeof themes)) {
        this.currentTheme = savedTheme
        this.applyTheme(savedTheme)
      } else {
        // Detect system preference - 检测系统偏好
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
        this.currentTheme = prefersDark ? 'dark' : 'light'
        this.applyTheme(this.currentTheme)
      }
    } catch (error) {
      console.warn('Failed to load theme preference:', error)
      this.applyTheme(this.currentTheme)
    }
  }

  // Listen for system theme changes - 监听系统主题变化
  watchSystemTheme(): void {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    mediaQuery.addEventListener('change', (e) => {
      if (!localStorage.getItem(this.storageKey)) {
        const systemTheme = e.matches ? 'dark' : 'light'
        this.setTheme(systemTheme)
      }
    })
  }

  // Notify theme change - 通知主题变化
  private notifyThemeChange(themeName: string): void {
    const event = new CustomEvent('themechange', {
      detail: { theme: themeName },
    })
    window.dispatchEvent(event)
  }
}

// Export theme manager instance - 导出主题管理器实例
export const themeManager = ThemeManager.getInstance()

// Export theme hook for React - 导出React主题钩子
export const useTheme = () => {
  const [currentTheme, setCurrentTheme] = React.useState(themeManager.getCurrentTheme())

  React.useEffect(() => {
    const handleThemeChange = (event: CustomEvent) => {
      setCurrentTheme(event.detail.theme)
    }

    window.addEventListener('themechange', handleThemeChange as EventListener)
    themeManager.watchSystemTheme()

    return () => {
      window.removeEventListener('themechange', handleThemeChange as EventListener)
    }
  }, [])

  return {
    theme: currentTheme,
    themeConfig: themeManager.getTheme(),
    setTheme: themeManager.setTheme.bind(themeManager),
    toggleTheme: themeManager.toggleTheme.bind(themeManager),
  }
}

// Import React for the hook
import React