import React, { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Play,
  Pause,
  Square,
  Edit,
  Trash2,
  MoreVertical,
  TrendingUp,
  TrendingDown,
  Eye,
  Copy,
  Download,
  Settings
} from 'lucide-react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/table'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { Badge } from '../../components/ui/badge'
import { Avatar, AvatarFallback, AvatarImage } from '../../components/ui/avatar'
import { Progress } from '../../components/ui/progress'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../../components/ui/dropdown-menu'
import { Grid } from '../square-ui/Grid'
import { MetricCard } from '../square-ui/MetricCard'
import { cn } from '../../lib/utils'
import { Strategy, StrategyStatus } from '../../types'

interface StrategyListModernProps {
  strategies: Strategy[]
  onStrategySelect: (strategy: Strategy) => void
  onStrategyEdit: (strategy: Strategy) => void
  onStrategyCreate: () => void
  viewMode: 'table' | 'card'
  isLoading?: boolean
}

const statusConfig = {
  active: {
    label: '运行中',
    color: 'bg-green-500',
    textColor: 'text-green-700',
    bgColor: 'bg-green-50',
    icon: Play
  },
  testing: {
    label: '测试中',
    color: 'bg-orange-500',
    textColor: 'text-orange-700',
    bgColor: 'bg-orange-50',
    icon: Settings
  },
  inactive: {
    label: '已暂停',
    color: 'bg-gray-500',
    textColor: 'text-gray-700',
    bgColor: 'bg-gray-50',
    icon: Pause
  },
  stopped: {
    label: '已停止',
    color: 'bg-red-500',
    textColor: 'text-red-700',
    bgColor: 'bg-red-50',
    icon: Square
  }
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2
  }).format(value)
}

const formatPercent = (value: number) => {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

const StrategyCard: React.FC<{
  strategy: Strategy
  onSelect: (strategy: Strategy) => void
  onEdit: (strategy: Strategy) => void
}> = ({ strategy, onSelect, onEdit }) => {
  const status = statusConfig[strategy.status as StrategyStatus]
  const StatusIcon = status.icon

  return (
    <motion.div
      whileHover={{ y: -4, boxShadow: '0 10px 30px rgba(0,0,0,0.1)' }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
    >
      <Card className="cursor-pointer overflow-hidden">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-3">
              <Avatar className="h-10 w-10">
                <AvatarImage src={strategy.avatar} />
                <AvatarFallback>{strategy.name.slice(0, 2).toUpperCase()}</AvatarFallback>
              </Avatar>
              <div>
                <CardTitle className="text-lg">{strategy.name}</CardTitle>
                <CardDescription className="text-sm">
                  {strategy.description || '暂无描述'}
                </CardDescription>
              </div>
            </div>
            <Badge className={cn(status.textColor, status.bgColor)}>
              <StatusIcon className="mr-1 h-3 w-3" />
              {status.label}
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Performance Metrics */}
          <Grid cols={{ xs: 2, sm: 3 }} gap={3}>
            <MetricCard
              title="总收益"
              value={formatPercent(strategy.totalReturn || 0)}
              icon={strategy.totalReturn && strategy.totalReturn > 0 ? TrendingUp : TrendingDown}
              trend={formatPercent(strategy.weeklyReturn || 0)}
              trendUp={!!strategy.weeklyReturn && strategy.weeklyReturn > 0}
              valueClassName={cn(
                strategy.totalReturn && strategy.totalReturn > 0 ? 'text-green-600' : 'text-red-600'
              )}
              className="p-3"
            />
            <MetricCard
              title="夏普比率"
              value={(strategy.sharpeRatio || 0).toFixed(2)}
              icon={TrendingUp}
              valueClassName={cn(
                (strategy.sharpeRatio || 0) > 1 ? 'text-green-600' : 'text-orange-600'
              )}
              className="p-3"
            />
            <MetricCard
              title="最大回撤"
              value={formatPercent(strategy.maxDrawdown || 0)}
              icon={TrendingDown}
              trend={formatPercent(-(strategy.dailyReturn || 0))}
              trendUp={!(strategy.dailyReturn || 0) || strategy.dailyReturn > 0}
              valueClassName="text-red-600"
              className="p-3"
            />
          </Grid>

          {/* Risk Metrics */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">风险等级</span>
              <Badge variant={strategy.riskLevel === 'low' ? 'secondary' :
                           strategy.riskLevel === 'medium' ? 'default' : 'destructive'}>
                {strategy.riskLevel === 'low' ? '低风险' :
                 strategy.riskLevel === 'medium' ? '中风险' : '高风险'}
              </Badge>
            </div>
            <Progress
              value={strategy.riskLevel === 'low' ? 30 : strategy.riskLevel === 'medium' ? 60 : 90}
              className="h-2"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-2">
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation()
                  onEdit(strategy)
                }}
              >
                <Edit className="mr-2 h-3 w-3" />
                编辑
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation()
                  onSelect(strategy)
                }}
              >
                <Eye className="mr-2 h-3 w-3" />
                详情
              </Button>
            </div>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => e.stopPropagation()}
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem>
                  <Copy className="mr-2 h-4 w-4" />
                  复制策略
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Download className="mr-2 h-4 w-4" />
                  导出数据
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-red-600">
                  <Trash2 className="mr-2 h-4 w-4" />
                  删除策略
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

const StrategyListModern: React.FC<StrategyListModernProps> = ({
  strategies,
  onStrategySelect,
  onStrategyEdit,
  viewMode,
  isLoading
}) => {
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([])

  // Filter and sort strategies
  const sortedStrategies = useMemo(() => {
    return [...strategies].sort((a, b) => {
      // Sort by status priority first (active > testing > inactive > stopped)
      const statusPriority = {
        active: 0,
        testing: 1,
        inactive: 2,
        stopped: 3
      }
      const aPriority = statusPriority[a.status as StrategyStatus] ?? 4
      const bPriority = statusPriority[b.status as StrategyStatus] ?? 4

      if (aPriority !== bPriority) {
        return aPriority - bPriority
      }

      // Then sort by name
      return a.name.localeCompare(b.name)
    })
  }, [strategies])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        >
          <Settings className="h-8 w-8 text-primary" />
        </motion.div>
      </div>
    )
  }

  if (viewMode === 'card') {
    return (
      <AnimatePresence>
        <Grid cols={{ xs: 1, md: 2, xl: 3 }} gap={6}>
          {sortedStrategies.map((strategy) => (
            <motion.div
              key={strategy.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.2 }}
              layout
            >
              <StrategyCard
                strategy={strategy}
                onSelect={onStrategySelect}
                onEdit={onStrategyEdit}
              />
            </motion.div>
          ))}
        </Grid>
      </AnimatePresence>
    )
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>策略名称</TableHead>
            <TableHead>状态</TableHead>
            <TableHead>总收益</TableHead>
            <TableHead>夏普比率</TableHead>
            <TableHead>最大回撤</TableHead>
            <TableHead>风险等级</TableHead>
            <TableHead>创建时间</TableHead>
            <TableHead className="w-[100px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <AnimatePresence>
            {sortedStrategies.map((strategy, index) => {
              const status = statusConfig[strategy.status as StrategyStatus]
              const StatusIcon = status.icon

              return (
                <motion.tr
                  key={strategy.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.2, delay: index * 0.05 }}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => onStrategySelect(strategy)}
                >
                  <TableCell>
                    <div className="flex items-center space-x-3">
                      <Avatar className="h-8 w-8">
                        <AvatarImage src={strategy.avatar} />
                        <AvatarFallback className="text-xs">
                          {strategy.name.slice(0, 2).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <div className="font-medium">{strategy.name}</div>
                        <div className="text-sm text-muted-foreground line-clamp-1">
                          {strategy.description || '暂无描述'}
                        </div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className={cn(status.textColor, status.bgColor)}>
                      <StatusIcon className="mr-1 h-3 w-3" />
                      {status.label}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className={cn(
                      'font-medium',
                      (strategy.totalReturn || 0) > 0 ? 'text-green-600' : 'text-red-600'
                    )}>
                      {formatPercent(strategy.totalReturn || 0)}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className={cn(
                      'font-medium',
                      (strategy.sharpeRatio || 0) > 1 ? 'text-green-600' :
                      (strategy.sharpeRatio || 0) > 0 ? 'text-orange-600' : 'text-red-600'
                    )}>
                      {(strategy.sharpeRatio || 0).toFixed(2)}
                    </div>
                  </TableCell>
                  <TableCell className="text-red-600 font-medium">
                    {formatPercent(strategy.maxDrawdown || 0)}
                  </TableCell>
                  <TableCell>
                    <Badge variant={strategy.riskLevel === 'low' ? 'secondary' :
                                   strategy.riskLevel === 'medium' ? 'default' : 'destructive'}>
                      {strategy.riskLevel === 'low' ? '低' :
                       strategy.riskLevel === 'medium' ? '中' : '高'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {new Date(strategy.createdAt).toLocaleDateString('zh-CN')}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          onStrategyEdit(strategy)
                        }}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>
                            <Copy className="mr-2 h-4 w-4" />
                            复制
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Download className="mr-2 h-4 w-4" />
                            导出
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem className="text-red-600">
                            <Trash2 className="mr-2 h-4 w-4" />
                            删除
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </TableCell>
                </motion.tr>
              )
            })}
          </AnimatePresence>
        </TableBody>
      </Table>
    </div>
  )
}

export default StrategyListModern