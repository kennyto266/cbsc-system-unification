import React, { useRef, useEffect, useState } from 'react'
import { ChartConfig, defaultChartTheme, ChartTheme } from '../../types/charts'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { cn } from '../../lib/utils'

interface BaseChartProps {
  config: ChartConfig
  theme?: Partial<ChartTheme>
  className?: string
  onDataPointClick?: (data: any) => void
}

export const BaseChart: React.FC<BaseChartProps> = ({
  config,
  theme,
  className,
  onDataPointClick
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })
  const animationRef = useRef<number>()
  const [isAnimating, setIsAnimating] = useState(false)

  const mergedTheme = { ...defaultChartTheme, ...theme }

  // Handle responsive resize
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const { width } = containerRef.current.getBoundingClientRect()
        setDimensions({
          width: config.responsive ? width : config.width || width,
          height: config.height || 300
        })
      }
    }

    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [config.responsive, config.width, config.height])

  // Real-time data update
  useEffect(() => {
    if (config.realTime && config.updateInterval) {
      const interval = setInterval(() => {
        // Animation frame for smooth updates
        setIsAnimating(true)
        animationRef.current = requestAnimationFrame(() => {
          setIsAnimating(false)
        })
      }, config.updateInterval)

      return () => {
        clearInterval(interval)
        if (animationRef.current) {
          cancelAnimationFrame(animationRef.current)
        }
      }
    }
  }, [config.realTime, config.updateInterval])

  // Canvas drawing (placeholder for actual chart library integration)
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Set canvas size
    canvas.width = dimensions.width
    canvas.height = dimensions.height

    // Clear canvas
    ctx.clearRect(0, 0, dimensions.width, dimensions.height)

    // Placeholder drawing - would be replaced with actual chart library
    ctx.fillStyle = mergedTheme.textColor
    ctx.font = '14px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(
      `${config.title} - ${config.type} Chart`,
      dimensions.width / 2,
      dimensions.height / 2
    )

    if (config.data.length > 0) {
      ctx.fillText(
        `${config.data.length} data points`,
        dimensions.width / 2,
        dimensions.height / 2 + 20
      )
    }
  }, [dimensions, config, mergedTheme, isAnimating])

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">{config.title}</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div ref={containerRef} className="relative w-full">
          <canvas
            ref={canvasRef}
            className={cn(
              "w-full cursor-crosshair",
              isAnimating && "transition-all duration-300"
            )}
            onClick={(e) => {
              const rect = canvasRef.current?.getBoundingClientRect()
              if (rect && onDataPointClick) {
                const x = e.clientX - rect.left
                const y = e.clientY - rect.top
                onDataPointClick({ x, y })
              }
            }}
          />
          {config.realTime && (
            <div className="absolute top-2 right-2">
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="text-xs text-muted-foreground">实时</span>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}