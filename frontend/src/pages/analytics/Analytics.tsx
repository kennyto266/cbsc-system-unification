import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import type { SelectOption } from '@/components/ui/select'
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart as PieChartIcon,
  Activity,
  LineChart as LineChartIcon,
} from 'lucide-react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { PageTemplate, StatCard } from '../../components/layout/PageTemplate'

// Time range options
const TIME_RANGE_OPTIONS: SelectOption[] = [
  { value: '1W', label: '1周' },
  { value: '1M', label: '1月' },
  { value: '3M', label: '3月' },
  { value: '6M', label: '6月' },
  { value: '1Y', label: '1年' },
]

// Mock data for charts
const performanceData = [
  { month: '1月', 收益率: 2.5, 基准: 1.2 },
  { month: '2月', 收益率: 1.8, 基准: 0.8 },
  { month: '3月', 收益率: 3.2, 基准: 1.5 },
  { month: '4月', 收益率: -1.2, 基準: -0.5 },
  { month: '5月', 收益率: 2.8, 基準: 1.1 },
  { month: '6月', 收益率: 4.1, 基準: 1.8 },
]

const sectorData = [
  { name: '科技', value: 35, color: '#06b6d4' },
  { name: '金融', value: 25, color: '#10b981' },
  { name: '医疗', value: 20, color: '#f59e0b' },
  { name: '消费', value: 12, color: '#f43f5e' },
  { name: '其他', value: 8, color: '#8b5cf6' },
]

const volumeData = [
  { date: '01/15', 成交量: 4500 },
  { date: '01/16', 成交量: 5200 },
  { date: '01/17', 成交量: 3800 },
  { date: '01/18', 成交量: 6100 },
  { date: '01/19', 成交量: 4900 },
  { date: '01/22', 成交量: 5800 },
  { date: '01/23', 成交量: 4200 },
]

