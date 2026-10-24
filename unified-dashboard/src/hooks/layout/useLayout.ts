import { useState, useEffect, useCallback } from 'react'
import { useAppSelector, useAppDispatch } from '../redux'
import { toggleSidebar, toggleTheme, setLanguage } from '../../store/slices/uiSlice'
import type { LayoutState, ViewportSize, ResponsiveBreakpoint } from '../../types/layout'

export const useLayout = () => {
  const dispatch = useAppDispatch()
  const { sidebarCollapsed, themeMode, language } = useAppSelector(state => state.ui)
  const [viewport, setViewport] = useState<ViewportSize>({
    width: window.innerWidth,
    height: window.innerHeight
  })
  const [breakpoint, setBreakpoint] = useState<ResponsiveBreakpoint>({
    xs: false,
    sm: false,
    md: false,
    lg: false,
    xl: false,
    xxl: false
  })

  // Update viewport size
  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth
      const height = window.innerHeight

      setViewport({ width, height })

      // Update breakpoints
      setBreakpoint({
        xs: width < 576,
        sm: width >= 576 && width < 768,
        md: width >= 768 && width < 992,
        lg: width >= 992 && width < 1200,
        xl: width >= 1200 && width < 1600,
        xxl: width >= 1600
      })
    }

    handleResize()
    window.addEventListener('resize', handleResize)

    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // Auto-collapse sidebar on mobile
  useEffect(() => {
    if (breakpoint.xs && !sidebarCollapsed) {
      dispatch(toggleSidebar())
    }
  }, [breakpoint.xs, sidebarCollapsed, dispatch])

  const toggleSidebarHandler = useCallback(() => {
    dispatch(toggleSidebar())
  }, [dispatch])

  const toggleThemeHandler = useCallback(() => {
    dispatch(toggleTheme())
  }, [dispatch])

  const setLanguageHandler = useCallback((lang: string) => {
    dispatch(setLanguage(lang))
  }, [dispatch])

  return {
    // State
    sidebarCollapsed,
    themeMode,
    language,
    viewport,
    breakpoint,

    // Actions
    toggleSidebar: toggleSidebarHandler,
    toggleTheme: toggleThemeHandler,
    setLanguage: setLanguageHandler,

    // Computed values
    isMobile: breakpoint.xs || breakpoint.sm,
    isTablet: breakpoint.md,
    isDesktop: breakpoint.lg || breakpoint.xl || breakpoint.xxl
  }
}