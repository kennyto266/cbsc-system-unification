/**
 * Strategy Performance Dashboard
 * Shows all strategy-related widgets in a unified dashboard
 */

import React, { useState } from 'react';
import {
  StrategyStatusWidget,
  PerformanceMetricsWidget,
  PortfolioOverviewWidget
} from '../components/Widgets';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts';
import {
  TrendingUp,
  Activity,
  DollarSign,
  Target,
  Settings,
  RefreshCw,
  Download,
  Bell
} from 'lucide-react';
import { cn } from '@/lib/utils';

// Sample historical data for combined performance
const generateCombinedData = () => {
  const data = [];
  const now = new Date();

  for (let i = 29; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);

    data.push({
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      portfolio: 100 + Math.random() * 20,
      benchmark: 100 + Math.random() * 10,
      strategies: 100 + Math.random() * 15
    });
  }

  return data;
};

const combinedData = generateCombinedData();

export const StrategyPerformanceDashboard: React.FC = () => {
  const [selectedPeriod, setSelectedPeriod] = useState('1M');
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Handle strategy toggle
  const handleToggleStrategy = (strategyId: string, enabled: boolean) => {
    console.log(`Strategy ${strategyId} ${enabled ? 'enabled' : 'disabled'}`);
    // In a real app, this would send a command to the backend
  };

  // Handle view details
  const handleViewDetails = (strategyId: string) => {
    console.log(`Viewing details for strategy ${strategyId}`);
    // In a real app, this would navigate to a detailed view
  };

  // Handle rebalance
  const handleRebalance = (suggestions: any[]) => {
    console.log('Executing rebalancing:', suggestions);
    // In a real app, this would execute the rebalancing
  };

  // Handle view asset
  const handleViewAsset = (symbol: string) => {
    console.log(`Viewing asset ${symbol}`);
    // In a real app, this would navigate to asset details
  };

  // Handle refresh
  const handleRefresh = async () => {
    setRefreshing(true);
    // Simulate refresh delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    setRefreshing(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Strategy Performance</h1>
            <p className="text-gray-600 mt-1">Monitor and manage your trading strategies in real-time</p>
          </div>
          <div className="flex items-center space-x-3">
            <Badge variant="outline" className="flex items-center space-x-1">
              <Activity className="w-3 h-3" />
              <span>Live</span>
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={cn(autoRefresh && 'bg-blue-50 border-blue-200')}
            >
              Auto Refresh: {autoRefresh ? 'ON' : 'OFF'}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              <RefreshCw className={cn('w-4 h-4 mr-2', refreshing && 'animate-spin')} />
              Refresh
            </Button>
            <Button size="sm">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        {/* Combined Performance Chart */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Combined Performance</span>
              <div className="flex items-center space-x-4 text-sm">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-blue-500 rounded-full" />
                  <span>Portfolio</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full" />
                  <span>Strategies</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-gray-400 rounded-full" />
                  <span>Benchmark</span>
                </div>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={combinedData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Area
                    type="monotone"
                    dataKey="strategies"
                    stackId="1"
                    stroke="#10b981"
                    fill="#10b981"
                    fillOpacity={0.6}
                  />
                  <Area
                    type="monotone"
                    dataKey="portfolio"
                    stackId="2"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.6}
                  />
                  <Line
                    type="monotone"
                    dataKey="benchmark"
                    stroke="#9ca3af"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Widgets Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Strategy Status Widget - Takes 2 columns */}
        <div className="lg:col-span-2">
          <StrategyStatusWidget
            onToggleStrategy={handleToggleStrategy}
            onViewDetails={handleViewDetails}
          />
        </div>

        {/* Performance Metrics Widget - Takes 1 column */}
        <div>
          <PerformanceMetricsWidget
            onPeriodChange={setSelectedPeriod}
          />
        </div>

        {/* Portfolio Overview Widget - Spans full width */}
        <div className="lg:col-span-3">
          <PortfolioOverviewWidget
            onRebalance={handleRebalance}
            onViewAsset={handleViewAsset}
          />
        </div>
      </div>

      {/* Quick Stats Footer */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <DollarSign className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <div className="text-xs text-gray-500">Daily P&L</div>
                <div className="text-lg font-semibold text-green-600">+$2,425.50</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <TrendingUp className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <div className="text-xs text-gray-500">Win Rate</div>
                <div className="text-lg font-semibold">68.5%</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Activity className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <div className="text-xs text-gray-500">Active Strategies</div>
                <div className="text-lg font-semibold">12 / 15</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Target className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <div className="text-xs text-gray-500">Sharpe Ratio</div>
                <div className="text-lg font-semibold">1.85</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default StrategyPerformanceDashboard;