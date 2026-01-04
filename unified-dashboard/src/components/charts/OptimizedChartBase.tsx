import React, { memo, useMemo, useCallback, useRef, useEffect } from 'react'
import { useResizeObserver } from '../../hooks/useResizeObserver'
import { useIntersectionObserver } from '../../hooks/useIntersectionObserver'
import { usePerformanceMonitor } from '../../hooks/usePerformanceMonitor'

interface OptimizedChartBaseProps {
  width?: number
  height?: number
  data: any
  options?: any
  type?: 'line' | 'bar' | 'scatter' | 'candlestick'
  lazy?: boolean
  debounceMs?: number
  onDataPointClick?: (data: any) => void
  className?: string
  children?: (props: {
    width: number,
    height: number,
    isIntersecting: boolean
  }) => React.ReactNode
}

// 使用 memo 优化组件重渲染
const OptimizedChartBase = memo<OptimizedChartBaseProps>(({
  width,
  height,
  data,
  options,
  type = 'line',
  lazy = true,
  debounceMs = 300,
  onDataPointClick,
  className,
  children
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const chartInstanceRef = useRef<any>(null)
  const resizeTimeoutRef = useRef<NodeJS.Timeout>()

  // 性能监控
  const { startMeasure, endMeasure } = usePerformanceMonitor()

  // 使用 Intersection Observer 实现懒加载
  const { isIntersecting, entry } = useIntersectionObserver(containerRef, {
    threshold: 0.1,
    rootMargin: '50px'
  })

  // 使用 Resize Observer 监听容器尺寸变化
  const { width: containerWidth, height: containerHeight } = useResizeObserver(containerRef)

  // 防抖处理尺寸变化
  const debouncedResize = useCallback(
    (() => {
      let timeoutId: NodeJS.Timeout
      return (callback: () => void) => {
        clearTimeout(timeoutId)
        timeoutId = setTimeout(callback, debounceMs)
      }
    })(),
    [debounceMs]
  )

  // 优化的数据处理
  const optimizedData = useMemo(() => {
    if (!data || !isIntersecting) return null

    startMeasure('dataOptimization')

    // 数据抽样 - 大数据集优化
    const maxDataPoints = 1000
    let processedData = data

    if (data.datasets) {
      const processedDatasets = data.datasets.map((dataset: any) => {
        const processedDataset = { ...dataset }
        if (dataset.data.length > maxDataPoints) {
          const step = Math.ceil(dataset.data.length / maxDataPoints)
          processedDataset.data = dataset.data.filter((_: any, i: number) => i % step === 0)
        }
        return processedDataset
      })
      processedData = { ...data, datasets: processedDatasets }
    }

    endMeasure('dataOptimization')
    return processedData
  }, [data, isIntersecting, startMeasure, endMeasure])

  // 优化的配置选项
  const optimizedOptions = useMemo(() => {
    if (!options) return {}

    return {
      ...options,
      // 性能优化配置
      animation: {
        duration: isIntersecting ? 300 : 0,
        easing: 'easeInOutQuart'
      },
      elements: {
        point: {
          radius: 0, // 默认不显示点以提高性能
          hoverRadius: 4
        }
      },
      interaction: {
        intersect: false,
        mode: 'index'
      },
      // 优化渲染
      sampling: {
        enabled: true,
        algorithm: 'min-max'
      },
      // 优化插件
      plugins: {
        ...options.plugins,
        legend: {
          ...options.plugins?.legend,
          labels: {
            ...options.plugins?.legend?.labels,
            usePointStyle: true,
            boxWidth: 8,
            padding: 12
          }
        },
        tooltip: {
          ...options.plugins?.tooltip,
          enabled: isIntersecting,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: '#fff',
          bodyColor: '#fff',
          borderColor: '#ddd',
          borderWidth: 1,
          cornerRadius: 4,
          displayColors: false,
          callbacks: {
            title: (context: any) => {
              return context[0].label
            },
            label: (context: any) => {
              const label = context.dataset.label || ''
              const value = context.parsed.y || context.parsed.x || 0
              return `${label}: ${value.toLocaleString()}`
            }
          }
        },
        zoom: {
          zoom: {
            wheel: {
              enabled: true,
            },
            pinch: {
              enabled: true
            },
            mode: 'x',
          },
          pan: {
            enabled: true,
            mode: 'x',
          }
        }
      },
      // 优化缩放
      scales: {
        ...options.scales,
        x: {
          ...options.scales?.x,
          ticks: {
            maxTicksLimit: 20, // 限制刻度数量
            maxRotation: 45,
            minRotation: 0
          },
          grid: {
            display: false, // 隐藏网格线以提高性能
            drawBorder: false
          }
        },
        y: {
          ...options.scales?.y,
          ticks: {
            maxTicksLimit: 10,
            callback: function(value: any) {
              return value.toLocaleString()
            }
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.05)',
            drawBorder: false
          }
        }
      }
    }
  }, [options, isIntersecting])

  // 处理数据点点击
  const handleDataPointClick = useCallback((event: any, elements: any[]) => {
    if (elements.length > 0 && onDataPointClick) {
      const datasetIndex = elements[0].datasetIndex
      const index = elements[0].index
      const dataset = optimizedData?.datasets[datasetIndex]
      const value = dataset?.data[index]

      onDataPointClick({
        datasetIndex,
        index,
        dataset,
        value,
        label: optimizedData?.labels?.[index]
      })
    }
  }, [onDataPointClick, optimizedData])

  // 处理容器尺寸变化
  useEffect(() => {
    if (containerWidth && containerHeight) {
      debouncedResize(() => {
        if (chartInstanceRef.current) {
          chartInstanceRef.current.resize()
        }
      })
    }
  }, [containerWidth, containerHeight, debouncedResize])

  // 清理资源
  useEffect(() => {
    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy()
        chartInstanceRef.current = null
      }
      if (resizeTimeoutRef.current) {
        clearTimeout(resizeTimeoutRef.current)
      }
    }
  }, [])

  // 如果启用懒加载且不在视口内，返回占位符
  if (lazy && !isIntersecting) {
    return (
      <div
        ref={containerRef}
        className={`chart-placeholder ${className || ''}`}
        style={{
          width: width || '100%',
          height: height || 400,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#f5f5f5',
          borderRadius: '4px'
        }}
      >
        <div style={{ textAlign: 'center', color: '#999' }}>
          <div style={{ fontSize: 48, marginBottom: 8 }}>📊</div>
          <div>图表加载中...</div>
        </div>
      </div>
    )
  }

  // 渲染图表
  return (
    <div
      ref={containerRef}
      className={`optimized-chart ${className || ''}`}
      style={{
        width: width || '100%',
        height: height || 400,
        position: 'relative'
      }}
    >
      {children && children({
        width: containerWidth || width || 800,
        height: containerHeight || height || 400,
        isIntersecting
      })}

      {/* 性能指标显示（开发模式） */}
      {process.env.NODE_ENV === 'development' && (
        <div
          style={{
            position: 'absolute',
            top: 8,
            right: 8,
            background: 'rgba(0, 0, 0, 0.7)',
            color: '#fff',
            padding: '4px 8px',
            borderRadius: '4px',
            fontSize: '12px',
            fontFamily: 'monospace',
            pointerEvents: 'none'
          }}
        >
          FPS: {60} | Data Points: {optimizedData?.datasets?.[0]?.data?.length || 0}
        </div>
      )}
    </div>
  )
})

OptimizedChartBase.displayName = 'OptimizedChartBase'

export default OptimizedChartBase