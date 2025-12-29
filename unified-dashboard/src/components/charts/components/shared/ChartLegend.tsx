import React, { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { LegendConfig } from '../../types/chart.types'

interface ChartLegendProps {
  items: Array<{
    id: string
    label: string
    color: string
    disabled?: boolean
    hidden?: boolean
  }>
  config?: LegendConfig
  className?: string
  style?: React.CSSProperties
}

const defaultLegendConfig: LegendConfig = {
  show: true,
  position: 'top',
  orientation: 'horizontal'
}

export default function ChartLegend({
  items,
  config = defaultLegendConfig,
  className = '',
  style
}: ChartLegendProps) {
  const [activeItem, setActiveItem] = useState<string | null>(null)

  const handleItemClick = useCallback((itemId: string) => {
    setActiveItem(itemId === activeItem ? null : itemId)
    config.itemClick?.(itemId)
  }, [activeItem, config.itemClick])

  const handleItemHover = useCallback((itemId: string | null) => {
    setActiveItem(itemId)
  }, [])

  if (!config.show) {
    return null
  }

  const isHorizontal = config.orientation === 'horizontal'
  const containerClass = `chart-legend chart-legend--${config.position} chart-legend--${config.orientation} ${className}`

  return (
    <motion.div
      className={containerClass}
      initial={{ opacity: 0, y: config.position === 'top' ? -20 : 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      style={{
        display: 'flex',
        flexDirection: isHorizontal ? 'row' : 'column',
        gap: '16px',
        padding: '8px',
        flexWrap: isHorizontal ? 'wrap' : 'nowrap',
        justifyContent: config.position === 'top' || config.position === 'bottom'
          ? (isHorizontal ? 'flex-start' : 'center')
          : 'center',
        alignItems: 'center',
        ...style
      }}
    >
      <AnimatePresence>
        {items.map((item, index) => (
          <motion.div
            key={item.id}
            className="legend-item"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ delay: index * 0.05 }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
              padding: '4px 8px',
              borderRadius: '4px',
              transition: 'all 0.2s',
              opacity: item.hidden ? 0.3 : 1,
              backgroundColor: activeItem === item.id ? 'rgba(0,0,0,0.05)' : 'transparent'
            }}
            onClick={() => !item.disabled && handleItemClick(item.id)}
            onMouseEnter={() => !item.disabled && handleItemHover(item.id)}
            onMouseLeave={() => handleItemHover(null)}
          >
            {/* Color indicator */}
            <div
              className="legend-color"
              style={{
                width: 12,
                height: 12,
                borderRadius: item.disabled ? 0 : '50%',
                backgroundColor: item.color,
                opacity: item.disabled ? 0.5 : 1,
                position: 'relative',
                transition: 'all 0.2s'
              }}
            >
              {/* Hidden indicator */}
              {item.hidden && (
                <div
                  style={{
                    position: 'absolute',
                    top: '50%',
                    left: 0,
                    right: 0,
                    height: 2,
                    backgroundColor: '#666',
                    transform: 'translateY(-50%)'
                  }}
                />
              )}
            </div>

            {/* Label */}
            <span
              className="legend-label"
              style={{
                fontSize: '12px',
                color: item.disabled ? '#999' : '#333',
                userSelect: 'none',
                textDecoration: item.hidden ? 'line-through' : 'none'
              }}
            >
              {config.formatter ? config.formatter(item.label, item.color) : item.label}
            </span>

            {/* Hover indicator */}
            {activeItem === item.id && !item.disabled && (
              <motion.div
                className="legend-hover-indicator"
                layoutId="legend-indicator"
                style={{
                  position: 'absolute',
                  inset: 0,
                  borderRadius: '4px',
                  border: '1px solid rgba(0,0,0,0.1)',
                  pointerEvents: 'none'
                }}
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              />
            )}
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Legend statistics */}
      {config.position === 'bottom' && items.length > 3 && (
        <div
          className="legend-stats"
          style={{
            fontSize: '10px',
            color: '#666',
            marginLeft: 'auto',
            opacity: 0.7
          }}
        >
          {items.filter(item => !item.hidden).length} / {items.length} 可见
        </div>
      )}
    </motion.div>
  )
}

// Hook for managing legend state
export function useChartLegend(initialItems: ChartLegendProps['items'] = []) {
  const [items, setItems] = useState(initialItems)

  const toggleItem = useCallback((itemId: string) => {
    setItems(prev => prev.map(item =>
      item.id === itemId
        ? { ...item, hidden: !item.hidden }
        : item
    ))
  }, [])

  const showItem = useCallback((itemId: string) => {
    setItems(prev => prev.map(item =>
      item.id === itemId
        ? { ...item, hidden: false }
        : item
    ))
  }, [])

  const hideItem = useCallback((itemId: string) => {
    setItems(prev => prev.map(item =>
      item.id === itemId
        ? { ...item, hidden: true }
        : item
    ))
  }, [])

  const showAll = useCallback(() => {
    setItems(prev => prev.map(item => ({ ...item, hidden: false })))
  }, [])

  const hideAll = useCallback(() => {
    setItems(prev => prev.map(item => ({ ...item, hidden: true })))
  }, [])

  const updateItem = useCallback((itemId: string, updates: Partial<ChartLegendProps['items'][0]>) => {
    setItems(prev => prev.map(item =>
      item.id === itemId
        ? { ...item, ...updates }
        : item
    ))
  }, [])

  const addItems = useCallback((newItems: ChartLegendProps['items']) => {
    setItems(prev => [...prev, ...newItems])
  }, [])

  const removeItems = useCallback((itemIds: string[]) => {
    setItems(prev => prev.filter(item => !itemIds.includes(item.id)))
  }, [])

  const visibleItems = items.filter(item => !item.hidden)
  const hiddenItems = items.filter(item => item.hidden)

  return {
    items,
    visibleItems,
    hiddenItems,
    toggleItem,
    showItem,
    hideItem,
    showAll,
    hideAll,
    updateItem,
    addItems,
    removeItems,
    setItems
  }
}