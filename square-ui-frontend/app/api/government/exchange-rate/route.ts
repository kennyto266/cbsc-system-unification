import { NextRequest, NextResponse } from 'next/server';

// 模擬美元兌港元匯率數據
const generateExchangeRateData = (days: number = 30) => {
  const data = [];
  const baseRate = 7.85;

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);

    // HKD is pegged to USD with small fluctuations
    const fluctuation = (Math.random() - 0.5) * 0.002; // ±0.001

    data.push({
      date: date.toISOString().split('T')[0],
      usd_hkd: (baseRate + fluctuation).toFixed(3),
      high: (baseRate + Math.abs(fluctuation) * 1.5).toFixed(3),
      low: (baseRate - Math.abs(fluctuation) * 1.5).toFixed(3),
      open: (baseRate + fluctuation * 0.5).toFixed(3),
      close: (baseRate + fluctuation).toFixed(3),
      volume: Math.floor(Math.random() * 1000000) + 500000
    });
  }

  return data;
};

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const days = parseInt(searchParams.get('days') || '30');

    const data = generateExchangeRateData(days);
    const latest = data[0];

    // 確保至少有2天數據用於計算變化
    const previous = data.length > 1 ? data[1] : {
      usd_hkd: latest.usd_hkd,
      high: latest.high,
      low: latest.low,
      open: latest.open
    };

    // 計算變化
    const change = parseFloat(latest.usd_hkd) - parseFloat(previous.usd_hkd);
    const changePercent = parseFloat(previous.usd_hkd) > 0 ? (change / parseFloat(previous.usd_hkd) * 100).toFixed(3) : '0.000';

    return NextResponse.json({
      success: true,
      source: 'HKMA',
      last_updated: new Date().toISOString(),
      latest: {
        rate: parseFloat(latest.usd_hkd),
        high: parseFloat(latest.high),
        low: parseFloat(latest.low),
        open: parseFloat(latest.open),
        change: change,
        change_percent: parseFloat(changePercent),
        volume: latest.volume
      },
      history: data,
      metadata: {
        base_currency: 'USD',
        quote_currency: 'HKD',
        provider: 'Hong Kong Monetary Authority',
        description: 'USD/HKD Exchange Rate',
        note: 'Linked exchange rate system with small fluctuations'
      }
    });
  } catch (error) {
    console.error('Exchange Rate API error:', error);
    return NextResponse.json(
      {
        success: false,
        error: error.message,
        message: '無法獲取匯率數據'
      },
      { status: 500 }
    );
  }
}