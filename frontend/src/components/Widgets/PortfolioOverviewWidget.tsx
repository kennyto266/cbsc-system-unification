/**
 * Portfolio Overview Widget
 * Displays portfolio allocation, holdings, and rebalancing suggestions
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  TreemapChart,
  Treemap
} from 'recharts';
import {
  PieChart as PieChartIcon,
  BarChart3,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  AlertTriangle,
  RefreshCw,
  Info
} from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';
import { cn } from '@/lib/utils';

// Type definitions
export interface AssetAllocation {
  symbol: string;
  name: string;
  value: number;
  weight: number;
  targetWeight: number;
  sector: string;
  change: number;
  changePercent: number;
}

export interface SectorAllocation {
  name: string;
  value: number;
  weight: number;
  targetWeight: number;
  assets: string[];
}

export interface PortfolioData {
  totalValue: number;
  cash: number;
  invested: number;
  availableMargin: number;
  dayChange: number;
  dayChangePercent: number;
  totalReturn: number;
  totalReturnPercent: number;
  assets: AssetAllocation[];
  sectors: SectorAllocation[];
  topHoldings: AssetAllocation[];
}

interface PortfolioOverviewWidgetProps {
  className?: string;
  portfolio?: PortfolioData;
  onRebalance?: (suggestions: RebalancingSuggestion[]) => void;
  onViewAsset?: (symbol: string) => void;
}

export interface RebalancingSuggestion {
  symbol: string;
  action: 'buy' | 'sell';
  targetWeight: number;
  currentWeight: number;
  amount: number;
}

// Mock data for development
const mockPortfolio: PortfolioData = {
  totalValue: 1000000,
  cash: 50000,
  invested: 950000,
  availableMargin: 150000,
  dayChange: 2500,
  dayChangePercent: 0.25,
  totalReturn: 125000,
  totalReturnPercent: 12.5,
  assets: [
    { symbol: 'AAPL', name: 'Apple Inc.', value: 150000, weight: 15, targetWeight: 12, sector: 'Technology', change: 1250, changePercent: 0.84 },
    { symbol: 'MSFT', name: 'Microsoft Corp.', value: 140000, weight: 14, targetWeight: 15, sector: 'Technology', change: 2100, changePercent: 1.52 },
    { symbol: 'GOOGL', name: 'Alphabet Inc.', value: 120000, weight: 12, targetWeight: 10, sector: 'Technology', change: -800, changePercent: -0.66 },
    { symbol: 'AMZN', name: 'Amazon.com Inc.', value: 100000, weight: 10, targetWeight: 10, sector: 'Consumer Discretionary', change: 1500, changePercent: 1.52 },
    { symbol: 'TSLA', name: 'Tesla Inc.', value: 80000, weight: 8, targetWeight: 6, sector: 'Consumer Discretionary', change: -2000, changePercent: -2.44 },
    { symbol: 'JPM', name: 'JPMorgan Chase', value: 90000, weight: 9, targetWeight: 10, sector: 'Financial', change: 450, changePercent: 0.50 },
    { symbol: 'JNJ', name: 'Johnson & Johnson', value: 85000, weight: 8.5, targetWeight: 8, sector: 'Healthcare', change: 325, changePercent: 0.38 },
    { symbol: 'V', name: 'Visa Inc.', value: 75000, weight: 7.5, targetWeight: 8, sector: 'Financial', change: 600, changePercent: 0.81 },
    { symbol: 'PG', name: 'Procter & Gamble', value: 60000, weight: 6, targetWeight: 7, sector: 'Consumer Staples', change: 200, changePercent: 0.33 },
    { symbol: 'UNH', name: 'UnitedHealth Group', value: 50000, weight: 5, targetWeight: 5, sector: 'Healthcare', change: 250, changePercent: 0.50 }
  ],
  sectors: [
    { name: 'Technology', value: 410000, weight: 41, targetWeight: 37, assets: ['AAPL', 'MSFT', 'GOOGL'] },
    { name: 'Financial', value: 165000, weight: 16.5, targetWeight: 18, assets: ['JPM', 'V'] },
    { name: 'Healthcare', value: 135000, weight: 13.5, targetWeight: 13, assets: ['JNJ', 'UNH'] },
    { name: 'Consumer Discretionary', value: 180000, weight: 18, targetWeight: 20, assets: ['AMZN', 'TSLA'] },
    { name: 'Consumer Staples', value: 60000, weight: 6, targetWeight: 7, assets: ['PG'] }
  ],
  topHoldings: [] // Will be populated from assets
};

// Populate top holdings from assets
mockPortfolio.topHoldings = mockPortfolio.assets
  .sort((a, b) => b.value - a.value)
  .slice(0, 10);

// Custom colors for charts
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

// Custom tooltip component
const CustomTooltip: React.FC<{ active?: any; payload?: any[]; label?: string }> = ({
  active,
  payload,
  label
}) => {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0].payload;

  return (
    <div className="bg-white p-3 border rounded-lg shadow-lg min-w-[200px]">
      <h4 className="font-medium mb-2">{data.name || label}</h4>
      <div className="space-y-1 text-sm">
        <div className="flex justify-between">
          <span>Value:</span>
          <span className="font-medium">${data.value?.toLocaleString()}</span>
        </div>
        <div className="flex justify-between">
          <span>Weight:</span>
          <span className="font-medium">{data.weight?.toFixed(1)}%</span>
        </div>
        {data.change && (
          <div className="flex justify-between">
            <span>Change:</span>
            <span className={cn(
              'font-medium',
              data.change >= 0 ? 'text-green-600' : 'text-red-600'
            )}>
              ${Math.abs(data.change)} ({data.changePercent?.toFixed(2)}%)
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

// Rebalancing suggestion component
const RebalancingSuggestions: React.FC<{
  suggestions: RebalancingSuggestion[];
  onExecute: () => void;
}> = ({ suggestions, onExecute }) => {
  const [expanded, setExpanded] = useState(false);

  if (suggestions.length === 0) return null;

  return (
    <div className="border rounded-lg p-3 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-yellow-500" />
          <span className="text-sm font-medium">Rebalancing Suggested</span>
          <Badge variant="outline" className="text-xs">
            {suggestions.length} adjustments
          </Badge>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? 'Hide' : 'Show'}
        </Button>
      </div>

      {expanded && (
        <div className="space-y-2">
          {suggestions.map((suggestion, index) => (
            <div key={index} className="flex items-center justify-between text-sm p-2 bg-gray-50 rounded">
              <div className="flex items-center space-x-2">
                <Badge variant={suggestion.action === 'buy' ? 'default' : 'secondary'}>
                  {suggestion.action.toUpperCase()}
                </Badge>
                <span className="font-medium">{suggestion.symbol}</span>
              </div>
              <div className="text-right">
                <div>{suggestion.currentWeight.toFixed(1)}% → {suggestion.targetWeight.toFixed(1)}%</div>
                <div className="text-xs text-gray-500">${suggestion.amount.toLocaleString()}</div>
              </div>
            </div>
          ))}
          <Button onClick={onExecute} className="w-full">
            Execute Rebalancing
          </Button>
        </div>
      )}
    </div>
  );
};

export const PortfolioOverviewWidget: React.FC<PortfolioOverviewWidgetProps> = ({
  className,
  portfolio = mockPortfolio,
  onRebalance,
  onViewAsset
}) => {
  const [selectedView, setSelectedView] = useState<'allocation' | 'holdings' | 'sectors'>('allocation');
  const [rebalancingSuggestions, setRebalancingSuggestions] = useState<RebalancingSuggestion[]>([]);

  // Subscribe to portfolio updates via WebSocket
  const { subscribe } = useWebSocket();

  useEffect(() => {
    const unsubscribe = subscribe('portfolio', (data) => {
      if (data.type === 'portfolio_update') {
        // Handle real-time portfolio updates
        console.log('Portfolio updated:', data);
      }
    });

    return unsubscribe;
  }, [subscribe]);

  // Calculate rebalancing suggestions
  useEffect(() => {
    const suggestions: RebalancingSuggestion[] = [];

    portfolio.assets.forEach(asset => {
      const diff = asset.targetWeight - asset.weight;
      if (Math.abs(diff) > 1) { // Only if difference is significant (>1%)
        const amount = (Math.abs(diff) / 100) * portfolio.totalValue;
        suggestions.push({
          symbol: asset.symbol,
          action: diff > 0 ? 'buy' : 'sell',
          targetWeight: asset.targetWeight,
          currentWeight: asset.weight,
          amount
        });
      }
    });

    setRebalancingSuggestions(suggestions);
  }, [portfolio]);

  // Prepare data for pie chart
  const pieChartData = useMemo(() => {
    if (selectedView === 'allocation') {
      return portfolio.assets.map(asset => ({
        name: asset.symbol,
        value: asset.value,
        weight: asset.weight
      }));
    } else if (selectedView === 'sectors') {
      return portfolio.sectors.map(sector => ({
        name: sector.name,
        value: sector.value,
        weight: sector.weight
      }));
    }
    return [];
  }, [portfolio, selectedView]);

  // Prepare data for treemap
  const treemapData = useMemo(() => {
    return portfolio.sectors.map(sector => ({
      name: sector.name,
      size: sector.value,
      children: portfolio.assets
        .filter(asset => asset.sector === sector.name)
        .map(asset => ({
          name: asset.symbol,
          size: asset.value
        }))
    }));
  }, [portfolio]);

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Portfolio Overview</CardTitle>
          <div className="flex items-center space-x-2">
            <Badge variant={portfolio.dayChange >= 0 ? 'default' : 'destructive'}>
              {portfolio.dayChange >= 0 ? '+' : ''}{portfolio.dayChangePercent.toFixed(2)}% Today
            </Badge>
            <Button variant="outline" size="sm">
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Portfolio Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="text-center p-3 border rounded-lg">
            <div className="text-xs text-gray-500 mb-1">Total Value</div>
            <div className="text-lg font-semibold">${portfolio.totalValue.toLocaleString()}</div>
            <div className={cn(
              'text-xs',
              portfolio.dayChange >= 0 ? 'text-green-600' : 'text-red-600'
            )}>
              {portfolio.dayChange >= 0 ? '+' : ''}${portfolio.dayChange.toLocaleString()}
            </div>
          </div>
          <div className="text-center p-3 border rounded-lg">
            <div className="text-xs text-gray-500 mb-1">Cash</div>
            <div className="text-lg font-semibold">${portfolio.cash.toLocaleString()}</div>
            <div className="text-xs text-gray-500">{((portfolio.cash / portfolio.totalValue) * 100).toFixed(1)}%</div>
          </div>
          <div className="text-center p-3 border rounded-lg">
            <div className="text-xs text-gray-500 mb-1">Invested</div>
            <div className="text-lg font-semibold">${portfolio.invested.toLocaleString()}</div>
            <div className="text-xs text-gray-500">{((portfolio.invested / portfolio.totalValue) * 100).toFixed(1)}%</div>
          </div>
          <div className="text-center p-3 border rounded-lg">
            <div className="text-xs text-gray-500 mb-1">Total Return</div>
            <div className={cn(
              'text-lg font-semibold',
              portfolio.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'
            )}>
              {portfolio.totalReturnPercent.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500">${portfolio.totalReturn.toLocaleString()}</div>
          </div>
        </div>

        {/* View Selector */}
        <div className="flex items-center space-x-2">
          <Button
            variant={selectedView === 'allocation' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedView('allocation')}
          >
            Allocation
          </Button>
          <Button
            variant={selectedView === 'sectors' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedView('sectors')}
          >
            Sectors
          </Button>
          <Button
            variant={selectedView === 'holdings' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedView('holdings')}
          >
            Holdings
          </Button>
        </div>

        {/* Allocation Charts */}
        {selectedView !== 'holdings' && (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {pieChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Top Holdings */}
        {selectedView === 'holdings' && (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {portfolio.topHoldings.map((holding, index) => (
              <div
                key={holding.symbol}
                className="flex items-center justify-between p-3 border rounded hover:bg-gray-50 cursor-pointer"
                onClick={() => onViewAsset?.(holding.symbol)}
              >
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-sm font-medium text-blue-600">
                    {holding.symbol.charAt(0)}
                  </div>
                  <div>
                    <div className="font-medium">{holding.symbol}</div>
                    <div className="text-xs text-gray-500">{holding.name}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-medium">${holding.value.toLocaleString()}</div>
                  <div className={cn(
                    'text-xs',
                    holding.change >= 0 ? 'text-green-600' : 'text-red-600'
                  )}>
                    {holding.change >= 0 ? '+' : ''}{holding.changePercent.toFixed(2)}%
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">{holding.weight.toFixed(1)}%</div>
                  <Progress value={holding.weight} className="w-12 h-1" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Sector Allocation (when in sectors view) */}
        {selectedView === 'sectors' && (
          <div className="space-y-2">
            {portfolio.sectors.map((sector, index) => (
              <div key={sector.name} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                  <span className="text-sm font-medium">{sector.name}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm">${sector.value.toLocaleString()}</span>
                  <span className="text-sm text-gray-500">{sector.weight.toFixed(1)}%</span>
                  <Progress value={sector.weight} className="w-20" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Rebalancing Suggestions */}
        <RebalancingSuggestions
          suggestions={rebalancingSuggestions}
          onExecute={() => onRebalance?.(rebalancingSuggestions)}
        />

        {/* Margin Info */}
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Available Margin: ${portfolio.availableMargin.toLocaleString()}</span>
          <span>Buying Power: ${(portfolio.availableMargin + portfolio.cash).toLocaleString()}</span>
        </div>
      </CardContent>
    </Card>
  );
};

export default PortfolioOverviewWidget;