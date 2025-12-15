import React, { useState } from 'react'
import {
  MoreHorizontal,
  Minimize2,
  Maximize2,
  Edit,
  Trash2,
  Settings,
  X
} from 'lucide-react'
import { WidgetProps } from '../../types/grid'
import { useGrid } from '../Grid/GridProvider'
import { Button } from '../ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../ui/dialog'
import { cn } from '../../lib/utils'

// Widget容器组件
export const WidgetContainer: React.FC<WidgetProps> = ({
  widget,
  onEdit,
  onDelete,
  onResize,
  onMove,
  onMinimize,
  children
}) => {
  const { removeWidget, updateWidget } = useGrid()
  const [isConfigOpen, setIsConfigOpen] = useState(false)
  const [isHovered, setIsHovered] = useState(false)

  // 处理最小化
  const handleMinimize = () => {
    const newMinimizedState = !widget.isMinimized
    updateWidget(widget.id, { isMinimized: newMinimizedState })
    onMinimize?.(widget.id, newMinimizedState)
  }

  // 处理删除
  const handleDelete = () => {
    removeWidget(widget.id)
    onDelete?.(widget.id)
  }

  // 处理编辑
  const handleEdit = () => {
    setIsConfigOpen(true)
    onEdit?.(widget)
  }

  return (
    <div
      className={cn(
        "widget-container relative bg-card border border-border rounded-lg shadow-sm transition-all duration-200",
        "hover:shadow-md",
        widget.isMinimized && "h-auto",
        isHovered && "ring-2 ring-primary ring-offset-2"
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Widget Header */}
      <div className="flex items-center justify-between p-3 border-b border-border">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-primary" />
          <h3 className="text-sm font-semibold text-foreground">
            {widget.title}
          </h3>
        </div>

        {/* Widget Actions */}
        <div className="flex items-center space-x-1">
          {/* 最小化按钮 */}
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={handleMinimize}
          >
            {widget.isMinimized ? (
              <Maximize2 className="h-4 w-4" />
            ) : (
              <Minimize2 className="h-4 w-4" />
            )}
          </Button>

          {/* 更多操作菜单 */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
              >
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuItem onClick={handleEdit}>
                <Edit className="mr-2 h-4 w-4" />
                编辑
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => {}}>
                <Settings className="mr-2 h-4 w-4" />
                设置
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={handleDelete}
                className="text-red-600 focus:text-red-600"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                删除
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Widget Content */}
      <div
        className={cn(
          "p-4 transition-all duration-200",
          widget.isMinimized ? "hidden" : "block"
        )}
      >
        {children}
      </div>

      {/* 配置对话框 */}
      <Dialog open={isConfigOpen} onOpenChange={setIsConfigOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>配置 {widget.title}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">标题</label>
              <input
                type="text"
                value={widget.title}
                onChange={(e) => updateWidget(widget.id, { title: e.target.value })}
                className="w-full px-3 py-2 border border-border rounded-md bg-background"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">宽度 (列)</label>
                <input
                  type="number"
                  value={widget.w}
                  min={widget.minW || 1}
                  max={widget.maxW || 12}
                  onChange={(e) => updateWidget(widget.id, { w: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-border rounded-md bg-background"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">高度 (行)</label>
                <input
                  type="number"
                  value={widget.h}
                  min={widget.minH || 1}
                  max={widget.maxH || 20}
                  onChange={(e) => updateWidget(widget.id, { h: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-border rounded-md bg-background"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={widget.isDraggable}
                  onChange={(e) => updateWidget(widget.id, { isDraggable: e.target.checked })}
                  className="rounded"
                />
                <span className="text-sm font-medium">允许拖拽</span>
              </label>
            </div>

            <div className="space-y-2">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={widget.isResizable}
                  onChange={(e) => updateWidget(widget.id, { isResizable: e.target.checked })}
                  className="rounded"
                />
                <span className="text-sm font-medium">允许调整大小</span>
              </label>
            </div>
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="outline" onClick={() => setIsConfigOpen(false)}>
              取消
            </Button>
            <Button onClick={() => setIsConfigOpen(false)}>
              保存
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default WidgetContainer