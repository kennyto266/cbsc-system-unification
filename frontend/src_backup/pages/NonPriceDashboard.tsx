import React, { useState, useEffect } from 'react';
import { Layout, Row, Col, Card, Tabs, Button, Space, Switch, Select, message } from 'antd';
import {
  FullscreenOutlined,
  SettingOutlined,
  ReloadOutlined,
  DownloadOutlined,
  LineChartOutlined,
  DashboardOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import { NonPriceDataProvider } from '../components/NonPrice/Common/NonPriceDataProvider';
import HIBORDisplay from '../components/NonPrice/MacroIndicators/HIBORDisplay';
import MonetaryBaseChart from '../components/NonPrice/MacroIndicators/MonetaryBaseChart';
import SentimentGauge from '../components/NonPrice/SentimentAnalysis/SentimentGauge';
import PerformanceComparison from '../components/NonPrice/StrategyComparison/PerformanceComparison';

const { Content } = Layout;
const { TabPane } = Tabs;

interface NonPriceDashboardProps {
  defaultSymbols?: string[];
  showHeader?: boolean;
}

const NonPriceDashboard: React.FC<NonPriceDashboardProps> = ({
  defaultSymbols = ['0700.HK', '9988.HK', '0941.HK'],
  showHeader = true
}) => {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [selectedSymbol, setSelectedSymbol] = useState<string>(defaultSymbols[0]);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);
  const [refreshInterval, setRefreshInterval] = useState<number>(60);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  // 切換全屏模式
  const toggleFullscreen = () => {
    if (!isFullscreen) {
      document.documentElement.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
    setIsFullscreen(!isFullscreen);
  };

  // 刷新所有組件
  const refreshAll = () => {
    message.success('所有組件已刷新');
    // 觸發子組件的重新渲染
    window.location.reload();
  };

  // 導出數據
  const exportData = () => {
    message.info('導出功能開發中...');
  };

  // 組件配置
  const componentSettings = {
    hibor: {
      showRealTime: autoRefresh,
      timeframe: '1M',
      height: 300
    },
    monetary: {
      timeframe: '3M',
      showComparison: true,
      showRealTime: autoRefresh,
      height: 350
    },
    sentiment: {
      showTrend: true,
      showDetails: true,
      autoRefresh: autoRefresh
    },
    performance: {
      defaultPeriod: '3M',
      showSettings: true,
      height: 400
    }
  };

  return (
    <NonPriceDataProvider>
      <Layout className="non-price-dashboard">
        {showHeader && (
          <div className="dashboard-header p-4 bg-white border-b">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold mb-2">非價格策略分析儀表板</h1>
                <p className="text-gray-600">基於宏觀指標和市場情緒的交易策略分析</p>
              </div>
              <div className="flex items-center gap-3">
                <Space>
                  <span className="text-sm">自動刷新</span>
                  <Switch
                    checked={autoRefresh}
                    onChange={setAutoRefresh}
                    checkedChildren="開"
                    unCheckedChildren="關"
                  />
                </Space>
                <Select
                  value={refreshInterval}
                  onChange={setRefreshInterval}
                  style={{ width: 120 }}
                  disabled={!autoRefresh}
                >
                  <Select.Option value={30}>30秒</Select.Option>
                  <Select.Option value={60}>1分鐘</Select.Option>
                  <Select.Option value={120}>2分鐘</Select.Option>
                  <Select.Option value={300}>5分鐘</Select.Option>
                </Select>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={refreshAll}
                >
                  刷新
                </Button>
                <Button
                  icon={<DownloadOutlined />}
                  onClick={exportData}
                >
                  導出
                </Button>
                <Button
                  icon={<FullscreenOutlined />}
                  onClick={toggleFullscreen}
                >
                  全屏
                </Button>
              </div>
            </div>
          </div>
        )}

        <Content className="p-4">
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={[
              {
                key: 'overview',
                label: (
                  <span>
                    <DashboardOutlined />
                    總覽
                  </span>
                ),
                children: (
                  <Row gutter={[16, 16]}>
                    {/* 宏觀指標行 */}
                    <Col xs={24} lg={12}>
                      <HIBORDisplay {...componentSettings.hibor} />
                    </Col>
                    <Col xs={24} lg={12}>
                      <MonetaryBaseChart {...componentSettings.monetary} />
                    </Col>

                    {/* 情緒分析行 */}
                    <Col xs={24} lg={12}>
                      <SentimentGauge
                        symbol={selectedSymbol}
                        {...componentSettings.sentiment}
                      />
                    </Col>
                    <Col xs={24} lg={12}>
                      <Card
                        title="市場情緒對比"
                        extra={
                          <Select
                            value={selectedSymbol}
                            onChange={setSelectedSymbol}
                            style={{ width: 120 }}
                            size="small"
                          >
                            {defaultSymbols.map(symbol => (
                              <Select.Option key={symbol} value={symbol}>
                                {symbol}
                              </Select.Option>
                            ))}
                          </Select>
                        }
                      >
                        {/* 可以添加多個股票的情緒對比 */}
                        <div className="text-center py-8 text-gray-500">
                          多股情緒對比功能開發中...
                        </div>
                      </Card>
                    </Col>
                  </Row>
                )
              },
              {
                key: 'macro',
                label: (
                  <span>
                    <LineChartOutlined />
                    宏觀指標
                  </span>
                ),
                children: (
                  <Row gutter={[16, 16]}>
                    <Col xs={24} lg={8}>
                      <HIBORDisplay {...componentSettings.hibor} />
                    </Col>
                    <Col xs={24} lg={8}>
                      <MonetaryBaseChart {...componentSettings.monetary} />
                    </Col>
                    <Col xs={24} lg={8}>
                      <Card title="匯率走勢" className="h-full">
                        <div className="text-center py-12 text-gray-500">
                          USD/HKD 匯率圖表開發中...
                        </div>
                      </Card>
                    </Col>
                  </Row>
                )
              },
              {
                key: 'sentiment',
                label: (
                  <span>
                    <BarChartOutlined />
                    情緒分析
                  </span>
                ),
                children: (
                  <Row gutter={[16, 16]}>
                    <Col xs={24} lg={12}>
                      <SentimentGauge
                        symbol={selectedSymbol}
                        {...componentSettings.sentiment}
                      />
                    </Col>
                    <Col xs={24} lg={12}>
                      <Card
                        title="情緒熱力圖"
                        extra={
                          <Select
                            value={selectedSymbol}
                            onChange={setSelectedSymbol}
                            style={{ width: 120 }}
                            size="small"
                          >
                            {defaultSymbols.map(symbol => (
                              <Select.Option key={symbol} value={symbol}>
                                {symbol}
                              </Select.Option>
                            ))}
                          </Select>
                        }
                      >
                        <div className="text-center py-12 text-gray-500">
                          情緒熱力圖開發中...
                        </div>
                      </Card>
                    </Col>
                  </Row>
                )
              },
              {
                key: 'performance',
                label: (
                  <span>
                    <BarChartOutlined />
                    策略比較
                  </span>
                ),
                children: (
                  <Row gutter={[16, 16]}>
                    <Col span={24}>
                      <PerformanceComparison {...componentSettings.performance} />
                    </Col>
                  </Row>
                )
              }
            ]}
          />

          {/* 市場洞察面板 */}
          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col span={24}>
              <Card
                title="市場洞察"
                extra={
                  <Button icon={<SettingOutlined />} size="small">
                    配置
                  </Button>
                }
              >
                <Row gutter={16}>
                  <Col xs={24} md={8}>
                    <div className="p-4 bg-blue-50 rounded">
                      <h4 className="font-medium mb-2 text-blue-800">宏觀環境</h4>
                      <ul className="text-sm text-blue-700 space-y-1">
                        <li>• HIBOR利率維持穩定，流動性適中</li>
                        <li>• 貨幣基礎呈現溫和增長趨勢</li>
                        <li>• 匯率波動性降低，市場預期趨於一致</li>
                      </ul>
                    </div>
                  </Col>
                  <Col xs={24} md={8}>
                    <div className="p-4 bg-green-50 rounded">
                      <h4 className="font-medium mb-2 text-green-800">情緒指標</h4>
                      <ul className="text-sm text-green-700 space-y-1">
                        <li>• 市場情緒整體偏中性，略偏樂觀</li>
                        <li>• 社交媒體情緒指數緩慢回升</li>
                        <li>• 投資者信心指數維持在健康水平</li>
                      </ul>
                    </div>
                  </Col>
                  <Col xs={24} md={8}>
                    <div className="p-4 bg-orange-50 rounded">
                      <h4 className="font-medium mb-2 text-orange-800">交易信號</h4>
                      <ul className="text-sm text-orange-700 space-y-1">
                        <li>• 建議關注非價格策略的配置機會</li>
                        <li>• 組合策略在當前環境下表現較佳</li>
                        <li>• 風險管理建議：適度降低槓桿</li>
                      </ul>
                    </div>
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>
        </Content>
      </Layout>
    </NonPriceDataProvider>
  );
};

export default NonPriceDashboard;