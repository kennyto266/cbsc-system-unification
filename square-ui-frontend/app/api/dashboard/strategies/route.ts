import { NextRequest, NextResponse } from 'next/server';

// 模擬從策略管理系統獲取的策略列表
const fetchRealStrategies = async () => {
  try {
    // 這裡應該調用真實的策略管理 API
    // const response = await fetch(`${process.env.BACKEND_API_URL}/api/strategies`);
    // return await response.json();

    // 基於 CBSC 數據創建的策略
    return [
      {
        id: 1,
        name: 'CBSC 牛熊證套利策略',
        type: 'arbitrage',
        status: 'active',
        performance: 12.5,
        lastUpdate: '2025-12-16',
        description: '基於牛熊證價差的套利策略'
      },
      {
        id: 2,
        name: 'HSI 波動率交易策略',
        type: 'volatility',
        status: 'active',
        performance: 8.3,
        lastUpdate: '2025-12-16',
        description: '捕捉恆指波動率的交易機會'
      },
      {
        id: 3,
        name: '市場情緒指標策略',
        type: 'sentiment',
        status: 'testing',
        performance: -1.2,
        lastUpdate: '2025-12-15',
        description: '基於市場恐懼貪婪指數的策略'
      },
      {
        id: 4,
        name: '支撐阻力位突破策略',
        type: 'breakout',
        status: 'paused',
        performance: 15.7,
        lastUpdate: '2025-12-14',
        description: '在關鍵價位突破時進場'
      },
      {
        id: 5,
        name: '時間價值衰減策略',
        type: 'theta',
        status: 'active',
        performance: 5.9,
        lastUpdate: '2025-12-16',
        description: '利用衍生品時間價值衰減'
      }
    ];
  } catch (error) {
    console.error('Failed to fetch strategies:', error);
    return [];
  }
};

export async function GET(request: NextRequest) {
  try {
    const strategies = await fetchRealStrategies();

    // 格式化性能顯示
    const formattedStrategies = strategies.map(strategy => ({
      id: strategy.id,
      name: strategy.name,
      type: strategy.type,
      status: strategy.status,
      performance: strategy.performance !== undefined ?
        `${strategy.performance > 0 ? '+' : ''}${strategy.performance.toFixed(2)}%` :
        '待定',
      performanceValue: strategy.performance || 0,
      lastUpdate: formatLastUpdate(strategy.lastUpdate),
      description: strategy.description
    }));

    return NextResponse.json({
      success: true,
      data: {
        strategies: formattedStrategies,
        summary: {
          total: strategies.length,
          active: strategies.filter(s => s.status === 'active').length,
          paused: strategies.filter(s => s.status === 'paused').length,
          testing: strategies.filter(s => s.status === 'testing').length,
          avgPerformance: strategies
            .filter(s => s.performance !== undefined)
            .reduce((sum, s) => sum + s.performance, 0) /
            strategies.filter(s => s.performance !== undefined).length
        }
      },
      last_updated: new Date().toISOString()
    });
  } catch (error) {
    console.error('Strategies API error:', error);
    return NextResponse.json(
      {
        success: false,
        error: error.message,
        message: '無法獲取策略數據'
      },
      { status: 500 }
    );
  }
}

function formatLastUpdate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

  if (diffHours < 1) {
    const diffMinutes = Math.floor(diffHours * 60);
    return `${diffMinutes}分鐘前`;
  } else if (diffHours < 24) {
    return `${Math.floor(diffHours)}小時前`;
  } else if (diffHours < 24 * 7) {
    return `${Math.floor(diffHours / 24)}天前`;
  } else {
    return dateStr;
  }
}