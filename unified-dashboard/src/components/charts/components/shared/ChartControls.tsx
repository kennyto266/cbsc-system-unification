import React, { useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import BaseChartProps from '../../types/chart.types'

interface ChartControlsProps {
  onZoomIn?: () => void
  onZoomOut?: () => void
  onReset?: () => void
  onExport?: (format: 'png' | 'svg' | 'csv') => void
  onToggleFullscreen?: () => void
  onToggleGrid?: () => void
  onToggleLegend?: () => void
  onToggleCrosshair?: () => void
  showZoom?: boolean
  showExport?: boolean
  showFullscreen?: boolean
  showGridToggle?: boolean
  showLegendToggle?: boolean
  showCrosshairToggle?: boolean
  isFullscreen?: boolean
  showGrid?: boolean
  showLegend?: boolean
  showCrosshair?: boolean
  className?: string
  style?: React.CSSProperties
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left'
}

const ChartControls: React.FC<ChartControlsProps> = ({
  onZoomIn,
  onZoomOut,
  onReset,
  onExport,
  onToggleFullscreen,
  onToggleGrid,
  onToggleLegend,
  onToggleCrosshair,
  showZoom = true,
  showExport = true,
  showFullscreen = true,
  showGridToggle = true,
  showLegendToggle = true,
  showCrosshairToggle = true,
  isFullscreen = false,
  showGrid = true,
  showLegend = true,
  showCrosshair = false,
  className = '',
  style,
  position = 'top-right'
}) => {
  const [exportMenuOpen, setExportMenuOpen] = useState(false)

  const handleExport = useCallback((format: 'png' | 'svg' | 'csv') => {
    onExport?.(format)
    setExportMenuOpen(false)
  }, [onExport])

  const positionStyles = {
    'top-right': {
      position: 'absolute' as const,
      top: 8,
      right: 8
    },
    'top-left': {
      position: 'absolute' as const,
      top: 8,
      left: 8
    },
    'bottom-right': {
      position: 'absolute' as const,
      bottom: 8,
      right: 8
    },
    'bottom-left': {
      position: 'absolute' as const,
      bottom: 8,
      left: 8
    }
  }

  return (
    <motion.div
      className={`chart-controls ${className}`}
      style={{
        display: 'flex',
        gap: '4px',
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        backdropFilter: 'blur(4px)',
        padding: '4px',
        borderRadius: '6px',
        border: '1px solid rgba(0, 0, 0, 0.1)',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
        zIndex: 10,
        ...positionStyles[position],
        ...style
      }}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.2 }}
    >
      {/* Zoom controls */}
      {showZoom && (
        <>
          <ControlButton
            icon="+"
            tooltip="放大"
            onClick={onZoomIn}
            disabled={!onZoomIn}
          />
          <ControlButton
            icon="-"
            tooltip="缩小"
            onClick={onZoomOut}
            disabled={!onZoomOut}
          />
        </>
      )}

      {/* Reset button */}
      <ControlButton
        icon="⟲"
        tooltip="重置视图"
        onClick={onReset}
        disabled={!onReset}
      />

      {/* Separator */}
      <div
        style={{
          width: '1px',
          backgroundColor: 'rgba(0, 0, 0, 0.1)',
          margin: '0 4px'
        }}
      />

      {/* Toggle controls */}
      {showGridToggle && (
        <ControlButton
          icon="⊞"
          tooltip={showGrid ? "隐藏网格" : "显示网格"}
          onClick={onToggleGrid}
          disabled={!onToggleGrid}
          active={showGrid}
        />
      )}

      {showLegendToggle && (
        <ControlButton
          icon="☰"
          tooltip={showLegend ? "隐藏图例" : "显示图例"}
          onClick={onToggleLegend}
          disabled={!onToggleLegend}
          active={showLegend}
        />
      )}

      {showCrosshairToggle && (
        <ControlButton
          icon="✛"
          tooltip={showCrosshair ? "隐藏十字线" : "显示十字线"}
          onClick={onToggleCrosshair}
          disabled={!onToggleCrosshair}
          active={showCrosshair}
        />
      )}

      {/* Separator */}
      <div
        style={{
          width: '1px',
          backgroundColor: 'rgba(0, 0, 0, 0.1)',
          margin: '0 4px'
        }}
      />

      {/* Export menu */}
      {showExport && onExport && (
        <div style={{ position: 'relative' }}>
          <ControlButton
            icon="↓"
            tooltip="导出"
            onClick={() => setExportMenuOpen(!exportMenuOpen)}
            active={exportMenuOpen}
          />

          <AnimatePresence>
            {exportMenuOpen && (
              <motion.div
                className="export-menu"
                initial={{ opacity: 0, scale: 0.95, y: -10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: -10 }}
                style={{
                  position: 'absolute',
                  top: '100%',
                  right: 0,
                  marginTop: '4px',
                  backgroundColor: 'white',
                  borderRadius: '4px',
                  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
                  border: '1px solid rgba(0, 0, 0, 0.1)',
                  overflow: 'hidden',
                  zIndex: 20
                }}
              >
                <ExportMenuItem onClick={() => handleExport('png')}>
                  导出为 PNG
                </ExportMenuItem>
                <ExportMenuItem onClick={() => handleExport('svg')}>
                  导出为 SVG
                </ExportMenuItem>
                <ExportMenuItem onClick={() => handleExport('csv')}>
                  导出数据 (CSV)
                </ExportMenuItem>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Fullscreen toggle */}
      {showFullscreen && onToggleFullscreen && (
        <ControlButton
          icon={isFullscreen ? "⊡" : "⛶"}
          tooltip={isFullscreen ? "退出全屏" : "全屏"}
          onClick={onToggleFullscreen}
        />
      )}
    </motion.div>
  )
}

// Control button component
interface ControlButtonProps {
  icon: string
  tooltip: string
  onClick?: () => void
  disabled?: boolean
  active?: boolean
}

const ControlButton: React.FC<ControlButtonProps> = ({
  icon,
  tooltip,
  onClick,
  disabled = false,
  active = false
}) => {
  return (
    <motion.button
      className="control-button"
      whileHover={{ scale: disabled ? 1 : 1.05 }}
      whileTap={{ scale: disabled ? 1 : 0.95 }}
      onClick={onClick}
      disabled={disabled}
      title={tooltip}
      style={{
        width: '28px',
        height: '28px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: active ? 'rgba(0, 0, 0, 0.1)' : 'transparent',
        border: 'none',
        borderRadius: '4px',
        cursor: disabled ? 'not-allowed' : 'pointer',
        fontSize: '14px',
        color: disabled ? '#ccc' : '#333',
        transition: 'all 0.2s',
        opacity: disabled ? 0.5 : 1
      }}
    >
      {icon}
    </motion.button>
  )
}

// Export menu item component
interface ExportMenuItemProps {
  onClick: () => void
  children: React.ReactNode
}

const ExportMenuItem: React.FC<ExportMenuItemProps> = ({ onClick, children }) => {
  return (
    <motion.button
      className="export-menu-item"
      whileHover={{ backgroundColor: 'rgba(0, 0, 0, 0.05)' }}
      onClick={onClick}
      style={{
        padding: '8px 16px',
        backgroundColor: 'transparent',
        border: 'none',
        textAlign: 'left',
        fontSize: '12px',
        color: '#333',
        cursor: 'pointer',
        width: '100%',
        whiteSpace: 'nowrap'
      }}
    >
      {children}
    </motion.button>
  )
}

export default ChartControls