import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm, Controller } from 'react-hook-form';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import {
  ArrowLeft,
  Save,
  Play,
  TestTube,
  Settings,
  TrendingUp,
  Shield,
  DollarSign,
  Calendar,
  BarChart3,
  Info
} from 'lucide-react';

interface StrategyFormData {
  name: string;
  description: string;
  strategyType: string;
  symbols: string[];
  initialCapital: number;
  timeframe: string;
  parameters: {
    riskLevel: number;
    leverage: number;
    maxPositions: number;
    positionSizing: string;
    stopLoss: number;
    takeProfit: number;
  };
  backtestConfig: {
    startDate: string;
    endDate: string;
    commission: number;
    slippage: number;
  };
  riskManagement: {
    enableVar: boolean;
    varThreshold: number;
    enableDrawdown: boolean;
    maxDrawdown: number;
    enableCorrelation: boolean;
    maxCorrelation: number;
  };
  tradingConfig: {
    broker: string;
    accountType: string;
    paperTrading: boolean;
    executionMode: string;
  };
}

const strategyTypes = [
  { value: 'momentum', label: '動量策略', description: '基於價格動量的交易策略' },
  { value: 'mean_reversion', label: '均值回歸', description: '基於價格回歸的套利策略' },
  { value: 'trend_following', label: '趨勢跟蹤', description: '跟蹤市場趨勢的策略' },
  { value: 'arbitrage', label: '套利策略', description: '跨市場或跨品種套利' },
  { value: 'statistical', label: '統計套利', description: '基於統計關係的策略' },
  { value: 'ai_ml', label: 'AI/機器學習', description: '基於機器學習的預測模型' },
];

const hkStocks = [
  { symbol: '0700.HK', name: '騰訊控股', sector: '科技' },
  { symbol: '0388.HK', name: '港交所', sector: '金融' },
  { symbol: '1398.HK', name: '工商銀行', sector: '金融' },
  { symbol: '0939.HK', name: '建設銀行', sector: '金融' },
  { symbol: '2318.HK', name: '中國平安', sector: '保險' },
  { symbol: '1299.HK', name: '友邦保險', sector: '保險' },
  { symbol: '0941.HK', name: '中國移動', sector: '電信' },
  { symbol: '0883.HK', name: '中國海洋石油', sector: '能源' },
];

const brokers = [
  { value: 'futu', label: '富途證券', description: '支持港股和美股交易' },
  { value: 'interactive_brokers', label: '盈透證券', description: '全球市場覆蓋' },
  { value: 'binance', label: '幣安', description: '數字貨幣交易所' },
  { value: 'simulation', label: '模擬交易', description: '僅用於回測和模擬' },
];

