// Animation utilities and configurations for charts

export interface ChartAnimationConfig {
  duration: number
  easing: string
  delay: number
  type: 'sequential' | 'simultaneous' | 'staggered'
  onComplete?: () => void
  onStart?: () => void
  onProgress?: (progress: number) => void
}

// Predefined animation configurations
export const chartAnimations: Record<string, ChartAnimationConfig> = {
  // Smooth and professional
  smooth: {
    duration: 1000,
    easing: 'easeInOutQuart',
    delay: 0,
    type: 'sequential',
  },

  // Quick and snappy
  snappy: {
    duration: 500,
    easing: 'easeOutCubic',
    delay: 0,
    type: 'simultaneous',
  },

  // Dramatic entrance
  dramatic: {
    duration: 1500,
    easing: 'easeInOutElastic',
    delay: 100,
    type: 'staggered',
  },

  // Gentle fade in
  gentle: {
    duration: 750,
    easing: 'easeInOutSine',
    delay: 0,
    type: 'sequential',
  },

  // No animation
  none: {
    duration: 0,
    easing: 'linear',
    delay: 0,
    type: 'simultaneous',
  },
}

// Animation easing functions
export const easingFunctions: Record<string, (t: number) => number> = {
  // Linear
  linear: (t: number) => t,

  // Quad
  easeInQuad: (t: number) => t * t,
  easeOutQuad: (t: number) => t * (2 - t),
  easeInOutQuad: (t: number) => t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t,

  // Cubic
  easeInCubic: (t: number) => t * t * t,
  easeOutCubic: (t: number) => (--t) * t * t + 1,
  easeInOutCubic: (t: number) =>
    t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1,

  // Quart
  easeInQuart: (t: number) => t * t * t * t,
  easeOutQuart: (t: number) => 1 - (--t) * t * t * t,
  easeInOutQuart: (t: number) =>
    t < 0.5 ? 8 * t * t * t * t : 1 - 8 * (--t) * t * t * t,

  // Quint
  easeInQuint: (t: number) => t * t * t * t * t,
  easeOutQuint: (t: number) => 1 + (--t) * t * t * t * t,
  easeInOutQuint: (t: number) =>
    t < 0.5 ? 16 * t * t * t * t * t : 1 + 16 * (--t) * t * t * t * t,

  // Sine
  easeInSine: (t: number) => 1 - Math.cos((t * Math.PI) / 2),
  easeOutSine: (t: number) => Math.sin((t * Math.PI) / 2),
  easeInOutSine: (t: number) => -(Math.cos(Math.PI * t) - 1) / 2,

  // Expo
  easeInExpo: (t: number) => (t === 0 ? 0 : Math.pow(2, 10 * t - 10)),
  easeOutExpo: (t: number) => (t === 1 ? 1 : 1 - Math.pow(2, -10 * t)),
  easeInOutExpo: (t: number) =>
    t === 0
      ? 0
      : t === 1
      ? 1
      : t < 0.5
      ? Math.pow(2, 20 * t - 10) / 2
      : (2 - Math.pow(2, -20 * t + 10)) / 2,

  // Circ
  easeInCirc: (t: number) => 1 - Math.sqrt(1 - Math.pow(t, 2)),
  easeOutCirc: (t: number) => Math.sqrt(1 - Math.pow(t - 1, 2)),
  easeInOutCirc: (t: number) =>
    t < 0.5
      ? (1 - Math.sqrt(1 - Math.pow(2 * t, 2))) / 2
      : (Math.sqrt(1 - Math.pow(-2 * t + 2, 2)) + 1) / 2,

  // Back
  easeInBack: (t: number) => {
    const c1 = 1.70158
    const c3 = c1 + 1
    return c3 * t * t * t - c1 * t * t
  },
  easeOutBack: (t: number) => {
    const c1 = 1.70158
    const c3 = c1 + 1
    return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2)
  },
  easeInOutBack: (t: number) => {
    const c1 = 1.70158
    const c2 = c1 * 1.525
    return t < 0.5
      ? (Math.pow(2 * t, 2) * ((c2 + 1) * 2 * t - c2)) / 2
      : (Math.pow(2 * t - 2, 2) * ((c2 + 1) * (t * 2 - 2) + c2) + 2) / 2
  },

  // Elastic
  easeInElastic: (t: number) => {
    const c4 = (2 * Math.PI) / 3
    return t === 0
      ? 0
      : t === 1
      ? 1
      : -Math.pow(2, 10 * t - 10) * Math.sin((t * 10 - 10.75) * c4)
  },
  easeOutElastic: (t: number) => {
    const c4 = (2 * Math.PI) / 3
    return t === 0
      ? 0
      : t === 1
      ? 1
      : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * c4) + 1
  },
  easeInOutElastic: (t: number) => {
    const c5 = (2 * Math.PI) / 4.5
    return t === 0
      ? 0
      : t === 1
      ? 1
      : t < 0.5
      ? -(Math.pow(2, 20 * t - 10) * Math.sin((20 * t - 11.125) * c5)) / 2
      : (Math.pow(2, -20 * t + 10) * Math.sin((20 * t - 11.125) * c5)) / 2 + 1
  },

  // Bounce
  easeInBounce: (t: number) => 1 - easeOutBounce(1 - t),
  easeOutBounce: (t: number) => {
    const n1 = 7.5625
    const d1 = 2.75

    if (t < 1 / d1) {
      return n1 * t * t
    } else if (t < 2 / d1) {
      return n1 * (t -= 1.5 / d1) * t + 0.75
    } else if (t < 2.5 / d1) {
      return n1 * (t -= 2.25 / d1) * t + 0.9375
    } else {
      return n1 * (t -= 2.625 / d1) * t + 0.984375
    }
  },
  easeInOutBounce: (t: number) =>
    t < 0.5 ? (1 - easeOutBounce(1 - 2 * t)) / 2 : (1 + easeOutBounce(2 * t - 1)) / 2,
}

