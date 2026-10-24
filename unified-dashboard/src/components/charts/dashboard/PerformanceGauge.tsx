import React, { useEffect, useRef, useMemo } from 'react'
import { Chart, registerables } from 'chart.js'
import { BaseChartProps } from '../types/chart.types'
import { Doughnut } from 'react-chartjs-2'
import { animated, useSpring } from '@react-spring/web'

// Register Chart.js components
Chart.register(...registerables)

export interface GaugeThreshold {
  value: number
  color: string
  label?: string
}

export interface PerformanceGaugeProps extends Omit<BaseChartProps, 'width' | 'height'> {
  value: number
  min?: number
  max?: number
  thresholds?: GaugeThreshold[]
  label?: string
  unit?: string
  formatValue?: (value: number) => string
  showValue?: boolean
  showThresholds?: boolean
  innerRadius?: number
  outerRadius?: number
  startAngle?: number
  endAngle?: number
  animationDuration?: number
  needle?: {
    show?: boolean
    width?: number
    length?: number
    color?: string
  }
  arc?: {
    backgroundColor?: string
    borderWidth?: number
    borderColor?: string
  }
}

export const PerformanceGauge: React.FC<PerformanceGaugeProps> = ({
  value,
  min = 0,
  max = 100,
  thresholds = [],
  label,
  unit = '',
  formatValue,
  showValue = true,
  showThresholds = true,
  innerRadius = 60,
  outerRadius = 80,
  startAngle = -135,
  endAngle = 135,
  animationDuration = 1000,
  needle = {},
  arc = {},
  className = '',
  theme = 'light',
  responsive = true,
  animation = true,
  dataTestId
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const chartRef = useRef<Chart<'doughnut'> | null>(null)

  // Animation for value
  const { animatedValue } = useSpring({
    from: { value: min },
    to: { value },
    config: { duration: animationDuration },
    reset: true
  })

  // Theme colors
  const themeColors = useMemo(() => {
    return theme === 'dark'
      ? {
          text: 'rgba(255, 255, 255, 0.9)',
          background: '#1f1f1f',
          grid: 'rgba(255, 255, 255, 0.1)'
        }
      : {
          text: 'rgba(0, 0, 0, 0.9)',
          background: '#ffffff',
          grid: 'rgba(0, 0, 0, 0.1)'
        }
  }, [theme])

  // Default thresholds if not provided
  const gaugeThresholds = useMemo(() => {
    if (thresholds.length > 0) return thresholds

    return [
      { value: max * 0.3, color: '#ef5350', label: 'Poor' },
      { value: max * 0.7, color: '#ff9800', label: 'Fair' },
      { value: max, color: '#66bb6a', label: 'Good' }
    ]
  }, [thresholds, max])

  // Prepare gauge segments
  const gaugeData = useMemo(() => {
    const segments: Array<{ value: number; color: string }> = []
    let prevValue = min

    gaugeThresholds.forEach((threshold, index) => {
      segments.push({
        value: threshold.value - prevValue,
        color: threshold.color
      })
      prevValue = threshold.value
    })

    return segments
  }, [gaugeThresholds, min])

  // Chart data
  const chartData = useMemo(() => ({
    datasets: [
      {
        data: gaugeData.map(segment => segment.value),
        backgroundColor: gaugeData.map(segment => segment.color),
        borderWidth: arc.borderWidth || 0,
        borderColor: arc.borderColor || 'transparent',
        hoverOffset: 0
      }
    ]
  }), [gaugeData, arc])

  // Chart options
  const chartOptions = useMemo(() => ({
    responsive,
    maintainAspectRatio: false,
    rotation: startAngle,
    circumference: endAngle - startAngle,
    cutout: `${(innerRadius / outerRadius) * 100}%`,
    animation: animation ? {
      animateRotate: true,
      animateScale: false,
      duration: animationDuration
    } : false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        enabled: false
      }
    },
    elements: {
      arc: {
        roundedCorners: true
      }
    }
  }), [responsive, animation, startAngle, endAngle, innerRadius, outerRadius, animationDuration])

  // Calculate needle angle
  const needleAngle = useMemo(() => {
    const valueRange = max - min
    const valuePercent = (value - min) / valueRange
    const angleRange = endAngle - startAngle
    return startAngle + (angleRange * valuePercent)
  }, [value, min, max, startAngle, endAngle])

  // Format value display
  const formattedValue = useMemo(() => {
    const val = animatedValue.get()
    if (formatValue) return formatValue(val)
    return `${val.toFixed(1)}${unit ? ` ${unit}` : ''}`
  }, [animatedValue, formatValue, unit])

  // Draw needle
  useEffect(() => {
    if (!canvasRef.current || !needle.show) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const centerX = canvas.width / 2
    const centerY = canvas.height / 2
    const needleLength = needle.length || outerRadius - 10
    const needleWidth = needle.width || 3

    // Clear previous needle
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Draw needle
    ctx.save()
    ctx.translate(centerX, centerY)
    ctx.rotate((needleAngle * Math.PI) / 180)

    ctx.beginPath()
    ctx.moveTo(0, 0)
    ctx.lineTo(0, -needleLength)
    ctx.strokeStyle = needle.color || themeColors.text
    ctx.lineWidth = needleWidth
    ctx.stroke()

    // Draw needle base
    ctx.beginPath()
    ctx.arc(0, 0, needleWidth * 2, 0, Math.PI * 2)
    ctx.fillStyle = needle.color || themeColors.text
    ctx.fill()

    ctx.restore()
  }, [needleAngle, needle, outerRadius, themeColors])

  return (
    <div
      className={`performance-gauge ${className}`}
      data-testid={dataTestId}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        position: 'relative'
      }}
    >
      {/* Gauge Chart */}
      <div style={{ position: 'relative', width: '200px', height: '200px' }}>
        <Doughnut data={chartData} options={chartOptions} />

        {/* Value Display */}
        {showValue && (
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              textAlign: 'center',
              color: themeColors.text
            }}
          >
            <div
              style={{
                fontSize: '28px',
                fontWeight: '600',
                fontFamily: 'Inter, sans-serif'
              }}
            >
              {formattedValue}
            </div>
            {label && (
              <div
                style={{
                  fontSize: '12px',
                  opacity: 0.8,
                  fontFamily: 'Inter, sans-serif'
                }}
              >
                {label}
              </div>
            )}
          </div>
        )}

        {/* Needle Canvas */}
        <canvas
          ref={canvasRef}
          width={200}
          height={200}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            pointerEvents: 'none'
          }}
        />
      </div>

      {/* Thresholds Legend */}
      {showThresholds && (
        <div
          style={{
            display: 'flex',
            gap: '16px',
            marginTop: '16px'
          }}
        >
          {gaugeThresholds.map((threshold, index) => (
            <div
              key={index}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <div
                style={{
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  backgroundColor: threshold.color
                }}
              />
              <span
                style={{
                  fontSize: '12px',
                  color: themeColors.text,
                  fontFamily: 'Inter, sans-serif'
                }}
              >
                {threshold.label || `${threshold.value}`}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default PerformanceGauge