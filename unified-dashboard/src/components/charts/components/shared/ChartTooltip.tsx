import React, { useState, useRef, useEffect, useMemo, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { TooltipConfig } from '../../types/chart.types'
import { createPortal } from 'react-dom'

interface ChartTooltipProps {
  visible: boolean
  x?: number
  y?: number
  content: React.ReactNode | ((props: any) => React.ReactNode)
  config?: TooltipConfig
  container?: HTMLElement
  className?: string
  style?: React.CSSProperties
}

const defaultTooltipConfig: TooltipConfig = {
  show: true,
  followCursor: true,
  format: {
    title: (value: any) => String(value),
    value: (value: any) => String(value)
  }
}

export default function ChartTooltip({
  visible,
  x = 0,
  y = 0,
  content,
  config = defaultTooltipConfig,
  container = document.body,
  className = '',
  style
}: ChartTooltipProps) {
  const tooltipRef = useRef<HTMLDivElement>(null)
  const [position, setPosition] = useState({ x, y })
  const [isFlipped, setIsFlipped] = useState(false)

  // Update position with boundary detection
  const updatePosition = useCallback((mouseX: number, mouseY: number) => {
    if (!tooltipRef.current || !config.followCursor) return

    const tooltip = tooltipRef.current
    const rect = tooltip.getBoundingClientRect()
    const containerRect = container.getBoundingClientRect()

    let newX = mouseX + 10
    let newY = mouseY - rect.height - 10

    // Check right boundary
    if (newX + rect.width > containerRect.right) {
      newX = mouseX - rect.width - 10
    }

    // Check left boundary
    if (newX < containerRect.left) {
      newX = containerRect.left + 10
    }

    // Check top boundary
    if (newY < containerRect.top) {
      newY = mouseY + 10
    }

    // Check bottom boundary
    if (newY + rect.height > containerRect.bottom) {
      newY = containerRect.bottom - rect.height - 10
    }

    // Determine if tooltip should flip
    const shouldFlip = mouseX > containerRect.left + containerRect.width / 2

    setIsFlipped(shouldFlip)
    setPosition({ x: newX, y: newY })
  }, [config.followCursor, container])

  // Update position on mouse move
  useEffect(() => {
    if (config.followCursor && visible) {
      updatePosition(x, y)
    }
  }, [x, y, visible, config.followCursor, updatePosition])

  // Handle escape key to hide tooltip
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        // Tooltip visibility should be controlled by parent
      }
    }

    if (visible) {
      document.addEventListener('keydown', handleKeyDown)
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [visible])

  // Render tooltip content
  const tooltipContent = useMemo(() => {
    if (typeof content === 'function') {
      return content({ x, y })
    }
    return content
  }, [content, x, y])

  if (!config.show) {
    return null
  }

  const tooltip = (
    <AnimatePresence mode="wait">
      {visible && (
        <motion.div
          ref={tooltipRef}
          className={`chart-tooltip ${className}`}
          style={{
            position: 'fixed',
            left: position.x,
            top: position.y,
            zIndex: 1000,
            pointerEvents: 'none',
            ...style
          }}
          initial={{
            opacity: 0,
            scale: 0.8,
            y: isFlipped ? 10 : -10
          }}
          animate={{
            opacity: 1,
            scale: 1,
            y: 0,
            transition: {
              type: 'spring',
              stiffness: 500,
              damping: 30
            }
          }}
          exit={{
            opacity: 0,
            scale: 0.8,
            y: isFlipped ? 10 : -10,
            transition: {
              duration: 0.15
            }
          }}
        >
          {/* Tooltip arrow */}
          <div
            className="tooltip-arrow"
            style={{
              position: 'absolute',
              [isFlipped ? 'right' : 'left']: isFlipped ? -6 : 'auto',
              [isFlipped ? 'left' : 'right']: isFlipped ? 'auto' : -6,
              top: '50%',
              transform: 'translateY(-50%)',
              width: 0,
              height: 0,
              borderTop: '6px solid transparent',
              borderBottom: '6px solid transparent',
              [isFlipped ? 'borderRight' : 'borderLeft']: `6px solid ${config.tooltip?.border || 'rgba(0,0,0,0.8)'}`
            }}
          />

          {/* Tooltip content */}
          <div
            className="tooltip-content"
            style={{
              backgroundColor: config.tooltip?.background || 'rgba(0,0,0,0.8)',
              color: config.tooltip?.foreground || '#fff',
              padding: '8px 12px',
              borderRadius: 6,
              fontSize: 12,
              lineHeight: 1.4,
              maxWidth: 300,
              wordWrap: 'break-word',
              border: `1px solid ${config.tooltip?.border || 'rgba(0,0,0,0.8)'}`,
              boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
              backdropFilter: 'blur(4px)'
            }}
          >
            {tooltipContent}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )

  // Use portal to render tooltip outside chart container
  return createPortal(tooltip, container)
}

// Hook for managing tooltip state
export function useChartTooltip(config: Partial<TooltipConfig> = {}) {
  const [visible, setVisible] = useState(false)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [content, setContent] = useState<React.ReactNode | null>(null)

  const show = useCallback((x: number, y: number, tooltipContent: React.ReactNode) => {
    setPosition({ x, y })
    setContent(tooltipContent)
    setVisible(true)
  }, [])

  const hide = useCallback(() => {
    setVisible(false)
    setContent(null)
  }, [])

  const update = useCallback((x: number, y: number) => {
    setPosition({ x, y })
  }, [])

  const TooltipComponent = useCallback((props: Omit<ChartTooltipProps, 'visible' | 'x' | 'y' | 'content'>) => (
    <ChartTooltip
      visible={visible}
      x={position.x}
      y={position.y}
      content={content || ''}
      config={{ ...defaultTooltipConfig, ...config }}
      {...props}
    />
  ), [visible, position, content, config])

  return {
    show,
    hide,
    update,
    isVisible: visible,
    Tooltip: TooltipComponent
  }
}