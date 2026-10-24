import React, { forwardRef, useRef, useImperativeHandle, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BaseChartProps, ChartRef, ChartTheme } from '../../types/chart.types'
import { useChartPerformance } from '../../hooks/useChartPerformance'

interface ChartContainerProps extends BaseChartProps {
  children: React.ReactNode
  title?: string
  subtitle?: string
  loading?: boolean
  error?: string
  toolbar?: React.ReactNode
  footer?: React.ReactNode
  className?: string
  theme?: ChartTheme
  containerRef?: React.RefObject<HTMLDivElement>
  onResize?: (dimensions: { width: number; height: number }) => void
}

const ChartContainer = forwardRef<ChartRef, ChartContainerProps>(({
  children,
  width = '100%',
  height = 400,
  className = '',
  title,
  subtitle,
  loading = false,
  error,
  toolbar,
  footer,
  theme,
  containerRef,
  onResize,
  ...props
}, ref) => {
  const internalRef = useRef<HTMLDivElement>(null)
  const containerElementRef = containerRef || internalRef
  const { metrics, startRenderTracking, endRenderTracking } = useChartPerformance()

  // Set up resize observer
  useEffect(() => {
    if (!containerElementRef.current || !onResize) return

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width: w, height: h } = entry.contentRect
        onResize({ width: w, height: h })
      }
    })

    resizeObserver.observe(containerElementRef.current)

    return () => {
      resizeObserver.disconnect()
    }
  }, [onResize])

  // Expose chart methods via ref
  useImperativeHandle(ref, () => ({
    updateData: () => {
      // To be implemented by child charts
    },
    zoomTo: () => {
      // To be implemented by child charts
    },
    resetZoom: () => {
      // To be implemented by child charts
    },
    exportImage: async (format: 'png' | 'svg' | 'pdf') => {
      // Default implementation - can be overridden by child charts
      if (containerElementRef.current) {
        const canvas = document.createElement('canvas')
        const ctx = canvas.getContext('2d')
        // Basic canvas creation - child charts should override this
        return new Blob([''], { type: 'image/png' })
      }
      return new Blob([''], { type: 'image/png' })
    },
    getPerformanceMetrics: () => metrics,
    destroy: () => {
      // Cleanup logic
    }
  }), [metrics])

  const containerStyle: React.CSSProperties = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
    backgroundColor: theme?.colors.background || 'transparent',
    fontFamily: theme?.typography.fontFamily || 'inherit',
    ...props.style
  }

  return (
    <motion.div
      ref={containerElementRef}
      className={`chart-container ${className}`}
      style={containerStyle}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      data-testid={props.dataTestId}
    >
      {/* Header */}
      {(title || subtitle) && (
        <motion.div
          className="chart-header"
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
          style={{
            padding: theme?.spacing.md,
            borderBottom: `1px solid ${theme?.colors.grid || 'rgba(0,0,0,0.1)'}`
          }}
        >
          {title && (
            <h3
              style={{
                margin: 0,
                fontSize: theme?.typography.fontSize.large,
                color: theme?.colors.foreground,
                fontWeight: 600
              }}
            >
              {title}
            </h3>
          )}
          {subtitle && (
            <p
              style={{
                margin: '4px 0 0 0',
                fontSize: theme?.typography.fontSize.small,
                color: theme?.colors.foreground,
                opacity: 0.7
              }}
            >
              {subtitle}
            </p>
          )}
        </motion.div>
      )}

      {/* Toolbar */}
      {toolbar && (
        <motion.div
          className="chart-toolbar"
          initial={{ y: -10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          style={{
            padding: `${theme?.spacing.sm}px ${theme?.spacing.md}px`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor: theme?.colors.background
          }}
        >
          {toolbar}
        </motion.div>
      )}

      {/* Chart Content */}
      <div
        className="chart-content"
        style={{
          position: 'relative',
          flex: 1,
          minHeight: 0,
          padding: theme?.spacing.md
        }}
      >
        <AnimatePresence mode="wait">
          {loading && (
            <motion.div
              key="loading"
              className="chart-loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: theme?.colors.background,
                zIndex: 10
              }}
            >
              <div style={{ textAlign: 'center' }}>
                <div
                  className="loading-spinner"
                  style={{
                    width: 40,
                    height: 40,
                    border: `3px solid ${theme?.colors.grid}`,
                    borderTop: `3px solid ${theme?.colors.primary[0]}`,
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite',
                    margin: '0 auto 8px'
                  }}
                />
                <div
                  style={{
                    fontSize: theme?.typography.fontSize.small,
                    color: theme?.colors.foreground,
                    opacity: 0.7
                  }}
                >
                  加载中...
                </div>
              </div>
            </motion.div>
          )}

          {error && !loading && (
            <motion.div
              key="error"
              className="chart-error"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: theme?.spacing.lg,
                zIndex: 10
              }}
            >
              <div
                style={{
                  textAlign: 'center',
                  color: theme?.colors.secondary[1] || '#ef4444',
                  backgroundColor: `${theme?.colors.secondary[1] || '#ef4444'}10`,
                  padding: theme?.spacing.lg,
                  borderRadius: 8,
                  border: `1px solid ${theme?.colors.secondary[1] || '#ef4444'}30`
                }}
              >
                <div
                  style={{
                    fontSize: theme?.typography.fontSize.medium,
                    marginBottom: theme?.spacing.sm,
                    fontWeight: 600
                  }}
                >
                  图表加载错误
                </div>
                <div
                  style={{
                    fontSize: theme?.typography.fontSize.small,
                    opacity: 0.8
                  }}
                >
                  {error}
                </div>
              </div>
            </motion.div>
          )}

          {!loading && !error && (
            <motion.div
              key="content"
              className="chart-wrapper"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{
                width: '100%',
                height: '100%'
              }}
              onAnimationStart={() => startRenderTracking()}
              onAnimationComplete={() => endRenderTracking()}
            >
              {children}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer */}
      {footer && (
        <motion.div
          className="chart-footer"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3 }}
          style={{
            padding: theme?.spacing.md,
            borderTop: `1px solid ${theme?.colors.grid || 'rgba(0,0,0,0.1)'}`,
            fontSize: theme?.typography.fontSize.small,
            color: theme?.colors.foreground,
            opacity: 0.7,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          {footer}
          {/* Performance metrics overlay for development */}
          {process.env.NODE_ENV === 'development' && (
            <div
              style={{
                fontSize: 10,
                opacity: 0.5,
                fontFamily: 'monospace'
              }}
            >
              FPS: {metrics.fps} | Render: {metrics.renderTime.toFixed(1)}ms
            </div>
          )}
        </motion.div>
      )}

      {/* Add keyframe animations */}
      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </motion.div>
  )
})

ChartContainer.displayName = 'ChartContainer'

export default ChartContainer