import React from 'react'
import { Card } from '../../../components/ui/Card'
import { getTheme } from '../utils/chartThemes'
import type { ChartTheme } from '../../../types/chart'

interface ChartContainerProps {
  title?: string
  subtitle?: string
  loading?: boolean
  error?: string | null
  height?: number | string
  width?: number | string
  className?: string
  theme?: 'light' | 'dark' | 'cbsc'
  children: React.ReactNode
  actions?: React.ReactNode
  toolbar?: React.ReactNode
}

const ChartContainer: React.FC<ChartContainerProps> = ({
  title,
  subtitle,
  loading = false,
  error = null,
  height = 400,
  width = '100%',
  className = '',
  theme = 'light',
  children,
  actions,
  toolbar
}) => {
  const chartTheme = getTheme(theme)

  if (loading) {
    return (
      <Card className={`p-6 ${className}`}>
        {(title || subtitle) && (
          <div className="mb-4">
            {title && (
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {subtitle}
              </p>
            )}
          </div>
        )}
        <div
          className="flex items-center justify-center"
          style={{ height: typeof height === 'number' ? `${height}px` : height }}
        >
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className={`p-6 ${className}`}>
        {(title || subtitle) && (
          <div className="mb-4">
            {title && (
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {subtitle}
              </p>
            )}
          </div>
        )}
        <div
          className="flex flex-col items-center justify-center text-red-500"
          style={{ height: typeof height === 'number' ? `${height}px` : height }}
        >
          <svg className="w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm font-medium">{error}</p>
        </div>
      </Card>
    )
  }

  return (
    <Card className={`overflow-hidden ${className}`}>
      {(title || subtitle || actions) && (
        <div className="px-6 pt-6 pb-2 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              {title && (
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {subtitle}
                </p>
              )}
            </div>
            {actions && (
              <div className="flex items-center space-x-2">
                {actions}
              </div>
            )}
          </div>
        </div>
      )}

      {toolbar && (
        <div className="px-6 pt-2 pb-2 border-b border-gray-200 dark:border-gray-700">
          {toolbar}
        </div>
      )}

      <div
        className="p-6"
        style={{
          width: typeof width === 'number' ? `${width}px` : width,
          height: typeof height === 'number' ? `${height}px` : height,
          backgroundColor: chartTheme.backgroundColor,
          color: chartTheme.textColor
        }}
      >
        {children}
      </div>
    </Card>
  )
}

export default ChartContainer