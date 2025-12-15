import { useState, useEffect } from 'react'
import type { DeviceType } from '@/types'

// Responsive breakpoint values (in px)
const breakpoints = {
  mobile: 0,
  tablet: 768,
  desktop: 1024,
}

// Hook to detect device type
export function useResponsive(): DeviceType {
  const [deviceType, setDeviceType] = useState<DeviceType>('desktop')

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth
      if (width < breakpoints.tablet) {
        setDeviceType('mobile')
      } else if (width < breakpoints.desktop) {
        setDeviceType('tablet')
      } else {
        setDeviceType('desktop')
      }
    }

    // Initial check
    handleResize()

    // Add event listener
    window.addEventListener('resize', handleResize)

    // Cleanup
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return deviceType
}