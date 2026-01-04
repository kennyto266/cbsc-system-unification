import { useState } from 'react'
import {
  useGetPortfolioSummaryQuery,
  useGetPortfolioHoldingsQuery,
  useGetPortfolioRiskQuery,
  useGetPortfolioDiversificationQuery,
  useGetPortfolioPerformanceQuery,
} from '../../api/endpoints/portfolioApi'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select } from '@/components/ui/select'
import type { SelectOption } from '@/components/ui/select'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  PieChart,
  Shield,
  BarChart3,
  RefreshCw,
  Wallet,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { PageTemplate } from '../../components/layout/PageTemplate'

// Format number as currency
const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2,
  }).format(value)
}

// Format percentage
const formatPercent = (value: number) => {
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

// Period options for performance chart
const PERIOD_OPTIONS: SelectOption[] = [
  { value: '1D', label: '1天' },
  { value: '1W', label: '1周' },
  { value: '1M', label: '1月' },
  { value: '3M', label: '3月' },
  { value: '6M', label: '6月' },
  { value: '1Y', label: '1年' },
  { value: 'ALL', label: '全部' },
]

export default function Portfolio() {
  const [period, setPeriod] = useState<'1D' | '1W' | '1M' | '3M' | '6M' | '1Y' | 'ALL'>('1M')

  // Queries
  const {
    data: summary,
    isLoading: summaryLoading,
    error: summaryError,
    refetch: refetchSummary,
  } = useGetPortfolioSummaryQuery()

  const {
    data: holdings = [],
    isLoading: holdingsLoading,
    error: holdingsError,
    refetch: refetchHoldings,
  } = useGetPortfolioHoldingsQuery()

  const {
    data: risk,
    isLoading: riskLoading,
  } = useGetPortfolioRiskQuery()

  const {
    data: diversification,
    isLoading: diversificationLoading,
  } = useGetPortfolioDiversificationQuery()

  const {
    data: performanceHistory = [],
    isLoading: performanceLoading,
  } = useGetPortfolioPerformanceQuery({ period })

  const handleRefresh = () => {
    refetchSummary()
    refetchHoldings()
  }

  return (
    <PageTemplate
      title="投资组合"
      description="查看和管理您的投资组合"
      icon={Wallet}
      headerActions={
        <Button onClick={handleRefresh} variant="outline" size="icon" className="border-slate-700 text-slate-100 hover:bg-slate-800">
          <RefreshCw className="h-4 w-4" />
        </Button>
      }
    >
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300">
          <div className="flex flex-row items-center justify-between space-y-0 pb-2">
            <div className="text-sm font-medium text-slate-400">总资产</div>
            <DollarSign className="h-4 w-4 text-slate-400" />
          </div>
          <div>
            {summaryLoading ? (
              <div className="animate-pulse h-8 bg-slate-950/50 rounded" />
            ) : (
              <>
                <div className="text-2xl font-bold font-['JetBrains_Mono'] text-slate-100">
                  {summary ? formatCurrency(summary.totalValue) : '-'}
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  总成本: {summary ? formatCurrency(summary.totalCost) : '-'}
                </p>
              </>
            )}
          </div>
        </div>

        <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300">
          <div className="flex flex-row items-center justify-between space-y-0 pb-2">
            <div className="text-sm font-medium text-slate-400">总盈亏</div>
            {summary && summary.totalPnL >= 0 ? (
              <TrendingUp className="h-4 w-4 text-emerald-400" />
            ) : (
              <TrendingDown className="h-4 w-4 text-rose-400" />
            )}
          </div>
          <div>
            {summaryLoading ? (
              <div className="animate-pulse h-8 bg-slate-950/50 rounded" />
            ) : (
              <>
                <div className={`text-2xl font-bold font-['JetBrains_Mono'] ${summary && summary.totalPnL >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {summary ? formatCurrency(summary.totalPnL) : '-'}
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  {summary ? formatPercent(summary.totalPnLPercent) : '-'}
                </p>
              </>
            )}
          </div>
        </div>

        <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300">
          <div className="flex flex-row items-center justify-between space-y-0 pb-2">
            <div className="text-sm font-medium text-slate-400">今日涨跌</div>
            {summary && summary.dailyChange >= 0 ? (
              <TrendingUp className="h-4 w-4 text-emerald-400" />
            ) : (
              <TrendingDown className="h-4 w-4 text-rose-400" />
            )}
          </div>
          <div>
            {summaryLoading ? (
              <div className="animate-pulse h-8 bg-slate-950/50 rounded" />
            ) : (
              <>
                <div className={`text-2xl font-bold font-['JetBrains_Mono'] ${summary && summary.dailyChange >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {summary ? formatCurrency(summary.dailyChange) : '-'}
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  {summary ? formatPercent(summary.dailyChangePercent) : '-'}
                </p>
              </>
            )}
          </div>
        </div>

        <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300">
          <div className="flex flex-row items-center justify-between space-y-0 pb-2">
            <div className="text-sm font-medium text-slate-400">持仓数量</div>
            <PieChart className="h-4 w-4 text-slate-400" />
          </div>
          <div>
            {summaryLoading ? (
              <div className="animate-pulse h-8 bg-slate-950/50 rounded" />
            ) : (
              <>
                <div className="text-2xl font-bold font-['JetBrains_Mono'] text-slate-100">
                  {summary?.holdingsCount || 0}
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  现金: {summary ? formatPercent(summary.cashPercent) : '-'}
                </p>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="holdings" className="space-y-4">
        <TabsList>
          <TabsTrigger value="holdings">持仓列表</TabsTrigger>
          <TabsTrigger value="risk">风险分析</TabsTrigger>
          <TabsTrigger value="diversification">分散化</TabsTrigger>
          <TabsTrigger value="performance">历史表现</TabsTrigger>
        </TabsList>

        <TabsContent value="holdings" className="space-y-4">
          <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300">
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-slate-100">持仓详情</h3>
              <p className="text-sm text-slate-400 mt-1">
                {holdingsError ? (
                  <span className="text-rose-400">加载失败</span>
                ) : (
                  `共 ${holdings.length} 个持仓`
                )}
              </p>
            </div>
            <div>
              {holdingsLoading ? (
                <div className="flex items-center justify-center h-64">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
                </div>
              ) : holdings.length === 0 ? (
                <div className="text-center py-12">
                  <PieChart className="mx-auto h-12 w-12 text-slate-500 opacity-50" />
                  <p className="mt-4 text-slate-400">暂无持仓</p>
                </div>
              ) : (
                <div className="rounded-md border border-slate-800/50">
                  <Table>
                    <TableHeader>
                      <TableRow className="hover:bg-slate-800/50 border-slate-800/50">
                        <TableHead className="text-slate-100">代码</TableHead>
                        <TableHead className="text-slate-100">名称</TableHead>
                        <TableHead className="text-right text-slate-100">持仓数量</TableHead>
                        <TableHead className="text-right text-slate-100">持仓成本</TableHead>
                        <TableHead className="text-right text-slate-100">当前市值</TableHead>
                        <TableHead className="text-right text-slate-100">盈亏</TableHead>
                        <TableHead className="text-right text-slate-100">权重</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {holdings.map((holding) => (
                        <TableRow key={holding.symbol} className="hover:bg-slate-800/30 border-slate-800/50">
                          <TableCell className="font-medium text-slate-100">{holding.symbol}</TableCell>
                          <TableCell className="text-slate-100">{holding.name}</TableCell>
                          <TableCell className="text-right text-slate-100">{holding.quantity}</TableCell>
                          <TableCell className="text-right font-['JetBrains_Mono'] text-slate-100">
                            {formatCurrency(holding.averageCost)}
                          </TableCell>
                          <TableCell className="text-right font-['JetBrains_Mono'] text-slate-100">
                            {formatCurrency(holding.marketValue)}
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex flex-col items-end">
                              <span className={`font-['JetBrains_Mono'] ${holding.unrealizedPnL >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                {formatCurrency(holding.unrealizedPnL)}
                              </span>
                              <span className={`text-xs font-['JetBrains_Mono'] ${holding.unrealizedPnLPercent >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                {formatPercent(holding.unrealizedPnLPercent)}
                              </span>
                            </div>
                          </TableCell>
                          <TableCell className="text-right font-['JetBrains_Mono'] text-slate-100">
                            {formatPercent(holding.weight)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="risk" className="space-y-4">
          <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300">
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
                <Shield className="h-5 w-5 text-cyan-400" />
                风险指标
              </h3>
              <p className="text-sm text-slate-400 mt-1">投资组合风险分析指标</p>
            </div>
            <div>
              {riskLoading ? (
                <div className="flex items-center justify-center h-64">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
                </div>
              ) : risk ? (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  <div className="space-y-2">
                    <p className="text-sm text-slate-400">波动率</p>
                    <p className="text-2xl font-bold font-['JetBrains_Mono'] text-slate-100">{formatPercent(risk.volatility)}</p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm text-slate-400">Beta</p>
                    <p className="text-2xl font-bold font-['JetBrains_Mono'] text-slate-100">{risk.beta.toFixed(2)}</p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm text-slate-400">VaR (95%)</p>
                    <p className="text-2xl font-bold font-['JetBrains_Mono'] text-slate-100">{formatPercent(risk.var)}</p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm text-slate-400">CVaR</p>
                    <p className="text-2xl font-bold font-['JetBrains_Mono'] text-slate-100">{formatPercent(risk.cvar)}</p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm text-slate-400">最大回撤</p>
                    <p className="text-2xl font-bold font-['JetBrains_Mono'] text-rose-400">{formatPercent(risk.maxDrawdown)}</p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm text-slate-400">夏普比率</p>
                    <p className="text-2xl font-bold font-['JetBrains_Mono'] text-slate-100">{risk.sharpeRatio.toFixed(2)}</p>
                  </div>
                </div>
              ) : (
                <p className="text-center text-slate-400 py-12">暂无风险数据</p>
              )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="diversification" className="space-y-4">
          <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300">
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-slate-100">分散化分析</h3>
              <p className="text-sm text-slate-400 mt-1">投资组合分散化程度分析</p>
            </div>
            <div>
              {diversificationLoading ? (
                <div className="flex items-center justify-center h-64">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
                </div>
              ) : diversification ? (
                <div className="space-y-6">
                  <div>
                    <h4 className="font-medium text-slate-100 mb-3">行业分布</h4>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(diversification.sectors).map(([sector, weight]) => (
                        <Badge key={sector} variant="secondary" className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20">
                          {sector}: {formatPercent(weight)}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium text-slate-100 mb-3">资产类别</h4>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(diversification.assetClasses).map(([assetClass, weight]) => (
                        <Badge key={assetClass} variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
                          {assetClass}: {formatPercent(weight)}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium text-slate-100 mb-3">集中度</h4>
                    <p className="text-2xl font-bold font-['JetBrains_Mono'] text-slate-100">{formatPercent(diversification.concentration)}</p>
                  </div>
                </div>
              ) : (
                <p className="text-center text-slate-400 py-12">暂无分散化数据</p>
              )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-cyan-400" />
                  历史表现
                </h3>
                <p className="text-sm text-slate-400 mt-1">投资组合历史表现数据</p>
              </div>
              <Select
                options={PERIOD_OPTIONS}
                value={period}
                onChange={setPeriod}
                size="sm"
                fullWidth={false}
                className="w-[120px]"
              />
            </div>
            <div>
              {performanceLoading ? (
                <div className="flex items-center justify-center h-64">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
                </div>
              ) : performanceHistory.length > 0 ? (
                <div className="rounded-md border border-slate-800/50">
                  <Table>
                    <TableHeader>
                      <TableRow className="hover:bg-slate-800/50 border-slate-800/50">
                        <TableHead className="text-slate-100">日期</TableHead>
                        <TableHead className="text-right text-slate-100">组合价值</TableHead>
                        <TableHead className="text-right text-slate-100">收益率</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {performanceHistory.slice().reverse().map((item, index) => (
                        <TableRow key={index} className="hover:bg-slate-800/30 border-slate-800/50">
                          <TableCell className="text-slate-100">{item.date}</TableCell>
                          <TableCell className="text-right font-['JetBrains_Mono'] text-slate-100">
                            {formatCurrency(item.value)}
                          </TableCell>
                          <TableCell className={`text-right font-['JetBrains_Mono'] ${item.returns >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {formatPercent(item.returns)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <p className="text-center text-slate-400 py-12">暂无表现数据</p>
              )}
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {/* Last Update */}
      <p className="text-sm text-slate-400 text-center">
        最后更新: {summary?.lastUpdate ? formatDistanceToNow(new Date(summary.lastUpdate), {
          addSuffix: true,
          locale: zhCN,
        }) : '未知'}
      </p>
    </PageTemplate>
  )
}
