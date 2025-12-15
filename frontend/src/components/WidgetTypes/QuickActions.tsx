import React, { useState } from 'react'
import {
  Play,
  Pause,
  Square,
  RefreshCw,
  Download,
  Settings,
  Plus,
  Rocket,
  BarChart3,
  FileText,
  Save,
  Copy,
  Trash2
} from 'lucide-react'
import { Button } from '../ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../ui/dialog'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Badge } from '../ui/badge'

interface QuickAction {
  id: string
  title: string
  description: string
  icon: React.ElementType
  action: () => void
  badge?: string
  color?: 'default' | 'destructive' | 'outline' | 'secondary'
  disabled?: boolean
}

const QuickActions: React.FC = () => {
  const [isExportDialogOpen, setIsExportDialogOpen] = useState(false)
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([])

  // 快捷操作列表
  const quickActions: QuickAction[] = [
    {
      id: 'start-all',
      title: '启动所有策略',
      description: '启动所有已暂停的策略',
      icon: Play,
      action: () => {
        console.log('启动所有策略')
        // 实际实现：调用API启动所有策略
      },
      color: 'default'
    },
    {
      id: 'pause-all',
      title: '暂停所有策略',
      description: '暂停所有正在运行的策略',
      icon: Pause,
      action: () => {
        console.log('暂停所有策略')
        // 实际实现：调用API暂停所有策略
      },
      color: 'secondary'
    },
    {
      id: 'quick-backtest',
      title: '快速回测',
      description: '对选中策略进行快速回测',
      icon: RefreshCw,
      badge: 'Beta',
      action: () => {
        console.log('快速回测')
        // 实现：打开回测配置对话框
      },
      color: 'default'
    },
    {
      id: 'new-strategy',
      title: '创建策略',
      description: '使用模板快速创建新策略',
      icon: Plus,
      action: () => {
        console.log('创建策略')
        // 实现：跳转到策略创建页面
      },
      color: 'default'
    }
  ]

  // 批量操作
  const batchActions = [
    {
      title: '导出配置',
      description: '导出当前布局配置',
      icon: Download,
      items: [
        { label: '导出为JSON', action: 'export-json' },
        { label: '导出为YAML', action: 'export-yaml' },
        { label: '导出为图片', action: 'export-image' }
      ]
    },
    {
      title: '布局管理',
      description: '管理仪表盘布局',
      icon: Settings,
      items: [
        { label: '保存当前布局', action: 'save-layout' },
        { label: '加载布局', action: 'load-layout' },
        { label: '重置布局', action: 'reset-layout' }
      ]
    }
  ]

  const handleActionClick = (action: QuickAction) => {
    action.action()
  }

  return (
    <div className="space-y-4 h-full">
      {/* 快速操作 */}
      <div className="grid grid-cols-2 gap-3">
        {quickActions.map((action) => (
          <Button
            key={action.id}
            variant="outline"
            className="h-auto p-3 flex flex-col items-center justify-center space-y-2 hover:bg-accent"
            onClick={() => handleActionClick(action)}
            disabled={action.disabled}
          >
            <action.icon className="h-4 w-4" />
            <span className="text-xs font-medium text-center">{action.title}</span>
            {action.badge && (
              <Badge variant="secondary" className="text-xs">
                {action.badge}
              </Badge>
            )}
          </Button>
        ))}
      </div>

      {/* 批量操作 */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold px-1">批量操作</h4>
        {batchActions.map((batch, index) => (
          <DropdownMenu key={index}>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-between p-3 hover:bg-accent"
              >
                <div className="flex items-center space-x-2">
                  <batch.icon className="h-4 w-4" />
                  <span className="text-sm font-medium">{batch.title}</span>
                </div>
                <BarChart3 className="h-3 w-3" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              {batch.items.map((item, itemIndex) => (
                <DropdownMenuItem
                  key={itemIndex}
                  onClick={() => {
                    if (item.action === 'export-json') {
                      setIsExportDialogOpen(true)
                    }
                    console.log('批量操作:', item.action)
                  }}
                >
                  {item.label}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        ))}
      </div>

      {/* 常用工具 */}
      <div className="p-3 bg-card border border-border rounded-lg">
        <h4 className="text-sm font-semibold mb-3">常用工具</h4>
        <div className="grid grid-cols-3 gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-8 p-0 flex flex-col items-center justify-center"
            onClick={() => {
              console.log('刷新数据')
              // 实现：刷新所有Widget数据
            }}
          >
            <RefreshCw className="h-3 w-3" />
            <span className="text-xs">刷新</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 p-0 flex flex-col items-center justify-center"
            onClick={() => {
              console.log('全屏模式')
              // 实现：切换全屏
            }}
          >
            <Square className="h-3 w-3" />
            <span className="text-xs">全屏</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 p-0 flex flex-col items-center justify-center"
            onClick={() => {
              console.log('截图保存')
              // 实现：保存当前截图
            }}
          >
            <Download className="h-3 w-3" />
            <span className="text-xs">截图</span>
          </Button>
        </div>
      </div>

      {/* 快捷提示 */}
      <div className="p-3 bg-blue-50 dark:bg-blue-950 rounded-lg">
        <div className="flex items-start space-x-2">
          <Rocket className="h-4 w-4 text-blue-600 mt-0.5" />
          <div>
            <p className="text-xs font-medium text-blue-800 dark:text-blue-200">
              提示：拖拽Widget边缘可调整大小
            </p>
            <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
              按住Shift键可多选Widget进行批量操作
            </p>
          </div>
        </div>
      </div>

      {/* 导出对话框 */}
      <Dialog open={isExportDialogOpen} onOpenChange={setIsExportDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>导出配置</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">导出格式</label>
              <div className="grid grid-cols-1 gap-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    // 实现JSON导出
                    const config = {
                      widgets: [],
                      layout: {},
                      timestamp: new Date().toISOString()
                    }
                    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' })
                    const url = URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url
                    a.download = 'dashboard-config.json'
                    a.click()
                    URL.revokeObjectURL(url)
                    setIsExportDialogOpen(false)
                  }}
                >
                  <FileText className="mr-2 h-4 w-4" />
                  JSON格式
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    // 实现图片导出
                    setIsExportDialogOpen(false)
                  }}
                >
                  <Copy className="mr-2 h-4 w-4" />
                  图片格式
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">包含数据</label>
              <div className="space-y-1">
                <label className="flex items-center space-x-2 text-sm">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="rounded"
                  />
                  <span>布局配置</span>
                </label>
                <label className="flex items-center space-x-2 text-sm">
                  <input
                    type="checkbox"
                    defaultChecked={true}
                    className="rounded"
                  />
                  <span>Widget设置</span>
                </label>
                <label className="flex items-center space-x-2 text-sm">
                  <input
                    type="checkbox"
                    className="rounded"
                  />
                  <span>用户数据</span>
                </label>
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-2">
            <Button
              variant="outline"
              onClick={() => setIsExportDialogOpen(false)}
            >
              取消
            </Button>
            <Button
              onClick={() => {
                console.log('执行导出')
                setIsExportDialogOpen(false)
              }}
            >
              导出
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default QuickActions