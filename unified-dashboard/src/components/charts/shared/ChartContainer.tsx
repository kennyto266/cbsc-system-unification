import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react'
import { BaseChartProps, ChartInteractionState, ChartEventHandlers } from '../types/chart.types'
import { Fullscreen, Minimize, Download, RefreshCw, Settings, Camera } from 'lucide-react'

export interface ChartContainerProps extends BaseChartProps {
  title?: string
  subtitle?: string
  description?: string
  footer?: React.ReactNode
  toolbar?: {
    enabled?: boolean
    showFullscreen?: boolean
    showDownload?: boolean
    showRefresh?: boolean
    showSettings?: boolean
    showScreenshot?: boolean
    customActions?: Array<{
      key: string
      icon: React.ReactNode
      tooltip: string
      onClick: () => void
      disabled?: boolean
    }>
  }
  loading?: boolean
  error?: string
  empty?: boolean
  emptyMessage?: string
  onRefresh?: () => void
  onSettings?: () => void
  exportFormats?: Array<'png' | 'svg' | 'pdf' | 'csv' | 'json'>
  children: React.ReactNode
  className?: string
  style?: React.CSSProperties
}

export interface ChartRef {
  exportChart: (format: 'png' | 'svg' | 'pdf') => Promise<Blob>
  refresh: () => void
  getScreenshot: () => Promise<string>
}

