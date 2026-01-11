import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ChevronRightOutlined, HomeOutlined } from '@ant-design/icons'
import { useAppSelector } from '../../hooks/redux'
import type { BreadcrumbItem } from '../../types/layout'

interface BreadcrumbProps {
  items?: BreadcrumbItem[]
  separator?: React.ReactNode
  showHome?: boolean
  maxItems?: number
}

const Breadcrumb: React.FC<BreadcrumbProps> = ({
  items: propItems,
  separator = <ChevronRightOutlined className="text-gray-400 text-xs" />,
  showHome = true,
  maxItems = 5
}) => {
  const location = useLocation()
  const { themeMode } = useAppSelector(state => state.ui)

  // Use provided items or generate from location
  const items = propItems || []

  // Truncate items if too many
  const displayItems = items.length > maxItems
    ? [
        items[0], // Always show first
        { title: '...', icon: null },
        ...items.slice(-(maxItems - 2)) // Show last few
      ]
    : items

  return (
    <nav className={`flex items-center space-x-2 text-sm ${
      themeMode === 'dark' ? 'text-gray-300' : 'text-gray-600'
    }`}>
      {showHome && (
        <Link
          to="/dashboard"
          className={`hover:text-blue-500 transition-colors flex items-center ${
            themeMode === 'dark' ? 'text-gray-400' : 'text-gray-500'
          }`}
        >
          <HomeOutlined className="text-base" />
        </Link>
      )}

      {displayItems.map((item, index) => {
        const isLast = index === displayItems.length - 1
        const isEllipsis = item.title === '...'

        return (
          <React.Fragment key={index}>
            {!isEllipsis && separator}
            {isEllipsis ? (
              <span className="text-gray-400">...</span>
            ) : item.path && !isLast ? (
              <Link
                to={item.path}
                className="hover:text-blue-500 transition-colors flex items-center space-x-1"
              >
                {item.icon && <span className="text-base">{item.icon}</span>}
                <span>{item.title}</span>
              </Link>
            ) : (
              <div className="flex items-center space-x-1">
                {item.icon && <span className="text-base">{item.icon}</span>}
                <span className={`font-medium ${
                  themeMode === 'dark' ? 'text-white' : 'text-gray-900'
                }`}>
                  {item.title}
                </span>
              </div>
            )}
          </React.Fragment>
        )
      })}
    </nav>
  )
}

export default Breadcrumb