import { NextRequest, NextResponse } from 'next/server';

// 使用 Twelve Data 免費 API (每天 800 次請求)
const TWELVE_DATA_API_KEY = process.env.TWELVE_DATA_API_KEY || 'demo';

// 使用 IEX Cloud 免費 API (每月 50,000 次請求)
const IEX_API_KEY = process.env.IEX_API_KEY || 'demo';

// 股票列表（支持美股和台股）
const DEFAULT_SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX'];

// 使用 Financial Modeling Prep 免費 API
async function getFMPData(symbol: string) {
  try {
    const response = await fetch(
      `https://financialmodelingprep.com/api/v3/quote/${symbol}?apikey=demo`,
      {
        method: 'GET',
        headers: {
          'Accept': 'application/json'
        }
      }
    );

    if (response.ok) {
      const data = await response.json();
      if (data && data.length > 0) {
        const quote = data[0];
        return {
          symbol: quote.symbol || symbol,
          name: quote.name || symbol,
          price: quote.price || 0,
          change: quote.change || 0,
          change_percent: quote.changesPercentage || 0,
          volume: quote.volume || 0,
          high: quote.dayHigh || 0,
          low: quote.dayLow || 0,
          open: quote.open || 0,
          previous_close: quote.previousClose || 0,
          market_cap: quote.marketCap || 0
        };
      }
    }
  } catch (error) {
    console.error(`Error fetching FMP data for ${symbol}:`, error);
  }
  return null;
}

// 使用 Alpha Vantage 免費 API
async function getAlphaVantageData(symbol: string) {
  try {
    const response = await fetch(
      `https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=${symbol}&apikey=demo`,
      {
        method: 'GET'
      }
    );

    if (response.ok) {
      const data = await response.json();
      if (data['Global Quote']) {
        const quote = data['Global Quote'];
        return {
          symbol: symbol,
          name: symbol,
          price: parseFloat(quote['05. price']) || 0,
          change: parseFloat(quote['09. change']) || 0,
          change_percent: parseFloat(quote['10. change percent'].replace('%', '')) || 0,
          volume: parseInt(quote['06. volume']) || 0
        };
      }
    }
  } catch (error) {
    console.error(`Error fetching Alpha Vantage data for ${symbol}:`, error);
  }
  return null;
}

// 使用 Yahoo Finance 爬蟲 (通過公共端點)
async function getYahooData(symbol: string) {
  try {
    const response = await fetch(
      `https://query1.finance.yahoo.com/v8/finance/chart/${symbol}`,
      {
        method: 'GET',
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
      }
    );

    if (response.ok) {
      const data = await response.json();
      const result = data.chart?.result?.[0];

      if (result && result.meta) {
        const meta = result.meta;
        const currentPrice = result.indicators?.quote?.[0]?.close?.[result.indicators.quote[0].close.length - 1] || meta.regularMarketPrice;
        const previousClose = meta.previousClose || 0;

        return {
          symbol: symbol,
          name: meta.longName || meta.shortName || symbol,
          price: currentPrice || 0,
          change: (currentPrice || 0) - previousClose,
          change_percent: previousClose > 0 ? ((currentPrice - previousClose) / previousClose * 100) : 0,
          volume: meta.regularMarketVolume || 0,
          high: meta.regularMarketDayHigh || 0,
          low: meta.regularMarketDayLow || 0,
          open: meta.regularMarketOpen || 0,
          previous_close: previousClose,
          currency: meta.currency || 'USD',
          market_state: meta.marketState || 'CLOSED'
        };
      }
    }
  } catch (error) {
    console.error(`Error fetching Yahoo data for ${symbol}:`, error);
  }
  return null;
}

// 獲取市場數據（嘗試多個源）
async function getMarketData(symbol: string) {
  // 嘗試按優先順序獲取數據
  const dataSources = [
    () => getYahooData(symbol),
    () => getFMPData(symbol),
    () => getAlphaVantageData(symbol)
  ];

  for (const dataSource of dataSources) {
    try {
      const data = await dataSource();
      if (data && data.price > 0) {
        return data;
      }
    } catch (error) {
      console.error(`Data source error for ${symbol}:`, error);
    }
  }

  // 生成模擬數據（基於歷史價格的隨機波動）
  const basePrice = {
    'AAPL': 195, 'MSFT': 380, 'GOOGL': 140, 'AMZN': 155, 'TSLA': 250,
    'META': 350, 'NVDA': 490, 'NFLX': 485, 'AMD': 180, 'BABA': 85
  }[symbol] || 100;

  const change = (Math.random() - 0.5) * basePrice * 0.03; // +/- 3%
  const changePercent = (change / basePrice) * 100;

  return {
    symbol,
    name: `${symbol} Corp`,
    price: Number((basePrice + change).toFixed(2)),
    change: Number(change.toFixed(2)),
    change_percent: Number(changePercent.toFixed(2)),
    volume: Math.floor(Math.random() * 50000000),
    high: Number((basePrice + Math.abs(change) * 1.5).toFixed(2)),
    low: Number((basePrice - Math.abs(change) * 1.5).toFixed(2)),
    open: Number((basePrice + change * 0.5).toFixed(2)),
    source: 'Simulated'
  };
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const symbols = searchParams.get('symbols')?.split(',') || DEFAULT_SYMBOLS;

    console.log(`Fetching market data for symbols: ${symbols.join(', ')}`);

    // 並行獲取所有股票數據
    const stockPromises = symbols.map(symbol => getMarketData(symbol));
    const stockData = await Promise.all(stockPromises);

    // 過濾並驗證數據
    const validStocks = stockData.filter(stock => {
      if (!stock) return false;
      if (stock.price <= 0) return false;
      return true;
    });

    // 確定數據源類型
    const hasRealData = validStocks.some(stock => !stock.source);
    const dataSource = hasRealData ? 'Real-time market data' : 'Simulated market data';

    // 按市值或成交量排序
    validStocks.sort((a, b) => (b.volume || 0) - (a.volume || 0));

    const response = {
      success: true,
      data: validStocks,
      source: dataSource,
      last_updated: new Date().toISOString(),
      market_status: new Date().getHours() >= 9 && new Date().getHours() <= 16 ? 'Market Open' : 'Market Closed',
      message: hasRealData
        ? '成功獲取實時市場數據'
        : '使用模擬數據（真實 API 不可用或未配置）'
    };

    console.log(`Successfully fetched ${validStocks.length} stocks from ${dataSource}`);

    return NextResponse.json(response);

  } catch (error) {
    console.error('Market Data API error:', error);

    return NextResponse.json({
      success: false,
      error: error.message,
      message: '獲取市場數據時發生錯誤'
    }, { status: 500 });
  }
}

// 支持 POST 請求以批量獲取數據
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const symbols = body.symbols || DEFAULT_SYMBOLS;

    // 轉發到 GET 處理器
    const url = new URL(request.url);
    url.searchParams.set('symbols', symbols.join(','));

    const response = await GET(new Request(url.toString(), {
      method: 'GET',
      headers: request.headers
    }));

    return response;
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: error.message
    }, { status: 400 });
  }
}

export async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}