import React, { useState } from 'react'
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline'

interface CollapsibleProps {
  children: React.ReactNode
  open?: boolean
  onOpenChange?: (open: boolean) => void
  className?: string
}

interface CollapsibleContentProps {
  children: React.ReactNode
  className?: string
}

interface CollapsibleTriggerProps {
  children: React.ReactNode
  className?: string
}

export const Collapsible: React.FC<CollapsibleProps> = ({
  children,
  open: controlledOpen,
  onOpenChange,
  className = ''
}) => {
  const [internalOpen, setInternalOpen] = useState(false)
  const isOpen = controlledOpen !== undefined ? controlledOpen : internalOpen

  const handleToggle = () => {
    const newOpen = !isOpen
    if (onOpenChange) {
      onOpenChange(newOpen)
    } else {
      setInternalOpen(newOpen)
    }
  }

  return (
    <div className={className}>
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child, {
            isOpen,
            onToggle: handleToggle
          } as any)
        }
        return child
      })}
    </div>
  )
}

export const CollapsibleContent: React.FC<CollapsibleContentProps> = ({ children, className = '' }) => {
  return (
    <div className={className}>
      {children}
    </div>
  )
}

export const CollapsibleTrigger: React.FC<CollapsibleTriggerProps & { isOpen?: boolean; onToggle?: () => void }> = ({
  children,
  isOpen,
  onToggle,
  className = ''
}) => {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={`flex items-center justify-between w-full px-4 py-2 text-sm font-medium text-left text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 ${className}`}
    >
      {children}
      {isOpen ? (
        <ChevronDownIcon className="h-5 w-5 text-gray-500" />
      ) : (
        <ChevronRightIcon className="h-5 w-5 text-gray-500" />
      )}
    </button>
  )
}