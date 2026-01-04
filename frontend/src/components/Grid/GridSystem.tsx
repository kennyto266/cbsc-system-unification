import React, { useCallback, useMemo } from 'react'
import { Responsive, WidthProvider } from 'react-grid-layout'
import { DndProvider } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import 'react-grid-layout/css/styles.css'
import 'react-resizable/css/styles.css'

import { GridSystemProps, ResponsiveLayout, LayoutItem, GRID_BREAKPOINTS, GRID_COLS } from '../../types/grid'
import { useGrid } from './GridProvider'
import { WidgetContainer } from '../Widgets/WidgetContainer'
import { cn } from '@/lib/utils'

// 响应式网格布局组件
const ResponsiveGridLayout = WidthProvider(Responsive)

// 网格系统组件
export const GridSystem: React.FC<GridSystemProps> = ({
  layout,
  onLayoutChange,
  widgets,
  children,
  className,
  width = 1200,
  isDraggable = true,
  isResizable = true,
  compactType = 'vertical',
  preventCollision = false,
  rowHeight = 60,
  margin = [16, 16],
  containerPadding = [16, 16],
  onDragStart,
  onDrag,
  onDragEnd
}) => {
  const { updateLayout } = useGrid()

  // 将widgets转换为布局项
  const layoutItems = useMemo(() => {
    return widgets.map(widget => ({
      i: widget.id,
      x: widget.x,
      y: widget.y,
      w: widget.w,
      h: widget.h,
      minW: widget.minW,
      minH: widget.minH,
      maxW: widget.maxW,
      maxH: widget.maxH,
      static: !widget.isDraggable,
      isDraggable: widget.isDraggable && isDraggable,
      isResizable: widget.isResizable && isResizable
    }))
  }, [widgets, isDraggable, isResizable])

  // 生成响应式布局
  const responsiveLayouts = useMemo<ResponsiveLayout>(() => {
    const breakpoints = Object.keys(GRID_BREAKPOINTS) as Array<keyof typeof GRID_BREAKPOINTS>
    const layouts: ResponsiveLayout = {}

    breakpoints.forEach(bp => {
      const breakpointWidth = GRID_BREAKPOINTS[bp]
      if (width >= breakpointWidth) {
        layouts[bp] = layoutItems
      }
    })

    return layouts
  }, [layoutItems, width])

  // 处理布局变化
  const handleLayoutChange = useCallback((currentLayout: LayoutItem[], allLayouts: ResponsiveLayout[]) => {
    // 更新widgets的位置信息
    const updatedWidgets = widgets.map(widget => {
      const layoutItem = currentLayout.find(item => item.i === widget.id)
      if (layoutItem) {
        return {
          ...widget,
          x: layoutItem.x,
          y: layoutItem.y,
          w: layoutItem.w,
          h: layoutItem.h
        }
      }
      return widget
    })

    // 调用外部回调
    if (onLayoutChange) {
      onLayoutChange(allLayouts, [allLayouts])
    }

    // 更新内部布局状态
    updateLayout(allLayouts)
  }, [widgets, onLayoutChange, updateLayout])

  // 拖拽开始处理
  const handleDragStart = useCallback((...args: any[]) => {
    if (onDragStart) {
      onDragStart(...args)
    }
  }, [onDragStart])

  // 拖拽中处理
  const handleDrag = useCallback((...args: any[]) => {
    if (onDrag) {
      onDrag(...args)
    }
  }, [onDrag])

  // 拖拽结束处理
  const handleDragEnd = useCallback((...args: any[]) => {
    if (onDragEnd) {
      onDragEnd(...args)
    }
  }, [onDragEnd])

  return (
    <DndProvider backend={HTML5Backend}>
      <div className={cn("grid-container", className)}>
        <ResponsiveGridLayout
          className="layout"
          layouts={responsiveLayouts}
          onLayoutChange={handleLayoutChange}
          breakpoints={GRID_BREAKPOINTS}
          cols={GRID_COLS}
          rowHeight={rowHeight}
          margin={margin}
          containerPadding={containerPadding}
          isDraggable={isDraggable}
          isResizable={isResizable}
          compactType={compactType}
          preventCollision={preventCollision}
          onDragStart={handleDragStart}
          onDrag={handleDrag}
          onDragEnd={handleDragEnd}
        >
          {children ||
            widgets.map(widget => (
              <div key={widget.id}>
                <WidgetContainer widget={widget} />
              </div>
            ))}
        </ResponsiveGridLayout>
      </div>
    </DndProvider>
  )
}

export default GridSystem