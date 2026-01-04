import React, { useState, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { Badge } from '../ui/Badge';
import { Alert, AlertDescription } from '../ui/Alert';
import {
  Settings,
  Play,
  Save,
  RotateCcw,
  Info,
  AlertTriangle,
  CheckCircle,
  Clock
} from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';

interface StrategyConfig {
  id: string;
  name: string;
  type: 'momentum' | 'mean_reversion' | 'trend' | 'volatility' | 'arbitrage' | 'statistical';
  symbols: string[];
  timeframe: string;
  startDate: string;
  endDate: string;
  initialCash: number;
  fees: number;
  slippage: number;
  parameters: Record<string, any>;
  riskManagement: {
    stopLoss: number | null;
    takeProfit: number | null;
    maxPositionSize: number;
    minPositionSize: number;
  };
  execution: {
    warmupPeriod: number;
    rebalanceOn: string;
    rebalanceFreq: string;
    enableShort: boolean;
    enableLeverage: boolean;
    leverage: number;
  };
}

interface VectorBTConfigPanelProps {
  onRunBacktest: (config: StrategyConfig) => void;
  onSaveConfig: (config: StrategyConfig) => void;
  isLoading?: boolean;
  savedConfigs?: StrategyConfig[];
}

const STRATEGY_TYPES = [
  { value: 'momentum', label: '動量策略', icon: '📈' },
  { value: 'mean_reversion', label: '均值回歸', icon: '🔄' },
  { value: 'trend', label: '趨勢策略', icon: '📊' },
  { value: 'volatility', label: '波動率策略', icon: '🌊' },
  { value: 'arbitrage', label: '套利策略', icon: '⚖️' },
  { value: 'statistical', label: '統計套利', icon: '📉' }
];

const TIMEFRAMES = [
  { value: '1m', label: '1分鐘' },
  { value: '5m', label: '5分鐘' },
  { value: '15m', label: '15分鐘' },
  { value: '30m', label: '30分鐘' },
  { value: '1h', label: '1小時' },
  { value: '4h', label: '4小時' },
  { value: '1d', label: '1天' },
  { value: '1w', label: '1週' }
];

const REBALANCE_OPTIONS = [
  { value: 'all', label: '所有信號' },
  { value: 'entry', label: '僅入場' },
  { value: 'exit', label: '僅出場' },
  { value: 'none', label: '不重新平衡' }
];

const DEFAULT_PARAMETERS = {
  momentum: {
    fastWindow: 10,
    slowWindow: 50,
    signalType: 'crossover'
  },
  mean_reversion: {
    rsiWindow: 14,
    oversoldThreshold: 30,
    overboughtThreshold: 70,
    exitThreshold: 50
  },
  trend: {
    lookbackPeriod: 12,
    riskFreeRate: 0.02,
    momentumThreshold: 0.0
  },
  volatility: {
    atrWindow: 14,
    breakoutMultiplier: 2.0,
    lookbackPeriod: 20
  },
  arbitrage: {
    lookbackPeriod: 60,
    zscoreThreshold: 2.0,
    exitThreshold: 0.0
  },
  statistical: {
    lookbackPeriod: 20,
    stdMultiplier: 2.0,
    exitOffset: 0.0
  }
};

export const VectorBTConfigPanel: React.FC<VectorBTConfigPanelProps> = ({
  onRunBacktest,
  onSaveConfig,
  isLoading = false,
  savedConfigs = []
}) => {
  const [config, setConfig] = useState<StrategyConfig>(() => ({
    id: uuidv4(),
    name: '新建策略',
    type: 'momentum',
    symbols: ['AAPL', 'GOOGL', 'MSFT'],
    timeframe: '1d',
    startDate: '2023-01-01',
    endDate: '2023-12-31',
    initialCash: 10000,
    fees: 0.001,
    slippage: 0.001,
    parameters: { ...DEFAULT_PARAMETERS.momentum },
    riskManagement: {
      stopLoss: null,
      takeProfit: null,
      maxPositionSize: 1.0,
      minPositionSize: 0.01
    },
    execution: {
      warmupPeriod: 0,
      rebalanceOn: 'all',
      rebalanceFreq: 'D',
      enableShort: false,
      enableLeverage: false,
      leverage: 1.0
    }
  }));

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [showAdvanced, setShowAdvanced] = useState(false);

  const validateConfig = useCallback((cfg: StrategyConfig): Record<string, string> => {
    const errors: Record<string, string> = {};

    // Basic validation
    if (!cfg.name.trim()) {
      errors.name = '策略名稱不能為空';
    }

    if (cfg.symbols.length === 0) {
      errors.symbols = '至少需要一個標的';
    }

    if (cfg.initialCash <= 0) {
      errors.initialCash = '初始資金必須大於0';
    }

    if (cfg.fees < 0 || cfg.fees > 1) {
      errors.fees = '手續費必須在0到1之間';
    }

    if (cfg.slippage < 0) {
      errors.slippage = '滑點不能為負數';
    }

    // Date validation
    if (new Date(cfg.startDate) >= new Date(cfg.endDate)) {
      errors.endDate = '結束日期必須晚於開始日期';
    }

    // Risk management validation
    if (cfg.riskManagement.maxPositionSize <= 0 || cfg.riskManagement.maxPositionSize > 1) {
      errors.maxPositionSize = '最大倉位必須在0到1之間';
    }

    if (cfg.riskManagement.minPositionSize < 0 || cfg.riskManagement.minPositionSize > cfg.riskManagement.maxPositionSize) {
      errors.minPositionSize = '最小倉位必須大於等於0且小於最大倉位';
    }

    if (cfg.riskManagement.stopLoss !== null && cfg.riskManagement.stopLoss <= 0) {
      errors.stopLoss = '止損必須大於0';
    }

    if (cfg.riskManagement.takeProfit !== null && cfg.riskManagement.takeProfit <= 0) {
      errors.takeProfit = '止盈必須大於0';
    }

    // Leverage validation
    if (cfg.execution.enableLeverage && cfg.execution.leverage <= 1) {
      errors.leverage = '槓桿必須大於1';
    }

    return errors;
  }, []);

  const updateConfig = useCallback((updates: Partial<StrategyConfig>) => {
    setConfig(prev => {
      const newConfig = { ...prev, ...updates };
      const errors = validateConfig(newConfig);
      setValidationErrors(errors);
      return newConfig;
    });
  }, [validateConfig]);

  const handleRunBacktest = useCallback(() => {
    const errors = validateConfig(config);
    if (Object.keys(errors).length === 0) {
      onRunBacktest(config);
    } else {
      setValidationErrors(errors);
    }
  }, [config, onRunBacktest, validateConfig]);

  const handleSaveConfig = useCallback(() => {
    const errors = validateConfig(config);
    if (Object.keys(errors).length === 0) {
      onSaveConfig(config);
    } else {
      setValidationErrors(errors);
    }
  }, [config, onSaveConfig, validateConfig]);

  const handleLoadConfig = useCallback((savedConfig: StrategyConfig) => {
    setConfig(savedConfig);
    setValidationErrors({});
  }, []);

  const handleResetConfig = useCallback(() => {
    const defaultConfig: StrategyConfig = {
      id: uuidv4(),
      name: '新建策略',
      type: 'momentum',
      symbols: ['AAPL', 'GOOGL', 'MSFT'],
      timeframe: '1d',
      startDate: '2023-01-01',
      endDate: '2023-12-31',
      initialCash: 10000,
      fees: 0.001,
      slippage: 0.001,
      parameters: { ...DEFAULT_PARAMETERS.momentum },
      riskManagement: {
        stopLoss: null,
        takeProfit: null,
        maxPositionSize: 1.0,
        minPositionSize: 0.01
      },
      execution: {
        warmupPeriod: 0,
        rebalanceOn: 'all',
        rebalanceFreq: 'D',
        enableShort: false,
        enableLeverage: false,
        leverage: 1.0
      }
    };
    setConfig(defaultConfig);
    setValidationErrors({});
  }, []);

  const handleStrategyTypeChange = useCallback((type: string) => {
    updateConfig({
      type: type as any,
      parameters: { ...DEFAULT_PARAMETERS[type as keyof typeof DEFAULT_PARAMETERS] }
    });
  }, [updateConfig]);

  const isValid = useMemo(() => Object.keys(validationErrors).length === 0, [validationErrors]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Settings className="h-5 w-5" />
          <h2 className="text-lg font-semibold">VectorBT 回測配置</h2>
        </div>
        <div className="flex items-center space-x-2">
          {savedConfigs.length > 0 && (
            <Select
              value=""
              onValueChange={(value) => {
                if (value) {
                  const config = savedConfigs.find(c => c.id === value);
                  if (config) handleLoadConfig(config);
                }
              }}
              placeholder="載入配置"
            >
              {savedConfigs.map(cfg => (
                <option key={cfg.id} value={cfg.id}>{cfg.name}</option>
              ))}
            </Select>
          )}
          <Button variant="outline" onClick={handleResetConfig} disabled={isLoading}>
            <RotateCcw className="h-4 w-4 mr-2" />
            重置
          </Button>
          <Button variant="outline" onClick={handleSaveConfig} disabled={!isValid || isLoading}>
            <Save className="h-4 w-4 mr-2" />
            保存配置
          </Button>
          <Button onClick={handleRunBacktest} disabled={!isValid || isLoading}>
            {isLoading ? (
              <Clock className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Play className="h-4 w-4 mr-2" />
            )}
            {isLoading ? '執行中...' : '執行回測'}
          </Button>
        </div>
      </div>

      {/* Validation Errors */}
      {Object.keys(validationErrors).length > 0 && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <div className="space-y-1">
              {Object.entries(validationErrors).map(([field, error]) => (
                <div key={field} className="text-sm">
                  <span className="font-medium">{field}:</span> {error}
                </div>
              ))}
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Basic Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Info className="h-5 w-5" />
            <span>基本配置</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">策略名稱</label>
              <Input
                value={config.name}
                onChange={(e) => updateConfig({ name: e.target.value })}
                placeholder="輸入策略名稱"
                className={validationErrors.name ? 'border-red-500' : ''}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">策略類型</label>
              <Select
                value={config.type}
                onValueChange={handleStrategyTypeChange}
              >
                {STRATEGY_TYPES.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.icon} {type.label}
                  </option>
                ))}
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">時間框架</label>
              <Select
                value={config.timeframe}
                onValueChange={(value) => updateConfig({ timeframe: value })}
              >
                {TIMEFRAMES.map(tf => (
                  <option key={tf.value} value={tf.value}>{tf.label}</option>
                ))}
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">交易標的 (用逗號分隔)</label>
              <Input
                value={config.symbols.join(', ')}
                onChange={(e) => updateConfig({
                  symbols: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                })}
                placeholder="AAPL, GOOGL, MSFT"
                className={validationErrors.symbols ? 'border-red-500' : ''}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">開始日期</label>
              <Input
                type="date"
                value={config.startDate}
                onChange={(e) => updateConfig({ startDate: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">結束日期</label>
              <Input
                type="date"
                value={config.endDate}
                onChange={(e) => updateConfig({ endDate: e.target.value })}
                className={validationErrors.endDate ? 'border-red-500' : ''}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">初始資金</label>
              <Input
                type="number"
                value={config.initialCash}
                onChange={(e) => updateConfig({ initialCash: parseFloat(e.target.value) || 0 })}
                className={validationErrors.initialCash ? 'border-red-500' : ''}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">手續費 (%)</label>
              <Input
                type="number"
                step="0.001"
                value={config.fees}
                onChange={(e) => updateConfig({ fees: parseFloat(e.target.value) || 0 })}
                className={validationErrors.fees ? 'border-red-500' : ''}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">滑點 (%)</label>
              <Input
                type="number"
                step="0.001"
                value={config.slippage}
                onChange={(e) => updateConfig({ slippage: parseFloat(e.target.value) || 0 })}
                className={validationErrors.slippage ? 'border-red-500' : ''}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Strategy Parameters */}
      <Card>
        <CardHeader>
          <CardTitle>策略參數</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(config.parameters).map(([key, value]) => (
              <div key={key}>
                <label className="block text-sm font-medium mb-1">
                  {key.replace(/([A-Z])/g, ' $1').trim()}
                </label>
                <Input
                  type={typeof value === 'number' ? 'number' : 'text'}
                  step={typeof value === 'number' ? '0.1' : undefined}
                  value={value}
                  onChange={(e) => updateConfig({
                    parameters: {
                      ...config.parameters,
                      [key]: typeof value === 'number' ? parseFloat(e.target.value) || 0 : e.target.value
                    }
                  })}
                />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Risk Management */}
      <Card>
        <CardHeader>
          <CardTitle>風險管理</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">止損 (%)</label>
              <Input
                type="number"
                step="0.01"
                value={config.riskManagement.stopLoss || ''}
                onChange={(e) => updateConfig({
                  riskManagement: {
                    ...config.riskManagement,
                    stopLoss: e.target.value ? parseFloat(e.target.value) : null
                  }
                })}
                placeholder="無"
                className={validationErrors.stopLoss ? 'border-red-500' : ''}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">止盈 (%)</label>
              <Input
                type="number"
                step="0.01"
                value={config.riskManagement.takeProfit || ''}
                onChange={(e) => updateConfig({
                  riskManagement: {
                    ...config.riskManagement,
                    takeProfit: e.target.value ? parseFloat(e.target.value) : null
                  }
                })}
                placeholder="無"
                className={validationErrors.takeProfit ? 'border-red-500' : ''}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">最大倉位 (%)</label>
              <Input
                type="number"
                step="0.01"
                max="100"
                value={config.riskManagement.maxPositionSize * 100}
                onChange={(e) => updateConfig({
                  riskManagement: {
                    ...config.riskManagement,
                    maxPositionSize: (parseFloat(e.target.value) || 0) / 100
                  }
                })}
                className={validationErrors.maxPositionSize ? 'border-red-500' : ''}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">最小倉位 (%)</label>
              <Input
                type="number"
                step="0.01"
                max="100"
                value={config.riskManagement.minPositionSize * 100}
                onChange={(e) => updateConfig({
                  riskManagement: {
                    ...config.riskManagement,
                    minPositionSize: (parseFloat(e.target.value) || 0) / 100
                  }
                })}
                className={validationErrors.minPositionSize ? 'border-red-500' : ''}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Advanced Settings */}
      <Card>
        <CardHeader>
          <CardTitle
            className="cursor-pointer flex items-center space-x-2"
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            <Settings className="h-5 w-5" />
            <span>進階設定</span>
            <Badge variant="secondary">{showAdvanced ? '收起' : '展開'}</Badge>
          </CardTitle>
        </CardHeader>
        {showAdvanced && (
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">預熱期 (天)</label>
                <Input
                  type="number"
                  value={config.execution.warmupPeriod}
                  onChange={(e) => updateConfig({
                    execution: {
                      ...config.execution,
                      warmupPeriod: parseInt(e.target.value) || 0
                    }
                  })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">重新平衡</label>
                <Select
                  value={config.execution.rebalanceOn}
                  onValueChange={(value) => updateConfig({
                    execution: {
                      ...config.execution,
                      rebalanceOn: value
                    }
                  })}
                >
                  {REBALANCE_OPTIONS.map(option => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </Select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">重新平衡頻率</label>
                <Select
                  value={config.execution.rebalanceFreq}
                  onValueChange={(value) => updateConfig({
                    execution: {
                      ...config.execution,
                      rebalanceFreq: value
                    }
                  })}
                >
                  <option value="D">每日</option>
                  <option value="W">每週</option>
                  <option value="M">每月</option>
                  <option value="H">每小時</option>
                </Select>
              </div>
            </div>

            <div className="flex items-center space-x-6 pt-4">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={config.execution.enableShort}
                  onChange={(e) => updateConfig({
                    execution: {
                      ...config.execution,
                      enableShort: e.target.checked
                    }
                  })}
                  className="rounded"
                />
                <span className="text-sm">允許做空</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={config.execution.enableLeverage}
                  onChange={(e) => updateConfig({
                    execution: {
                      ...config.execution,
                      enableLeverage: e.target.checked
                    }
                  })}
                  className="rounded"
                />
                <span className="text-sm">啟用槓桿</span>
              </label>

              {config.execution.enableLeverage && (
                <div>
                  <label className="block text-sm font-medium mb-1">槓桿倍數</label>
                  <Input
                    type="number"
                    step="0.1"
                    min="1"
                    value={config.execution.leverage}
                    onChange={(e) => updateConfig({
                      execution: {
                        ...config.execution,
                        leverage: parseFloat(e.target.value) || 1
                      }
                    })}
                    className={validationErrors.leverage ? 'border-red-500' : ''}
                  />
                </div>
              )}
            </div>
          </CardContent>
        )}
      </Card>

      {/* Status */}
      {isValid && (
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>
            配置已完成，可以執行回測。
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};