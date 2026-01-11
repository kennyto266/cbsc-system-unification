'use client';

import { SquareCard, SquareBadge, SquareButton } from '@/components/ui';
import {
  PlusIcon,
  TrendingUp as TrendingUp,
  FileTextIcon,
  DownloadIcon
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import HiborRatesTable from '@/components/dashboard/HiborRatesTable';
import MarketRegimeIndicator from '@/components/dashboard/MarketRegimeIndicator';
import GovernmentDataOverview from '@/components/dashboard/GovernmentDataOverview';
import NorthboundFundsTable from '@/components/dashboard/NorthboundFundsTable';
import RealDataOverview from '@/components/dashboard/RealDataOverview';
import MarketSentimentCard from '@/components/dashboard/MarketSentimentCard';
import TopCBBCContracts from '@/components/dashboard/TopCBBCContracts';

// 導入動態組件
import DashboardStats from '@/components/dashboard/DashboardStats';
import RecentStrategies from '@/components/dashboard/RecentStrategies';
import StrategyPerformanceChart from '@/components/dashboard/StrategyPerformanceChart';
import StrategyToggle from '@/components/dashboard/StrategyToggle';

export default function DashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState<string | null>(null);

  // API基础URL - 假设后端在3004端口
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3004';

  // 处理创建新策略
  const handleCreateStrategy = async () => {
    console.log('=== handleCreateStrategy 被调用 ===');
    setLoading('create');
    try {
      // 这里可以打开一个模态框或者跳转到创建页面
      // 现在先跳转到策略管理页面
      console.log('正在跳转到策略创建页面...');
      router.push('/dashboard/strategies?action=create');
    } catch (error) {
      console.error('创建策略失败:', error);
      alert('创建策略失败，请稍后重试');
    } finally {
      setLoading(null);
    }
  };

  // 处理查看市场数据
  const handleViewMarketData = async () => {
    console.log('=== handleViewMarketData 被调用 ===');
    setLoading('market');
    try {
      // 使用前端代理路由
      console.log('正在获取市场数据...');
      const response = await fetch('/api/data/stocks');

      if (response.ok) {
        const data = await response.json();
        console.log('市场数据:', data);

        // 在新窗口中显示市场数据
        const newWindow = window.open('', '_blank');
        const marketStatus = data.market_status || 'Unknown';
        const source = data.source || 'Unknown';
        const lastUpdated = new Date(data.last_updated).toLocaleString('zh-TW', {
          timeZone: 'Asia/Taipei',
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        });

        newWindow.document.write(`
          <html>
            <head>
              <title>实时市场数据</title>
              <meta charset="UTF-8">
              <style>
                body {
                  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                  padding: 20px;
                  background-color: #f5f5f5;
                  margin: 0;
                }
                .container {
                  max-width: 1200px;
                  margin: 0 auto;
                  background: white;
                  padding: 30px;
                  border-radius: 10px;
                  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 { color: #333; margin-bottom: 10px; }
                .info-bar {
                  display: flex;
                  gap: 20px;
                  margin-bottom: 20px;
                  padding: 15px;
                  background: #f8f9fa;
                  border-radius: 5px;
                  font-size: 14px;
                  color: #666;
                }
                .info-item {
                  display: flex;
                  align-items: center;
                  gap: 5px;
                }
                .status-badge {
                  padding: 4px 12px;
                  border-radius: 20px;
                  font-weight: 500;
                  font-size: 13px;
                }
                .status-open { background: #d4edda; color: #155724; }
                .status-closed { background: #f8d7da; color: #721c24; }
                table {
                  border-collapse: collapse;
                  width: 100%;
                  margin-top: 20px;
                  border-radius: 8px;
                  overflow: hidden;
                  box-shadow: 0 0 20px rgba(0,0,0,0.05);
                }
                th, td {
                  border: none;
                  padding: 15px;
                  text-align: left;
                  border-bottom: 1px solid #eee;
                }
                th {
                  background-color: #2c3e50;
                  color: white;
                  font-weight: 600;
                  font-size: 14px;
                  text-transform: uppercase;
                  letter-spacing: 0.5px;
                }
                tr:last-child td { border-bottom: none; }
                tr:hover { background-color: #f8f9fa; }
                .symbol { font-weight: 600; color: #3498db; }
                .name { color: #555; }
                .price { font-size: 18px; font-weight: 600; }
                .positive { color: #27ae60; }
                .negative { color: #e74c3c; }
                .neutral { color: #95a5a6; }
                .volume { font-size: 14px; color: #7f8c8d; }
                .source-indicator {
                  display: inline-block;
                  padding: 2px 8px;
                  border-radius: 4px;
                  font-size: 12px;
                  margin-left: 10px;
                }
                .source-real { background: #d4edda; color: #155724; }
                .source-simulated { background: #fff3cd; color: #856404; }
                .footer {
                  margin-top: 30px;
                  padding-top: 20px;
                  border-top: 1px solid #eee;
                  color: #666;
                  font-size: 14px;
                  text-align: center;
                }
                @keyframes pulse {
                  0% { opacity: 1; }
                  50% { opacity: 0.5; }
                  100% { opacity: 1; }
                }
                .live-indicator {
                  display: inline-block;
                  width: 8px;
                  height: 8px;
                  background: #e74c3c;
                  border-radius: 50%;
                  margin-right: 5px;
                  animation: pulse 2s infinite;
                }
              </style>
            </head>
            <body>
              <div class="container">
                <h1>
                  <span class="live-indicator"></span>
                  实时市场数据
                  <span class="source-indicator ${source === 'Real-time market data' ? 'source-real' : 'source-simulated'}">
                    ${source === 'Real-time market data' ? '实时数据' : '模拟数据'}
                  </span>
                </h1>

                <div class="info-bar">
                  <div class="info-item">
                    <strong>市场状态:</strong>
                    <span class="status-badge ${marketStatus === 'Market Open' ? 'status-open' : 'status-closed'}">
                      ${marketStatus === 'Market Open' ? '🟢 交易中' : '🔴 已休市'}
                    </span>
                  </div>
                  <div class="info-item">
                    <strong>数据源:</strong> ${source}
                  </div>
                  <div class="info-item">
                    <strong>更新时间:</strong> ${lastUpdated}
                  </div>
                </div>

                <table>
                  <thead>
                    <tr>
                      <th>代码</th>
                      <th>公司名称</th>
                      <th>当前价格</th>
                      <th>涨跌额</th>
                      <th>涨跌幅</th>
                      <th>成交量</th>
                      <th>日内最高</th>
                      <th>日内最低</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${data.data.map(stock => {
                      const changeClass = stock.change > 0 ? 'positive' : stock.change < 0 ? 'negative' : 'neutral';
                      const changeSymbol = stock.change > 0 ? '+' : '';
                      return `
                        <tr>
                          <td class="symbol">${stock.symbol}</td>
                          <td class="name">${stock.name}</td>
                          <td class="price">$${stock.price.toFixed(2)}</td>
                          <td class="${changeClass}">${changeSymbol}${stock.change.toFixed(2)}</td>
                          <td class="${changeClass}">${changeSymbol}${stock.change_percent.toFixed(2)}%</td>
                          <td class="volume">${(stock.volume / 1000000).toFixed(2)}M</td>
                          <td>$${(stock.high || 0).toFixed(2)}</td>
                          <td>$${(stock.low || 0).toFixed(2)}</td>
                        </tr>
                      `;
                    }).join('')}
                  </tbody>
                </table>

                ${data.message ? `
                  <div class="footer">
                    <p>${data.message}</p>
                  </div>
                ` : ''}
              </div>
            </body>
          </html>
        `);
        newWindow.document.close();
      } else {
        throw new Error('获取市场数据失败');
      }
    } catch (error) {
      console.error('获取市场数据失败:', error);
      alert('获取市场数据失败，请稍后重试');
    } finally {
      setLoading(null);
    }
  };

  // 处理运行回测
  const handleRunBacktest = async () => {
    console.log('=== handleRunBacktest 被调用 ===');
    setLoading('backtest');
    try {
      console.log('正在启动回测...');
      // 使用代理避免CORS問題
      const response = await fetch('/api/backtest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          strategy_id: '1', // 示例策略ID
          start_date: '2023-01-01',
          end_date: '2023-12-31',
        }),
      });

      if (response.ok) {
        const result = await response.json();
        alert('回测已启动！结果ID: ' + result.result_id);
      } else {
        // 嘗試直接調用後端API
        console.log('尝试直接调用后端API...');
        const directResponse = await fetch(`${API_BASE_URL}/api/backtest/strategy`, {
          method: 'POST',
          mode: 'cors',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            strategy_id: '1',
            start_date: '2023-01-01',
            end_date: '2023-12-31',
          }),
        });

        if (directResponse.ok) {
          const result = await directResponse.json();
          alert('回测已启动！结果ID: ' + result.result_id);
        } else {
          throw new Error('回测启动失败');
        }
      }
    } catch (error) {
      console.error('运行回测失败:', error);
      // 顯示更具體的錯誤信息
      if (error.message.includes('Failed to fetch')) {
        alert('無法連接到後端服務，請確保後端運行在端口 3004');
      } else {
        alert('运行回测失败: ' + error.message);
      }
    } finally {
      setLoading(null);
    }
  };

  // 处理导出报告
  const handleExportReport = async () => {
    console.log('=== handleExportReport 被调用 ===');
    setLoading('export');
    try {
      console.log('正在导出报告...');
      // 先嘗試通過代理導出
      const response = await fetch('/api/export/strategy/1?format=pdf');

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `strategy_report_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        // 嘗試直接調用後端API
        console.log('尝试直接调用后端API...');
        const directResponse = await fetch(`${API_BASE_URL}/api/v1/strategies/1/report?format=pdf`, {
          mode: 'cors',
        });

        if (directResponse.ok) {
          const blob = await directResponse.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `strategy_report_${new Date().toISOString().split('T')[0]}.pdf`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
        } else {
          throw new Error('导出失败');
        }
      }
    } catch (error) {
      console.error('导出报告失败:', error);
      if (error.message.includes('Failed to fetch')) {
        alert('無法連接到後端服務，請確保後端運行在端口 3004');
      } else {
        alert('导出报告失败: ' + error.message);
      }
    } finally {
      setLoading(null);
    }
  };
  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">儀表板</h1>
        <p className="mt-2 text-gray-600">歡迎回來！這是您的策略管理概覽。</p>
      </div>

      {/* Stats - 使用動態組件 */}
      <DashboardStats />

      {/* Strategy Performance Chart */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">策略表現分析</h2>
        <StrategyPerformanceChart />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Market Overview with Non-Price Data */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Government Data Overview - Left 2 columns */}
        <div className="lg:col-span-2 space-y-6">
          <GovernmentDataOverview />
          <HiborRatesTable />
          <NorthboundFundsTable />
        </div>

        {/* Market Regime Indicator - Right 1 column */}
        <div className="space-y-6">
          <MarketRegimeIndicator />
          <RealDataOverview />
        </div>
      </div>

      {/* CBSC Market Data */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <MarketSentimentCard />
        <TopCBBCContracts />
      </div>

      {/* Strategy Toggle - 策略控制 */}
      <StrategyToggle />

      {/* Recent Strategies - 使用動態組件 */}
      <RecentStrategies />

      {/* Quick Actions */}
      <SquareCard>
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">快速操作</h3>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            <SquareButton
              variant="primary"
              className="w-full"
              onClick={handleCreateStrategy}
              loading={loading === 'create'}
              icon={<PlusIcon size={16} />}
            >
              創建新策略
            </SquareButton>
            <SquareButton
              variant="outline"
              className="w-full"
              onClick={handleViewMarketData}
              loading={loading === 'market'}
              icon={<TrendingUp size={16} />}
            >
              查看市場數據
            </SquareButton>
            <SquareButton
              variant="outline"
              className="w-full"
              onClick={handleRunBacktest}
              loading={loading === 'backtest'}
              icon={<FileTextIcon size={16} />}
            >
              運行回測
            </SquareButton>
            <SquareButton
              variant="outline"
              className="w-full"
              onClick={handleExportReport}
              loading={loading === 'export'}
              icon={<DownloadIcon size={16} />}
            >
              導出報告
            </SquareButton>
          </div>
        </div>
      </SquareCard>
      </div>
    </div>
  );
}