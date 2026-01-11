import { NextRequest, NextResponse } from 'next/server';
import { readFile } from 'fs/promises';
import { parse } from 'csv-parse/sync';

// CBBC 數據文件路徑
const CBBC_DATA_PATH = 'C:\\Users\\Penguin8n\\爬蟲\\hkex爬蟲\\data\\top_stocks';

interface CBBCData {
  Date: string;
  Rank: string;
  Code: string;
  Ticker: string;
  Product: string;
  Name_CHI: string;
  Currency: string;
  Shares_Traded: string;
  Turnover_HKD: string;
  High: string;
  Low: string;
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const type = searchParams.get('type') || 'sentiment';
    const days = parseInt(searchParams.get('days') || '7');

    // 讀取最新的 CBBC 數據文件
    let cbbcData: CBBCData[] = [];
    const dataSources = [
      { file: 'cbbc_latest_fixed.csv', name: 'CBBC 最新數據' },
      { file: 'latest_cbbc_data.csv', name: 'CBBC 備用數據' },
      { file: 'top_stocks_by_shares_all.csv', name: '歷史數據（按成交量）' },
      { file: 'top_stocks_by_turnover_all.csv', name: '歷史數據（按成交額）' }
    ];

    // 按日期排序查找最新文件
    const date = new Date();
    for (let i = 0; i < 30; i++) {
      const checkDate = new Date(date);
      checkDate.setDate(checkDate.getDate() - i);
      const dateStr = checkDate.toISOString().slice(0, 10).replace(/-/g, '');

      // 檢查按日期的文件
      dataSources.unshift({
        file: `top_stocks_by_shares_${checkDate.toISOString().slice(0, 10)}.csv`,
        name: `日數據 ${checkDate.toISOString().slice(0, 10)}`
      });
    }

    // 嘗試讀取可用的數據文件
    for (const source of dataSources) {
      try {
        const csvContent = await readFile(`${CBBC_DATA_PATH}\\${source.file}`, 'utf-8');
        const parsedData = parse(csvContent, {
          columns: true,
          skip_empty_lines: true
        });

        if (parsedData.length > 0) {
          cbbcData = parsedData;
          console.log(`✅ 成功讀取 ${source.name}，共 ${cbbcData.length} 條記錄`);

          // 如果是累積數據文件，按日期過濾只取最新記錄
          if (source.file.includes('_all.csv')) {
            const latestDate = cbbcData[0]?.Date;
            if (latestDate) {
              cbbcData = cbbcData.filter(d => d.Date === latestDate);
              console.log(`📅 過濾最新日期 ${latestDate} 的數據，共 ${cbbcData.length} 條記錄`);
            }
          }
          break;
        }
      } catch (error) {
        // 文件不存在或無法讀取，繼續下一個
        continue;
      }
    }

    // 如果沒有真實數據，返回錯誤
    if (cbbcData.length === 0) {
      return NextResponse.json(
        {
          success: false,
          error: 'No real CBBC data available',
          message: '爬蟲數據文件不存在，請先運行爬蟲獲取數據'
        },
        { status: 404 }
      );
    }

    // 根據請求類型返回不同的數據
    switch (type) {
      case 'sentiment':
        return getMarketSentiment(cbbcData);
      case 'top-10':
        return getTopContracts(cbbcData);
      case 'historical':
        return getHistoricalData(cbbcData, days);
      default:
        return getDashboardSummary(cbbcData);
    }

  } catch (error) {
    console.error('CBBC API error:', error);
    return NextResponse.json(
      {
        success: false,
        error: error.message,
        message: '無法獲取 CBSC 數據'
      },
      { status: 500 }
    );
  }
}