const StrategyConfigurationPage: React.FC = () => {
  const navigate = useNavigate();
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>([]);
  const [testResults, setTestResults] = useState<any>(null);

  const {
    register,
    control,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<StrategyFormData>({
    defaultValues: {
      name: '',
      description: '',
      strategyType: 'momentum',
      symbols: [],
      initialCapital: 100000,
      timeframe: '1D',
      parameters: {
        riskLevel: 50,
        leverage: 1,
        maxPositions: 5,
        positionSizing: 'equal',
        stopLoss: 5,
        takeProfit: 10,
      },
      backtestConfig: {
        startDate: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        endDate: new Date().toISOString().split('T')[0],
        commission: 0.001,
        slippage: 0.0005,
      },
      riskManagement: {
        enableVar: true,
        varThreshold: 2.5,
        enableDrawdown: true,
        maxDrawdown: 15,
        enableCorrelation: false,
        maxCorrelation: 0.7,
      },
      tradingConfig: {
        broker: 'simulation',
        accountType: 'individual',
        paperTrading: true,
        executionMode: 'immediate',
      },
    },
  });

  const watchedValues = watch();

  const handleSymbolToggle = (symbol: string) => {
    setSelectedSymbols(prev =>
      prev.includes(symbol)
        ? prev.filter(s => s !== symbol)
        : [...prev, symbol]
    );
  };

  const onSave = async (data: StrategyFormData) => {
    setIsSaving(true);
    try {
      // API call to save strategy
      console.log('Saving strategy:', { ...data, symbols: selectedSymbols });
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      navigate('/strategies');
    } catch (error) {
      console.error('Failed to save strategy:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const onTest = async () => {
    setIsTesting(true);
    try {
      // Simulate backtest
      await new Promise(resolve => setTimeout(resolve, 2000));
      setTestResults({
        totalReturn: 15.2,
        sharpeRatio: 1.6,
        maxDrawdown: -8.5,
        winRate: 0.62,
        totalTrades: 142,
      });
    } catch (error) {
      console.error('Failed to run backtest:', error);
    } finally {
      setIsTesting(false);
    }
  };

  const renderBasicInfo = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Info className="w-5 h-5" />
          <span>基本資訊</span>
        </CardTitle>
        <CardDescription>配置策略的基本信息</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="name">策略名稱 *</Label>
            <Input
              id="name"
              placeholder="輸入策略名稱"
              {...register('name', { required: '策略名稱不能為空' })}
            />
            {errors.name && (
              <p className="text-sm text-red-500 mt-1">{errors.name.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="strategyType">策略類型 *</Label>
            <Controller
              name="strategyType"
              control={control}
              render={({ field }) => (
                <Select onValueChange={field.onChange} value={field.value}>
                  <SelectTrigger>
                    <SelectValue placeholder="選擇策略類型" />
                  </SelectTrigger>
                  <SelectContent>
                    {strategyTypes.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.strategyType && (
              <p className="text-sm text-red-500 mt-1">{errors.strategyType.message}</p>
            )}
          </div>
        </div>

        <div>
          <Label htmlFor="description">策略描述</Label>
          <Textarea
            id="description"
            placeholder="描述策略的投資理念和執行邏輯"
            rows={3}
            {...register('description')}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Label htmlFor="initialCapital">初始資金 (HKD) *</Label>
            <Input
              id="initialCapital"
              type="number"
              {...register('initialCapital', {
                required: '初始資金不能為空',
                min: { value: 10000, message: '最小資金為 HKD 10,000' }
              })}
            />
            {errors.initialCapital && (
              <p className="text-sm text-red-500 mt-1">{errors.initialCapital.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="timeframe">時間週期</Label>
            <Controller
              name="timeframe"
              control={control}
              render={({ field }) => (
                <Select onValueChange={field.onChange} value={field.value}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1m">1分鐘</SelectItem>
                    <SelectItem value="5m">5分鐘</SelectItem>
                    <SelectItem value="15m">15分鐘</SelectItem>
                    <SelectItem value="1h">1小時</SelectItem>
                    <SelectItem value="4h">4小時</SelectItem>
                    <SelectItem value="1D">1天</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
          </div>

          <div>
            <Label>選定標的 ({selectedSymbols.length})</Label>
            <div className="mt-2">
              <Badge variant="secondary">
                {selectedSymbols.length > 0 ? `${selectedSymbols.length} 個標的` : '未選擇標的'}
              </Badge>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderSymbolSelection = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <BarChart3 className="w-5 h-5" />
          <span>標的選擇</span>
        </CardTitle>
        <CardDescription>選擇策略交易的標的</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center space-x-2 mb-4">
            <Input
              placeholder="搜索股票代碼或名稱..."
              className="flex-1"
            />
            <Button variant="outline">搜索</Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {hkStocks.map((stock) => (
              <div
                key={stock.symbol}
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedSymbols.includes(stock.symbol)
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => handleSymbolToggle(stock.symbol)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{stock.symbol}</div>
                    <div className="text-sm text-gray-600">{stock.name}</div>
                    <div className="text-xs text-gray-500">{stock.sector}</div>
                  </div>
                  <Checkbox
                    checked={selectedSymbols.includes(stock.symbol)}
                    onChange={() => {}}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderParameters = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Settings className="w-5 h-5" />
          <span>策略參數</span>
        </CardTitle>
        <CardDescription>配置策略的交易參數和風險控制</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Risk Parameters */}
        <div>
          <h4 className="font-medium mb-4 flex items-center space-x-2">
            <Shield className="w-4 h-4" />
            <span>風險參數</span>
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>風險水平: {watchedValues.parameters?.riskLevel}%</Label>
              <Controller
                name="parameters.riskLevel"
                control={control}
                render={({ field }) => (
                  <Slider
                    min={0}
                    max={100}
                    step={1}
                    value={[field.value]}
                    onValueChange={(value) => field.onChange(value[0])}
                    className="mt-2"
                  />
                )}
              />
            </div>

            <div>
              <Label>槓桿倍數: {watchedValues.parameters?.leverage}x</Label>
              <Controller
                name="parameters.leverage"
                control={control}
                render={({ field }) => (
                  <Slider
                    min={1}
                    max={5}
                    step={0.5}
                    value={[field.value]}
                    onValueChange={(value) => field.onChange(value[0])}
                    className="mt-2"
                  />
                )}
              />
            </div>
          </div>
        </div>

        <Separator />

        {/* Position Management */}
        <div>
          <h4 className="font-medium mb-4">持倉管理</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label htmlFor="maxPositions">最大持倉數</Label>
              <Controller
                name="parameters.maxPositions"
                control={control}
                render={({ field }) => (
                  <Input
                    type="number"
                    min={1}
                    max={20}
                    value={field.value}
                    onChange={(e) => field.onChange(Number(e.target.value))}
                  />
                )}
              />
            </div>

            <div>
              <Label>持倉分配方式</Label>
              <Controller
                name="parameters.positionSizing"
                control={control}
                render={({ field }) => (
                  <RadioGroup
                    value={field.value}
                    onValueChange={field.onChange}
                    className="mt-2"
                  >
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="equal" id="equal" />
                      <Label htmlFor="equal">等權重</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="volatility" id="volatility" />
                      <Label htmlFor="volatility">基於波動率</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="momentum" id="momentum" />
                      <Label htmlFor="momentum">基於動量</Label>
                    </div>
                  </RadioGroup>
                )}
              />
            </div>

            <div>
              <Label htmlFor="stopLoss">止損 (%)</Label>
              <Controller
                name="parameters.stopLoss"
                control={control}
                render={({ field }) => (
                  <Input
                    type="number"
                    min={0.5}
                    max={20}
                    step={0.5}
                    value={field.value}
                    onChange={(e) => field.onChange(Number(e.target.value))}
                  />
                )}
              />
            </div>

            <div>
              <Label htmlFor="takeProfit">止盈 (%)</Label>
              <Controller
                name="parameters.takeProfit"
                control={control}
                render={({ field }) => (
                  <Input
                    type="number"
                    min={1}
                    max={50}
                    step={0.5}
                    value={field.value}
                    onChange={(e) => field.onChange(Number(e.target.value))}
                  />
                )}
              />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderBacktestConfig = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <TestTube className="w-5 h-5" />
          <span>回測配置</span>
        </CardTitle>
        <CardDescription>設置回測參數和交易成本</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="startDate">開始日期</Label>
            <Input
              id="startDate"
              type="date"
              {...register('backtestConfig.startDate')}
            />
          </div>

          <div>
            <Label htmlFor="endDate">結束日期</Label>
            <Input
              id="endDate"
              type="date"
              {...register('backtestConfig.endDate')}
            />
          </div>

          <div>
            <Label htmlFor="commission">佣金率 (%)</Label>
            <Input
              id="commission"
              type="number"
              step={0.0001}
              {...register('backtestConfig.commission')}
            />
          </div>

          <div>
            <Label htmlFor="slippage">滑點 (%)</Label>
            <Input
              id="slippage"
              type="number"
              step={0.0001}
              {...register('backtestConfig.slippage')}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderRiskManagement = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Shield className="w-5 h-5" />
          <span>風險管理</span>
        </CardTitle>
        <CardDescription>配置實時風險監控和限制</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Controller
              name="riskManagement.enableVar"
              control={control}
              render={({ field }) => (
                <Checkbox
                  id="enableVar"
                  checked={field.value}
                  onCheckedChange={field.onChange}
                />
              )}
            />
            <Label htmlFor="enableVar">啟用 VaR 監控</Label>
          </div>

          {watchedValues.riskManagement?.enableVar && (
            <div className="ml-6">
              <Label>VaR 閾值 (%)</Label>
              <Controller
                name="riskManagement.varThreshold"
                control={control}
                render={({ field }) => (
                  <Input
                    type="number"
                    min={0.5}
                    max={10}
                    step={0.5}
                    value={field.value}
                    onChange={(e) => field.onChange(Number(e.target.value))}
                    className="mt-1"
                  />
                )}
              />
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Controller
              name="riskManagement.enableDrawdown"
              control={control}
              render={({ field }) => (
                <Checkbox
                  id="enableDrawdown"
                  checked={field.value}
                  onCheckedChange={field.onChange}
                />
              )}
            />
            <Label htmlFor="enableDrawdown">啟用回撤控制</Label>
          </div>

          {watchedValues.riskManagement?.enableDrawdown && (
            <div className="ml-6">
              <Label>最大回撤 (%)</Label>
              <Controller
                name="riskManagement.maxDrawdown"
                control={control}
                render={({ field }) => (
                  <Input
                    type="number"
                    min={5}
                    max={50}
                    step={1}
                    value={field.value}
                    onChange={(e) => field.onChange(Number(e.target.value))}
                    className="mt-1"
                  />
                )}
              />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  const renderTradingConfig = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <DollarSign className="w-5 h-5" />
          <span>交易配置</span>
        </CardTitle>
        <CardDescription>配置券商和執行參數</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label>選擇券商</Label>
            <Controller
              name="tradingConfig.broker"
              control={control}
              render={({ field }) => (
                <Select onValueChange={field.onChange} value={field.value}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {brokers.map((broker) => (
                      <SelectItem key={broker.value} value={broker.value}>
                        {broker.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </div>

          <div>
            <Label>執行模式</Label>
            <Controller
              name="tradingConfig.executionMode"
              control={control}
              render={({ field }) => (
                <Select onValueChange={field.onChange} value={field.value}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="immediate">立即執行</SelectItem>
                    <SelectItem value="batch">批量執行</SelectItem>
                    <SelectItem value="smart">智能執行</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Controller
            name="tradingConfig.paperTrading"
            control={control}
            render={({ field }) => (
              <Checkbox
                id="paperTrading"
                checked={field.value}
                onCheckedChange={field.onChange}
              />
            )}
          />
          <Label htmlFor="paperTrading">使用模擬交易</Label>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            onClick={() => navigate('/strategies')}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            返回
          </Button>
          <div>
            <h1 className="text-3xl font-bold">策略配置</h1>
            <p className="text-muted-foreground">創建和配置新的交易策略</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            onClick={onTest}
            disabled={isTesting || selectedSymbols.length === 0}
          >
            <TestTube className="w-4 h-4 mr-2" />
            {isTesting ? '測試中...' : '運行回測'}
          </Button>
          <Button
            onClick={handleSubmit(onSave)}
            disabled={isSaving}
          >
            <Save className="w-4 h-4 mr-2" />
            {isSaving ? '保存中...' : '保存策略'}
          </Button>
        </div>
      </div>

      {/* Test Results */}
      {testResults && (
        <Alert>
          <TrendingUp className="w-4 h-4" />
          <AlertDescription>
            回測結果：總回報 {testResults.totalReturn}% |
            Sharpe比率 {testResults.sharpeRatio} |
            最大回撤 {testResults.maxDrawdown}% |
            勝率 {(testResults.winRate * 100).toFixed(1)}%
          </AlertDescription>
        </Alert>
      )}

      {/* Configuration Form */}
      <form onSubmit={handleSubmit(onSave)}>
        <Tabs defaultValue="basic" className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="basic">基本資訊</TabsTrigger>
            <TabsTrigger value="symbols">標的選擇</TabsTrigger>
            <TabsTrigger value="parameters">策略參數</TabsTrigger>
            <TabsTrigger value="backtest">回測配置</TabsTrigger>
            <TabsTrigger value="trading">交易設置</TabsTrigger>
          </TabsList>

          <TabsContent value="basic" className="space-y-6">
            {renderBasicInfo()}
          </TabsContent>

          <TabsContent value="symbols" className="space-y-6">
            {renderSymbolSelection()}
          </TabsContent>

          <TabsContent value="parameters" className="space-y-6">
            {renderParameters()}
            {renderRiskManagement()}
          </TabsContent>

          <TabsContent value="backtest" className="space-y-6">
            {renderBacktestConfig()}
          </TabsContent>

          <TabsContent value="trading" className="space-y-6">
            {renderTradingConfig()}
          </TabsContent>
        </Tabs>
      </form>
    </div>
  );
};

export default StrategyConfigurationPage;