// Animation helper functions
export const createAnimation = (
  config: Partial<ChartAnimationConfig> = {}
): ChartAnimationConfig => {
  return {
    duration: 1000,
    easing: 'easeInOutQuart',
    delay: 0,
    type: 'sequential',
    ...config,
  }
}

export const staggerAnimation = (
  baseConfig: ChartAnimationConfig,
  itemCount: number,
  staggerDelay: number = 50
): ChartAnimationConfig[] => {
  const animations: ChartAnimationConfig[] = []

  for (let i = 0; i < itemCount; i++) {
    animations.push({
      ...baseConfig,
      delay: baseConfig.delay + (i * staggerDelay),
    })
  }

  return animations
}

export const sequentialAnimation = (
  configs: ChartAnimationConfig[],
  onComplete?: () => void
): void => {
  let currentIndex = 0

  const runNext = () => {
    if (currentIndex >= configs.length) {
      onComplete?.()
      return
    }

    const config = configs[currentIndex]
    config.onStart?.()

    animate(
      config.duration,
      (progress) => {
        config.onProgress?.(progress)
      },
      () => {
        config.onComplete?.()
        currentIndex++
        setTimeout(runNext, config.delay)
      },
      config.easing
    )
  }

  runNext()
}

// Core animation function
export const animate = (
  duration: number,
  onUpdate: (progress: number) => void,
  onComplete: () => void,
  easing: string = 'linear'
): void => {
  const startTime = Date.now()
  const easingFunc = easingFunctions[easing] || easingFunctions.linear

  const tick = () => {
    const elapsed = Date.now() - startTime
    const progress = Math.min(elapsed / duration, 1)

    onUpdate(easingFunc(progress))

    if (progress < 1) {
      requestAnimationFrame(tick)
    } else {
      onComplete()
    }
  }

  requestAnimationFrame(tick)
}

