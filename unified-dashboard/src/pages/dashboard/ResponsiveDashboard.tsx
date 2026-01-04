import React, { useState, useEffect, useCallback, useMemo, memo } from 'react'
import { Button, Space, Typography, Card, Switch, Tooltip, Alert, Badge } from 'antd'
import {
  SettingOutlined,
  PlusOutlined,
  SaveOutlined,
  EyeOutlined,
  EditOutlined,
  AppstoreOutlined,
  TrendingUp,
  TrendingDown,
  Activity,
  Zap,
  Shield,
  Bell,
  DollarSign,
  BarChart3,
  Lock,
  Unlock,
} from '@ant-design/icons'
import Grid from '../../components/dashboard/Grid'
import { useGridLayout } from '../../hooks/dashboard/useGridLayout'
import { createGridItem } from '../../utils/dashboard/gridHelpers'

const { Title, Text } = Typography

// Memoized widget card component for performance
const WidgetCard = memo(({ type, title, onClick, description }: {
  type: string
  title: string
  onClick: () => void
  description: string
}) => (
  <Button
    key={type}
    size="small"
    className="text-left bg-slate-800/50 border-slate-700 text-slate-200 hover:bg-slate-700/50 hover:border-slate-600 hover:text-white transition-all"
    onClick={onClick}
    title={description}
  >
    <AppstoreOutlined className="mr-1" />
    {title}
  </Button>
))
WidgetCard.displayName = 'WidgetCard'

// Get icon for widget type
const getWidgetIcon = (type: string) => {
  const icons: Record<string, React.ReactNode> = {
    'market-overview': <Activity className="h-5 w-5" />,
    'strategy-monitor': <TrendingUp className="h-5 w-5" />,
    'portfolio-summary': <DollarSign className="h-5 w-5" />,
    'risk-metrics': <Shield className="h-5 w-5" />,
    'trading-panel': <Zap className="h-5 w-5" />,
    'news-feed': <Bell className="h-5 w-5" />,
    'system-status': <Activity className="h-5 w-5" />,
    'performance-chart': <BarChart3 className="h-5 w-5" />,
    'order-book': <BarChart3 className="h-5 w-5" />,
    'alert-center': <Bell className="h-5 w-5" />,
  }
  return icons[type] || <AppstoreOutlined className="h-5 w-5" />
}

// Get color for widget type
const getWidgetColor = (type: string): string => {
  const colors: Record<string, string> = {
    'market-overview': 'from-blue-500/20 to-cyan-500/20 border-blue-500/30',
    'strategy-monitor': 'from-emerald-500/20 to-green-500/20 border-emerald-500/30',
    'portfolio-summary': 'from-amber-500/20 to-orange-500/20 border-amber-500/30',
    'risk-metrics': 'from-rose-500/20 to-pink-500/20 border-rose-500/30',
    'trading-panel': 'from-violet-500/20 to-purple-500/20 border-violet-500/30',
    'news-feed': 'from-sky-500/20 to-blue-500/20 border-sky-500/30',
    'system-status': 'from-teal-500/20 to-cyan-500/20 border-teal-500/30',
    'performance-chart': 'from-indigo-500/20 to-blue-500/20 border-indigo-500/30',
    'order-book': 'from-fuchsia-500/20 to-pink-500/20 border-fuchsia-500/30',
    'alert-center': 'from-red-500/20 to-orange-500/20 border-red-500/30',
  }
  return colors[type] || 'from-slate-500/20 to-gray-500/20 border-slate-500/30'
}

