import React, { useState } from 'react';
import { motion } from 'framer-motion';
import PullToRefresh from '../../components/mobile/PullToRefresh';
import MobileChart, { MobileChartCard } from '../../components/mobile/MobileChart';
import MobileTable from '../../components/mobile/MobileTable';
import SwipeContainer from '../../components/mobile/SwipeContainer';
import TouchFeedback from '../../components/mobile/TouchFeedback';
import LazyImage from '../../components/common/LazyImage';
import { useResponsive } from '../../hooks/useResponsive';
import { useSwipeGesture } from '../../hooks/useSwipeGesture';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';

// Mock data for demonstration
const mockTableData = [
  { id: 1, name: '策略 A', profit: 12.5, winRate: 65, status: '運行中' },
  { id: 2, name: '策略 B', profit: -3.2, winRate: 45, status: '已停止' },
  { id: 3, name: '策略 C', profit: 8.7, winRate: 58, status: '運行中' },
  { id: 4, name: '策略 D', profit: 15.3, winRate: 72, status: '運行中' },
  { id: 5, name: '策略 E', profit: -1.5, winRate: 51, status: '已停止' },
];

const chartData = {
  labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
  datasets: [
    {
      label: '收益率',
      data: [3.2, 5.4, 2.8, 8.5, 6.3, 9.2],
      borderColor: 'rgb(59, 130, 246)',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      tension: 0.4,
    },
  ],
};

const MobileDemo: React.FC = () => {
  const { isMobile, width } = useResponsive();
  const [refreshCount, setRefreshCount] = useState(0);
  const [swipeDirection, setSwipeDirection] = useState<string | null>(null);
  const [containerRef, swipeState] = useSwipeGesture({
    onSwipeLeft: () => setSwipeDirection('left'),
    onSwipeRight: () => setSwipeDirection('right'),
    onSwipeUp: () => setSwipeDirection('up'),
    onSwipeDown: () => setSwipeDirection('down'),
  });

  const handleRefresh = async () => {
    // Simulate data refresh
    await new Promise(resolve => setTimeout(resolve, 1000));
    setRefreshCount(prev => prev + 1);
  };

  const columns = [
    {
      key: 'name',
      title: '策略名稱',
      sortable: true,
      sorter: (a: any, b: any) => a.name.localeCompare(b.name),
    },
    {
      key: 'profit',
      title: '收益率',
      sortable: true,
      sorter: (a: any, b: any) => a.profit - b.profit,
      render: (value: number) => `${value > 0 ? '+' : ''}${value}%`,
    },
    {
      key: 'winRate',
      title: '勝率',
      sortable: true,
      sorter: (a: any, b: any) => a.winRate - b.winRate,
      render: (value: number) => `${value}%`,
    },
    {
      key: 'status',
      title: '狀態',
      render: (value: string) => (
        <span className={`px-2 py-1 text-xs rounded-full ${
          value === '運行中'
            ? 'bg-green-100 text-green-800'
            : 'bg-gray-100 text-gray-800'
        }`}>
          {value}
        </span>
      ),
    },
  ];

  const swipeCards = [
    <div key="1" className="p-6 bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-2xl">
      <h3 className="text-xl font-bold mb-2">卡片 1</h3>
      <p>左右滑動查看更多卡片</p>
    </div>,
    <div key="2" className="p-6 bg-gradient-to-br from-green-500 to-teal-600 text-white rounded-2xl">
      <h3 className="text-xl font-bold mb-2">卡片 2</h3>
      <p>支持觸摸手勢操作</p>
    </div>,
    <div key="3" className="p-6 bg-gradient-to-br from-orange-500 to-red-600 text-white rounded-2xl">
      <h3 className="text-xl font-bold mb-2">卡片 3</h3>
      <p>流暢的動畫效果</p>
    </div>,
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm px-4 py-3 mb-4">
        <h1 className="text-xl font-semibold">移動端適配演示</h1>
        <p className="text-sm text-gray-500">當前寬度: {width}px</p>
        {isMobile && <p className="text-sm text-green-600">移動端模式</p>}
        {swipeDirection && <p className="text-sm text-blue-600">滑動方向: {swipeDirection}</p>}
      </div>

      <PullToRefresh onRefresh={handleRefresh}>
        <div className="p-4 space-y-6" ref={containerRef}>
          {/* Swipe Detection Area */}
          <Card>
            <CardHeader>
              <CardTitle>觸摸手勢檢測區</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-32 bg-gray-100 rounded-lg flex items-center justify-center">
                <p className="text-gray-600">在此區域滑動以檢測手勢</p>
              </div>
              {swipeState.isSwiping && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-center mt-2 text-primary-600"
                >
                  檢測到滑動！
                </motion.p>
              )}
            </CardContent>
          </Card>

          {/* Touch Feedback Examples */}
          <Card>
            <CardHeader>
              <CardTitle>觸摸反饋示例</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <TouchFeedback className="w-full">
                <button className="w-full py-3 bg-blue-500 text-white rounded-lg">
                  按壓查看效果
                </button>
              </TouchFeedback>
              <TouchFeedback scale={0.95} rippleColor="rgba(34, 197, 94, 0.3)">
                <button className="w-full py-3 bg-green-500 text-white rounded-lg">
                  自定義反饋
                </button>
              </TouchFeedback>
            </CardContent>
          </Card>

          {/* Swipe Container */}
          <Card>
            <CardHeader>
              <CardTitle>滑動卡片容器</CardTitle>
            </CardHeader>
            <CardContent>
              <SwipeContainer
                showDots
                autoplay={false}
                className="h-48"
              >
                {swipeCards}
              </SwipeContainer>
            </CardContent>
          </Card>

          {/* Mobile Chart */}
          <MobileChartCard
            title="收監率趨勢"
            subtitle={`刷新次數: ${refreshCount}`}
          >
            <MobileChart
              type="line"
              data={chartData}
              height={250}
              zoomable={isMobile}
            />
          </MobileChartCard>

          {/* Mobile Table */}
          <Card>
            <CardHeader>
              <CardTitle>策略列表</CardTitle>
            </CardHeader>
            <CardContent>
              <MobileTable
                data={mockTableData}
                columns={columns}
                cardMode={isMobile}
                rowKey="id"
              />
            </CardContent>
          </Card>

          {/* Lazy Image Example */}
          <Card>
            <CardHeader>
              <CardTitle>懶加載圖片</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <LazyImage
                  src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400"
                  alt="市場數據"
                  className="rounded-lg"
                  height={200}
                />
                <LazyImage
                  src="https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=400"
                  alt="交易圖表"
                  className="rounded-lg"
                  height={200}
                />
              </div>
            </CardContent>
          </Card>

          {/* Performance Stats */}
          <Card>
            <CardHeader>
              <CardTitle>性能指標</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <p className="text-2xl font-bold text-blue-600">98%</p>
                  <p className="text-sm text-gray-600">可用性</p>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <p className="text-2xl font-bold text-green-600">&lt;100ms</p>
                  <p className="text-sm text-gray-600">響應時間</p>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <p className="text-2xl font-bold text-purple-600">60fps</p>
                  <p className="text-sm text-gray-600">動畫幀率</p>
                </div>
                <div className="text-center p-4 bg-orange-50 rounded-lg">
                  <p className="text-2xl font-bold text-orange-600">A+</p>
                  <p className="text-sm text-gray-600">性能評分</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </PullToRefresh>
    </div>
  );
};

export default MobileDemo;