/**
 * Theme Context - Dark mode support
 * 主題上下文 - 支持暗黑模式
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  systemTheme: 'light' | 'dark';
  resolvedTheme: 'light' | 'dark';
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: ReactNode;
  defaultTheme?: Theme;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  defaultTheme = 'system'
}) => {
  const [theme, setTheme] = useState<Theme>(() => {
    // Get saved theme from localStorage or use default
    if (typeof window !== 'undefined') {
      const saved = window.localStorage.getItem('ui-theme');
      if (saved === 'light' || saved === 'dark' || saved === 'system') {
        return saved;
      }
    }
    return defaultTheme;
  });

  const [systemTheme, setSystemTheme] = useState<'light' | 'dark'>('light');
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('light');

  // Detect system theme
  useEffect(() => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      const media = window.matchMedia('(prefers-color-scheme: dark)');
      setSystemTheme(media.matches ? 'dark' : 'light');

      const listener = (event: MediaQueryListEvent) => {
        setSystemTheme(event.matches ? 'dark' : 'light');
      };

      if (media.addEventListener) {
        media.addEventListener('change', listener);
        return () => media.removeEventListener('change', listener);
      } else {
        // Fallback for older browsers
        media.addListener(listener);
        return () => media.removeListener(listener);
      }
    }
  }, []);

  // Update resolved theme based on user preference and system theme
  useEffect(() => {
    const resolved = theme === 'system' ? systemTheme : theme;
    setResolvedTheme(resolved);
  }, [theme, systemTheme]);

  // Apply theme to document
  useEffect(() => {
    if (typeof document !== 'undefined') {
      const root = document.documentElement;

      // Remove previous theme classes
      root.classList.remove('light', 'dark');

      // Add current theme class
      root.classList.add(resolvedTheme);

      // Store meta theme-color for mobile browsers
      const metaThemeColor = document.querySelector('meta[name="theme-color"]');
      if (metaThemeColor) {
        metaThemeColor.setAttribute('content', resolvedTheme === 'dark' ? '#1f2937' : '#ffffff');
      }
    }
  }, [resolvedTheme]);

  // Save theme preference
  const handleSetTheme = (newTheme: Theme) => {
    setTheme(newTheme);
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('ui-theme', newTheme);
    }
  };

  const value: ThemeContextType = {
    theme,
    setTheme: handleSetTheme,
    systemTheme,
    resolvedTheme,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};