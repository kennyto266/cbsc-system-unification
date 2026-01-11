import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RealTimePrice } from '../../../types/dashboard';
import Card from '../../../components/ui/Card';
import { formatCurrency } from '../../../utils/formatters';

interface RealTimePricesProps {
  prices?: RealTimePrice[];
}

interface PriceItemProps {
  price: RealTimePrice;
  delay: number;
}

const PriceItem: React.FC<PriceItemProps> = ({ price, delay }) => {
  const [prevPrice, setPrevPrice] = useState(price.price);
  const [priceChange, setPriceChange] = useState(0);

  useEffect(() => {
    if (price.price !== prevPrice) {
      setPriceChange(price.price - prevPrice);
      setPrevPrice(price.price);

      // Clear the change indicator after animation
      const timer = setTimeout(() => setPriceChange(0), 1000);
      return () => clearTimeout(timer);
    }
  }, [price.price, prevPrice]);

  const isPositive = priceChange > 0;
  const isNegative = priceChange < 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay }}
      className={`flex items-center justify-between p-3 rounded-lg transition-all duration-300 ${
        isPositive ? 'bg-green-50' : isNegative ? 'bg-red-50' : 'bg-gray-50'
      }`}
    >
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-gray-900">{price.symbol}</span>
          <span className="text-xs text-gray-500">
            Vol: {(price.volume / 10000).toFixed(1)}万
          </span>
        </div>
        <div className="mt-1">
          <span className={`text-lg font-bold ${
            price.change >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {formatCurrency(price.price)}
          </span>
        </div>
      </div>
      <div className={`text-right transition-all duration-300 ${
        isPositive ? 'text-green-600' : isNegative ? 'text-red-600' : 'text-gray-600'
      }`}>
        <div className="text-sm font-medium">
          {price.change >= 0 ? '+' : ''}{formatCurrency(price.change)}
        </div>
        <div className="text-xs">
          ({price.changePercent >= 0 ? '+' : ''}{price.changePercent.toFixed(2)}%)
        </div>
      </div>
    </motion.div>
  );
};

export const RealTimePrices: React.FC<RealTimePricesProps> = ({ prices = [] }) => {
  const [priceList, setPriceList] = useState<RealTimePrice[]>(prices);
  const [sortBy, setSortBy] = useState<'change' | 'volume' | 'symbol'>('change');

  // Update prices when props change
  useEffect(() => {
    setPriceList(prices);
  }, [prices]);

  // Sort prices based on selected criteria
  const sortedPrices = [...priceList].sort((a, b) => {
    switch (sortBy) {
      case 'change':
        return Math.abs(b.changePercent) - Math.abs(a.changePercent);
      case 'volume':
        return b.volume - a.volume;
      case 'symbol':
        return a.symbol.localeCompare(b.symbol);
      default:
        return 0;
    }
  });

  // Simulate real-time price updates
  useEffect(() => {
    const interval = setInterval(() => {
      setPriceList(prev => prev.map(price => ({
        ...price,
        price: price.price * (1 + (Math.random() - 0.5) * 0.001),
        change: price.change + (Math.random() - 0.5) * 0.01,
        changePercent: price.changePercent + (Math.random() - 0.5) * 0.1,
        volume: price.volume + Math.floor(Math.random() * 1000),
        timestamp: new Date().toISOString(),
      })));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <Card title="实时行情" className="h-full flex flex-col">
      {/* Sort Controls */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-2">
          {[
            { key: 'change', label: '涨跌' },
            { key: 'volume', label: '成交量' },
            { key: 'symbol', label: '代码' },
          ].map(option => (
            <button
              key={option.key}
              onClick={() => setSortBy(option.key as any)}
              className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
                sortBy === option.key
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
        <span className="text-xs text-gray-500">
          {new Date().toLocaleTimeString('zh-CN')}
        </span>
      </div>

      {/* Price List */}
      <div className="flex-1 overflow-y-auto space-y-2">
        <AnimatePresence mode="popLayout">
          {sortedPrices.slice(0, 8).map((price, index) => (
            <PriceItem
              key={price.symbol}
              price={price}
              delay={index * 0.05}
            />
          ))}
        </AnimatePresence>

        {/* Empty State */}
        {sortedPrices.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-gray-500">
            <svg
              className="h-12 w-12 text-gray-300 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
              />
            </svg>
            <p className="text-sm">暂无实时行情数据</p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-gray-200">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>共 {sortedPrices.length} 个品种</span>
          <span>数据每3秒更新</span>
        </div>
      </div>
    </Card>
  );
};