// 計算市場情緒指標
function getMarketSentiment(data: CBBCData[]) {
  // 根據 Product 字段最後一個字符判斷牛熊（R=牛證，P=熊證）
  const bullCount = data.filter(d => d.Product && d.Product.endsWith('R')).length;
  const bearCount = data.filter(d => d.Product && d.Product.endsWith('P')).length;
  const totalContracts = bullCount + bearCount;

  // 計算總成交額
  const totalTurnover = data.reduce((sum, item) => {
    const turnover = parseFloat(item.Turnover_HKD.replace(/,/g, '')) || 0;
    return sum + turnover;
  }, 0);

  // 計算平均成交量
  const avgVolume = data.reduce((sum, item) => {
    const volume = parseFloat(item.Shares_Traded.replace(/,/g, '')) || 0;
    return sum + volume;
  }, 0) / data.length;

  // 恐懼貪婪指數 (基於牛熊比例)
  const bullBearRatio = totalContracts > 0 ? bullCount / totalContracts : 0.5;
  const fearGreedIndex = Math.round(bullBearRatio * 100);

  // RSI - 基於牛熊比例計算
  const rsi = Math.round(40 + (bullBearRatio * 40));

  let sentiment = '中性';
  let sentimentColor = 'yellow';
  if (fearGreedIndex > 60) {
    sentiment = '貪婪';
    sentimentColor = 'green';
  } else if (fearGreedIndex < 40) {
    sentiment = '恐懼';
    sentimentColor = 'red';
  }

  return NextResponse.json({
    success: true,
    data: {
      fear_greed_index: fearGreedIndex,
      fear_greed_level: sentiment,
      fear_greed_color: sentimentColor,
      bull_count: bullCount,
      bear_count: bearCount,
      bull_bear_ratio: bullBearRatio.toFixed(2),
      total_turnover: totalTurnover.toFixed(0),
      avg_volume: avgVolume.toFixed(0),
      rsi: rsi.toFixed(2),
      volatility: (15 + (fearGreedIndex - 50) * 0.3).toFixed(2),
      last_updated: new Date().toISOString()
    }
  });
}

// 獲取前十名合約
function getTopContracts(data: CBBCData[]) {
  // 按成交額排序
  const sortedData = data
    .filter(item => parseFloat(item.Turnover_HKD.replace(/,/g, '')) > 0)
    .sort((a, b) => {
      const turnoverA = parseFloat(a.Turnover_HKD.replace(/,/g, '')) || 0;
      const turnoverB = parseFloat(b.Turnover_HKD.replace(/,/g, '')) || 0;
      return turnoverB - turnoverA;
    })
    .slice(0, 10);

  return NextResponse.json({
    success: true,
    data: sortedData.map(item => ({
      rank: parseInt(item.Rank),
      code: item.Code,
      ticker: item.Ticker,
      name: item.Name_CHI,
      type: item.Product && item.Product.endsWith('R') ? '牛證' : '熊證',
      currency: item.Currency,
      volume: parseFloat(item.Shares_Traded.replace(/,/g, '')) || 0,
      turnover: parseFloat(item.Turnover_HKD.replace(/,/g, '')) || 0,
      high: parseFloat(item.High) || 0,
      low: parseFloat(item.Low) || 0
    }))
  });
}

// 獲取歷史數據趨勢
function getHistoricalData(data: CBBCData[], days: number) {
  // 由於只有單日數據，返回當前數據點
  if (data.length === 0) {
    return NextResponse.json(
      {
        success: false,
        error: 'No historical data available',
        message: '暫無歷史數據'
      },
      { status: 404 }
    );
  }

  // 計算當日市場情緒
  // 根據 Product 字段最後一個字符判斷牛熊（R=牛證，P=熊證）
  const bullCount = data.filter(d => d.Product && d.Product.endsWith('R')).length;
  const bearCount = data.filter(d => d.Product && d.Product.endsWith('P')).length;
  const totalContracts = bullCount + bearCount;
  const bullBearRatio = totalContracts > 0 ? bullCount / totalContracts : 0.5;
  const sentiment = Math.round(bullBearRatio * 100);

  // 計算總成交量和成交額
  const totalVolume = data.reduce((sum, item) => {
    const volume = parseFloat(item.Shares_Traded.replace(/,/g, '')) || 0;
    return sum + volume;
  }, 0);

  const totalTurnover = data.reduce((sum, item) => {
    const turnover = parseFloat(item.Turnover_HKD.replace(/,/g, '')) || 0;
    return sum + turnover;
  }, 0);

  const historicalData = [{
    date: data[0]?.Date || new Date().toISOString().slice(0, 10),
    sentiment: sentiment,
    volume: totalVolume,
    turnover: totalTurnover
  }];

  return NextResponse.json({
    success: true,
    data: historicalData,
    note: '目前只有單日數據，需要運行爬蟲獲取更多歷史數據'
  });
}

// 獲取儀表板摘要
function getDashboardSummary(data: CBBCData[]) {
  const sentiment = getMarketSentiment(data);
  const topContracts = getTopContracts(data);

  // 解析兩個響應的數據
  const sentimentData = JSON.parse(sentiment.body as string);
  const contractsData = JSON.parse(topContracts.body as string);

  return NextResponse.json({
    success: true,
    data: {
      sentiment: sentimentData.data,
      top_contracts: contractsData.data,
      summary: {
        total_contracts: data.length,
        active_bulls: sentimentData.data.bull_count,
        active_bears: sentimentData.data.bear_count,
        market_mood: sentimentData.data.fear_greed_level,
        total_turnover: sentimentData.data.total_turnover
      }
    }
  });
}