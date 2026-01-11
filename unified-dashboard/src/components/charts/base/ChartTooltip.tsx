import React, { useMemo } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'

export interface TooltipData {
  label?: string
  value: number
  color?: string
  formatter?: (value: number) => string
}

export interface ChartTooltipProps {
  active?: boolean
  payload?: TooltipData[]
  label?: string
  coordinate?: { x: number; y: number }
  className?: string
  theme?: 'light' | 'dark'
  showLabel?: boolean
  showIndicator?: boolean
  formatter?: (value: number) => string
  customContent?: (payload: TooltipData[]) => React.ReactNode
  offset?: { x: number; y: number }
  position?: 'top' | 'bottom' | 'left' | 'right' | 'auto'
}

const ChartTooltip: React.FC<ChartTooltipProps> = ({
  active,
  payload = [],
  label,
  coordinate = { x: 0, y: 0 },
  className,
  theme = 'dark',
  showLabel = true,
  showIndicator = true,
  formatter,
  customContent,
  offset = { x: 0, y: 0 },
  position = 'auto',
}) => {
  // Determine tooltip position
  const tooltipPosition = useMemo(() => {
    if (!coordinate) return { top: 0, left: 0 }

    const tooltipWidth = 200
    const tooltipHeight = payload.length * 30 + (showLabel && label ? 30 : 0) + 20
    const padding = 10

    let left = coordinate.x + offset.x
    let top = coordinate.y + offset.y

    // Auto position adjustment
    if (position === 'auto') {
      const windowWidth = window.innerWidth
      const windowHeight = window.innerHeight

      // Adjust horizontal position
      if (left + tooltipWidth > windowWidth - padding) {
        left = coordinate.x - tooltipWidth + offset.x
      }
      if (left < padding) {
        left = padding
      }

      // Adjust vertical position
      if (top + tooltipHeight > windowHeight - padding) {
        top = coordinate.y - tooltipHeight + offset.y
      }
      if (top < padding) {
        top = padding
      }
    } else {
      // Apply specific position adjustments
      switch (position) {
        case 'top':
          top = coordinate.y - tooltipHeight + offset.y
          left = coordinate.x - tooltipWidth / 2 + offset.x
          break
        case 'bottom':
          top = coordinate.y + offset.y
          left = coordinate.x - tooltipWidth / 2 + offset.x
          break
        case 'left':
          top = coordinate.y - tooltipHeight / 2 + offset.y
          left = coordinate.x - tooltipWidth + offset.x
          break
        case 'right':
          top = coordinate.y - tooltipHeight / 2 + offset.y
          left = coordinate.x + offset.x
          break
      }
    }

    return { top, left }
  }, [coordinate, offset, position, payload.length, showLabel, label])

  // Format value function
  const formatValue = (value: number, item: TooltipData) => {
    if (item.formatter) return item.formatter(value)
    if (formatter) return formatter(value)

    // Default formatting
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`
    } else if (value < 0.01 && value > 0) {
      return value.toFixed(4)
    } else if (value < 1) {
      return value.toFixed(3)
    } else {
      return value.toFixed(2)
    }
  }

  // Custom tooltip content
  if (!active || !payload.length) return null

  const content = customContent ? (
    customContent(payload)
  ) : (
    <div className={cn(
      'rounded-lg shadow-lg border p-3 min-w-[150px]',
      theme === 'dark'
        ? 'bg-gray-900 border-gray-700 text-white'
        : 'bg-white border-gray-200 text-gray-900',
      className
    )}>
      {showLabel && label && (
        <div className={cn(
          'text-xs font-medium mb-2 pb-2 border-b',
          theme === 'dark' ? 'border-gray-700 text-gray-300' : 'border-gray-200 text-gray-600'
        )}>
          {label}
        </div>
      )}

      <div className="space-y-1">
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2">
              {showIndicator && entry.color && (
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: entry.color }}
                />
              )}
              <span className={cn(
                theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
              )}>
                {entry.label || `Value ${index + 1}`}
              </span>
            </div>
            <span className="font-medium ml-4">
              {formatValue(entry.value, entry)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )

  return createPortal(
    <AnimatePresence>
      {active && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={{ duration: 0.15, ease: 'easeOut' }}
          className="fixed z-50 pointer-events-none"
          style={{
            top: tooltipPosition.top,
            left: tooltipPosition.left,
          }}
        >
          {content}
        </motion.div>
      )}
    </AnimatePresence>,
    document.body
  )
}

// Tooltip wrapper for Chart.js
export const createChartTooltip = (options: Partial<ChartTooltipProps> = {}) => {
  return (context: any) => {
    const tooltipModel = context.tooltip

    if (tooltipModel.opacity === 0) {
      return
    }

    const tooltipElement = document.getElementById('chartjs-tooltip')
    if (!tooltipElement) {
      return
    }

    // Set tooltip position
    const position = context.chart.canvas.getBoundingClientRect()
    tooltipElement.style.left = position.left + window.pageXOffset + tooltipModel.caretX + 'px'
    tooltipElement.style.top = position.top + window.pageYOffset + tooltipModel.caretY + 'px'

    // Set tooltip content
    if (tooltipModel.body) {
      const tooltipData = tooltipModel.body.map((bodyItem: any) => ({
        label: bodyItem.lines[0].split(':')[0]?.trim(),
        value: parseFloat(bodyItem.lines[0].split(':')[1]?.trim() || '0'),
        color: bodyItem.lines[0].split(':')[0]?.trim(),
      }))

      // Render tooltip content here
      // This is a simplified version - you might want to use React Portal for better integration
    }
  }
}

export default ChartTooltip