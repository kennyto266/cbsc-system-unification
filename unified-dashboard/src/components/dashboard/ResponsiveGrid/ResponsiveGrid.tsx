import React, { useCallback, useRef, useEffect, useState } from 'react'
import { Responsive, WidthProvider, Layout } from 'react-grid-layout'
import { useResponsiveGrid, GridWidget } from './ResponsiveGridProvider'
import WidgetRenderer from './WidgetRenderer'
import GridToolbar from './GridToolbar'
// import { useResizeDetector } from 'react-resize-detector'
import { useResizeDetector } from '../../../hooks/useResizeDetector'

// Import CSS
import 'react-grid-layout/css/styles.css'
import 'react-resizable/css/styles.css'

const ResponsiveGridLayout = WidthProvider(Responsive)

interface ResponsiveGridProps {
  className?: string
  editable?: boolean
  showToolbar?: boolean
  onLayoutChange?: (layout: Layout[]) => void
  onWidgetClick?: (widget: GridWidget) => void
  onWidgetDoubleClick?: (widget: GridWidget) => void
  children?: React.ReactNode
}

// Breakpoint configuration
const BREAKPOINTS = {
  lg: 1200,
  md: 992,
  sm: 768,
  xs: 576,
  xxs: 0
}

// Grid configuration for different breakpoints
const COLS = {
  lg: 12,
  md: 10,
  sm: 6,
  xs: 4,
  xxs: 2
}

