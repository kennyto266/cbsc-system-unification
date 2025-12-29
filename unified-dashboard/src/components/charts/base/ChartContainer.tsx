import React, { useState, useCallback, useEffect } from 'react'
import { Card, Button, Space, Select, Tooltip, Dropdown } from 'antd'
import {
  FullscreenOutlined,
  FullscreenExitOutlined,
  DownloadOutlined,
  SettingOutlined,
  ReloadOutlined,
  MoreOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  UndoOutlined,
} from '@ant-design/icons'
import { motion, AnimatePresence } from 'framer-motion'
import Chart, { ChartRef, ChartExportOptions } from './Chart'
import { ChartTheme } from '../../utils/charts'
import { cn } from '@/lib/utils'

const { Option } = Select

export interface ChartContainerProps {
  title?: string
  subtitle?: string
  description?: string
  className?: string
  children: React.ReactNode
  loading?: boolean
  error?: string
  actions?: React.ReactNode
  toolbar?: React.ReactNode
  showToolbar?: boolean
  fullscreen?: boolean
  onFullscreenChange?: (fullscreen: boolean) => void
  exportable?: boolean
  exportOptions?: ChartExportOptions
  refreshable?: boolean
  onRefresh?: () => void
  resizable?: boolean
  height?: number | string
  theme?: ChartTheme
  timeRange?: string
  onTimeRangeChange?: (range: string) => void
  timeRangeOptions?: Array<{ label: string; value: string }>
  showZoom?: boolean
  chartRef?: React.RefObject<ChartRef>
}

const ChartContainer: React.FC<ChartContainerProps> = ({
  title,
  subtitle,
  description,
  className,
  children,
  loading,
  error,
  actions,
  toolbar,
  showToolbar = true,
  fullscreen = false,
  onFullscreenChange,
  exportable = true,
  exportOptions,
  refreshable = true,
  onRefresh,
  resizable = false,
  height,
  theme,
  timeRange,
  onTimeRangeChange,
  timeRangeOptions = [
    { label: '1D', value: '1D' },
    { label: '1W', value: '1W' },
    { label: '1M', value: '1M' },
    { label: '3M', value: '3M' },
    { label: '6M', value: '6M' },
    { label: '1Y', value: '1Y' },
  ],
  showZoom = true,
  chartRef,
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)

  // Handle fullscreen toggle
  const handleFullscreenToggle = useCallback(() => {
    const newFullscreen = !isFullscreen
    setIsFullscreen(newFullscreen)
    onFullscreenChange?.(newFullscreen)
  }, [isFullscreen, onFullscreenChange])

  // Handle export
  const handleExport = useCallback(async () => {
    if (chartRef && 'current' in chartRef && chartRef.current) {
      try {
        await chartRef.current.exportChart(exportOptions)
      } catch (error) {
        console.error('Export failed:', error)
      }
    }
  }, [chartRef, exportOptions])

  // Handle refresh
  const handleRefresh = useCallback(() => {
    onRefresh?.()
  }, [onRefresh])

  // Handle zoom
  const handleZoomIn = useCallback(() => {
    if (chartRef && 'current' in chartRef && chartRef.current) {
      chartRef.current.zoomIn()
    }
  }, [chartRef])

  const handleZoomOut = useCallback(() => {
    if (chartRef && 'current' in chartRef && chartRef.current) {
      chartRef.current.zoomOut()
    }
  }, [chartRef])

  const handleResetZoom = useCallback(() => {
    if (chartRef && 'current' in chartRef && chartRef.current) {
      chartRef.current.resetZoom()
    }
  }, [chartRef])

  // Default toolbar actions
  const defaultToolbarActions = (
    <Space size="small">
      {timeRange && onTimeRangeChange && (
        <Select
          value={timeRange}
          onChange={onTimeRangeChange}
          size="small"
          style={{ width: 80 }}
        >
          {timeRangeOptions.map(option => (
            <Option key={option.value} value={option.value}>
              {option.label}
            </Option>
          ))}
        </Select>
      )}

      {showZoom && (
        <Space size="small">
          <Tooltip title="Zoom In">
            <Button
              size="small"
              icon={<ZoomInOutlined />}
              onClick={handleZoomIn}
            />
          </Tooltip>
          <Tooltip title="Zoom Out">
            <Button
              size="small"
              icon={<ZoomOutOutlined />}
              onClick={handleZoomOut}
            />
          </Tooltip>
          <Tooltip title="Reset Zoom">
            <Button
              size="small"
              icon={<UndoOutlined />}
              onClick={handleResetZoom}
            />
          </Tooltip>
        </Space>
      )}

      {refreshable && (
        <Tooltip title="Refresh">
          <Button
            size="small"
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={loading}
          />
        </Tooltip>
      )}

      {exportable && (
        <Tooltip title="Export">
          <Button
            size="small"
            icon={<DownloadOutlined />}
            onClick={handleExport}
          />
        </Tooltip>
      )}

      <Dropdown
        menu={{
          items: [
            {
              key: 'fullscreen',
              label: isFullscreen ? 'Exit Fullscreen' : 'Fullscreen',
              icon: isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />,
              onClick: handleFullscreenToggle,
            },
          ],
        }}
        trigger={['click']}
        open={isDropdownOpen}
        onOpenChange={setIsDropdownOpen}
      >
        <Button size="small" icon={<MoreOutlined />} />
      </Dropdown>
    </Space>
  )

  // Chart content
  const chartContent = (
    <AnimatePresence mode="wait">
      <motion.div
        key={isFullscreen ? 'fullscreen' : 'normal'}
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 1.05 }}
        transition={{ duration: 0.2 }}
        className={cn(
          'relative',
          isFullscreen && 'fixed inset-0 z-50 bg-white p-6',
          !isFullscreen && 'h-full'
        )}
        style={!isFullscreen && height ? { height } : undefined}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  )

  // Render fullscreen mode
  if (isFullscreen) {
    return (
      <div className="flex flex-col h-full">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
            {subtitle && (
              <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
            )}
          </div>
          {defaultToolbarActions}
        </div>
        {chartContent}
      </div>
    )
  }

  // Render normal mode
  return (
    <Card
      className={cn('h-full', className)}
      bodyStyle={{ padding: 0, height: '100%' }}
      title={
        title && (
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="text-base font-semibold text-gray-900">{title}</div>
              {subtitle && (
                <div className="text-sm text-gray-500 mt-1">{subtitle}</div>
              )}
              {description && (
                <div className="text-xs text-gray-400 mt-1">{description}</div>
              )}
            </div>
            {actions && (
              <div className="ml-4">{actions}</div>
            )}
          </div>
        )
      }
      extra={
        showToolbar && (
          <div className="flex items-center space-x-2">
            {toolbar || defaultToolbarActions}
          </div>
        )
      }
    >
      {chartContent}
    </Card>
  )
}

export default ChartContainer