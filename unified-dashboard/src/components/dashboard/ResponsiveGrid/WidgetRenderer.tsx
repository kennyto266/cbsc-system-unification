import React, { memo, useMemo } from 'react'
import { Card, Button, Dropdown, Space, Tooltip, Badge } from 'antd'
import {
  MoreOutlined,
  SettingOutlined,
  ExpandOutlined,
  CompressOutlined,
  ReloadOutlined,
  CloseOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined
} from '@ant-design/icons'
import { GridWidget } from './ResponsiveGridProvider'
import { useResponsiveGrid } from './ResponsiveGridProvider'

// Import widget components
import MetricCard from '../MetricCard'
import MarketOverview from '../MarketOverview'
import StrategyPerformanceChart from '../../Charts/StrategyPerformanceChart'
import AssetAllocationChart from '../../Charts/AssetAllocationChart'
import SystemHealth from '../SystemHealth'
import RecentSignals from '../RecentSignals'
import QuickActions from '../QuickActions'
import TechnicalIndicatorWidget from './widgets/TechnicalIndicatorWidget'
import CustomWidget from './widgets/CustomWidget'

// Widget configuration interface
interface WidgetRendererProps {
  widget: GridWidget
  selected?: boolean
  editable?: boolean
  onConfig?: (widget: GridWidget) => void
  onRemove?: (widgetId: string) => void
  onDuplicate?: (widget: GridWidget) => void
  onExpand?: (widget: GridWidget) => void
}

// Widget content renderer
const WidgetContent: React.FC<{ widget: GridWidget }> = memo(({ widget }) => {
  // Memoize widget content to prevent unnecessary re-renders
  const content = useMemo(() => {
    switch (widget.type) {
      case 'market-overview':
        return <MarketOverview />

      case 'metric':
        return (
          <MetricCard
            title={widget.name}
            value={widget.data?.value || 0}
            precision={widget.config?.precision || 2}
            prefix={widget.config?.prefix}
            suffix={widget.config?.suffix}
            trend={widget.data?.trend}
            icon={widget.config?.icon}
            loading={widget.data?.loading}
          />
        )

      case 'strategy-performance':
        return (
          <StrategyPerformanceChart
            strategies={widget.data?.strategies || []}
            timeRange={widget.config?.timeRange || '1M'}
            onTimeRangeChange={widget.config?.onTimeRangeChange}
          />
        )

      case 'asset-allocation':
        return (
          <AssetAllocationChart
            strategies={widget.data?.strategies || []}
            totalValue={widget.data?.totalValue || 100000}
            showDetails={widget.config?.showDetails !== false}
          />
        )

      case 'system-health':
        return <SystemHealth />

      case 'recent-signals':
        return <RecentSignals />

      case 'quick-actions':
        return <QuickActions />

      case 'technical-indicator':
        return (
          <TechnicalIndicatorWidget
            indicator={widget.config?.indicator || 'RSI'}
            symbol={widget.config?.symbol || 'BTC/USDT'}
            timeFrame={widget.config?.timeFrame || '1h'}
            params={widget.config?.params || {}}
          />
        )

      case 'custom':
        return (
          <CustomWidget
            widgetId={widget.id}
            config={widget.config || {}}
            data={widget.data}
          />
        )

      default:
        return (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-6xl mb-4">📦</div>
              <div className="text-gray-500">未知组件类型: {widget.type}</div>
            </div>
          </div>
        )
    }
  }, [widget])

  return <div className="widget-content">{content}</div>
})

WidgetContent.displayName = 'WidgetContent'

// Widget header component
const WidgetHeader: React.FC<{
  widget: GridWidget
  editable?: boolean
  onConfig?: () => void
  onRemove?: () => void
  onDuplicate?: () => void
  onExpand?: () => void
}> = memo(({ widget, editable, onConfig, onRemove, onDuplicate, onExpand }) => {
  // Show loading indicator if widget is updating
  const isUpdating = widget.lastUpdated &&
    new Date(widget.lastUpdated).getTime() > Date.now() - 1000

  // Dropdown menu items
  const menuItems = useMemo(() => {
    const items = []

    if (editable) {
      items.push(
        {
          key: 'config',
          label: '配置',
          icon: <SettingOutlined />,
          onClick: onConfig
        },
        {
          key: 'duplicate',
          label: '复制',
          icon: <ExpandOutlined />,
          onClick: onDuplicate
        },
        {
          type: 'divider' as const
        }
      )
    }

    items.push(
      {
        key: 'refresh',
        label: '刷新',
        icon: <ReloadOutlined />,
        onClick: () => window.location.reload()
      },
      {
        key: 'expand',
        label: '全屏',
        icon: <FullscreenOutlined />,
        onClick: onExpand
      }
    )

    if (editable) {
      items.push(
        {
          type: 'divider' as const
        },
        {
          key: 'remove',
          label: '删除',
          icon: <CloseOutlined />,
          danger: true,
          onClick: onRemove
        }
      )
    }

    return items
  }, [editable, onConfig, onRemove, onDuplicate, onExpand])

  return (
    <div className="widget-header">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <h4 className="widget-title m-0">{widget.name}</h4>
          {isUpdating && (
            <Badge status="processing" />
          )}
          {widget.category && (
            <span className="widget-category text-xs text-gray-500">
              {widget.category}
            </span>
          )}
        </div>

        <Space size="small">
          {widget.config?.actions?.map((action: any, index: number) => (
            <Button
              key={index}
              type="text"
              size="small"
              icon={action.icon}
              onClick={action.onClick}
              title={action.tooltip}
            />
          ))}

          <Dropdown
            menu={{ items: menuItems }}
            trigger={['click']}
            placement="bottomRight"
          >
            <Button
              type="text"
              size="small"
              icon={<MoreOutlined />}
              className="widget-menu-button"
            />
          </Dropdown>
        </Space>
      </div>
    </div>
  )
})

