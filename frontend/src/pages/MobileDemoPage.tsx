import React, { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { clsx } from 'clsx';
import {
  LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import {
  TrendingUp, TrendingDown, Activity, Users, DollarSign,
  Search, Filter, Plus, RefreshCw, Share2, Download,
  CheckCircle, AlertCircle, Info
} from 'lucide-react';

import MobileOptimizedChart from '../components/Mobile/Optimization/MobileOptimizedChart';
import MobileOptimizedForm from '../components/Mobile/Optimization/MobileOptimizedForm';
import MobileOptimizedList from '../components/Mobile/Optimization/MobileOptimizedList';
import MobileNavigation from '../components/Mobile/MobileNavigation';
import OfflineMode from '../components/Mobile/Offline/OfflineMode';
import TouchFeedback from '../components/Mobile/TouchFeedback';
import useMobileOptimization from '../hooks/useMobileOptimization';
import useResponsive from '../hooks/useResponsive';

// Sample data for charts
const chartData = [
  { name: '1月', value: 4000, value2: 2400 },
  { name: '2月', value: 3000, value2: 1398 },
  { name: '3月', value: 2000, value2: 9800 },
  { name: '4月', value: 2780, value2: 3908 },
  { name: '5月', value: 1890, value2: 4800 },
  { name: '6月', value: 2390, value2: 3800 },
];

// Sample list data
const listData = [
  {
    id: 1,
    title: '量化策略 Alpha',
    subtitle: '高頻交易策略',
    description: '基於技術分析的高頻交易策略，適合短期投資',
    badge: '熱門',
    badgeColor: 'bg-red-500',
    tags: ['高頻', '短期', '技術分析'],
    timestamp: Date.now() - 1000 * 60 * 5,
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Alpha',
  },
  {
    id: 2,
    title: '趨勢跟蹤策略',
    subtitle: '中長期策略',
    description: '跟蹤市場趨勢，捕捉長期投資機會',
    tags: ['中長期', '趨勢', '穩健'],
    timestamp: Date.now() - 1000 * 60 * 30,
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Trend',
  },
  {
    id: 3,
    title: '均值回歸策略',
    subtitle: '統計套利',
    description: '利用價格均值回歸特性進行套利交易',
    badge: '新',
    badgeColor: 'bg-green-500',
    tags: ['套利', '統計', '中性'],
    timestamp: Date.now() - 1000 * 60 * 60,
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Mean',
  },
];

// Form fields example
const formFields = [
  {
    name: 'name',
    label: '策略名稱',
    type: 'text' as const,
    placeholder: '輸入策略名稱',
    required: true,
    validation: {
      minLength: 2,
      maxLength: 50,
    },
  },
  {
    name: 'type',
    label: '策略類型',
    type: 'select' as const,
    required: true,
    options: [
      { label: '高頻交易', value: 'high-frequency' },
      { label: '趨勢跟蹤', value: 'trend-following' },
      { label: '均值回歸', value: 'mean-reversion' },
      { label: '套利策略', value: 'arbitrage' },
    ],
  },
  {
    name: 'description',
    label: '策略描述',
    type: 'textarea' as const,
    placeholder: '描述您的策略...',
    validation: {
      maxLength: 500,
    },
  },
  {
    name: 'risk',
    label: '風險等級',
    type: 'select' as const,
    required: true,
    options: [
      { label: '低風險', value: 'low' },
      { label: '中等風險', value: 'medium' },
      { label: '高風險', value: 'high' },
    ],
  },
];

/**
 * MobileDemoPage - Demonstrates all mobile optimization features
 */
const MobileDemoPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedItems, setSelectedItems] = useState<number[]>([]);
  const { screenInfo, networkInfo } = useMobileOptimization();
  const { isMobile, isTablet } = useResponsive();

  // Handle form submission
  const handleFormSubmit = async (values: Record<string, any>) => {
    console.log('Form submitted:', values);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    alert('策略創建成功！');
  };

  // Handle list item click
  const handleItemClick = (item: any) => {
    console.log('Item clicked:', item);
  };

  // Handle list item swipe
  const handleItemSwipe = (item: any, direction: 'left' | 'right') => {
    console.log(`Swiped ${item.title} ${direction}`);
  };

  // Handle refresh
  const handleRefresh = async () => {
    console.log('Refreshing data...');
    await new Promise(resolve => setTimeout(resolve, 1000));
  };

  // Render overview cards
  const renderOverviewCards = () => (
    <div className="grid grid-cols-2 gap-4 mb-6">
      <motion.div
        whileTap={{ scale: 0.98 }}
        className="bg-white p-4 rounded-lg shadow-sm"
      >
        <div className="flex items-center justify-between mb-2">
          <TrendingUp className="w-5 h-5 text-green-500" />
          <span className="text-xs text-green-600">+12.5%</span>
        </div>
        <div className="text-2xl font-bold text-gray-900">$24,568</div>
        <div className="text-xs text-gray-500 mt-1">總收益</div>
      </motion.div>

      <motion.div
        whileTap={{ scale: 0.98 }}
        className="bg-white p-4 rounded-lg shadow-sm"
      >
        <div className="flex items-center justify-between mb-2">
          <Activity className="w-5 h-5 text-blue-500" />
          <span className="text-xs text-blue-600">活躍</span>
        </div>
        <div className="text-2xl font-bold text-gray-900">12</div>
        <div className="text-xs text-gray-500 mt-1">活躍策略</div>
      </motion.div>

      <motion.div
        whileTap={{ scale: 0.98 }}
        className="bg-white p-4 rounded-lg shadow-sm"
      >
        <div className="flex items-center justify-between mb-2">
          <Users className="w-5 h-5 text-purple-500" />
          <span className="text-xs text-purple-600">+8</span>
        </div>
        <div className="text-2xl font-bold text-gray-900">156</div>
        <div className="text-xs text-gray-500 mt-1">關注用戶</div>
      </motion.div>

      <motion.div
        whileTap={{ scale: 0.98 }}
        className="bg-white p-4 rounded-lg shadow-sm"
      >
        <div className="flex items-center justify-between mb-2">
          <DollarSign className="w-5 h-5 text-yellow-500" />
          <span className="text-xs text-yellow-600">+5.2%</span>
        </div>
        <div className="text-2xl font-bold text-gray-900">89.2%</div>
        <div className="text-xs text-gray-500 mt-1">勝率</div>
      </motion.div>
    </div>
  );

  // Render tab content
  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div>
            {renderOverviewCards()}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-4">收監趨勢</h3>
              <MobileOptimizedChart
                data={chartData}
                type="area"
                title="策略表現"
                height={250}
                showTrendIndicator
                enableGestures
                simplified={isMobile}
              />
            </div>
          </div>
        );

      case 'strategies':
        return (
          <div>
            <div className="mb-4">
              <h3 className="text-lg font-semibold mb-4">策略列表</h3>
              <MobileOptimizedList
                items={listData}
                searchable
                filterable
                pullToRefresh
                onRefresh={handleRefresh}
                onItemClick={handleItemClick}
                onItemSwipe={handleItemSwipe}
                enableSwipeActions
                swipeActions={{
                  left: [
                    { icon: <CheckCircle className="w-5 h-5" />, label: '啟用', color: 'bg-green-500', onPress: () => {} },
                  ],
                  right: [
                    { icon: <AlertCircle className="w-5 h-5" />, label: '暫停', color: 'bg-yellow-500', onPress: () => {} },
                  ],
                }}
              />
            </div>
          </div>
        );

      case 'create':
        return (
          <div>
            <h3 className="text-lg font-semibold mb-4">創建新策略</h3>
            <MobileOptimizedForm
              fields={formFields}
              onSubmit={handleFormSubmit}
              submitButtonText="創建策略"
              largeTouchTargets
              stickySubmit
            />
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Offline mode component */}
      <OfflineMode />

      {/* Mobile navigation */}
      <MobileNavigation
        title="策略管理"
        subtitle="移動優化演示"
        sticky
        showBackButton
        showSearch
        showNotifications
        rightActions={
          <div className="flex items-center gap-2">
            <TouchFeedback className="p-2 rounded-full">
              <RefreshCw className="w-5 h-5" />
            </TouchFeedback>
            <TouchFeedback className="p-2 rounded-full">
              <Share2 className="w-5 h-5" />
            </TouchFeedback>
            <TouchFeedback className="p-2 rounded-full">
              <Download className="w-5 h-5" />
            </TouchFeedback>
          </div>
        }
      />

      {/* Main content */}
      <main className="pt-16 pb-20 px-4">
        {/* Device info */}
        {import.meta.env.DEV && (
          <div className="mb-4 p-3 bg-blue-50 rounded-lg text-xs">
            <div className="font-semibold mb-1">設備信息:</div>
            <div>屏幕: {screenInfo.width}x{screenInfo.height}</div>
            <div>設備類型: {screenInfo.isMobile ? '手機' : screenInfo.isTablet ? '平板' : '桌面'}</div>
            <div>朝向: {screenInfo.isLandscape ? '橫屏' : '豎屏'}</div>
            <div>網絡: {networkInfo.online ? '在線' : '離線'} ({networkInfo.effectiveType})</div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {[
            { id: 'overview', label: '概覽' },
            { id: 'strategies', label: '策略' },
            { id: 'create', label: '創建' },
          ].map((tab) => (
            <TouchFeedback
              key={tab.id}
              className={clsx(
                'px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap',
                activeTab === tab.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-600'
              )}
              onPress={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </TouchFeedback>
          ))}
        </div>

        {/* Tab content */}
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {renderTabContent()}
        </motion.div>
      </main>

      {/* Feature showcase */}
      <div className="mt-8 px-4 pb-8">
        <h3 className="text-lg font-semibold mb-4">移動優化功能</h3>
        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
            <div>
              <div className="font-medium">響應式佈局</div>
              <div className="text-sm text-gray-500">自動適配各種屏幕尺寸</div>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
            <div>
              <div className="font-medium">手勢支持</div>
              <div className="text-sm text-gray-500">滑動、捏合、長按等手勢操作</div>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
            <div>
              <div className="font-medium">離線模式</div>
              <div className="text-sm text-gray-500">離線緩存和數據同步</div>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
            <div>
              <div className="font-medium">觸摸優化</div>
              <div className="text-sm text-gray-500">大觸摸區域和視覺反饋</div>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
            <div>
              <div className="font-medium">性能優化</div>
              <div className="text-sm text-gray-500">流暢動畫和快速加載</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MobileDemoPage;