export const ChartContainer: React.FC<ChartContainerProps> = ({
  title,
  subtitle,
  description,
  footer,
  toolbar = {},
  loading = false,
  error,
  empty = false,
  emptyMessage = 'No data available',
  onRefresh,
  onSettings,
  exportFormats = ['png'],
  children,
  className = '',
  style,
  theme = 'light',
  dataTestId
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [showExportMenu, setShowExportMenu] = useState(false)

  // Theme styles
  const themeStyles = useMemo(() => {
    return theme === 'dark'
      ? {
          background: '#1f1f1f',
          color: 'rgba(255, 255, 255, 0.9)',
          border: 'rgba(255, 255, 255, 0.1)',
          toolbarBg: 'rgba(255, 255, 255, 0.05)',
          overlay: 'rgba(0, 0, 0, 0.8)'
        }
      : {
          background: '#ffffff',
          color: 'rgba(0, 0, 0, 0.9)',
          border: 'rgba(0, 0, 0, 0.1)',
          toolbarBg: 'rgba(0, 0, 0, 0.02)',
          overlay: 'rgba(255, 255, 255, 0.95)'
        }
  }, [theme])

  // Handle fullscreen
  const toggleFullscreen = useCallback(() => {
    if (!containerRef.current) return

    if (!isFullscreen) {
      if (containerRef.current.requestFullscreen) {
        containerRef.current.requestFullscreen()
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen()
      }
    }
    setIsFullscreen(!isFullscreen)
  }, [isFullscreen])

  // Listen for fullscreen changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }

    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange)
    }
  }, [])

  // Export chart
  const exportChart = useCallback(async (format: 'png' | 'svg' | 'pdf') => {
    if (!containerRef.current) return

    const canvas = containerRef.current.querySelector('canvas')
    if (!canvas) return

    let blob: Blob

    switch (format) {
      case 'png':
        blob = await new Promise<Blob>((resolve) => {
          canvas.toBlob((blob) => resolve(blob!), 'image/png')
        })
        break
      case 'svg':
        // For SVG export, we need to capture the SVG element or convert canvas to SVG
        // This is a simplified version - you might want to use a library like canvas2svg
        const svgString = `<svg xmlns="http://www.w3.org/2000/svg" width="${canvas.width}" height="${canvas.height}">
          <foreignObject width="100%" height="100%">
            <img src="${canvas.toDataURL()}" width="${canvas.width}" height="${canvas.height}" />
          </foreignObject>
        </svg>`
        blob = new Blob([svgString], { type: 'image/svg+xml' })
        break
      case 'pdf':
        // For PDF export, you would typically use a library like jsPDF
        // This is a placeholder implementation
        console.log('PDF export not implemented')
        return
    }

    // Download the file
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `chart_${Date.now()}.${format}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }, [])

  // Screenshot
  const getScreenshot = useCallback(async (): Promise<string> => {
    if (!containerRef.current) return ''

    const canvas = containerRef.current.querySelector('canvas') as HTMLCanvasElement
    if (!canvas) return ''

    return canvas.toDataURL('image/png')
  }, [])

  // Loading overlay
  const LoadingOverlay = () => (
    <div className="chart-loading-overlay" style={{
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: themeStyles.overlay,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      backdropFilter: 'blur(4px)'
    }}>
      <div style={{ textAlign: 'center' }}>
        <RefreshCw size={32} className="animate-spin" style={{ margin: '0 auto 8px' }} />
        <div style={{ color: themeStyles.color }}>Loading chart...</div>
      </div>
    </div>
  )

  // Error overlay
  const ErrorOverlay = () => (
    <div className="chart-error-overlay" style={{
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: themeStyles.overlay,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px',
      textAlign: 'center'
    }}>
      <div>
        <div style={{ color: '#ff4d4f', fontSize: '16px', marginBottom: '8px' }}>
          Error loading chart
        </div>
        <div style={{ color: themeStyles.color, opacity: 0.8 }}>
          {error}
        </div>
      </div>
    </div>
  )

  // Empty state
  const EmptyState = () => (
    <div className="chart-empty-state" style={{
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px',
      textAlign: 'center'
    }}>
      <div style={{ color: themeStyles.color, opacity: 0.6 }}>
        {emptyMessage}
      </div>
    </div>
  )

  // Toolbar component
  const Toolbar = () => {
    if (!toolbar.enabled) return null

    return (
      <div className="chart-toolbar" style={{
        position: 'absolute',
        top: '8px',
        right: '8px',
        display: 'flex',
        gap: '4px',
        zIndex: 100
      }}>
        {toolbar.showRefresh && (
          <button
            onClick={onRefresh}
            className="toolbar-button"
            style={{
              padding: '6px',
              background: themeStyles.toolbarBg,
              border: `1px solid ${themeStyles.border}`,
              borderRadius: '4px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            title="Refresh"
          >
            <RefreshCw size={16} color={themeStyles.color} />
          </button>
        )}

        {toolbar.showScreenshot && (
          <button
            onClick={() => getScreenshot().then(dataUrl => {
              const link = document.createElement('a')
              link.download = `chart_${Date.now()}.png`
              link.href = dataUrl
              link.click()
            })}
            className="toolbar-button"
            style={{
              padding: '6px',
              background: themeStyles.toolbarBg,
              border: `1px solid ${themeStyles.border}`,
              borderRadius: '4px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            title="Screenshot"
          >
            <Camera size={16} color={themeStyles.color} />
          </button>
        )}

        {toolbar.showDownload && (
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setShowExportMenu(!showExportMenu)}
              className="toolbar-button"
              style={{
                padding: '6px',
                background: themeStyles.toolbarBg,
                border: `1px solid ${themeStyles.border}`,
                borderRadius: '4px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
              title="Export"
            >
              <Download size={16} color={themeStyles.color} />
            </button>
            {showExportMenu && (
              <div className="export-menu" style={{
                position: 'absolute',
                top: '100%',
                right: 0,
                marginTop: '4px',
                background: themeStyles.background,
                border: `1px solid ${themeStyles.border}`,
                borderRadius: '4px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                zIndex: 1000,
                minWidth: '120px'
              }}>
                {exportFormats.map(format => (
                  <button
                    key={format}
                    onClick={() => {
                      exportChart(format as 'png' | 'svg' | 'pdf')
                      setShowExportMenu(false)
                    }}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      textAlign: 'left',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      color: themeStyles.color,
                      fontSize: '14px'
                    }}
                  >
                    Export as {format.toUpperCase()}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {toolbar.showFullscreen && (
          <button
            onClick={toggleFullscreen}
            className="toolbar-button"
            style={{
              padding: '6px',
              background: themeStyles.toolbarBg,
              border: `1px solid ${themeStyles.border}`,
              borderRadius: '4px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
          >
            {isFullscreen ? (
              <Minimize size={16} color={themeStyles.color} />
            ) : (
              <Fullscreen size={16} color={themeStyles.color} />
            )}
          </button>
        )}

        {toolbar.showSettings && (
          <button
            onClick={onSettings}
            className="toolbar-button"
            style={{
              padding: '6px',
              background: themeStyles.toolbarBg,
              border: `1px solid ${themeStyles.border}`,
              borderRadius: '4px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            title="Settings"
          >
            <Settings size={16} color={themeStyles.color} />
          </button>
        )}

        {toolbar.customActions?.map(action => (
          <button
            key={action.key}
            onClick={action.onClick}
            disabled={action.disabled}
            className="toolbar-button"
            style={{
              padding: '6px',
              background: themeStyles.toolbarBg,
              border: `1px solid ${themeStyles.border}`,
              borderRadius: '4px',
              cursor: action.disabled ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              opacity: action.disabled ? 0.5 : 1
            }}
            title={action.tooltip}
          >
            {action.icon}
          </button>
        ))}
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className={`chart-container ${className} ${isFullscreen ? 'fullscreen' : ''}`}
      data-testid={dataTestId}
      style={{
        position: 'relative',
        backgroundColor: themeStyles.background,
        color: themeStyles.color,
        border: `1px solid ${themeStyles.border}`,
        borderRadius: '8px',
        padding: '16px',
        ...style
      }}
    >
      {/* Header */}
      {(title || subtitle) && (
        <div className="chart-header" style={{ marginBottom: '16px' }}>
          {title && (
            <h3 style={{
              margin: 0,
              fontSize: '18px',
              fontWeight: '600',
              fontFamily: 'Inter, sans-serif'
            }}>
              {title}
            </h3>
          )}
          {subtitle && (
            <p style={{
              margin: '4px 0 0',
              fontSize: '14px',
              opacity: 0.8,
              fontFamily: 'Inter, sans-serif'
            }}>
              {subtitle}
            </p>
          )}
        </div>
      )}

      {/* Description */}
      {description && (
        <div className="chart-description" style={{ marginBottom: '16px', fontSize: '14px' }}>
          {description}
        </div>
      )}

      {/* Toolbar */}
      <Toolbar />

      {/* Chart Content */}
      <div className="chart-content" style={{ position: 'relative', minHeight: '200px' }}>
        {loading && <LoadingOverlay />}
        {error && <ErrorOverlay />}
        {empty && !loading && !error && <EmptyState />}
        {children}
      </div>

      {/* Footer */}
      {footer && (
        <div className="chart-footer" style={{
          marginTop: '16px',
          paddingTop: '16px',
          borderTop: `1px solid ${themeStyles.border}`,
          fontSize: '12px',
          opacity: 0.8
        }}>
          {footer}
        </div>
      )}
    </div>
  )
}

export default ChartContainer