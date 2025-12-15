import React, { useState, useEffect } from 'react';
import { Widget } from '../../../types/widget';
import { Badge } from '../../ui/badge';
import { Card, CardContent } from '../../ui/card';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MarketMonitorWidgetProps {
  widget: Widget;
}

interface MarketData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: string;
  marketCap?: string;
}

export function MarketMonitorWidget({ widget }: MarketMonitorWidgetProps) {
  const [markets, setMarkets] = useState<MarketData[]>([
    {
      symbol: 'HSI',
      name: '恒生指數',
      price: 17850.32,
      change: 125.67,
      changePercent: 0.71,
      volume: '125.6B',
      marketCap: 'N/A',
    },
    {
      symbol: 'HSCEI',
      name: '國企指數',
      price: 6032.18,
      change: -45.23,
      changePercent: -0.74,
      volume: '89.3B',
      marketCap: 'N/A',
    },
    {
      symbol: 'HS_TECH',
      name: '恒生科技指數',
      price: 3520.45,
      change: 32.18,
      changePercent: 0.92,
      volume: '67.8B',
      marketCap: 'N/A',
    },
    {
      symbol: 'TCEHY',
      name: '騰訊控股',
      price: 312.60,
      change: -2.40,
      changePercent: -0.76,
      volume: '23.5M',
      marketCap: '3.0T',
    },
    {
      symbol: 'BABA',
      name: '阿里巴巴',
      price: 72.85,
      change: 1.25,
      changePercent: 1.74,
      volume: '18.2M',
      marketCap: '191.2B',
    },
    {
      symbol: 'BIDU',
      name: '百度',
      price: 98.42,
      change: -0.58,
      changePercent: -0.59,
      volume: '2.8M',
      marketCap: '27.5B',
    },
  ]);

  const [selectedMarket, setSelectedMarket] = useState<string | null>(null);

  // Simulate real-time market updates
  useEffect(() => {
    const interval = setInterval(() => {
      setMarkets(prev =>
        prev.map(market => {
          const changeAmount = (Math.random() - 0.5) * 2;
          const newPrice = market.price + changeAmount;
          const newChange = newPrice - (market.price - market.change);
          const newChangePercent = (newChange / (market.price - market.change)) * 100;

          return {
            ...market,
            price: newPrice,
            change: newChange,
            changePercent: newChangePercent,
          };
        })
      );
    }, (widget.config?.refreshInterval || 3) * 1000);

    return () => clearInterval(interval);
  }, [widget.config?.refreshInterval]);

  const formatPrice = (price: number) => {
    return price.toLocaleString('zh-TW', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  };

  const getTrendIcon = (change: number) => {
    if (change > 0) return <TrendingUp className="h-3 w-3 text-green-600" />;
    if (change < 0) return <TrendingDown className="h-3 w-3 text-red-600" />;
    return <Minus className="h-3 w-3 text-gray-600" />;
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <div className="space-y-3">
      {/* Market indices */}
      <div className="grid grid-cols-1 gap-2">
        {markets
          .filter(m => ['HSI', 'HSCEI', 'HS_TECH'].includes(m.symbol))
          .map(market => (
            <Card
              key={market.symbol}
              className={`p-3 cursor-pointer transition-all ${
                selectedMarket === market.symbol
                  ? 'ring-2 ring-primary'
                  : 'hover:shadow-md'
              }`}
              onClick={() => setSelectedMarket(
                selectedMarket === market.symbol ? null : market.symbol
              )}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-sm">{market.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {market.symbol}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-sm">
                    {formatPrice(market.price)}
                  </div>
                  <div className={`flex items-center justify-end gap-1 text-xs ${getChangeColor(market.change)}`}>
                    {getTrendIcon(market.change)}
                    <span>
                      {market.change > 0 ? '+' : ''}{market.change.toFixed(2)}
                      ({market.changePercent.toFixed(2)}%)
                    </span>
                  </div>
                </div>
              </div>
            </Card>
          ))}
      </div>

      {/* Divider */}
      <div className="border-t my-2" />

      {/* Stock watches */}
      <div className="space-y-2">
        <div className="text-xs font-medium text-muted-foreground px-1">
          監控股票
        </div>
        {markets
          .filter(m => !['HSI', 'HSCEI', 'HS_TECH'].includes(m.symbol))
          .map(market => (
            <div
              key={market.symbol}
              className="flex items-center justify-between p-2 rounded hover:bg-muted/50"
            >
              <div>
                <div className="font-medium text-sm">{market.symbol}</div>
                <div className="text-xs text-muted-foreground truncate max-w-20">
                  {market.name}
                </div>
              </div>
              <div className="text-right">
                <div className="font-medium text-sm">
                  ${formatPrice(market.price)}
                </div>
                <div className={`text-xs ${getChangeColor(market.change)}`}>
                  {market.change > 0 ? '+' : ''}{market.changePercent.toFixed(2)}%
                </div>
              </div>
            </div>
          ))}
      </div>

      {/* Market summary */}
      <div className="bg-muted/30 rounded p-3">
        <div className="text-xs font-medium text-muted-foreground mb-2">
          市場概況
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-muted-foreground">上漲：</span>
            <span className="text-green-600 font-medium">
              {markets.filter(m => m.change > 0).length}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">下跌：</span>
            <span className="text-red-600 font-medium">
              {markets.filter(m => m.change < 0).length}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">平盤：</span>
            <span className="text-gray-600 font-medium">
              {markets.filter(m => Math.abs(m.change) < 0.01).length}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">成交量：</span>
            <span className="font-medium">
              {markets[0]?.volume || '-'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}