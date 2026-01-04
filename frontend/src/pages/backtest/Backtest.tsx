import { useState } from 'react'
import {
  useListBacktestsQuery,
  useCreateBacktestMutation,
  useRunBacktestMutation,
  useStopBacktestMutation,
  useDeleteBacktestMutation,
  useGetBacktestProgressQuery,
} from '../../api/endpoints/backtestApi'
import { type BacktestConfig } from '../../api/endpoints/backtestApi'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import type { SelectOption } from '@/components/ui/select'
import {
  Play,
  Square,
  Trash2,
  Plus,
  RefreshCw,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  FlaskConical,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { PageTemplate } from '../../components/layout/PageTemplate'

const formatPercent = (value: number) => {
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2,
  }).format(value)
}

// Strategy options
const STRATEGY_OPTIONS: SelectOption[] = [
  { value: '1', label: '双均线策略' },
  { value: '2', label: '布林带策略' },
  { value: '3', label: 'MACD策略' },
]

const statusConfig = {
  pending: {
    label: '等待中',
    icon: Clock,
    variant: 'secondary' as const,
  },
  running: {
    label: '运行中',
    icon: Loader2,
    variant: 'default' as const,
  },
  completed: {
    label: '已完成',
    icon: CheckCircle2,
    variant: 'default' as const,
  },
  failed: {
    label: '失败',
    icon: XCircle,
    variant: 'destructive' as const,
  },
}

