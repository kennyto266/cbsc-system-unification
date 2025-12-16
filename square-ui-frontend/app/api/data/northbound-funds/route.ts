import { NextRequest, NextResponse } from 'next/server';
import { readFile } from 'fs/promises';
import { parse } from 'csv-parse/sync';

const CSV_PATH = 'C:\\Users\\Penguin8n\\Desktop\\爬蟲\\HKEX_北向資金_5年數據_20250620_224241.csv';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const days = parseInt(searchParams.get('days') || '30');

    try {
      // 讀取 CSV 文件
      const csvContent = await readFile(CSV_PATH, 'utf-8');

      // 解析 CSV
      const records = parse(csvContent, {
        columns: true,
        skip_empty_lines: true
      });

      // 取最後 N 天的數據
      const recentData = records
        .slice(-days)
        .map(record => ({
          date: record.date,
          net_flow: parseFloat(record.northbound_net_flow) || 0,
          source: record.source,
          status: record.status
        }));

      // 計算統計信息
      const latest = recentData[recentData.length - 1];
      const previous = recentData.length > 1 ? recentData[recentData.length - 2] : latest;
      const change = latest.net_flow - previous.net_flow;
      const changePercent = previous.net_flow !== 0 ?
        ((change / Math.abs(previous.net_flow)) * 100).toFixed(2) : '0.00';

      // 計算統計數據
      const netFlows = recentData.map(d => d.net_flow);
      const avgFlow = netFlows.reduce((sum, val) => sum + val, 0) / netFlows.length;
      const maxFlow = Math.max(...netFlows);
      const minFlow = Math.min(...netFlows);
      const positiveDays = netFlows.filter(val => val > 0).length;
      const negativeDays = netFlows.filter(val => val < 0).length;

      return NextResponse.json({
        success: true,
        source: 'HKEX',
        last_updated: new Date().toISOString(),
        summary: {
          latest: {
            date: latest.date,
            net_flow: latest.net_flow,
            change: change,
            change_percent: parseFloat(changePercent)
          },
          statistics: {
            avg_flow: Math.round(avgFlow * 100) / 100,
            max_flow: maxFlow,
            min_flow: minFlow,
            positive_days: positiveDays,
            negative_days: negativeDays,
            total_days: recentData.length
          }
        },
        history: recentData,
        metadata: {
          currency: 'CNY',
          unit: 'million',
          provider: 'Hong Kong Stock Exchange',
          description: 'Northbound Connect Fund Flow',
          note: 'Simulated data based on HKMA Northbound Connect statistics'
        }
      });
    } catch (fileError) {
      console.error('Failed to read CSV file:', fileError);

      // 如果無法讀取文件，返回備用數據
      return generateFallbackData(days);
    }
  } catch (error) {
    console.error('Northbound Funds API error:', error);
    return NextResponse.json(
      {
        success: false,
        error: error.message,
        message: '無法獲取北向資金數據'
      },
      { status: 500 }
    );
  }
}

// 生成備用數據的函數
function generateFallbackData(days: number) {
  const data = [];
  const baseFlow = 2000;

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);

    const randomFlow = (Math.random() - 0.3) * 10000;

    data.push({
      date: date.toISOString().split('T')[0],
      net_flow: Math.round((baseFlow + randomFlow) * 100) / 100,
      source: 'fallback',
      status: 'simulated'
    });
  }

  const latest = data[data.length - 1];
  const previous = data.length > 1 ? data[data.length - 2] : latest;
  const change = latest.net_flow - previous.net_flow;
  const changePercent = previous.net_flow !== 0 ?
    ((change / Math.abs(previous.net_flow)) * 100).toFixed(2) : '0.00';

  return NextResponse.json({
    success: true,
    source: 'Fallback',
    last_updated: new Date().toISOString(),
    summary: {
      latest: {
        date: latest.date,
        net_flow: latest.net_flow,
        change: change,
        change_percent: parseFloat(changePercent)
      },
      statistics: {
        avg_flow: baseFlow,
        max_flow: Math.max(...data.map(d => d.net_flow)),
        min_flow: Math.min(...data.map(d => d.net_flow)),
        positive_days: data.filter(d => d.net_flow > 0).length,
        negative_days: data.filter(d => d.net_flow < 0).length,
        total_days: data.length
      }
    },
    history: data,
    metadata: {
      currency: 'CNY',
      unit: 'million',
      provider: 'Fallback System',
      description: 'Northbound Connect Fund Flow (Simulated)',
      note: 'Unable to access HKEX data file'
    }
  });
}