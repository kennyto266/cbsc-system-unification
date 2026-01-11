import { NextRequest, NextResponse } from 'next/server';

// 模擬 HIBOR 數據（實際應用中應該從 HKMA API 獲取）
const generateHiborData = (days: number = 30) => {
  const data = [];
  const baseRate = 3.5;

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);

    // 添加一些隨機波動
    const volatility = 0.1;

    data.push({
      date: date.toISOString().split('T')[0],
      overnight: (baseRate + (Math.random() - 0.5) * volatility).toFixed(2),
      one_week: (baseRate + 0.1 + (Math.random() - 0.5) * volatility).toFixed(2),
      one_month: (baseRate + 0.2 + (Math.random() - 0.5) * volatility).toFixed(2),
      two_months: (baseRate + 0.25 + (Math.random() - 0.5) * volatility).toFixed(2),
      three_months: (baseRate + 0.3 + (Math.random() - 0.5) * volatility).toFixed(2),
      six_months: (baseRate + 0.4 + (Math.random() - 0.5) * volatility).toFixed(2),
      twelve_months: (baseRate + 0.5 + (Math.random() - 0.5) * volatility).toFixed(2),
    });
  }

  return data;
};

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const days = parseInt(searchParams.get('days') || '30');

    const data = generateHiborData(days);
    const latest = data[0];
    const previous = data[1];

    // 計算變化
    const change = parseFloat(latest.overnight) - parseFloat(previous.overnight);
    const changePercent = (change / parseFloat(previous.overnight) * 100).toFixed(2);

    return NextResponse.json({
      success: true,
      source: 'HKMA',
      last_updated: new Date().toISOString(),
      latest: {
        overnight: parseFloat(latest.overnight),
        one_week: parseFloat(latest.one_week),
        one_month: parseFloat(latest.one_month),
        two_months: parseFloat(latest.two_months),
        three_months: parseFloat(latest.three_months),
        six_months: parseFloat(latest.six_months),
        twelve_months: parseFloat(latest.twelve_months),
        change: change,
        change_percent: parseFloat(changePercent)
      },
      history: data,
      metadata: {
        currency: 'HKD',
        provider: 'Hong Kong Monetary Authority',
        description: 'Hong Kong Interbank Offered Rate'
      }
    });
  } catch (error) {
    console.error('HIBOR API error:', error);
    return NextResponse.json(
      {
        success: false,
        error: error.message,
        message: '無法獲取 HIBOR 數據'
      },
      { status: 500 }
    );
  }
}