WidgetHeader.displayName = 'WidgetHeader'

// Main widget renderer component
const WidgetRenderer: React.FC<WidgetRendererProps> = ({
  widget,
  selected = false,
  editable = true,
  onConfig,
  onRemove,
  onDuplicate,
  onExpand
}) => {
  const { removeWidget, addWidget, widgetTypes } = useResponsiveGrid()

  // Get widget type configuration
  const widgetType = widgetTypes[widget.type]

  // Handle widget configuration
  const handleConfig = () => {
    if (onConfig) {
      onConfig(widget)
    }
  }

  // Handle widget removal
  const handleRemove = () => {
    if (onRemove) {
      onRemove(widget.id)
    } else {
      removeWidget(widget.id)
    }
  }

  // Handle widget duplication
  const handleDuplicate = () => {
    if (onDuplicate) {
      onDuplicate(widget)
    } else {
      // Create a duplicate with a new ID
      const duplicateWidget: GridWidget = {
        ...widget,
        id: `${widget.id}-copy-${Date.now()}`,
        name: `${widget.name} (副本)`,
        x: (widget.x || 0) + 1,
        y: (widget.y || 0) + 1
      }
      addWidget(duplicateWidget)
    }
  }

  // Handle widget expansion
  const handleExpand = () => {
    if (onExpand) {
      onExpand(widget)
    } else {
      // Default expand behavior - open in modal
      console.log('Expand widget:', widget)
    }
  }

  return (
    <Card
      className={`widget-card ${selected ? 'selected' : ''} ${editable ? 'editable' : 'readonly'}`}
      bordered={false}
      size="small"
      title={
        <WidgetHeader
          widget={widget}
          editable={editable}
          onConfig={handleConfig}
          onRemove={handleRemove}
          onDuplicate={handleDuplicate}
          onExpand={handleExpand}
        />
      }
      extra={null}
      styles={{
        body: {
          padding: 0,
          height: '100%',
          display: 'flex',
          flexDirection: 'column'
        }
      }}
    >
      <div className="widget-body">
        <WidgetContent widget={widget} />
      </div>

      <style jsx>{`
        .widget-card {
          height: 100%;
          display: flex;
          flex-direction: column;
          background: rgba(255, 255, 255, 0.8);
          backdrop-filter: blur(10px);
          transition: all 0.2s ease;
        }

        .widget-card:hover {
          background: rgba(255, 255, 255, 0.95);
        }

        .widget-card.selected {
          background: rgba(255, 255, 255, 0.95);
          box-shadow: 0 0 0 2px #1890ff;
        }

        .widget-card.editable {
          cursor: move;
        }

        .widget-card :global(.ant-card-head) {
          padding: 8px 12px;
          min-height: 40px;
          border-bottom: 1px solid rgba(0, 0, 0, 0.06);
        }

        .widget-card :global(.ant-card-head-title) {
          padding: 0;
        }

        .widget-card :global(.ant-card-body) {
          padding: 0;
          flex: 1;
          overflow: hidden;
        }

        .widget-header {
          width: 100%;
        }

        .widget-title {
          font-size: 14px;
          font-weight: 600;
          color: rgba(0, 0, 0, 0.85);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .widget-category {
          background: rgba(0, 0, 0, 0.04);
          padding: 2px 6px;
          border-radius: 4px;
          text-transform: uppercase;
          font-weight: 500;
        }

        .widget-menu-button {
          opacity: 0.6;
          transition: opacity 0.2s;
        }

        .widget-menu-button:hover {
          opacity: 1;
        }

        .widget-body {
          flex: 1;
          overflow: hidden;
          padding: 12px;
        }

        .widget-content {
          width: 100%;
          height: 100%;
          display: flex;
          flex-direction: column;
        }

        /* Dark theme support */
        .dark .widget-card {
          background: rgba(0, 0, 0, 0.8);
        }

        .dark .widget-card:hover,
        .dark .widget-card.selected {
          background: rgba(0, 0, 0, 0.95);
        }

        .dark .widget-title {
          color: rgba(255, 255, 255, 0.85);
        }

        .dark .widget-category {
          background: rgba(255, 255, 255, 0.1);
          color: rgba(255, 255, 255, 0.65);
        }
      `}</style>
    </Card>
  )
}

export default WidgetRenderer