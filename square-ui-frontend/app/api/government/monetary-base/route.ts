import { NextRequest, NextResponse } from 'next/server';

// 模擬貨幣基礎數據
const generateMonetaryBaseData = (days: number = 30) => {
  const data = [];
  const baseAmount = 2100000000000; // 2.1萬億港幣

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);

    const growth = 1 + (Math.random() - 0.4) * 0.005; // 0.999 to 1.003

    data.push({
      date: date.toISOString().split('T')[0],
      total: Math.round(baseAmount * growth),
      certificates_of_indebtedness: Math.round(baseAmount * 0.85 * growth),
      government_banknotes_coins: Math.round(baseAmount * 0.15 * growth),
      exchange_fund_bills: Math.round(baseAmount * 0.02 * growth),
      others: Math.round(baseAmount * 0.03 * growth)
    });
  }

  return data;
};

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const days = parseInt(searchParams.get('days') || '30');

    const data = generateMonetaryBaseData(days);
    const latest = data[0];

    // 確保至少有2天數據用於計算變化
    const previous = data.length > 1 ? data[1] : {
      total: latest.total,
      certificates_of_indebtedness: latest.certificates_of_indebtedness,
      government_banknotes_coins: latest.government_banknotes_coins,
      exchange_fund_bills: latest.exchange_fund_bills
    };

    // 轉換為萬億單位
    const formatInTrillions = (value: number) => (value / 100000000000).toFixed(2);

    // 計算變化
    const change = latest.total - previous.total;
    const changePercent = previous.total > 0 ? (change / previous.total * 100).toFixed(2) : '0.00';

    return NextResponse.json({
      success: true,
      source: 'HKMA',
      last_updated: new Date().toISOString(),
      latest: {
        total: latest.total,
        total_trillions: parseFloat(formatInTrillions(latest.total)),
        certificates_of_indebtedness: latest.certificates_of_indebtedness,
        government_banknotes_coins: latest.government_banknotes_coins,
        exchange_fund_bills: latest.exchange_fund_bills,
        change: change,
        change_percent: parseFloat(changePercent)
      },
      history: data.map(item => ({
        ...item,
        total_trillions: parseFloat(formatInTrillions(item.total))
      })),
      metadata: {
        currency: 'HKD',
        unit: 'trillion',
        provider: 'Hong Kong Monetary Authority',
        description: 'Monetary Base Statistics'
      }
    });
  } catch (error) {
    console.error('Monetary Base API error:', error);
    return NextResponse.json(
      {
        success: false,
        error: error.message,
        message: '無法獲取貨幣基礎數據'
      },
      { status: 500 }
    );
  }
}