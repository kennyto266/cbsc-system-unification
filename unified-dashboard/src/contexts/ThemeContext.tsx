import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'

// Theme type definitions
export type Theme = 'light' | 'dark' | 'auto'

export interface ThemeConfig {
  colors: {
    primary: string
    secondary: string
    accent: string
    background: string
    surface: string
    text: string
    textSecondary: string
    border: string
    success: string
    warning: string
    error: string
    info: string
  }
  spacing: {
    xs: string
    sm: string
    md: string
    lg: string
    xl: string
    xxl: string
  }
  borderRadius: {
    sm: string
    md: string
    lg: string
    full: string
  }
  shadows: {
    sm: string
    md: string
    lg: string
    xl: string
  }
}

// Light theme configuration
const lightTheme: ThemeConfig = {
  colors: {
    primary: '#1890ff',
    secondary: '#722ed1',
    accent: '#13c2c2',
    background: '#ffffff',
    surface: '#fafafa',
    text: '#000000',
    textSecondary: '#8c8c8c',
    border: '#d9d9d9',
    success: '#52c41a',
    warning: '#faad14',
    error: '#f5222d',
    info: '#1890ff',
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    xxl: '3rem',
  },
  borderRadius: {
    sm: '0.25rem',
    md: '0.5rem',
    lg: '0.75rem',
    full: '9999px',
  },
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  },
}

// Dark theme configuration
const darkTheme: ThemeConfig = {
  ...lightTheme,
  colors: {
    primary: '#177ddc',
    secondary: '#642ab5',
    accent: '#13a8a8',
    background: '#141414',
    surface: '#1f1f1f',
    text: '#ffffff',
    textSecondary: '#a6a6a6',
    border: '#434343',
    success: '#49aa19',
    warning: '#d89614',
    error: '#dc4446',
    info: '#177ddc',
  },
}

// Theme context interface
interface ThemeContextType {
  theme: Theme
  themeConfig: ThemeConfig
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
  isDark: boolean
}

// Create theme context
const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

// Theme provider props
interface ThemeProviderProps {
  children: ReactNode
  defaultTheme?: Theme
}

// Theme provider component
export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  defaultTheme = 'light'
}) => {
  // Get system theme preference
  const getSystemTheme = (): 'light' | 'dark' => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    }
    return 'light'
  }

  // Initialize theme from localStorage or system preference
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('cbsc-dashboard-theme')
      if (saved === 'light' || saved === 'dark' || saved === 'auto') {
        return saved
      }
    }
    return defaultTheme
  })

  // Calculate actual theme
  const getActualTheme = (): 'light' | 'dark' => {
    if (theme === 'auto') {
      return getSystemTheme()
    }
    return theme as 'light' | 'dark'
  }

  // Get theme configuration
  const themeConfig = getActualTheme() === 'dark' ? darkTheme : lightTheme

  // Update theme
  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme)
    if (typeof window !== 'undefined') {
      localStorage.setItem('cbsc-dashboard-theme', newTheme)
    }
  }

  // Toggle between light and dark
  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light')
  }

  // Listen for system theme changes
  useEffect(() => {
    if (theme === 'auto' && typeof window !== 'undefined' && window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      const handleChange = () => {
        // Force re-render when system theme changes
        setThemeState('auto')
      }

      mediaQuery.addEventListener('change', handleChange)
      return () => mediaQuery.removeEventListener('change', handleChange)
    }
  }, [theme])

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement
    const actualTheme = getActualTheme()

    // Update CSS custom properties
    Object.entries(themeConfig.colors).forEach(([key, value]) => {
      root.style.setProperty(`--color-${key}`, value)
    })

    Object.entries(themeConfig.spacing).forEach(([key, value]) => {
      root.style.setProperty(`--spacing-${key}`, value)
    })

    Object.entries(themeConfig.borderRadius).forEach(([key, value]) => {
      root.style.setProperty(`--radius-${key}`, value)
    })

    Object.entries(themeConfig.shadows).forEach(([key, value]) => {
      root.style.setProperty(`--shadow-${key}`, value)
    })

    // Update data-theme attribute
    root.setAttribute('data-theme', actualTheme)

  }, [themeConfig])

  const value: ThemeContextType = {
    theme,
    themeConfig,
    setTheme,
    toggleTheme,
    isDark: getActualTheme() === 'dark',
  }

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  )
}

// Hook to use theme
export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

// Export theme configurations
export { lightTheme, darkTheme }