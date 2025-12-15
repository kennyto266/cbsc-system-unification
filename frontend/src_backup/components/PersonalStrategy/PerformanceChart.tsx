import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { UserPortfolio } from '../../types/index';
import { Card } from '../ui/Card';

interface PerformanceChartProps {
  portfolio: UserPortfolio | null;
  timeRange: '1d' | '1w' | '1m' | '3m';
}

export const PerformanceChart: React.FC<PerformanceChartProps> = ({
  portfolio,
  timeRange
}) => {
  // Generate mock data for demonstration
  const chartData = useMemo(() => {
    if (!portfolio?.performanceHistory) {
      // Generate mock data
      const dataPoints = timeRange === '1d' ? 24 : timeRange === '1w' ? 7 : timeRange === '1m' ? 30 : 90;
      const baseValue = portfolio?.totalValue || 100000;

      return Array.from({ length: dataPoints }, (_, i) => {
        const date = new Date();
        date.setHours(date.getHours() - (dataPoints - i) * (timeRange === '1d' ? 1 : 24));

        const randomReturn = (Math.random() - 0.3) * 0.02; // -0.6% to +1.4% daily
        const value = baseValue * (1 + randomReturn * i / dataPoints);

        return {
          date: date.toISOString().split('T')[0],
          portfolioValue: value,
          dailyReturn: i > 0 ? ((value - chartData?.[i - 1]?.portfolioValue || baseValue) / chartData?.[i - 1]?.portfolioValue || baseValue) * 100 : 0,
          cumulativeReturn: ((value - baseValue) / baseValue) * 100
        };
      });
    }

    return portfolio.performanceHistory.map(snapshot => ({
      date: snapshot.date.toISOString().split('T')[0],
      portfolioValue: snapshot.totalValue,
      dailyReturn: snapshot.dailyReturn * 100,
      cumulativeReturn: snapshot.cumulativeReturn * 100
    }));
  }, [portfolio, timeRange]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    if (timeRange === '1d') {
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    }
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border border-neutral-200">
          <p className="text-sm font-medium text-neutral-900 mb-2">
            {formatDate(label)}
          </p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.name === '投资组合价值'
                ? formatCurrency(entry.value)
                : `${entry.value.toFixed(2)}%`
              }
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const totalReturn = chartData.length > 0 ? chartData[chartData.length - 1].cumulativeReturn : 0;
  const maxValue = Math.max(...chartData.map(d => d.portfolioValue));
  const minValue = Math.min(...chartData.map(d => d.portfolioValue));

  return (
    <Card className="p-6">
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold text-neutral-900 mb-1">投资组合表现</h3>
            <p className="text-sm text-neutral-600">跟踪您的投资组合价值变化</p>
          </div>
          <div className="text-right">
            <div className={`text-2xl font-bold ${
              totalReturn >= 0 ? 'text-success-600' : 'text-error-600'
            }`}>
              {totalReturn >= 0 ? '+' : ''}{totalReturn.toFixed(2)}%
            </div>
            <div className="text-sm text-neutral-600">总收益率</div>
          </div>
        </div>
      </div>

      {/* Main Portfolio Value Chart */}
      <div className="mb-8">
        <h4 className="text-sm font-medium text-neutral-700 mb-3">投资组合价值</h4>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorPortfolio" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              stroke="#6b7280"
              fontSize={12}
            />
            <YAxis
              tickFormatter={formatCurrency}
              stroke="#6b7280"
              fontSize={12}
              domain={[minValue * 0.99, maxValue * 1.01]}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="portfolioValue"
              stroke="#3b82f6"
              strokeWidth={2}
              fill="url(#colorPortfolio)"
              name="投资组合价值"
            />
            <ReferenceLine
              y={chartData[0]?.portfolioValue}
              stroke="#9ca3af"
              strokeDasharray="3 3"
              label="初始价值"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Daily Returns Chart */}
      <div>
        <h4 className="text-sm font-medium text-neutral-700 mb-3">日收益率</h4>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              stroke="#6b7280"
              fontSize={12}
            />
            <YAxis
              tickFormatter={(value) => `${value.toFixed(1)}%`}
              stroke="#6b7280"
              fontSize={12}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="dailyReturn"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
              name="日收益率"
            />
            <ReferenceLine y={0} stroke="#9ca3af" strokeDasharray="3 3" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Chart Statistics */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <div className="text-sm text-neutral-600 mb-1">最高值</div>
          <div className="font-semibold text-neutral-900">
            {formatCurrency(maxValue)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-sm text-neutral-600 mb-1">最低值</div>
          <div className="font-semibold text-neutral-900">
            {formatCurrency(minValue)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-sm text-neutral-600 mb-1">波动率</div>
          <div className="font-semibold text-neutral-900">
            {portfolio?.riskMetrics.volatility
              ? `${(portfolio.riskMetrics.volatility * 100).toFixed(2)}%`
              : '--'
            }
          </div>
        </div>
        <div className="text-center">
          <div className="text-sm text-neutral-600 mb-1">数据点</div>
          <div className="font-semibold text-neutral-900">
            {chartData.length}
          </div>
        </div>
      </div>
    </Card>
  );
};