const ResponsiveDashboard: React.FC = () => {
  const {
    layout,
    isEditMode,
    addNewWidget,
    toggleEditMode,
    resetLayout,
    lockLayout,
    unlockLayout,
    exportCurrentLayout,
    stats,
    setError,
  } = useGridLayout()

  const [mounted, setMounted] = useState(false)

  // Handle mounted state to avoid SSR mismatch
  useEffect(() => {
    setMounted(true)
  }, [])

  // Initialize dashboard with default widgets (only once)
  useEffect(() => {
    if (mounted && layout.items.length === 0) {
      const defaultWidgets = [
        { type: 'market-overview', title: '市場概覽', position: { x: 0, y: 0 }, size: { w: 2, h: 3 } },
        { type: 'strategy-monitor', title: '策略監控', position: { x: 2, y: 0 }, size: { w: 2, h: 3 } },
        { type: 'portfolio-summary', title: '投資組合', position: { x: 4, y: 0 }, size: { w: 2, h: 3 } },
        { type: 'risk-metrics', title: '風險指標', position: { x: 0, y: 3 }, size: { w: 3, h: 2 } },
        { type: 'trading-panel', title: '交易面板', position: { x: 3, y: 3 }, size: { w: 3, h: 2 } },
        { type: 'news-feed', title: '新聞動態', position: { x: 0, y: 5 }, size: { w: 2, h: 2 } },
        { type: 'system-status', title: '系統狀態', position: { x: 2, y: 5 }, size: { w: 2, h: 2 } },
        { type: 'alert-center', title: '警報中心', position: { x: 4, y: 5 }, size: { w: 2, h: 2 } },
      ]

      defaultWidgets.forEach(widget => {
        addNewWidget(widget.type, widget.title, widget.position, widget.size)
      })
    }
  }, [mounted, layout.items.length, addNewWidget])

  // Memoize available widgets
  const availableWidgets = useMemo(() => [
    { type: 'market-overview', name: '市場概覽', description: '實時市場數據和指標' },
    { type: 'strategy-monitor', name: '策略監控', description: '監控活躍交易策略' },
    { type: 'portfolio-summary', name: '投資組合', description: '投資組合價值和配置' },
    { type: 'risk-metrics', name: '風險指標', description: '風險分析和指標' },
    { type: 'trading-panel', name: '交易面板', description: '快速交易界面' },
    { type: 'news-feed', name: '新聞動態', description: '最新市場新聞' },
    { type: 'system-status', name: '系統狀態', description: '系統健康監控' },
    { type: 'performance-chart', name: '性能圖表', description: '性能可視化' },
    { type: 'order-book', name: '訂單簿', description: '實時訂單簿數據' },
    { type: 'alert-center', name: '警報中心', description: '交易警報和通知' },
  ], [])

  // Memoize stats display
  const statsDisplay = useMemo(() => (
    <Space className="text-slate-400">
      <Badge count={stats.totalWidgets} showZero className="bg-slate-700">
        <Text className="text-slate-400 text-sm">組件</Text>
      </Badge>
      <Text type="secondary" className="text-slate-400 text-sm">
        利用率 {stats.utilizationRate.toFixed(0)}%
      </Text>
    </Space>
  ), [stats.totalWidgets, stats.utilizationRate])

  // Memoize layout export handler
  const handleExportLayout = useCallback(() => {
    const layoutData = exportCurrentLayout()
    const blob = new Blob([layoutData], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `cbsc-dashboard-layout-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }, [exportCurrentLayout])

  // Memoize add widget handler
  const handleAddWidget = useCallback((type: string, name: string) => {
    const cols = layout.breakpoints[layout.activeBreakpoint || 'lg'].cols

    // Find empty space
    let placed = false

    // Try to place widget in the first available spot
    for (let row = 0; row < 20 && !placed; row++) {
      for (let col = 0; col <= cols - 2 && !placed; col++) {
        const wouldOverlap = layout.items.some(item => {
          const itemRight = item.position.x + item.size.w
          const itemBottom = item.position.y + item.size.h
          const widgetRight = col + 2
          const widgetBottom = row + 2

          return !(
            col >= itemRight ||
            widgetRight <= item.position.x ||
            row >= itemBottom ||
            widgetBottom <= item.position.y
          )
        })

        if (!wouldOverlap) {
          addNewWidget(type, name, { x: col, y: row }, { w: 2, h: 2 })
          placed = true
        }
      }
    }

    // If no space found, add to the bottom
    if (!placed) {
      const maxY = Math.max(...layout.items.map(item => item.position.y + item.size.h), 0)
      addNewWidget(type, name, { x: 0, y: maxY }, { w: 2, h: 2 })
    }
  }, [layout.breakpoints, layout.activeBreakpoint, layout.items, addNewWidget])

  // Memoize widget panel render
  const widgetPanel = useMemo(() => {
    if (!isEditMode) return null

    return (
      <div className="bg-slate-900/50 border-b border-slate-800 px-6 py-4 backdrop-blur-sm">
        <div className="flex items-center gap-4 flex-wrap">
          <Text strong className="text-cyan-400 font-['Outfit']">
            可用組件:
          </Text>
          <div className="flex flex-wrap gap-2">
            {availableWidgets.map(widget => (
              <WidgetCard
                key={widget.type}
                type={widget.type}
                title={widget.name}
                description={widget.description}
                onClick={() => handleAddWidget(widget.type, widget.name)}
              />
            ))}
          </div>
        </div>
      </div>
    )
  }, [isEditMode, availableWidgets, handleAddWidget])

  if (!mounted) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-cyan-500 border-r-transparent"></div>
          <p className="mt-4 text-slate-400 font-['Outfit']">載入中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen w-full flex flex-col bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 font-['Outfit']">
      {/* Header */}
      <div className="bg-slate-900/50 border-b border-slate-800 px-6 py-4 backdrop-blur-sm">
        <div className="flex justify-between items-center flex-wrap gap-4">
          <div>
            <Title level={3} className="!mb-0 !text-white font-['Outfit']">
              CBSC 量化交易儀表板
            </Title>
            <Text type="secondary" className="text-slate-400">
              拖拽和調整組件來自定義您的交易工作區
            </Text>
          </div>

          <Space size="middle" wrap>
            {/* Layout Stats */}
            {statsDisplay}

            {/* Edit Mode Toggle */}
            <Space>
              <Text className="text-sm text-slate-300">編輯模式</Text>
              <Switch
                checked={isEditMode}
                onChange={toggleEditMode}
                checkedChildren={<EditOutlined />}
                unCheckedChildren={<EyeOutlined />}
                className={isEditMode ? 'bg-cyan-500' : ''}
              />
            </Space>

            {/* Quick Actions */}
            <Tooltip title="添加組件">
              <Button
                type="primary"
                icon={<PlusOutlined />}
                className="bg-cyan-600 hover:bg-cyan-700 border-cyan-600"
                onClick={() => console.log('Open widget panel')}
              >
                添加組件
              </Button>
            </Tooltip>

            <Tooltip title={layout.isLocked ? '解鎖佈局' : '鎖定佈局'}>
              <Button
                type={layout.isLocked ? 'default' : 'dashed'}
                icon={layout.isLocked ? <Lock /> : <Unlock />}
                onClick={layout.isLocked ? unlockLayout : lockLayout}
                className={layout.isLocked ? 'bg-slate-700 border-slate-600 text-white' : 'border-slate-600 text-slate-300'}
              >
                {layout.isLocked ? '已鎖定' : '未鎖定'}
              </Button>
            </Tooltip>

            <Tooltip title="導出佈局">
              <Button
                icon={<SaveOutlined />}
                className="border-slate-600 text-slate-300 hover:border-slate-500 hover:text-white"
                onClick={handleExportLayout}
              >
                導出
              </Button>
            </Tooltip>

            <Tooltip title="重置佈局">
              <Button
                onClick={resetLayout}
                danger
                className="bg-rose-600/20 border-rose-600/50 text-rose-400 hover:bg-rose-600/30"
              >
                重置
              </Button>
            </Tooltip>
          </Space>
        </div>
      </div>

      {/* Widget Panel */}
      {widgetPanel}

      {/* Main Grid Container */}
      <div className="flex-1 p-4 overflow-hidden">
        {isEditMode && (
          <Alert
            message="編輯模式已啟用"
            description="拖拽組件移動位置。使用角落手柄調整大小。右鍵單擊查看更多選項。"
            type="info"
            showIcon
            closable
            className="mb-4 bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
          />
        )}

        <div className="h-full">
          <Grid
            className="bg-slate-900/50 border border-slate-800 backdrop-blur-sm rounded-lg"
            onWidgetClick={(widgetId) => console.log('Widget clicked:', widgetId)}
            onWidgetDoubleClick={(widgetId) => console.log('Widget double-clicked:', widgetId)}
          />
        </div>
      </div>

      {/* Footer */}
      <div className="bg-slate-900/50 border-t border-slate-800 px-6 py-2 backdrop-blur-sm">
        <div className="flex justify-between items-center text-xs">
          <Text className="text-slate-500 font-['JetBrains_Mono']">
            最後更新: {new Date().toLocaleString('zh-CN', {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </Text>
          <Text className="text-slate-500 font-['JetBrains_Mono']">
            斷點: {layout.activeBreakpoint || 'lg'} |
            列數: {layout.breakpoints[layout.activeBreakpoint || 'lg'].cols}
          </Text>
        </div>
      </div>

      {/* Custom animations */}
      <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .fade-in {
          animation: fadeIn 0.3s ease-out;
        }

        /* Custom scrollbar */
        ::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }

        ::-webkit-scrollbar-track {
          background: rgba(15, 23, 42, 0.5);
        }

        ::-webkit-scrollbar-thumb {
          background: rgba(51, 65, 85, 0.8);
          border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
          background: rgba(71, 85, 105, 0.9);
        }
      `}</style>
    </div>
  )
}

export default memo(ResponsiveDashboard)
