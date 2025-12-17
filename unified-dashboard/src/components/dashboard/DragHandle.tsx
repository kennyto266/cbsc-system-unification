import React from 'react'
import { DragOutlined } from '@ant-design/icons'

interface DragHandleProps {
  className?: string
  size?: 'small' | 'default' | 'large'
}

const DragHandle: React.FC<DragHandleProps> = ({
  className = '',
  size = 'default'
}) => {
  const sizeClasses = {
    small: 'text-xs',
    default: 'text-sm',
    large: 'text-base'
  }

  return (
    <div
      className={`
        drag-handle
        ${sizeClasses[size]}
        ${className}
        inline-flex items-center justify-center
        p-1 cursor-move
        text-gray-400 hover:text-gray-600
        transition-colors duration-200
        select-none
      `}
      title="Drag to move"
    >
      <DragOutlined />
    </div>
  )
}

export default DragHandle