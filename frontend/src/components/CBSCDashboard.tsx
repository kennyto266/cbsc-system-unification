/**
 * CBSC Dashboard Component
 * Displays real-time CBBC data and market sentiment analysis
 */

import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { TrendingUp, TrendingDown, Activity, AlertTriangle, Target, Shield } from 'lucide-react';

// API service imports
import { cbbcApi } from '@/services/api';

// Types
interface CBBCLatestData {
  timestamp: string;
  hsif_close: number;
  hsif_return: number;
  bull_price: number;
  bear_price: number;
  bull_bear_ratio: number;
  fear_greed_index: number;
  rsi_signal: number;
  realized_volatility: number;
  volume: number;
}

interface SentimentSummary {
  sentiment_level: string;
  sentiment_score: number;
  sentiment_strength: number;
  momentum_direction: string;
  volume_trend: string;
  key_support: number;
  key_resistance: number;
  market_breadth: number;
}

interface TradingRecommendation {
  action: string;
  confidence: number;
  entry_zone?: [number, number];
  exit_zone?: [number, number];
  stop_loss?: number;
  target_price?: number;
  position_size: string;
  holding_period: string;
}

interface DataPoint {
  date: string;
  hsif_close: number;
  bull_bear_ratio: number;
  fear_greed_index: number;
  rsi_signal: number;
  realized_volatility: number;
  volume: number;
}

const CBSCDashboard: React.FC = () => {
  // State management
  const [latestData, setLatestData] = useState<CBBCLatestData | null>(null);
  const [historicalData, setHistoricalData] = useState<DataPoint[]>([]);
  const [sentiment, setSentiment] = useState<SentimentSummary | null>(null);
  const [recommendation, setRecommendation] = useState<TradingRecommendation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch data on component mount
  useEffect(() => {
    fetchData();
    // Set up polling for real-time updates
    const interval = setInterval(fetchData, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch latest data
      const latestResponse = await cbbcApi.getLatestData();
      setLatestData(latestResponse.data);

      // Fetch historical data (last 30 days)
      const historyResponse = await cbbcApi.getHistoricalData(30);
      setHistoricalData(historyResponse.data.data_points);

      // Fetch sentiment analysis
      const sentimentResponse = await cbbcApi.getSentimentAnalysis();
      setSentiment(sentimentResponse.data.sentiment_summary);

      // Fetch trading recommendation
      const recommendationResponse = await cbbcApi.getTradingRecommendation();
      setRecommendation(recommendation.data.recommendation);

    } catch (err) {
      console.error('Error fetching CBSC data:', err);
      setError('Failed to fetch data. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  // Helper functions
  const getSentimentColor = (level: string) => {
    switch (level) {
      case 'extreme_fear': return 'bg-green-500';
      case 'fear': return 'bg-green-400';
      case 'neutral': return 'bg-yellow-500';
      case 'greed': return 'bg-red-400';
      case 'extreme_greed': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getSentimentTextColor = (level: string) => {
    switch (level) {
      case 'extreme_fear': return 'text-green-600';
      case 'fear': return 'text-green-500';
      case 'neutral': return 'text-yellow-600';
      case 'greed': return 'text-red-500';
      case 'extreme_greed': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'BUY': return 'text-green-600 bg-green-50';
      case 'SELL': return 'text-red-600 bg-red-50';
      case 'HOLD': return 'text-yellow-600 bg-yellow-50';
      case 'CAUTION': return 'text-orange-600 bg-orange-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const formatNumber = (num: number | null | undefined, decimals: number = 2) => {
    if (num === null || num === undefined) return 'N/A';
    return num.toFixed(decimals);
  };

  const formatPercent = (num: number | null | undefined) => {
    if (num === null || num === undefined) return 'N/A';
    return `${(num * 100).toFixed(2)}%`;
  };

  // Render loading state
  if (loading && !latestData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Activity className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading CBSC Dashboard...</p>
        </div>
      </div>
    );
  }

  // Render error state
  if (error && !latestData) {
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">CBSC Market Dashboard</h1>
          <p className="text-gray-600">Real-time CBBC market sentiment and trading analysis</p>
        </div>
        <Badge
          variant="outline"
          className={`px-3 py-1 text-sm font-semibold ${getSentimentTextColor(sentiment?.sentiment_level || 'neutral')}`}
        >
          {sentiment?.sentiment_level?.replace('_', ' ').toUpperCase() || 'NEUTRAL'}
        </Badge>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">HSIF Price</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {latestData ? formatNumber(latestData.hsif_close, 0) : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">
              Return: {latestData ? formatPercent(latestData.hsif_return) : 'N/A'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Bull/Bear Ratio</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {latestData ? formatNumber(latestData.bull_bear_ratio, 3) : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">
              {sentiment?.momentum_direction || 'N/A'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Fear & Greed Index</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {latestData ? formatNumber(latestData.fear_greed_index, 1) : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">
              Score out of 100
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Realized Volatility</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {latestData ? formatPercent(latestData.realized_volatility) : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">
              {sentiment?.volume_trend || 'N/A'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Trading Recommendation */}
      {recommendation && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Trading Recommendation
            </CardTitle>
            <CardDescription>
              AI-powered trading signal based on market sentiment analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-600 mb-1">Action</p>
                <Badge className={getActionColor(recommendation.action)}>
                  {recommendation.action}
                </Badge>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Confidence</p>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${recommendation.confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium">
                    {formatPercent(recommendation.confidence)}
                  </span>
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Position Size</p>
                <p className="font-semibold">{recommendation.position_size}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Holding Period</p>
                <p className="font-semibold">{recommendation.holding_period}</p>
              </div>
            </div>

            {/* Entry/Exit Zones */}
            {(recommendation.entry_zone || recommendation.exit_zone) && (
              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                {recommendation.entry_zone && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Entry Zone</p>
                    <p className="text-sm">
                      {formatNumber(recommendation.entry_zone[0])} - {formatNumber(recommendation.entry_zone[1])}
                    </p>
                  </div>
                )}
                {recommendation.exit_zone && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Exit Zone</p>
                    <p className="text-sm">
                      {formatNumber(recommendation.exit_zone[0])} - {formatNumber(recommendation.exit_zone[1])}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Stop Loss and Target */}
            {(recommendation.stop_loss || recommendation.target_price) && (
              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                {recommendation.stop_loss && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Stop Loss</p>
                    <p className="font-semibold text-red-600">{formatNumber(recommendation.stop_loss)}</p>
                  </div>
                )}
                {recommendation.target_price && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Target Price</p>
                    <p className="font-semibold text-green-600">{formatNumber(recommendation.target_price)}</p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Charts and Analysis */}
      <Tabs defaultValue="price" className="space-y-4">
        <TabsList>
          <TabsTrigger value="price">Price & Ratio</TabsTrigger>
          <TabsTrigger value="sentiment">Sentiment Analysis</TabsTrigger>
          <TabsTrigger value="volatility">Volatility & Volume</TabsTrigger>
          <TabsTrigger value="signals">Technical Signals</TabsTrigger>
        </TabsList>

        {/* Price and Bull/Bear Ratio Chart */}
        <TabsContent value="price" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>HSIF Price & Bull/Bear Ratio</CardTitle>
              <CardDescription>
                Historical price movements and market sentiment indicator
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={historicalData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tickFormatter={(value) => new Date(value).toLocaleDateString()}
                    />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                    />
                    <Legend />
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey="hsif_close"
                      stroke="#2563eb"
                      name="HSIF Close"
                      strokeWidth={2}
                    />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="bull_bear_ratio"
                      stroke="#dc2626"
                      name="Bull/Bear Ratio"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Sentiment Analysis Chart */}
        <TabsContent value="sentiment" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Fear & Greed Index</CardTitle>
              <CardDescription>
                Market sentiment indicator (0 = Extreme Fear, 100 = Extreme Greed)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={historicalData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tickFormatter={(value) => new Date(value).toLocaleDateString()}
                    />
                    <YAxis domain={[0, 100]} />
                    <Tooltip
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="fear_greed_index"
                      stroke="#f59e0b"
                      name="Fear & Greed Index"
                      strokeWidth={2}
                    />
                    <Line
                      type="monotone"
                      dataKey="rsi_signal"
                      stroke="#8b5cf6"
                      name="RSI Signal"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Volatility and Volume Chart */}
        <TabsContent value="volatility" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Volatility & Volume Analysis</CardTitle>
              <CardDescription>
                Market volatility and trading volume trends
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={historicalData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tickFormatter={(value) => new Date(value).toLocaleDateString()}
                    />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                    />
                    <Legend />
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey="realized_volatility"
                      stroke="#10b981"
                      name="Realized Volatility"
                      strokeWidth={2}
                    />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="volume"
                      stroke="#6366f1"
                      name="Volume"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Technical Signals */}
        <TabsContent value="signals" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Key Support & Resistance Levels</CardTitle>
              <CardDescription>
                Important price levels based on market sentiment analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Key Support</p>
                  <p className="text-2xl font-bold text-green-600">
                    {sentiment ? formatNumber(sentiment.key_support, 0) : 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Key Resistance</p>
                  <p className="text-2xl font-bold text-red-600">
                    {sentiment ? formatNumber(sentiment.key_resistance, 0) : 'N/A'}
                  </p>
                </div>
              </div>
              <div className="mt-4">
                <p className="text-sm text-gray-600 mb-1">Market Breadth</p>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-600 h-2 rounded-full"
                      style={{ width: `${(sentiment?.market_breadth || 0) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium">
                    {formatPercent(sentiment?.market_breadth || 0)}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CBSCDashboard;