export default function Backtest() {
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [selectedStrategy, setSelectedStrategy] = useState('')
  const [symbols, setSymbols] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [initialCapital, setInitialCapital] = useState('100000')

  const {
    data: backtests = [],
    isLoading,
    error,
    refetch,
  } = useListBacktestsQuery({})

  const [createBacktest] = useCreateBacktestMutation()
  const [runBacktest] = useRunBacktestMutation()
  const [stopBacktest] = useStopBacktestMutation()
  const [deleteBacktest] = useDeleteBacktestMutation()

  const handleCreateBacktest = async () => {
    try {
      const config: BacktestConfig = {
        strategyId: selectedStrategy,
        symbols: symbols.split(',').map(s => s.trim()),
        startDate,
        endDate,
        initialCapital: parseFloat(initialCapital),
      }
      await createBacktest(config).unwrap()
      setCreateDialogOpen(false)
      setSelectedStrategy('')
      setSymbols('')
      refetch()
    } catch (error) {
      console.error('Failed to create backtest:', error)
    }
  }

  const handleRun = async (id: string) => {
    try {
      await runBacktest(id).unwrap()
      refetch()
    } catch (error) {
      console.error('Failed to run backtest:', error)
    }
  }

  const handleStop = async (id: string) => {
    try {
      await stopBacktest(id).unwrap()
      refetch()
    } catch (error) {
      console.error('Failed to stop backtest:', error)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteBacktest(id).unwrap()
      refetch()
    } catch (error) {
      console.error('Failed to delete backtest:', error)
    }
  }

  return (
    <PageTemplate
      title="回测分析"
      description="创建和管理策略回测任务"
      icon={FlaskConical}
      headerActions={
        <div className="flex gap-2">
          <Button onClick={() => refetch()} variant="outline" size="icon" className="border-slate-700 text-slate-100 hover:bg-slate-800">
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                新建回测
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>创建回测任务</DialogTitle>
                <DialogDescription>
                  配置回测参数并创建新的回测任务
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="strategy">策略</Label>
                  <Select
                    id="strategy"
                    options={STRATEGY_OPTIONS}
                    value={selectedStrategy}
                    onChange={setSelectedStrategy}
                    placeholder="选择策略"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="symbols">交易品种</Label>
                  <Input
                    id="symbols"
                    placeholder="AAPL, MSFT, GOOGL"
                    value={symbols}
                    onChange={(e) => setSymbols(e.target.value)}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="start-date">开始日期</Label>
                    <Input
                      id="start-date"
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="end-date">结束日期</Label>
                    <Input
                      id="end-date"
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="capital">初始资金</Label>
                  <Input
                    id="capital"
                    type="number"
                    value={initialCapital}
                    onChange={(e) => setInitialCapital(e.target.value)}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                  取消
                </Button>
                <Button onClick={handleCreateBacktest} disabled={!selectedStrategy || !symbols}>
                  创建
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      }
    >
      {/* Backtest List */}
      <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-slate-100">回测任务列表</h3>
          <p className="text-sm text-slate-400 mt-1">
            {error ? (
              <span className="text-rose-400">加载失败</span>
            ) : (
              `共 ${backtests.length} 个任务`
            )}
          </p>
        </div>
        <div>
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
            </div>
          ) : backtests.length === 0 ? (
            <div className="text-center py-12">
              <Clock className="mx-auto h-12 w-12 text-slate-500 opacity-50" />
              <p className="mt-4 text-slate-400">暂无回测任务</p>
            </div>
          ) : (
            <div className="rounded-md border border-slate-800/50">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-slate-800/50 border-slate-800/50">
                    <TableHead className="text-slate-100">任务名称</TableHead>
                    <TableHead className="text-slate-100">策略</TableHead>
                    <TableHead className="text-slate-100">交易品种</TableHead>
                    <TableHead className="text-slate-100">状态</TableHead>
                    <TableHead className="text-slate-100">总收益</TableHead>
                    <TableHead className="text-slate-100">夏普比率</TableHead>
                    <TableHead className="text-slate-100">最大回撤</TableHead>
                    <TableHead className="text-slate-100">创建时间</TableHead>
                    <TableHead className="text-right text-slate-100">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {backtests.map((backtest) => {
                    const status = statusConfig[backtest.status as keyof typeof statusConfig] || statusConfig.pending
                    const StatusIcon = status.icon
                    return (
                      <TableRow key={backtest.id} className="hover:bg-slate-800/30 border-slate-800/50">
                        <TableCell className="font-medium text-slate-100">{backtest.name}</TableCell>
                        <TableCell className="text-slate-100">{backtest.strategyId}</TableCell>
                        <TableCell>
                          <div className="flex gap-1">
                            {backtest.symbols.slice(0, 2).map((symbol) => (
                              <Badge key={symbol} variant="outline" className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20">{symbol}</Badge>
                            ))}
                            {backtest.symbols.length > 2 && (
                              <Badge variant="outline" className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20">+{backtest.symbols.length - 2}</Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={status.variant}
                            className={`
                              flex items-center gap-1 w-fit
                              ${status.variant === 'default' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : ''}
                              ${status.variant === 'destructive' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' : ''}
                              ${status.variant === 'secondary' ? 'bg-slate-500/10 text-slate-400 border-slate-500/20' : ''}
                            `}
                          >
                            <StatusIcon className="h-3 w-3" />
                            {status.label}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {backtest.totalReturn !== undefined ? (
                            <span className={`font-['JetBrains_Mono'] ${backtest.totalReturn >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                              {formatPercent(backtest.totalReturn)}
                            </span>
                          ) : '-'}
                        </TableCell>
                        <TableCell>
                          <span className="font-['JetBrains_Mono'] text-slate-100">
                            {backtest.sharpeRatio !== undefined ? backtest.sharpeRatio.toFixed(2) : '-'}
                          </span>
                        </TableCell>
                        <TableCell>
                          {backtest.maxDrawdown !== undefined ? (
                            <span className="font-['JetBrains_Mono'] text-rose-400">{formatPercent(backtest.maxDrawdown)}</span>
                          ) : '-'}
                        </TableCell>
                        <TableCell className="text-sm text-slate-400">
                          {formatDistanceToNow(new Date(backtest.createdAt), {
                            addSuffix: true,
                            locale: zhCN,
                          })}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            {backtest.status === 'running' ? (
                              <Button
                                size="icon"
                                variant="outline"
                                onClick={() => handleStop(backtest.id)}
                                className="border-slate-700 text-slate-100 hover:bg-slate-800"
                              >
                                <Square className="h-4 w-4" />
                              </Button>
                            ) : backtest.status === 'pending' || backtest.status === 'failed' ? (
                              <Button
                                size="icon"
                                variant="outline"
                                onClick={() => handleRun(backtest.id)}
                                className="border-slate-700 text-slate-100 hover:bg-slate-800"
                              >
                                <Play className="h-4 w-4" />
                              </Button>
                            ) : null}
                            <AlertDialog>
                              <AlertDialogTrigger asChild>
                                <Button size="icon" variant="ghost" className="text-slate-100 hover:text-rose-400">
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </AlertDialogTrigger>
                              <AlertDialogContent className="bg-slate-900 border-slate-800">
                                <AlertDialogHeader>
                                  <AlertDialogTitle className="text-slate-100">确认删除</AlertDialogTitle>
                                  <AlertDialogDescription className="text-slate-400">
                                    确定要删除回测任务 <strong>{backtest.name}</strong> 吗？
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel className="text-slate-100">取消</AlertDialogCancel>
                                  <AlertDialogAction
                                    onClick={() => handleDelete(backtest.id)}
                                    className="bg-rose-500 text-white hover:bg-rose-600"
                                  >
                                    删除
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
                          </div>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </div>
      </div>
    </PageTemplate>
  )
}
