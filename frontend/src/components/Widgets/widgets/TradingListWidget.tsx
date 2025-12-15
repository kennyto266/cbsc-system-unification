import React, { useState, useEffect } from 'react';
import { Widget } from '../../../types/widget';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Card, CardContent } from '../../ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../ui/table';
import {
  ChevronUp,
  ChevronDown,
  X,
  ExternalLink,
  Clock,
  DollarSign,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';

interface Trade {
  id: string;
  symbol: string;
  name: string;
  type: 'buy' | 'sell';
  strategy: string;
  price: number;
  quantity: number;
  amount: number;
  status: 'filled' | 'pending' | 'cancelled';
  timestamp: Date;
  profit?: number;
  profitPercent?: number;
}

interface TradingListWidgetProps {
  widget: Widget;
}

export function TradingListWidget({ widget }: TradingListWidgetProps) {
  const [trades, setTrades] = useState<Trade[]>([
    {
      id: '1',
      symbol: '0700.HK',
      name: '騰訊控股',
      type: 'buy',
      strategy: 'CBSC多因子策略',
      price: 312.60,
      quantity: 1000,
      amount: 312600,
      status: 'filled',
      timestamp: new Date(Date.now() - 1000 * 60 * 5),
      profit: 1560,
      profitPercent: 0.5,
    },
    {
      id: '2',
      symbol: '9988.HK',
      name: '阿里巴巴',
      type: 'sell',
      strategy: '動量突破策略',
      price: 72.85,
      quantity: 5000,
      amount: 364250,
      status: 'filled',
      timestamp: new Date(Date.now() - 1000 * 60 * 15),
      profit: -2185,
      profitPercent: -0.6,
    },
    {
      id: '3',
      symbol: '2318.HK',
      name: '中國平安',
      type: 'buy',
      strategy: '均值回歸策略',
      price: 45.20,
      quantity: 10000,
      amount: 452000,
      status: 'pending',
      timestamp: new Date(Date.now() - 1000 * 60 * 30),
    },
    {
      id: '4',
      symbol: '3690.HK',
      name: '美團',
      type: 'buy',
      strategy: 'CBSC多因子策略',
      price: 125.40,
      quantity: 2000,
      amount: 250800,
      status: 'filled',
      timestamp: new Date(Date.now() - 1000 * 60 * 60),
      profit: 5020,
      profitPercent: 2.0,
    },
  ]);

  const [filter, setFilter] = useState<'all' | 'buy' | 'sell'>('all');
  const [sortBy, setSortBy] = useState<'time' | 'amount' | 'profit'>('time');

  // Simulate new trades
  useEffect(() => {
    const interval = setInterval(() => {
      const newTrade: Trade = {
        id: Date.now().toString(),
        symbol: Math.random() > 0.5 ? '0941.HK' : '1299.HK',
        name: Math.random() > 0.5 ? '中國移動' : '友邦保險',
        type: Math.random() > 0.5 ? 'buy' : 'sell',
        strategy: ['CBSC多因子策略', '動量突破策略', '均值回歸策略'][Math.floor(Math.random() * 3)],
        price: 50 + Math.random() * 100,
        quantity: Math.floor(1000 + Math.random() * 5000),
        amount: 0,
        status: Math.random() > 0.2 ? 'filled' : 'pending',
        timestamp: new Date(),
      };
      newTrade.amount = newTrade.price * newTrade.quantity;

      if (newTrade.status === 'filled') {
        newTrade.profit = (Math.random() - 0.4) * 5000;
        newTrade.profitPercent = (newTrade.profit / newTrade.amount) * 100;
      }

      setTrades(prev => [newTrade, ...prev.slice(0, 9)]);
    }, (widget.config?.refreshInterval || 10) * 1000);

    return () => clearInterval(interval);
  }, [widget.config?.refreshInterval]);

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);

    if (minutes < 1) return '剛剛';
    if (minutes < 60) return `${minutes} 分鐘前`;
    if (minutes < 1440) return `${Math.floor(minutes / 60)} 小時前`;
    return date.toLocaleDateString('zh-TW');
  };

  const formatAmount = (amount: number) => {
    if (amount >= 1000000) {
      return `${(amount / 1000000).toFixed(2)}M`;
    }
    if (amount >= 1000) {
      return `${(amount / 1000).toFixed(2)}K`;
    }
    return amount.toFixed(2);
  };

  const filteredTrades = trades.filter(trade => {
    if (filter === 'all') return true;
    return trade.type === filter;
  });

  const sortedTrades = [...filteredTrades].sort((a, b) => {
    switch (sortBy) {
      case 'time':
        return b.timestamp.getTime() - a.timestamp.getTime();
      case 'amount':
        return b.amount - a.amount;
      case 'profit':
        return (b.profit || 0) - (a.profit || 0);
      default:
        return 0;
    }
  });

  return (
    <div className="h-full flex flex-col">
      {/* Controls */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Button
            variant={filter === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('all')}
            className="h-7 text-xs"
          >
            全部
          </Button>
          <Button
            variant={filter === 'buy' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('buy')}
            className="h-7 text-xs"
          >
            買入
          </Button>
          <Button
            variant={filter === 'sell' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('sell')}
            className="h-7 text-xs"
          >
            賣出
          </Button>
        </div>

        <div className="flex items-center gap-1">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="text-xs border rounded px-2 py-1 bg-background"
          >
            <option value="time">時間</option>
            <option value="amount">金額</option>
            <option value="profit">收益</option>
          </select>
        </div>
      </div>

      {/* Trades list */}
      <div className="flex-1 overflow-auto">
        <Table>
          <TableHeader>
            <TableRow className="text-xs">
              <TableHead>時間</TableHead>
              <TableHead>股票</TableHead>
              <TableHead>類型</TableHead>
              <TableHead>價格</TableHead>
              <TableHead>金額</TableHead>
              <TableHead>狀態</TableHead>
              <TableHead>收益</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedTrades.map((trade) => (
              <TableRow key={trade.id} className="text-xs">
                <TableCell className="w-16">
                  <div className="flex items-center gap-1 text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    <span>{formatTime(trade.timestamp)}</span>
                  </div>
                </TableCell>
                <TableCell className="font-medium">
                  <div>
                    <div>{trade.symbol}</div>
                    <div className="text-muted-foreground truncate max-w-20">
                      {trade.name}
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge
                    variant={trade.type === 'buy' ? 'default' : 'destructive'}
                    className="text-xs"
                  >
                    {trade.type === 'buy' ? '買入' : '賣出'}
                  </Badge>
                </TableCell>
                <TableCell>
                  ${trade.price.toFixed(2)}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <DollarSign className="h-3 w-3" />
                    <span>{formatAmount(trade.amount)}</span>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge
                    variant={
                      trade.status === 'filled'
                        ? 'default'
                        : trade.status === 'pending'
                        ? 'secondary'
                        : 'outline'
                    }
                    className="text-xs"
                  >
                    {trade.status === 'filled' ? '成交' :
                     trade.status === 'pending' ? '待成交' : '已取消'}
                  </Badge>
                </TableCell>
                <TableCell>
                  {trade.profit !== undefined ? (
                    <div className={`flex items-center gap-1 ${
                      trade.profit > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {trade.profit > 0 ? (
                        <TrendingUp className="h-3 w-3" />
                      ) : (
                        <TrendingDown className="h-3 w-3" />
                      )}
                      <span>
                        {trade.profit > 0 ? '+' : ''}{trade.profit.toFixed(0)}
                        ({trade.profitPercent?.toFixed(2)}%)
                      </span>
                    </div>
                  ) : (
                    <span className="text-muted-foreground">-</span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Summary */}
      <div className="mt-3 pt-3 border-t">
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="text-center">
            <div className="text-muted-foreground">總交易</div>
            <div className="font-semibold">{trades.length}</div>
          </div>
          <div className="text-center">
            <div className="text-muted-foreground">總收益</div>
            <div className={`font-semibold ${
              trades.reduce((sum, t) => sum + (t.profit || 0), 0) > 0
                ? 'text-green-600'
                : 'text-red-600'
            }`}>
              ${trades.reduce((sum, t) => sum + (t.profit || 0), 0).toFixed(0)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-muted-foreground">勝率</div>
            <div className="font-semibold">
              {(
                (trades.filter(t => (t.profit || 0) > 0).length /
                  trades.filter(t => t.profit !== undefined).length) *
                100
              ).toFixed(1)}%
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}