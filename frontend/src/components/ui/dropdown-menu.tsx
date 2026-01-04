import React, { useState } from 'react'
import { ChevronDownIcon } from '@heroicons/react/24/outline'

interface DropdownMenuProps {
  trigger: React.ReactNode
  children: React.ReactNode
  className?: string
}

interface DropdownMenuContentProps {
  children: React.ReactNode
  className?: string
}

interface DropdownMenuItemProps {
  children: React.ReactNode
  onClick?: () => void
  className?: string
}

export const DropdownMenu: React.FC<DropdownMenuProps> = ({ trigger, children, className = '' }) => {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className={`relative inline-block text-left ${className}`}>
      <div onClick={() => setIsOpen(!isOpen)}>
        {trigger}
      </div>
      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-50">
          <div className="py-1">
            {children}
          </div>
        </div>
      )}
    </div>
  )
}

export const DropdownMenuContent: React.FC<DropdownMenuContentProps> = ({ children, className = '' }) => {
  return <div className={className}>{children}</div>
}

export const DropdownMenuItem: React.FC<DropdownMenuItemProps> = ({ children, onClick, className = '' }) => {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900 ${className}`}
    >
      {children}
    </button>
  )
}

export const DropdownMenuSeparator: React.FC<{ className?: string }> = ({ className = '' }) => {
  return <div className={`border-t border-gray-100 my-1 ${className}`} />
}

export const DropdownMenuLabel: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = ''
}) => {
  return (
    <div className={`px-4 py-2 text-sm font-medium text-gray-700 ${className}`}>
      {children}
    </div>
  )
}

export const DropdownMenuTrigger: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = ''
}) => {
  return (
    <button
      type="button"
      className={`inline-flex justify-center w-full rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${className}`}
    >
      {children}
      <ChevronDownIcon className="-mr-1 ml-2 h-5 w-5" aria-hidden="true" />
    </button>
  )
}