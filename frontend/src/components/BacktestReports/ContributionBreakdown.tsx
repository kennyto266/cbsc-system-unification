import React from 'react';
import {
  ChartPieIcon,
  InformationCircleIcon,
  ArrowsRightLeftIcon
} from '@heroicons/react/24/outline';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';

interface ContributionBreakdownProps {
  data: Array<{
    factor: string;
    contribution: number;
    weight: number;
  }>;
  className?: string;
}

const ContributionBreakdown: React.FC<ContributionBreakdownProps> = ({ data, className = '' }) => {
  const formatNumber = (value: number, decimals: number = 2) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${formatNumber(value * 100, 2)}%`;
  };

  // Calculate total contribution for percentage calculation
  const totalContribution = data.reduce((sum, item) => sum + item.contribution, 0);

  // Sort data by contribution (descending)
  const sortedData = [...data].sort((a, b) => b.contribution - a.contribution);

  // Prepare data for charts
  const pieData = sortedData.map(item => ({
    name: item.factor,
    value: item.contribution,
    percentage: (item.contribution / totalContribution) * 100
  }));

  const barData = sortedData.map(item => ({
    name: item.factor,
    contribution: item.contribution * 100,
    weight: item.weight * 100,
    effectiveness: item.weight > 0 ? (item.contribution / item.weight) : 0
  }));

  // Color palette
  const COLORS = [
    '#3B82F6', // blue
    '#10B981', // green
    '#F59E0B', // yellow
    '#EF4444', // red
    '#8B5CF6', // purple
    '#EC4899', // pink
    '#6366F1', // indigo
    '#14B8A6', // teal
    '#F97316', // orange
    '#84CC16'  // lime
  ];

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="text-sm font-medium text-gray-900">{payload[0].payload.name}</p>
          <p className="text-sm text-gray-600">
            Contribution: {formatPercent(payload[0].payload.contribution)}
          </p>
          <p className="text-sm text-gray-600">
            Weight: {formatPercent(payload[0].payload.weight)}
          </p>
          <p className="text-sm text-gray-600">
            Effectiveness: {formatNumber(payload[0].payload.effectiveness, 2)}x
          </p>
        </div>
      );
    }
    return null;
  };

  const RADIAN = Math.PI / 180;
  const renderCustomizedLabel = ({
    cx, cy, midAngle, innerRadius, outerRadius, percent
  }: any) => {
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    if (percent < 0.05) return null; // Don't show label for small slices

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor={x > cx ? 'start' : 'end'}
        dominantBaseline="central"
        className="text-xs font-medium"
      >
        {`${(percent * 100).toFixed(1)}%`}
      </text>
    );
  };

  if (!data || data.length === 0) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <ChartPieIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No contribution data available</h3>
        <p className="mt-1 text-sm text-gray-500">Factor breakdown not available for this report.</p>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="flex items-center space-x-2 mb-4">
        <ChartPieIcon className="w-5 h-5 text-gray-600" />
        <h2 className="text-xl font-semibold text-gray-900">Performance Contribution Breakdown</h2>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Total Contribution</h3>
          <p className="text-2xl font-bold text-green-600">{formatPercent(totalContribution)}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Number of Factors</h3>
          <p className="text-2xl font-bold text-blue-600">{data.length}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Top Contributor</h3>
          <p className="text-lg font-bold text-gray-900 truncate">
            {sortedData[0]?.factor || 'N/A'}
          </p>
          <p className="text-sm text-gray-600">{formatPercent(sortedData[0]?.contribution || 0)}</p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pie Chart */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Contribution Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderCustomizedLabel}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: any) => [formatPercent(value), 'Contribution']}
              />
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(value, entry: any) => (
                  <span className="text-xs">
                    {value} ({formatPercent(entry.payload.value)})
                  </span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Bar Chart */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Contribution vs Weight</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis
                dataKey="name"
                stroke="#6B7280"
                tick={{ fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis
                stroke="#6B7280"
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `${value}%`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Bar dataKey="contribution" fill={COLORS[0]} name="Contribution" />
              <Bar dataKey="weight" fill={COLORS[1]} name="Weight" opacity={0.6} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Factor Rankings */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Factor Rankings</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rank
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Factor
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contribution
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Weight
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Effectiveness
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sortedData.map((item, index) => {
                const effectiveness = item.weight > 0 ? item.contribution / item.weight : 0;
                return (
                  <tr key={item.factor}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full ${
                        index === 0 ? 'bg-yellow-100 text-yellow-800' :
                        index === 1 ? 'bg-gray-100 text-gray-800' :
                        index === 2 ? 'bg-orange-100 text-orange-800' :
                        'bg-blue-50 text-blue-600'
                      } text-sm font-medium`}>
                        #{index + 1}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {item.factor}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={item.contribution > 0 ? 'text-green-600' : 'text-red-600'}>
                        {formatPercent(item.contribution)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {formatPercent(item.weight)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        effectiveness > 1.5 ? 'bg-green-100 text-green-800' :
                        effectiveness > 1.0 ? 'bg-yellow-100 text-yellow-800' :
                        effectiveness > 0.5 ? 'bg-gray-100 text-gray-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {formatNumber(effectiveness, 2)}x
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Insights */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <InformationCircleIcon className="h-5 w-5 text-blue-400 mt-0.5" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Performance Insights</h3>
            <div className="mt-2 text-sm text-blue-700">
              <p>
                The top contributing factor is <span className="font-semibold">{sortedData[0]?.factor}</span>,
                accounting for {formatPercent(sortedData[0]?.contribution || 0)} of total performance.
              </p>
              {sortedData.length > 1 && (
                <p className="mt-1">
                  The top 3 factors contribute {formatPercent(
                    sortedData.slice(0, 3).reduce((sum, item) => sum + item.contribution, 0)
                  )} of total return.
                </p>
              )}
              <div className="mt-2 space-y-1">
                {sortedData
                  .filter(item => item.weight > 0 && item.contribution / item.weight > 1.5)
                  .slice(0, 2)
                  .map(item => (
                    <p key={item.factor} className="text-xs">
                      • {item.factor} shows strong effectiveness ({formatNumber(item.contribution / item.weight, 2)}x return relative to weight)
                    </p>
                  ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContributionBreakdown;