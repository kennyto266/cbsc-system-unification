import React, { useState, useEffect } from 'react';
import { Card, Statistic, Row, Col, Progress, Tag, Tooltip, Select } from 'antd';
import { PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts';
import {
  SmileOutlined,
  FrownOutlined,
  MehOutlined,
  InfoCircleOutlined,
  ReloadOutlined,
  FireOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';
import { nonPriceService, SentimentData } from '../Common/NonPriceDataProvider';

interface SentimentGaugeProps {
  symbol: string;
  showTrend?: boolean;
  showDetails?: boolean;
  autoRefresh?: boolean;
}

const SentimentGauge: React.FC<SentimentGaugeProps> = ({
  symbol,
  showTrend = true,
  showDetails = true,
  autoRefresh = true
}) => {
  const [sentimentData, setSentimentData] = useState<SentimentData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [historicalData, setHistoricalData] = useState<any[]>([]);

  // 生成模擬情緒數據
  const generateMockData = async () => {
    setLoading(true);

    try {
      // 獲取當前情緒數據
      const data = await nonPriceService.getSentimentData(symbol);
      setSentimentData(data);

      // 生成歷史趨勢數據
      const historical = [];
      let baseSentiment = Math.random() * 0.4 - 0.2; // -0.2 to 0.2

      for (let i = 30; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);

        // 添加隨機波動
        baseSentiment += (Math.random() - 0.5) * 0.1;
        baseSentiment = Math.max(-1, Math.min(1, baseSentiment));

        historical.push({
          date: date.toISOString().split('T')[0],
          sentiment: parseFloat(baseSentiment.toFixed(3)),
          confidence: 0.6 + Math.random() * 0.35
        });
      }

      setHistoricalData(historical);
    } catch (error) {
      console.error('Failed to fetch sentiment data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    generateMockData();

    if (autoRefresh) {
      const interval = setInterval(generateMockData, 60000); // 每分鐘更新
      return () => clearInterval(interval);
    }
  }, [symbol, autoRefresh]);

  // 獲取情緒顏色
  const getSentimentColor = (sentiment: number) => {
    if (sentiment > 0.5) return '#52c41a'; // 強烈看漲 - 綠色
    if (sentiment > 0.2) return '#95de64'; // 看漲 - 淺綠
    if (sentiment > -0.2) return '#1890ff'; // 中性 - 藍色
    if (sentiment > -0.5) return '#ff7875'; // 看跌 - 淺紅
    return '#f5222d'; // 強烈看跌 - 紅色
  };

  // 獲取情緒標籤
  const getSentimentLabel = (sentiment: number) => {
    if (sentiment > 0.6) return '強烈看漲';
    if (sentiment > 0.3) return '看漲';
    if (sentiment > 0.1) return '偏漲';
    if (sentiment > -0.1) return '中性';
    if (sentiment > -0.3) return '偏跌';
    if (sentiment > -0.6) return '看跌';
    return '強烈看跌';
  };

  // 獲取情緒圖標
  const getSentimentIcon = (sentiment: number) => {
    if (sentiment > 0.2) return <SmileOutlined style={{ fontSize: '48px' }} />;
    if (sentiment > -0.2) return <MehOutlined style={{ fontSize: '48px' }} />;
    return <FrownOutlined style={{ fontSize: '48px' }} />;
  };

  // 計算儀表盤角度
  const calculateGaugeAngle = (sentiment: number) => {
    // 將 -1 到 1 映射到 -90 到 90 度
    return (sentiment + 1) * 90 - 90;
  };

  // 情緒分佈數據 (用於圓餅圖)
  const getEmotionData = () => {
    if (!sentimentData) return [];

    return [
      { name: '恐懼', value: Math.round(sentimentData.emotions.fear * 100), color: '#f5222d' },
      { name: '中性', value: Math.round(sentimentData.emotions.neutral * 100), color: '#1890ff' },
      { name: '貪婪', value: Math.round(sentimentData.emotions.greed * 100), color: '#52c41a' }
    ];
  };

  // 信號強度數據
  const getSignalStrength = () => {
    if (!sentimentData) return [];

    return [
      { source: '社交媒體', strength: Math.round(sentimentData.sources.social * 100) },
      { source: '新聞情緒', strength: Math.round(sentimentData.sources.news * 100) },
      { source: '技術分析', strength: Math.round(sentimentData.sources.technical * 100) }
    ];
  };

  if (!sentimentData) {
    return (
      <Card title={`${symbol} 市場情緒`} loading={true}>
        <div style={{ height: 400 }}>載入情緒數據中...</div>
      </Card>
    );
  }

  const gaugeAngle = calculateGaugeAngle(sentimentData.sentiment);
  const emotionData = getEmotionData();
  const signalStrength = getSignalStrength();

  return (
    <Card
      title={
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span>{symbol} 市場情緒</span>
            <Tooltip title="基於社交媒體、新聞和技術分析的情緒指標">
              <InfoCircleOutlined className="text-gray-400" />
            </Tooltip>
          </div>
          <Tooltip title="刷新數據">
            <ReloadOutlined
              onClick={generateMockData}
              className="cursor-pointer hover:text-blue-500"
            />
          </Tooltip>
        </div>
      }
      className="sentiment-gauge"
    >
      {/* 主要情緒顯示 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <div className="text-center">
            <div style={{ color: getSentimentColor(sentimentData.sentiment) }}>
              {getSentimentIcon(sentimentData.sentiment)}
            </div>
            <div className="mt-2">
              <div
                className="text-2xl font-bold"
                style={{ color: getSentimentColor(sentimentData.sentiment) }}
              >
                {((sentimentData.sentiment + 1) * 50).toFixed(0)}
              </div>
              <div className="text-sm text-gray-500">情緒分數 (0-100)</div>
            </div>
          </div>
        </Col>

        <Col span={8}>
          <div className="text-center">
            <div className="text-lg font-medium mb-2">
              {getSentimentLabel(sentimentData.sentiment)}
            </div>
            <Tag
              color={sentimentData.sentiment > 0.1 ? 'green' : sentimentData.sentiment < -0.1 ? 'red' : 'blue'}
              style={{ fontSize: '16px', padding: '4px 12px' }}
            >
              {sentimentData.sentiment > 0 ? '看漲' : sentimentData.sentiment < 0 ? '看跌' : '中性'}
            </Tag>
            <div className="mt-3">
              <Progress
                type="circle"
                percent={Math.round(sentimentData.confidence * 100)}
                size={80}
                strokeColor={getSentimentColor(sentimentData.sentiment)}
                format={percent => `${percent}%`}
              />
              <div className="text-xs text-gray-500 mt-1">信心指數</div>
            </div>
          </div>
        </Col>

        <Col span={8}>
          <div className="text-center">
            <div className="text-lg font-medium mb-3">情緒分佈</div>
            <ResponsiveContainer width="100%" height={120}>
              <PieChart>
                <Pie
                  data={emotionData}
                  cx="50%"
                  cy="50%"
                  innerRadius={30}
                  outerRadius={50}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {emotionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: any) => [`${value}%`, '比例']} />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex justify-center gap-4 mt-2">
              {emotionData.map((item) => (
                <div key={item.name} className="flex items-center gap-1">
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-xs text-gray-600">{item.name}</span>
                </div>
              ))}
            </div>
          </div>
        </Col>
      </Row>

      {/* 詳細信息 */}
      {showDetails && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={12}>
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm font-medium mb-3 flex items-center gap-2">
                <FireOutlined />
                信號來源強度
              </div>
              {signalStrength.map((item) => (
                <div key={item.source} className="mb-2">
                  <div className="flex justify-between text-xs mb-1">
                    <span>{item.source}</span>
                    <span>{item.strength}%</span>
                  </div>
                  <Progress
                    percent={item.strength}
                    size="small"
                    strokeColor={
                      item.source === '社交媒體' ? '#ff7875' :
                      item.source === '新聞情緒' ? '#1890ff' : '#52c41a'
                    }
                  />
                </div>
              ))}
            </div>
          </Col>

          <Col span={12}>
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm font-medium mb-3 flex items-center gap-2">
                <ThunderboltOutlined />
                交易信號
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">建議:</span>
                  <Tag color={
                    sentimentData.sentiment > 0.3 ? 'green' :
                    sentimentData.sentiment < -0.3 ? 'red' : 'blue'
                  }>
                    {sentimentData.sentiment > 0.3 ? '考慮買入' :
                     sentimentData.sentiment < -0.3 ? '考慮賣出' : '觀望'}
                  </Tag>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">風險等級:</span>
                  <span className={`text-sm font-medium ${
                    sentimentData.confidence > 0.8 ? 'text-red-500' :
                    sentimentData.confidence > 0.6 ? 'text-orange-500' : 'text-green-500'
                  }`}>
                    {sentimentData.confidence > 0.8 ? '高' :
                     sentimentData.confidence > 0.6 ? '中' : '低'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">信號強度:</span>
                  <span className="text-sm font-medium">
                    {Math.abs(sentimentData.sentiment) > 0.5 ? '強' :
                     Math.abs(sentimentData.sentiment) > 0.2 ? '中等' : '弱'}
                  </span>
                </div>
              </div>
            </div>
          </Col>
        </Row>
      )}

      {/* 歷史趨勢 */}
      {showTrend && historicalData.length > 0 && (
        <div>
          <div className="text-sm font-medium mb-3">情緒趨勢 (30天)</div>
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={historicalData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="date"
                tickFormatter={(value) => {
                  const date = new Date(value);
                  return date.toLocaleDateString('zh-TW', { month: '2-digit', day: '2-digit' });
                }}
                tick={{ fontSize: 10 }}
              />
              <YAxis
                domain={[-1, 1]}
                tickFormatter={(value) => value > 0 ? `+${value}` : value.toString()}
                tick={{ fontSize: 10 }}
              />
              <Tooltip
                formatter={(value: any) => [
                  parseFloat(value).toFixed(3),
                  '情緒分數'
                ]}
                labelFormatter={(label) => {
                  const date = new Date(label);
                  return date.toLocaleDateString('zh-TW');
                }}
              />
              <Line
                type="monotone"
                dataKey="sentiment"
                stroke={getSentimentColor(sentimentData.sentiment)}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* 更新時間 */}
      <div className="text-center text-gray-400 text-xs mt-4">
        最後更新: {new Date().toLocaleString('zh-TW')}
      </div>
    </Card>
  );
};

export default SentimentGauge;