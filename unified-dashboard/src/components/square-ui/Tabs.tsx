import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'

interface TabItem {
  key: string
  label: React.ReactNode
  icon?: React.ReactNode
  disabled?: boolean
  badge?: string | number
  content?: React.ReactNode
  onClick?: () => void
}

interface TabsProps {
  items: TabItem[]
  defaultActiveKey?: string
  activeKey?: string
  onChange?: (key: string) => void
  type?: 'line' | 'card' | 'pills' | 'segment'
  size?: 'small' | 'default' | 'large'
  centered?: boolean
  className?: string
  contentClassName?: string
  animated?: boolean
  tabBarExtraContent?: React.ReactNode
  destroyInactiveTabPane?: boolean
}

export const Tabs: React.FC<TabsProps> = ({
  items,
  defaultActiveKey,
  activeKey: controlledActiveKey,
  onChange,
  type = 'line',
  size = 'default',
  centered = false,
  className,
  contentClassName,
  animated = true,
  tabBarExtraContent,
  destroyInactiveTabPane = false,
}) => {
  const [internalActiveKey, setInternalActiveKey] = useState(
    defaultActiveKey || (items.length > 0 ? items[0].key : '')
  )
  const [indicatorStyle, setIndicatorStyle] = useState<React.CSSProperties>({})
  const tabsRef = useRef<HTMLDivElement>(null)
  const activeTabRef = useRef<HTMLButtonElement>(null)

  // Use controlled or internal state
  const activeKey = controlledActiveKey !== undefined ? controlledActiveKey : internalActiveKey

  // Update indicator position when active tab changes
  useEffect(() => {
    if (activeTabRef.current && tabsRef.current && type === 'line') {
      const tabElement = activeTabRef.current
      const tabsElement = tabsRef.current
      const tabRect = tabElement.getBoundingClientRect()
      const tabsRect = tabsElement.getBoundingClientRect()

      setIndicatorStyle({
        left: tabRect.left - tabsRect.left,
        width: tabRect.width,
      })
    }
  }, [activeKey, type])

  const handleTabClick = (key: string, item: TabItem) => {
    if (item.disabled) return

    // Call custom onClick if provided
    item.onClick?.()

    // Update state
    if (controlledActiveKey === undefined) {
      setInternalActiveKey(key)
    }

    // Call onChange callback
    onChange?.(key)
  }

  // Get active tab item
  const activeItem = items.find(item => item.key === activeKey)

  // Tab list styles based on type
  const tabListStyles = cn(
    'relative flex',
    {
      // Line type
      'border-b border-gray-200': type === 'line',
      'space-x-8': type === 'line' && !centered,
      'justify-center space-x-8': type === 'line' && centered,

      // Card type
      'border-b border-gray-200 space-x-2': type === 'card',
      'bg-gray-50 p-1 rounded-lg': type === 'segment',

      // Pills type
      'space-x-2': type === 'pills',
      'justify-center space-x-2': type === 'pills' && centered,

      // Size adjustments
      'text-sm': size === 'small',
      'text-base': size === 'default',
      'text-lg': size === 'large',
    }
  )

  // Tab button styles based on type and state
  const getTabButtonStyles = (item: TabItem) => cn(
    'relative px-1 py-4 font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
    {
      // Line type
      'border-b-2 border-transparent -mb-px': type === 'line',
      'border-primary-500 text-primary-600': type === 'line' && activeKey === item.key,
      'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300': type === 'line' && activeKey !== item.key,

      // Card type
      'border-b-2 border-transparent -mb-px rounded-t-lg': type === 'card',
      'bg-white border-primary-500 text-primary-600': type === 'card' && activeKey === item.key,
      'text-gray-500 hover:text-gray-700 hover:border-gray-300': type === 'card' && activeKey !== item.key,

      // Segment type
      'flex-1 justify-center py-2 px-4 rounded-md': type === 'segment',
      'bg-white shadow-sm text-primary-600': type === 'segment' && activeKey === item.key,
      'text-gray-500 hover:text-gray-700': type === 'segment' && activeKey !== item.key,

      // Pills type
      'py-2 px-4 rounded-full': type === 'pills',
      'bg-primary-500 text-white': type === 'pills' && activeKey === item.key,
      'bg-gray-100 text-gray-600 hover:bg-gray-200': type === 'pills' && activeKey !== item.key,

      // Disabled state
      'opacity-50 cursor-not-allowed': item.disabled,

      // Size adjustments
      'py-3': type === 'line' && size === 'large',
      'py-2': type === 'line' && size === 'small',
    }
  )

  // Content animation variants
  const contentVariants = {
    initial: { opacity: 0, y: 10 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -10 },
  }

  return (
    <div className={cn('w-full', className)}>
      {/* Tab List */}
      <div className="relative">
        <div
          ref={tabsRef}
          className={tabListStyles}
          role="tablist"
        >
          {items.map((item) => (
            <button
              key={item.key}
              ref={activeKey === item.key ? activeTabRef : undefined}
              className={getTabButtonStyles(item)}
              onClick={() => handleTabClick(item.key, item)}
              disabled={item.disabled}
              role="tab"
              aria-selected={activeKey === item.key}
              aria-controls={`tabpanel-${item.key}`}
            >
              <div className="flex items-center gap-2">
                {item.icon && (
                  <span className={cn(
                    'flex-shrink-0',
                    activeKey === item.key ? 'text-current' : 'text-current opacity-70'
                  )}>
                    {item.icon}
                  </span>
                )}
                <span>{item.label}</span>
                {item.badge && (
                  <span className={cn(
                    'inline-flex items-center justify-center px-2 py-0.5 text-xs font-bold rounded-full',
                    activeKey === item.key
                      ? 'bg-primary-100 text-primary-600'
                      : 'bg-gray-100 text-gray-600'
                  )}>
                    {item.badge}
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>

        {/* Tab bar extra content */}
        {tabBarExtraContent && (
          <div className="absolute right-0 top-0 flex items-center h-full">
            {tabBarExtraContent}
          </div>
        )}

        {/* Indicator for line type */}
        {type === 'line' && (
          <motion.div
            className="absolute bottom-0 h-0.5 bg-primary-500"
            style={indicatorStyle}
            layout
            transition={{ type: "spring", stiffness: 500, damping: 30 }}
          />
        )}
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        {activeItem && (
          <motion.div
            key={activeKey}
            variants={animated ? contentVariants : undefined}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.2 }}
            className={cn('mt-6', contentClassName)}
            role="tabpanel"
            id={`tabpanel-${activeKey}`}
            aria-labelledby={`tab-${activeKey}`}
          >
            {activeItem.content || (
              <div className="text-center py-8 text-gray-500">
                No content for {activeItem.label}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default Tabs