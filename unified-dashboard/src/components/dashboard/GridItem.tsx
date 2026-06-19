import React, { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Card } from 'antd'
import {
  MoreOutlined,
  ExpandOutlined,
  CompressOutlined,
  MinusOutlined,
  CopyOutlined,
  DeleteOutlined,
  SettingOutlined
} from '@ant-design/icons'
import { GridItem as GridItemType } from '../../types/dashboard/grid'
import { Button, Dropdown, Space, Tooltip } from 'antd'
import DragHandle from './DragHandle'
import ResizeHandle from './ResizeHandle'

interface GridItemProps {
  item: GridItemType
  isSelected: boolean
  isEditMode: boolean
  isLocked: boolean
  onClick?: () => void
  onDoubleClick?: () => void
  onMinimize?: () => void
  onMaximize?: () => void
  onRemove?: () => void
  onDuplicate?: () => void
  onSettings?: () => void
}

const GridItem: React.FC<GridItemProps> = ({
  item,
  isSelected,
  isEditMode,
  isLocked,
  onClick,
  onDoubleClick,
  onMinimize,
  onMaximize,
  onRemove,
  onDuplicate,
  onSettings,
}) => {
  const [isHovered, setIsHovered] = useState(false)
  const [isMenuVisible, setIsMenuVisible] = useState(false)

  // Handle context menu
  const handleContextMenu = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    if (!isEditMode || isLocked) return
    setIsMenuVisible(true)
  }, [isEditMode, isLocked])

  // Handle menu click
  const handleMenuClick = useCallback(({ key }: { key: string }) => {
    setIsMenuVisible(false)

    switch (key) {
      case 'minimize':
        onMinimize?.()
        break
      case 'maximize':
        onMaximize?.()
        break
      case 'duplicate':
        onDuplicate?.()
        break
      case 'remove':
        onRemove?.()
        break
      case 'settings':
        onSettings?.()
        break
    }
  }, [onMinimize, onMaximize, onDuplicate, onRemove, onSettings])

  // Menu items
  const menuItems = [
    ...(item.isMinimized ? [{ key: 'maximize', label: 'Maximize', icon: <ExpandOutlined /> }] :
      item.isMaximized ? [{ key: 'minimize', label: 'Minimize', icon: <CompressOutlined /> }] :
      [
        { key: 'minimize', label: 'Minimize', icon: <MinusOutlined /> },
        { key: 'maximize', label: 'Maximize', icon: <ExpandOutlined /> },
      ]),
    { type: 'divider' as const },
    { key: 'duplicate', label: 'Duplicate', icon: <CopyOutlined /> },
    { key: 'settings', label: 'Settings', icon: <SettingOutlined /> },
    { type: 'divider' as const },
    { key: 'remove', label: 'Remove', icon: <DeleteOutlined />, danger: true },
  ]

  // Card actions based on mode
  const cardActions = isEditMode && !isLocked ? [
    <Tooltip title="Widget Menu">
      <Dropdown
        menu={{ items: menuItems, onClick: handleMenuClick }}
        trigger={['click']}
        open={isMenuVisible}
        onOpenChange={setIsMenuVisible}
      >
        <Button
          type="text"
          size="small"
          icon={<MoreOutlined />}
          onClick={(e) => e.stopPropagation()}
        />
      </Dropdown>
    </Tooltip>,
  ] : []

  // Widget content component
  const WidgetComponent = React.lazy(() => {
    // Dynamic import based on widget type
    switch (item.type) {
      case 'market-overview':
        return import('../../widgets/MarketOverview')
      case 'strategy-monitor':
        return import('../../widgets/StrategyMonitor')
      case 'portfolio-summary':
        return import('../../widgets/PortfolioSummary')
      case 'risk-metrics':
        return import('../../analytics/RiskMetrics')
      case 'trading-panel':
        return import('../charts/widgets/TradingPanel')
      case 'news-feed':
        return import('../../widgets/StrategyMonitor')
      case 'system-status':
        return import('../../widgets/SystemStatus')
      default:
        return import('../../widgets/MarketOverview') // Fallback
    }
  })

  return (
    <motion.div
      className={`grid-item ${isSelected ? 'selected' : ''} ${item.isMinimized ? 'minimized' : ''} ${item.isMaximized ? 'maximized' : ''}`}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.2 }}
      whileHover={{ scale: isEditMode ? 1.02 : 1 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      onDoubleClick={onDoubleClick}
      onContextMenu={handleContextMenu}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <Card
        className={`h-full w-full transition-all duration-200 ${isEditMode ? 'cursor-move' : 'cursor-default'}`}
        size="small"
        title={item.isMinimized ? item.title : undefined}
        extra={
          !item.isMinimized && (
            <Space size="small">
              {isEditMode && !isLocked && (
                <DragHandle />
              )}
              {cardActions}
            </Space>
          )
        }
        bodyStyle={{
          padding: item.isMinimized ? 0 : '12px',
          height: item.isMinimized ? 0 : '100%',
          overflow: item.isMinimized ? 'hidden' : 'auto',
        }}
        actions={!isEditMode ? [] : cardActions}
        bordered={isSelected}
        hoverable={!isLocked}
      >
        <AnimatePresence mode="wait">
          {!item.isMinimized && (
            <motion.div
              key={item.id}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="h-full"
            >
              <React.Suspense fallback={
                <div className="flex items-center justify-center h-full">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                </div>
              }>
                <WidgetComponent
                  config={item.config}
                  isMinimized={item.isMinimized}
                  isMaximized={item.isMaximized}
                  onConfigChange={(config: any) => {
                    // Handle config change
                    console.log('Config changed for widget', item.id, config)
                  }}
                />
              </React.Suspense>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Resize Handles */}
        {isEditMode && !isLocked && item.isResizable !== false && !item.isMaximized && (
          <ResizeHandle
            position="se"
            onResizeStart={() => console.log('Resize start')}
            onResizeEnd={() => console.log('Resize end')}
          />
        )}
      </Card>

      {/* Selection Indicator */}
      <AnimatePresence>
        {isSelected && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 pointer-events-none"
          >
            <div className="absolute inset-0 border-2 border-blue-500 border-dashed rounded"></div>
            <div className="absolute -top-1 -left-1 w-3 h-3 bg-blue-500 rounded-full"></div>
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full"></div>
            <div className="absolute -bottom-1 -left-1 w-3 h-3 bg-blue-500 rounded-full"></div>
            <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-blue-500 rounded-full"></div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Hover Overlay */}
      <AnimatePresence>
        {isHovered && isEditMode && !isLocked && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black bg-opacity-5 pointer-events-none rounded"
          />
        )}
      </AnimatePresence>

      {/* Custom styles */}
      <style jsx>{`
        .grid-item {
          position: relative;
          height: 100%;
          width: 100%;
          overflow: hidden;
        }

        .grid-item.minimized {
          min-height: auto;
        }

        .grid-item.maximized {
          z-index: 100;
        }

        .grid-item :global(.ant-card) {
          height: 100%;
          display: flex;
          flex-direction: column;
        }

        .grid-item :global(.ant-card-body) {
          flex: 1;
          padding: 0;
        }

        .grid-item.selected :global(.ant-card) {
          box-shadow: 0 0 0 2px #3b82f6;
        }

        .grid-item.edit-mode :global(.ant-card-head) {
          cursor: move;
          user-select: none;
        }

        @media (prefers-reduced-motion: reduce) {
          .grid-item {
            transition: none !important;
          }
        }
      `}</style>
    </motion.div>
  )
}

export default GridItem