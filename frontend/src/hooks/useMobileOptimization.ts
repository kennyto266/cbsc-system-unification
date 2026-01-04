import { useState, useEffect, useCallback, useRef } from 'react';

// Breakpoints for different screen sizes
export const BREAKPOINTS = {
  xs: 0,
  sm: 480,
  md: 768,
  lg: 992,
  xl: 1200,
  xxl: 1600,
} as const;

export type Breakpoint = keyof typeof BREAKPOINTS;

export interface ScreenInfo {
  width: number;
  height: number;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isLandscape: boolean;
  isPortrait: boolean;
  breakpoint: Breakpoint;
  isSmallDevice: boolean; // width < 480px
  isLargeDevice: boolean; // width > 1200px
  pixelRatio: number;
  touchSupport: boolean;
}

export interface OrientationInfo {
  angle: number;
  type: 'portrait-primary' | 'portrait-secondary' | 'landscape-primary' | 'landscape-secondary';
}

export interface NetworkInfo {
  online: boolean;
  type: ConnectionType;
  effectiveType: EffectiveConnectionType;
  downlink: number;
  rtt: number;
  saveData: boolean;
}

type ConnectionType = 'bluetooth' | 'cellular' | 'ethernet' | 'none' | 'wifi' | 'wimax' | 'other' | 'unknown';
type EffectiveConnectionType = 'slow-2g' | '2g' | '3g' | '4g';

/**
 * useMobileOptimization - Comprehensive mobile optimization utilities
 */
export const useMobileOptimization = () => {
  const [screenInfo, setScreenInfo] = useState<ScreenInfo>(() => getScreenInfo());
  const [orientation, setOrientation] = useState<OrientationInfo>(getOrientation());
  const [networkInfo, setNetworkInfo] = useState<NetworkInfo>(getNetworkInfo());
  const [visibility, setVisibility] = useState(!document.hidden);
  const [safeArea, setSafeArea] = useState(getSafeAreaInsets());

  const resizeTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Get current screen information
  function getScreenInfo(): ScreenInfo {
    const width = window.innerWidth;
    const height = window.innerHeight;

    let breakpoint: Breakpoint = 'xs';
    for (const [key, value] of Object.entries(BREAKPOINTS)) {
      if (width >= value) {
        breakpoint = key as Breakpoint;
      }
    }

    return {
      width,
      height,
      isMobile: width < BREAKPOINTS.md,
      isTablet: width >= BREAKPOINTS.md && width < BREAKPOINTS.lg,
      isDesktop: width >= BREAKPOINTS.lg,
      isLandscape: width > height,
      isPortrait: height > width,
      breakpoint,
      isSmallDevice: width < BREAKPOINTS.sm,
      isLargeDevice: width >= BREAKPOINTS.xl,
      pixelRatio: window.devicePixelRatio || 1,
      touchSupport: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
    };
  }

  // Get device orientation
  function getOrientation(): OrientationInfo {
    if (!screen.orientation) {
      // Fallback for older browsers
      return {
        angle: window.orientation || 0,
        type: window.innerWidth > window.innerHeight ? 'landscape-primary' : 'portrait-primary',
      };
    }

    return {
      angle: screen.orientation.angle,
      type: screen.orientation.type as OrientationInfo['type'],
    };
  }

  // Get network information
  function getNetworkInfo(): NetworkInfo {
    // @ts-ignore - NetworkInformation API
    const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;

    if (!connection) {
      return {
        online: navigator.onLine,
        type: 'unknown',
        effectiveType: '4g',
        downlink: 10,
        rtt: 100,
        saveData: false,
      };
    }

    return {
      online: navigator.onLine,
      type: connection.type || 'unknown',
      effectiveType: connection.effectiveType || '4g',
      downlink: connection.downlink || 10,
      rtt: connection.rtt || 100,
      saveData: connection.saveData || false,
    };
  }

  // Get safe area insets
  function getSafeAreaInsets() {
    const style = getComputedStyle(document.documentElement);
    return {
      top: parseInt(style.getPropertyValue('env(safe-area-inset-top)') || '0', 10),
      right: parseInt(style.getPropertyValue('env(safe-area-inset-right)') || '0', 10),
      bottom: parseInt(style.getPropertyValue('env(safe-area-inset-bottom)') || '0', 10),
      left: parseInt(style.getPropertyValue('env(safe-area-inset-left)') || '0', 10),
    };
  }

  // Handle screen resize
  const handleResize = useCallback(() => {
    // Debounce resize events
    if (resizeTimeoutRef.current) {
      clearTimeout(resizeTimeoutRef.current);
    }

    resizeTimeoutRef.current = setTimeout(() => {
      setScreenInfo(getScreenInfo());
    }, 100);
  }, []);

  // Handle orientation change
  const handleOrientationChange = useCallback(() => {
    setOrientation(getOrientation());
    // Also update screen info as dimensions change
    setScreenInfo(getScreenInfo());
  }, []);

  // Handle network changes
  const handleOnline = useCallback(() => {
    setNetworkInfo(prev => ({ ...prev, online: true }));
  }, []);

  const handleOffline = useCallback(() => {
    setNetworkInfo(prev => ({ ...prev, online: false }));
  }, []);

  const handleConnectionChange = useCallback(() => {
    setNetworkInfo(getNetworkInfo());
  }, []);

  // Handle visibility change
  const handleVisibilityChange = useCallback(() => {
    setVisibility(!document.hidden);
  }, []);

  // Setup event listeners
  useEffect(() => {
    // Screen resize
    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleOrientationChange);

    // Network
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // @ts-ignore - NetworkInformation API
    const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    if (connection) {
      connection.addEventListener('change', handleConnectionChange);
    }

    // Visibility
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleOrientationChange);
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);

      if (connection) {
        connection.removeEventListener('change', handleConnectionChange);
      }

      document.removeEventListener('visibilitychange', handleVisibilityChange);

      if (resizeTimeoutRef.current) {
        clearTimeout(resizeTimeoutRef.current);
      }
    };
  }, [handleResize, handleOrientationChange, handleOnline, handleOffline, handleConnectionChange, handleVisibilityChange]);

  return {
    screenInfo,
    orientation,
    networkInfo,
    visibility,
    safeArea,
  };
};