// Chart.js specific animation configurations
export const chartJSAnimations = {
  // Line chart animations
  lineChart: {
    animation: {
      duration: 1000,
      easing: 'easeInOutQuart',
      delay: (context: any) => {
        let delay = 0
        if (context.type === 'data' && context.mode === 'default') {
          delay = context.dataIndex * 100 + context.datasetIndex * 50
        }
        return delay
      },
    },
  },

  // Bar chart animations
  barChart: {
    animation: {
      duration: 750,
      easing: 'easeOutQuart',
      delay: (context: any) => {
        let delay = 0
        if (context.type === 'data' && context.mode === 'default') {
          delay = context.dataIndex * 50
        }
        return delay
      },
    },
  },

  // Pie chart animations
  pieChart: {
    animation: {
      animateRotate: true,
      animateScale: true,
      duration: 1000,
      easing: 'easeInOutQuart',
    },
  },

  // Radar chart animations
  radarChart: {
    animation: {
      duration: 1500,
      easing: 'easeInOutQuart',
      delay: (context: any) => {
        let delay = 0
        if (context.type === 'data' && context.mode === 'default') {
          delay = context.datasetIndex * 200
        }
        return delay
      },
    },
  },

  // Financial chart animations
  candlestickChart: {
    animation: {
      duration: 500,
      easing: 'easeOutCubic',
      delay: (context: any) => {
        let delay = 0
        if (context.type === 'data' && context.mode === 'default') {
          delay = context.dataIndex * 25
        }
        return delay
      },
    },
  },
}

// Morphing animations between chart states
export const morphAnimation = (
  fromData: any,
  toData: any,
  duration: number = 1000,
  onUpdate: (interpolatedData: any) => void,
  onComplete?: () => void
): void => {
  const startTime = Date.now()

  const interpolate = (start: any, end: any, progress: number): any => {
    if (typeof start === 'number' && typeof end === 'number') {
      return start + (end - start) * progress
    } else if (Array.isArray(start) && Array.isArray(end)) {
      return start.map((val, i) => interpolate(val, end[i], progress))
    } else if (typeof start === 'object' && typeof end === 'object' && start !== null && end !== null) {
      const result: any = {}
      for (const key in start) {
        if (end.hasOwnProperty(key)) {
          result[key] = interpolate(start[key], end[key], progress)
        } else {
          result[key] = start[key]
        }
      }
      return result
    }
    return end
  }

  const tick = () => {
    const elapsed = Date.now() - startTime
    const progress = Math.min(elapsed / duration, 1)
    const easedProgress = easingFunctions.easeInOutQuart(progress)

    const interpolatedData = interpolate(fromData, toData, easedProgress)
    onUpdate(interpolatedData)

    if (progress < 1) {
      requestAnimationFrame(tick)
    } else {
      onComplete?.()
    }
  }

  requestAnimationFrame(tick)
}

// Performance-optimized animation for large datasets
export const optimizedAnimation = (
  data: any[],
  updateFunc: (index: number, item: any, progress: number) => void,
  batchSize: number = 50,
  staggerDelay: number = 16
): void => {
  let currentIndex = 0

  const processBatch = () => {
    const endIndex = Math.min(currentIndex + batchSize, data.length)

    for (let i = currentIndex; i < endIndex; i++) {
      updateFunc(i, data[i], 1)
    }

    currentIndex = endIndex

    if (currentIndex < data.length) {
      setTimeout(processBatch, staggerDelay)
    }
  }

  processBatch()
}

// Animation presets for specific use cases
export const animationPresets = {
  // Loading animation for initial data load
  loading: createAnimation({
    duration: 1200,
    easing: 'easeOutCubic',
    type: 'staggered',
    delay: 50,
  }),

  // Update animation for real-time data
  realtime: createAnimation({
    duration: 300,
    easing: 'easeInOutSine',
    type: 'simultaneous',
    delay: 0,
  }),

  // Transition animation between different datasets
  transition: createAnimation({
    duration: 800,
    easing: 'easeInOutQuart',
    type: 'sequential',
    delay: 100,
  }),

  // Highlight animation for user interactions
  highlight: createAnimation({
    duration: 400,
    easing: 'easeOutBack',
    type: 'simultaneous',
    delay: 0,
  }),

  // Error state animation
  error: createAnimation({
    duration: 500,
    easing: 'easeInOutElastic',
    type: 'staggered',
    delay: 25,
  }),
}