export default function Analytics() {
  const [timeRange, setTimeRange] = useState('1M')

  return (
    <PageTemplate
      title="數據分析"
      description="策略表現分析和市場數據"
      icon={BarChart3}
      headerActions={
        <Select
          options={TIME_RANGE_OPTIONS}
          value={timeRange}
          onChange={setTimeRange}
          size="sm"
          fullWidth={false}
          className="w-[120px]"
        />
      }
    >
      {/* Custom styles for Recharts */}
      <style>{`
        .recharts-text {
          fill: #94a3b8 !important;
        }
        .recharts-tooltip-content {
          background: #1e293b !important;
          border: 1px solid #334155 !important;
          border-radius: 8px !important;
        }
        .recharts-tooltip-wrapper {
          outline: none !important;
        }
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300" style={{ animation: `fadeInUp 0.5s ease-out 0ms both` }}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">總收益率</span>
            <TrendingUp className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-bold font-['JetBrains_Mono'] text-emerald-400">+12.8%</div>
          <p className="text-xs text-slate-500 mt-1">vs 基準 +6.5%</p>
        </div>

        <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300" style={{ animation: `fadeInUp 0.5s ease-out 50ms both` }}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">夏普比率</span>
            <Activity className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-bold font-['JetBrains_Mono']">1.85</div>
          <p className="text-xs text-slate-500 mt-1">風險調整後收益</p>
        </div>

        <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300" style={{ animation: `fadeInUp 0.5s ease-out 100ms both` }}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">最大回撤</span>
            <TrendingDown className="h-4 w-4 text-rose-400" />
          </div>
          <div className="text-3xl font-bold font-['JetBrains_Mono'] text-rose-400">-8.2%</div>
          <p className="text-xs text-slate-500 mt-1">發生在 4月</p>
        </div>

        <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300" style={{ animation: `fadeInUp 0.5s ease-out 150ms both` }}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">勝率</span>
            <BarChart3 className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-bold font-['JetBrains_Mono']">62.5%</div>
          <p className="text-xs text-slate-500 mt-1">總交易次數: 120</p>
        </div>
      </div>

      {/* Charts */}
      <Tabs defaultValue="performance" className="space-y-4">
        <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-2 backdrop-blur-sm">
          <TabsList className="bg-slate-800/50">
            <TabsTrigger value="performance" className="data-[state=active]:bg-slate-700 data-[state=active]:text-cyan-400">收益率分析</TabsTrigger>
            <TabsTrigger value="sector" className="data-[state=active]:bg-slate-700 data-[state=active]:text-cyan-400">行業分布</TabsTrigger>
            <TabsTrigger value="volume" className="data-[state=active]:bg-slate-700 data-[state=active]:text-cyan-400">交易量</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="performance" className="space-y-4">
          <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm" style={{ animation: `fadeInUp 0.5s ease-out 200ms both` }}>
            <div className="flex items-center gap-3 mb-4">
              <LineChartIcon className="h-5 w-5 text-cyan-400" />
              <h3 className="text-lg font-semibold text-slate-100">策略 vs 基準表現</h3>
            </div>
            <p className="text-slate-400 text-sm mb-6">策略收益率與基準收益率對比</p>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="month" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="收益率"
                  stroke="#06b6d4"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="基準"
                  stroke="#64748b"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </TabsContent>

        <TabsContent value="sector" className="space-y-4">
          <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm" style={{ animation: `fadeInUp 0.5s ease-out 200ms both` }}>
            <div className="flex items-center gap-3 mb-4">
              <PieChartIcon className="h-5 w-5 text-cyan-400" />
              <h3 className="text-lg font-semibold text-slate-100">行業配置分布</h3>
            </div>
            <p className="text-slate-400 text-sm mb-6">投資組合各行業權重分布</p>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={sectorData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {sectorData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex flex-wrap gap-4 mt-4 justify-center">
              {sectorData.map((sector) => (
                <div key={sector.name} className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded"
                    style={{ backgroundColor: sector.color }}
                  />
                  <span className="text-sm text-slate-300">{sector.name}: {sector.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="volume" className="space-y-4">
          <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm" style={{ animation: `fadeInUp 0.5s ease-out 200ms both` }}>
            <div className="flex items-center gap-3 mb-4">
              <BarChart3 className="h-5 w-5 text-cyan-400" />
              <h3 className="text-lg font-semibold text-slate-100">每日交易量</h3>
            </div>
            <p className="text-slate-400 text-sm mb-6">最近7個交易日成交量統計</p>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={volumeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                />
                <Legend />
                <Bar dataKey="成交量" fill="#06b6d4" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </TabsContent>
      </Tabs>

      {/* Additional Metrics */}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300" style={{ animation: `fadeInUp 0.5s ease-out 300ms both` }}>
          <div className="flex items-center gap-3 mb-4">
            <Activity className="h-5 w-5 text-cyan-400" />
            <h3 className="text-lg font-semibold text-slate-100">風險指標</h3>
          </div>
          <p className="text-slate-400 text-sm mb-4">組合風險度量</p>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-slate-400">波動率</span>
              <span className="font-medium text-slate-100 font-['JetBrains_Mono']">15.2%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-slate-400">Beta</span>
              <span className="font-medium text-slate-100 font-['JetBrains_Mono']">0.95</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-slate-400">VaR (95%)</span>
              <span className="font-medium text-rose-400 font-['JetBrains_Mono']">-2.8%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-slate-400">信息比率</span>
              <span className="font-medium text-slate-100 font-['JetBrains_Mono']">1.42</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300" style={{ animation: `fadeInUp 0.5s ease-out 350ms both` }}>
          <div className="flex items-center gap-3 mb-4">
            <BarChart3 className="h-5 w-5 text-cyan-400" />
            <h3 className="text-lg font-semibold text-slate-100">交易統計</h3>
          </div>
          <p className="text-slate-400 text-sm mb-4">策略交易活動統計</p>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-slate-400">總交易次數</span>
              <span className="font-medium text-slate-100 font-['JetBrains_Mono']">120</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-slate-400">盈利交易</span>
              <span className="font-medium text-emerald-400 font-['JetBrains_Mono']">75 (62.5%)</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-slate-400">平均收益</span>
              <span className="font-medium text-emerald-400 font-['JetBrains_Mono']">+2.1%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-slate-400">平均虧損</span>
              <span className="font-medium text-rose-400 font-['JetBrains_Mono']">-1.6%</span>
            </div>
          </div>
        </div>
      </div>
    </PageTemplate>
  )
}