/**
 * useResponsive breakpoint hook
 */
export const useResponsive = () => {
  const { screenInfo } = useMobileOptimization();

  return {
    ...screenInfo,
    // Convenience getters
    isXs: screenInfo.breakpoint === 'xs',
    isSm: screenInfo.breakpoint === 'sm',
    isMd: screenInfo.breakpoint === 'md',
    isLg: screenInfo.breakpoint === 'lg',
    isXl: screenInfo.breakpoint === 'xl',
    isXxl: screenInfo.breakpoint === 'xxl',

    // Range checks
    up: (breakpoint: Breakpoint) => screenInfo.width >= BREAKPOINTS[breakpoint],
    down: (breakpoint: Breakpoint) => screenInfo.width < BREAKPOINTS[breakpoint],
    between: (min: Breakpoint, max: Breakpoint) =>
      screenInfo.width >= BREAKPOINTS[min] && screenInfo.width < BREAKPOINTS[max],

    // Media query helpers
    matches: (query: string) => {
      if (typeof window !== 'undefined' && window.matchMedia) {
        return window.matchMedia(query).matches;
      }
      return false;
    },
  };
};

/**
 * useViewportSize hook with debouncing
 */
export const useViewportSize = (debounceMs: number = 100) => {
  const [size, setSize] = useState(() => ({
    width: window.innerWidth,
    height: window.innerHeight,
  }));

  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const handleResize = () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        setSize({
          width: window.innerWidth,
          height: window.innerHeight,
        });
      }, debounceMs);
    };

    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [debounceMs]);

  return size;
};

/**
 * useTouchDetection hook
 */
export const useTouchDetection = () => {
  const [isTouch, setIsTouch] = useState(false);
  const [touchPoints, setTouchPoints] = useState(0);

  useEffect(() => {
    // Check if touch is supported
    const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    setIsTouch(hasTouch);

    if (hasTouch) {
      // Get number of touch points
      setTouchPoints(navigator.maxTouchPoints || 0);
    }
  }, []);

  return {
    isTouch,
    touchPoints,
    isCoarse: window.matchMedia('(pointer: coarse)').matches,
    isFine: window.matchMedia('(pointer: fine)').matches,
  };
};

/**
 * useNetworkStatus hook
 */
export const useNetworkStatus = () => {
  const { networkInfo } = useMobileOptimization();
  const [connectionQuality, setConnectionQuality] = useState<'good' | 'fair' | 'poor'>('good');

  useEffect(() => {
    // Determine connection quality based on effective type
    switch (networkInfo.effectiveType) {
      case 'slow-2g':
      case '2g':
        setConnectionQuality('poor');
        break;
      case '3g':
        setConnectionQuality('fair');
        break;
      case '4g':
        setConnectionQuality('good');
        break;
    }
  }, [networkInfo.effectiveType]);

  return {
    ...networkInfo,
    connectionQuality,
    isSlow: connectionQuality === 'poor',
    isFast: connectionQuality === 'good' && networkInfo.downlink > 5,
  };
};

/**
 * useBatteryStatus hook (if supported)
 */
export const useBatteryStatus = () => {
  const [battery, setBattery] = useState<{
    level: number;
    charging: boolean;
    chargingTime: number;
    dischargingTime: number;
  } | null>(null);

  useEffect(() => {
    if ('getBattery' in navigator) {
      (navigator as any).getBattery().then((batteryManager: any) => {
        const updateBatteryInfo = () => {
          setBattery({
            level: batteryManager.level,
            charging: batteryManager.charging,
            chargingTime: batteryManager.chargingTime,
            dischargingTime: batteryManager.dischargingTime,
          });
        };

        updateBatteryInfo();

        batteryManager.addEventListener('levelchange', updateBatteryInfo);
        batteryManager.addEventListener('chargingchange', updateBatteryInfo);
        batteryManager.addEventListener('chargingtimechange', updateBatteryInfo);
        batteryManager.addEventListener('dischargingtimechange', updateBatteryInfo);

        return () => {
          batteryManager.removeEventListener('levelchange', updateBatteryInfo);
          batteryManager.removeEventListener('chargingchange', updateBatteryInfo);
          batteryManager.removeEventListener('chargingtimechange', updateBatteryInfo);
          batteryManager.removeEventListener('dischargingtimechange', updateBatteryInfo);
        };
      });
    }
  }, []);

  if (!battery) {
    return {
      supported: false,
    };
  }

  return {
    supported: true,
    ...battery,
    percentage: Math.round(battery.level * 100),
    isLow: battery.level < 0.2 && !battery.charging,
  };
};

/**
 * useDevicePerformance hook
 */
export const useDevicePerformance = () => {
  const [performance, setPerformance] = useState({
    cores: navigator.hardwareConcurrency || 4,
    memory: (navigator as any).deviceMemory || 4,
    pixelRatio: window.devicePixelRatio || 1,
    reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    colorScheme: window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light',
  });

  // Check if device is low-end
  const isLowEnd = performance.cores <= 2 || performance.memory <= 2;
  const isHighEnd = performance.cores >= 8 && performance.memory >= 8;

  return {
    ...performance,
    isLowEnd,
    isHighEnd,
    tier: isLowEnd ? 'low' : isHighEnd ? 'high' : 'medium',
  };
};