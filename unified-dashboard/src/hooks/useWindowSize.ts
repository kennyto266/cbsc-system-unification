import { useState, useEffect } from 'react'

interface WindowSize {
  width: number
  height: number
}

// Hook to track window size changes
export const useWindowSize = (): WindowSize => {
  const [windowSize, setWindowSize] = useState<WindowSize>({
    width: typeof window !== 'undefined' ? window.innerWidth : 1920,
    height: typeof window !== 'undefined' ? window.innerHeight : 1080,
  })

  useEffect(() => {
    // Only run on client side
    if (typeof window === 'undefined') return

    const handleResize = () => {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight,
      })
    }

    // Add event listener
    window.addEventListener('resize', handleResize)

    // Call handler right away so state gets updated with initial window size
    handleResize()

    // Remove event listener on cleanup
    return () => window.removeEventListener('resize', handleResize)
  }, []) // Empty array ensures that effect is only run on mount and unmount

  return windowSize
}

// Breakpoint helpers
export const useBreakpoints = () => {
  const { width } = useWindowSize()

  return {
    isMobile: width < 768,
    isTablet: width >= 768 && width < 1024,
    isDesktop: width >= 1024 && width < 1440,
    isWide: width >= 1440,
    isSmall: width < 640,
    isMedium: width >= 640 && width < 1024,
    isLarge: width >= 1024,
  }
}

export default useWindowSize