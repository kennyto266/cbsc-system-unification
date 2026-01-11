import React, { useState, useCallback } from 'react'
import { motion } from 'framer-motion'

type Position = 'se' | 'e' | 's' | 'sw' | 'ne' | 'nw' | 'n' | 'w'

interface ResizeHandleProps {
  position: Position
  className?: string
  onResizeStart?: () => void
  onResizeEnd?: () => void
  onResize?: (deltaX: number, deltaY: number) => void
}

const ResizeHandle: React.FC<ResizeHandleProps> = ({
  position,
  className = '',
  onResizeStart,
  onResizeEnd,
  onResize,
}) => {
  const [isResizing, setIsResizing] = useState(false)
  const [startPos, setStartPos] = useState({ x: 0, y: 0 })

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()

    setIsResizing(true)
    setStartPos({ x: e.clientX, y: e.clientY })
    onResizeStart?.()

    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return

      const deltaX = e.clientX - startPos.x
      const deltaY = e.clientY - startPos.y

      onResize?.(deltaX, deltaY)
    }

    const handleMouseUp = () => {
      setIsResizing(false)
      onResizeEnd?.()

      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }, [isResizing, startPos, onResizeStart, onResizeEnd, onResize])

  const getPositionClasses = (pos: Position): string => {
    switch (pos) {
      case 'se':
        return 'bottom-2 right-2 cursor-se-resize'
      case 'e':
        return 'top-1/2 right-2 -translate-y-1/2 cursor-e-resize'
      case 's':
        return 'bottom-2 left-1/2 -translate-x-1/2 cursor-s-resize'
      case 'sw':
        return 'bottom-2 left-2 cursor-sw-resize'
      case 'ne':
        return 'top-2 right-2 cursor-ne-resize'
      case 'nw':
        return 'top-2 left-2 cursor-nw-resize'
      case 'n':
        return 'top-2 left-1/2 -translate-x-1/2 cursor-n-resize'
      case 'w':
        return 'top-1/2 left-2 -translate-y-1/2 cursor-w-resize'
      default:
        return 'bottom-2 right-2 cursor-se-resize'
    }
  }

  const getHandleIcon = (pos: Position): React.ReactNode => {
    const iconClass = "absolute w-1 h-1 bg-blue-500 rounded-full"

    switch (pos) {
      case 'se':
        return (
          <>
            <span className={`${iconClass} bottom-0 right-0`}></span>
            <span className={`${iconClass} bottom-1 right-1`}></span>
            <span className={`${iconClass} bottom-2 right-2`}></span>
          </>
        )
      case 'e':
      case 'w':
        return (
          <>
            <span className={`${iconClass} top-0`}></span>
            <span className={`${iconClass} top-1`}></span>
            <span className={`${iconClass} top-2`}></span>
          </>
        )
      case 's':
      case 'n':
        return (
          <>
            <span className={`${iconClass} left-0`}></span>
            <span className={`${iconClass} left-1`}></span>
            <span className={`${iconClass} left-2`}></span>
          </>
        )
      default:
        return <span className={iconClass}></span>
    }
  }

  return (
    <motion.div
      className={`
        resize-handle
        absolute z-10
        ${getPositionClasses(position)}
        ${isResizing ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}
        ${className}
        transition-opacity duration-200
        w-4 h-4
        flex items-center justify-center
        bg-blue-500
        hover:bg-blue-600
        rounded-full
        shadow-sm
      `}
      onMouseDown={handleMouseDown}
      whileHover={{ scale: 1.2 }}
      whileTap={{ scale: 0.9 }}
      animate={{
        opacity: isResizing ? 1 : 0,
      }}
    >
      {getHandleIcon(position)}
    </motion.div>
  )
}

export default ResizeHandle