import React from 'react'
import { Button, Tooltip, Space } from 'antd'
import { motion } from 'framer-motion'
import { useAppSelector } from '../../hooks/redux'
import type { QuickAction } from '../../types/layout'

interface QuickActionsProps {
  actions: QuickAction[]
  maxVisible?: number
  size?: 'small' | 'middle' | 'large'
  type?: 'default' | 'primary' | 'ghost' | 'dashed' | 'link' | 'text'
}

const QuickActions: React.FC<QuickActionsProps> = ({
  actions,
  maxVisible = 3,
  size = 'small',
  type = 'default'
}) => {
  const { themeMode } = useAppSelector(state => state.ui)

  if (!actions || actions.length === 0) {
    return null
  }

  const visibleActions = actions.slice(0, maxVisible)

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
      className="flex items-center"
    >
      <Space size="small">
        {visibleActions.map((action, index) => (
          <Tooltip
            key={action.id}
            title={action.description || action.label}
            placement="bottom"
          >
            <Button
              type={type}
              size={size}
              icon={action.icon}
              onClick={action.onClick}
              disabled={action.disabled}
              className={`${
                type === 'text'
                  ? `hover:bg-gray-100 dark:hover:bg-gray-800 ${
                      themeMode === 'dark' ? 'text-gray-300' : 'text-gray-600'
                    }`
                  : ''
              }`}
            >
              <span className="hidden sm:inline">{action.label}</span>
            </Button>
          </Tooltip>
        ))}
      </Space>

      {/* Show more indicator if there are more actions */}
      {actions.length > maxVisible && (
        <Tooltip title={`還有 ${actions.length - maxVisible} 個操作`} placement="bottom">
          <Button
            type="text"
            size={size}
            className={`text-gray-400 ${
              themeMode === 'dark' ? 'hover:text-gray-200' : 'hover:text-gray-600'
            }`}
          >
            +{actions.length - maxVisible}
          </Button>
        </Tooltip>
      )}
    </motion.div>
  )
}

export default QuickActions