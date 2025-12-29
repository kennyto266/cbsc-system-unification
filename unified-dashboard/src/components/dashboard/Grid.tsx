import React, { useCallback, useRef, useEffect } from 'react'
import { Responsive, WidthProvider, Layout } from 'react-grid-layout'
import { motion, AnimatePresence } from 'framer-motion'
import { useGridLayout } from '../../hooks/dashboard/useGridLayout'
import { GridItem } from '../../types/dashboard/grid'
import GridItemComponent from './GridItem'
import GridSettings from './GridSettings'
import { useResizeObserver } from '../../hooks/useResizeObserver'
import { getResponsiveGridConfig } from '../../utils/dashboard/responsiveUtils'

const ResponsiveGridLayout = WidthProvider(Responsive)

interface GridProps {
  widgets?: React.ComponentType<any>[]
  className?: string
  style?: React.CSSProperties
  onWidgetClick?: (widgetId: string) => void
  onWidgetDoubleClick?: (widgetId: string) => void
}

const Grid: React.FC<GridProps> = ({
  widgets = [],
  className = '',
  style,
  onWidgetClick,
  onWidgetDoubleClick,
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const {
    layout,
    isEditMode,
    isLoading,
    error,
    selectedWidgets,
    moveWidgetById,
    resizeWidgetById,
    selectWidget,
    toggleEditMode,
    config,
  } = useGridLayout()

  // Get container dimensions
  const { width = 1200, height = 800 } = useResizeObserver(containerRef) || {}

  // Get responsive configuration
  const gridConfig = getResponsiveGridConfig(width)

  // Convert layout items to react-grid-layout format
  const getLayoutFromItems = useCallback((items: GridItem[]): Layout[] => {
    return items
      .filter(item => item.isVisible !== false)
      .map(item => ({
        i: item.id,
        x: item.position.x,
        y: item.position.y,
        w: item.size.w,
        h: item.size.h,
        minW: item.size.minW || 1,
        minH: item.size.minH || 1,
        maxW: item.size.maxW,
        maxH: item.size.maxH,
        isDraggable: isEditMode && item.isDraggable !== false && !layout.isLocked,
        isResizable: isEditMode && item.isResizable !== false && !layout.isLocked,
        static: !isEditMode || layout.isLocked || item.isDraggable === false,
      }))
  }, [isEditMode, layout.isLocked])

  // Handle layout changes
  const handleLayoutChange = useCallback((newLayout: Layout[]) => {
    newLayout.forEach(item => {
      const existingItem = layout.items.find(i => i.id === item.i)
      if (!existingItem) return

      const positionChanged = existingItem.position.x !== item.x || existingItem.position.y !== item.y
      const sizeChanged = existingItem.size.w !== item.w || existingItem.size.h !== item.h

      if (positionChanged) {
        moveWidgetById(item.i, { x: item.x, y: item.y })
      }
      if (sizeChanged) {
        resizeWidgetById(item.i, { w: item.w, h: item.h })
      }
    })
  }, [layout.items, moveWidgetById, resizeWidgetById])

  // Handle widget click
  const handleWidgetClick = useCallback((widgetId: string) => {
    selectWidget(widgetId)
    onWidgetClick?.(widgetId)
  }, [selectWidget, onWidgetClick])

  // Handle widget double click
  const handleWidgetDoubleClick = useCallback((widgetId: string) => {
    onWidgetDoubleClick?.(widgetId)
  }, [onWidgetDoubleClick])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ctrl/Cmd + E: Toggle edit mode
      if ((event.ctrlKey || event.metaKey) && event.key === 'e') {
        event.preventDefault()
        toggleEditMode()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [toggleEditMode])

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-red-500">
          <p className="text-lg font-semibold">Grid Error</p>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className={`relative h-full w-full ${className}`}
      style={style}
    >
      {/* Edit Mode Indicator */}
      {isEditMode && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          className="absolute top-4 left-4 z-50 bg-yellow-500 text-white px-3 py-1 rounded-md text-sm font-medium shadow-lg"
        >
          Edit Mode
        </motion.div>
      )}

      {/* Grid Settings */}
      <AnimatePresence>
        {isEditMode && (
          <motion.div
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 300 }}
            className="absolute top-4 right-4 z-40"
          >
            <GridSettings />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Grid Layout */}
      <ResponsiveGridLayout
        className={`layout ${isEditMode ? 'edit-mode' : ''} ${isLoading ? 'loading' : ''}`}
        layouts={{
          [gridConfig.breakpoint]: getLayoutFromItems(layout.items),
        }}
        breakpoints={{
          [gridConfig.breakpoint]: gridConfig.breakpoint === 'xs' ? 0 :
            gridConfig.breakpoint === 'sm' ? 640 :
            gridConfig.breakpoint === 'md' ? 768 :
            gridConfig.breakpoint === 'lg' ? 1024 :
            gridConfig.breakpoint === 'xl' ? 1280 :
            gridConfig.breakpoint === '2xl' ? 1536 : 2560,
        }}
        cols={{
          [gridConfig.breakpoint]: gridConfig.cols,
        }}
        rowHeight={gridConfig.rowHeight}
        margin={gridConfig.margin}
        containerPadding={gridConfig.containerPadding}
        onLayoutChange={handleLayoutChange}
        isDraggable={isEditMode && !layout.isLocked}
        isResizable={isEditMode && !layout.isLocked}
        useCSSTransforms={config.useCSSTransforms}
        preventCollision={config.preventCollision}
        compactType={config.compactType}
        animateTransitions={config.animateTransitions}
        animationDuration={200}
        resizeHandles={['se', 'e', 's']}
      >
        {layout.items
          .filter(item => item.isVisible !== false)
          .map(item => (
            <div key={item.id} className="grid-item-wrapper">
              <GridItemComponent
                item={item}
                isSelected={selectedWidgets.includes(item.id)}
                isEditMode={isEditMode}
                isLocked={layout.isLocked}
                onClick={() => handleWidgetClick(item.id)}
                onDoubleClick={() => handleWidgetDoubleClick(item.id)}
              />
            </div>
          ))}
      </ResponsiveGridLayout>

      {/* Loading Overlay */}
      <AnimatePresence>
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50"
          >
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              <p className="mt-2 text-sm text-gray-600">Loading grid...</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Custom styles for grid */}
      <style jsx>{`
        .grid-item-wrapper {
          height: 100%;
          width: 100%;
        }

        .layout.edit-mode :global(.react-grid-item) {
          transition: none;
        }

        .layout.edit-mode :global(.react-grid-item:hover) {
          outline: 2px solid #3b82f6;
          outline-offset: 2px;
        }

        .layout.edit-mode :global(.react-grid-item.selected) {
          outline: 2px solid #ef4444;
          outline-offset: 2px;
        }

        .layout.edit-mode :global(.react-grid-item.css-transforms) {
          transition: all 200ms ease;
        }

        .layout.edit-mode :global(.react-resizable-handle) {
          position: absolute;
          width: 20px;
          height: 20px;
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%233b82f6'%3E%3Cpath d='M22 22H20V20H22V22M22 18H20V16H22V18M18 22H16V20H18V22M18 18H16V16H18V18M14 22H12V20H14V22Z'/%3E%3C/svg%3E");
          background-position: bottom right;
          background-repeat: no-repeat;
          background-size: 12px;
          z-index: 10;
        }

        .layout.edit-mode :global(.react-grid-placeholder) {
          background: #3b82f6;
          opacity: 0.3;
          border-radius: 0.375rem;
          border: 2px dashed #1e40af;
        }

        @media (prefers-reduced-motion: reduce) {
          .layout :global(.react-grid-item) {
            transition: none !important;
          }
        }
      `}</style>
    </div>
  )
}

export default Grid