const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({
  className = '',
  editable = true,
  showToolbar = true,
  onLayoutChange,
  onWidgetClick,
  onWidgetDoubleClick,
  children
}) => {
  const {
    layouts,
    currentBreakpoint,
    gridConfig,
    widgets,
    updateLayout,
    moveWidget,
    resizeWidget,
    setBreakpoint,
    getBreakpointFromWidth
  } = useResponsiveGrid()

  const [selectedWidgets, setSelectedWidgets] = useState<Set<string>>(new Set())
  const [isDragging, setIsDragging] = useState(false)
  const gridRef = useRef<HTMLDivElement>(null)

  // Detect container size changes
  const { width, ref: sizeRef } = useResizeDetector({
    handleHeight: false,
    refreshMode: 'debounce',
    refreshRate: 100
  })

  // Update breakpoint when container size changes
  useEffect(() => {
    if (width) {
      const newBreakpoint = getBreakpointFromWidth(width)
      if (newBreakpoint !== currentBreakpoint) {
        setBreakpoint(newBreakpoint)
      }
    }
  }, [width, currentBreakpoint, setBreakpoint, getBreakpointFromWidth])

  // Handle layout changes
  const handleLayoutChange = useCallback((layout: Layout[], layouts: any) => {
    // Update layouts state
    updateLayout(layout, currentBreakpoint)

    // Notify parent component
    if (onLayoutChange) {
      onLayoutChange(layout)
    }

    // Update widget positions in state
    layout.forEach(item => {
      const widget = widgets.find(w => w.id === item.i)
      if (widget) {
        // Check if position or size changed
        if (widget.x !== item.x || widget.y !== item.y || widget.w !== item.w || widget.h !== item.h) {
          if (widget.w !== item.w || widget.h !== item.h) {
            resizeWidget(item.i, item)
          } else {
            moveWidget(item.i, item)
          }
        }
      }
    })
  }, [currentBreakpoint, widgets, updateLayout, onLayoutChange, moveWidget, resizeWidget])

  // Handle widget selection
  const handleWidgetClick = useCallback((widget: GridWidget, e: React.MouseEvent) => {
    e.stopPropagation()

    if (editable) {
      const newSelection = new Set(selectedWidgets)
      if (e.ctrlKey || e.metaKey) {
        // Toggle selection with Ctrl/Cmd key
        if (newSelection.has(widget.id)) {
          newSelection.delete(widget.id)
        } else {
          newSelection.add(widget.id)
        }
      } else {
        // Single selection
        newSelection.clear()
        newSelection.add(widget.id)
      }
      setSelectedWidgets(newSelection)
    }

    if (onWidgetClick) {
      onWidgetClick(widget)
    }
  }, [editable, selectedWidgets, onWidgetClick])

  // Handle widget double click
  const handleWidgetDoubleClick = useCallback((widget: GridWidget, e: React.MouseEvent) => {
    e.stopPropagation()

    if (onWidgetDoubleClick) {
      onWidgetDoubleClick(widget)
    }
  }, [onWidgetDoubleClick])

  // Handle drag start
  const handleDragStart = useCallback(() => {
    setIsDragging(true)
  }, [])

  // Handle drag end
  const handleDragEnd = useCallback(() => {
    setIsDragging(false)
  }, [])

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!editable) return

      // Delete selected widgets
      if (e.key === 'Delete' || e.key === 'Backspace') {
        selectedWidgets.forEach(widgetId => {
          const { removeWidget } = useResponsiveGrid.getState()
          removeWidget(widgetId)
        })
        setSelectedWidgets(new Set())
      }

      // Select all widgets (Ctrl/Cmd + A)
      if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
        e.preventDefault()
        setSelectedWidgets(new Set(widgets.map(w => w.id)))
      }

      // Clear selection (Escape)
      if (e.key === 'Escape') {
        setSelectedWidgets(new Set())
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [editable, selectedWidgets, widgets])

  // Generate current layout from widgets
  const currentLayout = widgets.map(widget => ({
    i: widget.id,
    x: widget.x || 0,
    y: widget.y || 0,
    w: widget.w || gridConfig.cols,
    h: widget.h || 3,
    minW: widget.minW || 1,
    minH: widget.minH || 1,
    maxW: widget.maxW || gridConfig.cols,
    maxH: widget.maxH || 12,
    isDraggable: widget.draggable !== false && editable,
    isResizable: widget.resizable !== false && editable
  }))

  return (
    <div
      ref={(node) => {
        gridRef.current = node || null
        if (sizeRef) {
          if (typeof sizeRef === 'function') {
            sizeRef(node)
          }
        }
      }}
      className={`responsive-grid-container ${className} ${isDragging ? 'dragging' : ''}`}
      style={{
        position: 'relative',
        width: '100%',
        height: '100%'
      }}
    >
      {/* Toolbar */}
      {showToolbar && (
        <GridToolbar
          selectedWidgets={selectedWidgets}
          onSelectionChange={setSelectedWidgets}
          editable={editable}
        />
      )}

      {/* Grid Layout */}
      <ResponsiveGridLayout
        className="responsive-grid"
        layouts={layouts}
        breakpoints={BREAKPOINTS}
        cols={COLS}
        rowHeight={gridConfig.rowHeight}
        margin={gridConfig.margin}
        containerPadding={gridConfig.containerPadding}
        onLayoutChange={handleLayoutChange}
        onDragStart={handleDragStart}
        onDragStop={handleDragEnd}
        onResizeStart={handleDragStart}
        onResizeStop={handleDragEnd}
        isDraggable={editable}
        isResizable={editable}
        preventCollision={false}
        autoSize={true}
        compactType="vertical"
        useCSSTransforms={true}
      >
        {currentLayout.map((item) => {
          const widget = widgets.find(w => w.id === item.i)
          if (!widget) return null

          return (
            <div
              key={item.i}
              className={`grid-widget ${selectedWidgets.has(item.i) ? 'selected' : ''}`}
              onClick={(e) => handleWidgetClick(widget, e)}
              onDoubleClick={(e) => handleWidgetDoubleClick(widget, e)}
              data-widget-id={widget.id}
              data-widget-type={widget.type}
              style={{
                position: 'relative',
                overflow: 'hidden',
                cursor: editable ? 'move' : 'default'
              }}
            >
              {/* Widget content */}
              <WidgetRenderer
                widget={widget}
                selected={selectedWidgets.has(item.i)}
                editable={editable}
              />

              {/* Selection overlay */}
              {selectedWidgets.has(item.i) && editable && (
                <div className="widget-selection-overlay" />
              )}
            </div>
          )
        })}
      </ResponsiveGridLayout>

      {/* Custom children (for additional overlays, etc.) */}
      {children}

      {/* Styles */}
      <style jsx>{`
        .responsive-grid-container {
          background: transparent;
        }

        .responsive-grid-container.dragging {
          cursor: grabbing;
        }

        .responsive-grid :global(.react-grid-item) {
          transition: all 200ms ease;
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid rgba(255, 255, 255, 0.05);
          border-radius: 8px;
          overflow: hidden;
        }

        .responsive-grid :global(.react-grid-item.css-transforms) {
          transition: none;
        }

        .responsive-grid :global(.react-grid-item.selected) {
          border-color: #1890ff;
          box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
        }

        .responsive-grid :global(.react-grid-item:hover) {
          border-color: rgba(255, 255, 255, 0.1);
          background: rgba(255, 255, 255, 0.04);
        }

        .responsive-grid :global(.react-grid-item.selected:hover) {
          border-color: #1890ff;
        }

        .grid-widget {
          width: 100%;
          height: 100%;
          display: flex;
          flex-direction: column;
        }

        .widget-selection-overlay {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          pointer-events: none;
          border: 2px solid #1890ff;
          border-radius: 8px;
          animation: selection-pulse 2s infinite;
        }

        @keyframes selection-pulse {
          0% {
            border-color: rgba(24, 144, 255, 0.8);
          }
          50% {
            border-color: rgba(24, 144, 255, 0.4);
          }
          100% {
            border-color: rgba(24, 144, 255, 0.8);
          }
        }

        /* Responsive adjustments */
        @media (max-width: 768px) {
          .responsive-grid :global(.react-grid-item) {
            border-radius: 4px;
          }
        }
      `}</style>
    </div>
  )
}

export default ResponsiveGrid