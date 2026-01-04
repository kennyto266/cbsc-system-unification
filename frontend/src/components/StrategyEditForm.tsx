/**
 * Strategy Edit Form Component
 * 策略編輯表單組件
 */

import React, { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';

import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Card } from './ui/Card';
import { Alert } from './ui/Alert';
import { Modal } from './ui/Modal';
import { Select } from './ui/Select';
import { Badge } from './ui/Badge';
import { Switch } from './ui/switch';

import {
  Strategy,
  StrategyType,
  RiskTolerance,
  StrategyUpdateRequest,
  StrategyStatus
} from '../types/strategyTypes';

import { useDispatch, useSelector } from 'react-redux';
import {
  updateStrategy,
  selectStrategiesLoading,
  selectStrategiesError,
  fetchStrategy
} from '../store/strategies/strategySlice';

// Form validation schema
const strategySchema = yup.object().shape({
  name: yup.string()
    .required('策略名稱是必需的')
    .min(2, '策略名稱至少需要2個字符')
    .max(100, '策略名稱不能超過100個字符'),
  description: yup.string()
    .required('策略描述是必需的')
    .min(10, '策略描述至少需要10個字符')
    .max(1000, '策略描述不能超過1000個字符'),
  strategy_type: yup.string()
    .required('策略類型是必需的')
    .oneOf(Object.values(StrategyType), '無效的策略類型'),
  risk_tolerance: yup.string()
    .required('風險承受度是必需的')
    .oneOf(Object.values(RiskTolerance), '無效的風險承受度'),
  version: yup.string()
    .required('版本號是必需的')
    .matches(/^\d+\.\d+\.\d+$/, '版本號格式應為 x.y.z')
});

interface StrategyEditFormProps {
  isOpen: boolean;
  onClose: () => void;
  strategyId: string;
  onSuccess?: (strategy: Strategy) => void;
}

// Strategy type descriptions
const strategyTypeDescriptions = {
  [StrategyType.TECHNICAL_INDICATORS]: '基於技術指標的量化策略，如MA、RSI、MACD等',
  [StrategyType.MOMENTUM]: '基於動量因子的策略，捕捉價格趨勢',
  [StrategyType.MEAN_REVERSION]: '均值回歸策略，基於價格回歸均值的特性',
  [StrategyType.VOLUME]: '基於成交量分析的策略',
  [StrategyType.VOLATILITY]: '基於波動率的策略，如VIX指標',
  [StrategyType.FUNDAMENTAL]: '基於基本面分析的策略',
  [StrategyType.PORTFOLIO]: '投資組合管理策略',
  [StrategyType.ARBITRAGE]: '套利策略，捕捉市場定價偏差',
  [StrategyType.MACRO]: '基於宏觀經濟因素的策略'
};

// Risk tolerance descriptions
const riskToleranceDescriptions = {
  [RiskTolerance.LOW]: '低風險承受度，追求穩定收益，最大回撤控制在5%以內',
  [RiskTolerance.MEDIUM]: '中等風險承受度，平衡收益與風險，最大回撤控制在10%以內',
  [RiskTolerance.HIGH]: '高風險承受度，追求高收益，最大回撤控制在20%以內',
  [RiskTolerance.EXTREME]: '極高風險承受度，追求極高收益，能承受較大回撤'
};

export const StrategyEditForm: React.FC<StrategyEditFormProps> = ({
  isOpen,
  onClose,
  strategyId,
  onSuccess
}) => {
  const dispatch = useDispatch();
  const loading = useSelector(selectStrategiesLoading);
  const error = useSelector(selectStrategiesError);

  // Form state
  const [currentStep, setCurrentStep] = useState(1);
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [originalStrategy, setOriginalStrategy] = useState<Strategy | null>(null);

  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isValid, isDirty },
    reset,
    watch,
    setValue,
    trigger
  } = useForm<StrategyUpdateRequest>({
    resolver: yupResolver(strategySchema),
    mode: 'onChange'
  });

  const watchedStrategyType = watch('strategy_type');
  const watchedRiskTolerance = watch('risk_tolerance');

  // Load strategy data when modal opens
  useEffect(() => {
    if (isOpen && strategyId) {
      loadStrategyData();
    }
  }, [isOpen, strategyId]);

  const loadStrategyData = async () => {
    try {
      const strategy = await dispatch(fetchStrategy(strategyId)).unwrap();
      setOriginalStrategy(strategy);

      // Set form values
      reset({
        name: strategy.name,
        description: strategy.description,
        strategy_type: strategy.strategy_type,
        risk_tolerance: strategy.risk_tolerance,
        version: strategy.version,
        is_active: strategy.is_active,
        parameters: strategy.parameters || {},
        config: strategy.config || {}
      });

      setTags(strategy.tags || []);
    } catch (error) {
      console.error('Failed to load strategy:', error);
    }
  };

  // Handle form submission
  const onSubmit = async (data: StrategyUpdateRequest) => {
    if (!strategyId) return;

    try {
      const strategyData = {
        ...data,
        tags,
        updated_at: new Date().toISOString()
      };

      const result = await dispatch(updateStrategy({ id: strategyId, data: strategyData })).unwrap();

      if (result) {
        reset();
        setTags([]);
        setTagInput('');
        setCurrentStep(1);
        onSuccess?.(result);
        onClose();
      }
    } catch (error) {
      console.error('Failed to update strategy:', error);
    }
  };

  // Handle tag management
  const handleAddTag = () => {
    if (tagInput.trim() && tags.length < 10 && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  // Handle modal close
  const handleClose = () => {
    if (!loading) {
      if (isDirty) {
        if (confirm('您有未保存的更改，確定要關閉嗎？')) {
          reset();
          setTags([]);
          setTagInput('');
          setCurrentStep(1);
          onClose();
        }
      } else {
        reset();
        setTags([]);
        setTagInput('');
        setCurrentStep(1);
        onClose();
      }
    }
  };

  const handleStatusToggle = (checked: boolean) => {
    setValue('is_active', checked);
    trigger('is_active');
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="編輯策略"
      size="lg"
    >
      <div className="space-y-6">
        {/* Progress Steps */}
        <div className="flex items-center justify-between">
          {[1, 2, 3].map((step) => (
            <div key={step} className="flex items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step <= currentStep
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-600'
                }`}
              >
                {step}
              </div>
              {step < 3 && (
                <div
                  className={`w-16 h-1 mx-2 ${
                    step < currentStep ? 'bg-blue-600' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        {/* Strategy Status */}
        {originalStrategy && (
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-sm font-medium text-gray-900">策略狀態</h4>
                <p className="text-sm text-gray-500">
                  當前狀態: {originalStrategy.is_active ? '活躍' : '非活躍'}
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-700">啟用策略:</span>
                <Controller
                  name="is_active"
                  control={control}
                  render={({ field }) => (
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  )}
                />
              </div>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <Alert
            variant="error"
            title="更新失敗"
            description={error}
          />
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Step 1: Basic Information */}
          {currentStep === 1 && (
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium mb-4">基本資訊</h3>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      策略名稱 *
                    </label>
                    <Input
                      {...register('name')}
                      placeholder="輸入策略名稱"
                      error={errors.name?.message}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      版本號 *
                    </label>
                    <Input
                      {...register('version')}
                      placeholder="1.0.0"
                      error={errors.version?.message}
                    />
                    <p className="mt-1 text-sm text-gray-500">
                      格式: x.y.z (例如: 1.1.0)
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      策略描述 *
                    </label>
                    <textarea
                      {...register('description')}
                      rows={4}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="詳細描述您的策略..."
                    />
                    {errors.description && (
                      <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
                    )}
                  </div>

                  {originalStrategy && (
                    <div className="bg-blue-50 p-3 rounded-md">
                      <p className="text-sm text-blue-800">
                        <strong>創建時間:</strong> {new Date(originalStrategy.created_at).toLocaleString()}
                      </p>
                      <p className="text-sm text-blue-800">
                        <strong>最後更新:</strong> {new Date(originalStrategy.updated_at).toLocaleString()}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Strategy Configuration */}
          {currentStep === 2 && (
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium mb-4">策略配置</h3>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      策略類型 *
                    </label>
                    <Controller
                      name="strategy_type"
                      control={control}
                      render={({ field }) => (
                        <Select
                          value={field.value}
                          onChange={field.onChange}
                          error={errors.strategy_type?.message}
                        >
                          {Object.values(StrategyType).map((type) => (
                            <option key={type} value={type}>
                              {type}
                            </option>
                          ))}
                        </Select>
                      )}
                    />
                    {watchedStrategyType && (
                      <p className="mt-1 text-sm text-gray-500">
                        {strategyTypeDescriptions[watchedStrategyType]}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      風險承受度 *
                    </label>
                    <Controller
                      name="risk_tolerance"
                      control={control}
                      render={({ field }) => (
                        <Select
                          value={field.value}
                          onChange={field.onChange}
                          error={errors.risk_tolerance?.message}
                        >
                          {Object.values(RiskTolerance).map((tolerance) => (
                            <option key={tolerance} value={tolerance}>
                              {tolerance}
                            </option>
                          ))}
                        </Select>
                      )}
                    />
                    {watchedRiskTolerance && (
                      <p className="mt-1 text-sm text-gray-500">
                        {riskToleranceDescriptions[watchedRiskTolerance]}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      標籤
                    </label>
                    <div className="flex space-x-2 mb-2">
                      <Input
                        value={tagInput}
                        onChange={(e) => setTagInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="添加標籤"
                        className="flex-1"
                      />
                      <Button
                        type="button"
                        onClick={handleAddTag}
                        disabled={!tagInput.trim() || tags.length >= 10}
                        variant="outline"
                      >
                        添加
                      </Button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {tags.map((tag) => (
                        <Badge
                          key={tag}
                          className="bg-blue-100 text-blue-800"
                          removable
                          onRemove={() => handleRemoveTag(tag)}
                        >
                          {tag}
                        </Badge>
                      ))}
                    </div>
                    <p className="mt-1 text-sm text-gray-500">
                      最多添加10個標籤，按Enter鍵快速添加
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Review and Update */}
          {currentStep === 3 && (
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium mb-4">確認更新</h3>

                <Card className="p-4">
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-600">策略名稱:</span>
                      <span className="text-sm">{watch('name')}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-600">版本:</span>
                      <span className="text-sm">{watch('version')}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-600">策略類型:</span>
                      <span className="text-sm">{watch('strategy_type')}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-600">風險承受度:</span>
                      <span className="text-sm">{watch('risk_tolerance')}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium text-gray-600">狀態:</span>
                      <span className="text-sm">{watch('is_active') ? '活躍' : '非活躍'}</span>
                    </div>
                    <div className="flex justify-between items-start">
                      <span className="text-sm font-medium text-gray-600">描述:</span>
                      <span className="text-sm text-right max-w-xs">{watch('description')}</span>
                    </div>
                    {tags.length > 0 && (
                      <div className="flex justify-between items-start">
                        <span className="text-sm font-medium text-gray-600">標籤:</span>
                        <div className="flex flex-wrap gap-1">
                          {tags.map((tag) => (
                            <Badge
                              key={tag}
                              className="bg-gray-100 text-gray-800 text-xs"
                            >
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </Card>

                {isDirty && (
                  <Alert
                    variant="warning"
                    title="有未保存的更改"
                    description="請確認所有更改後點擊更新按鈕保存"
                  />
                )}
              </div>
            </div>
          )}

          {/* Form Actions */}
          <div className="flex justify-between pt-6 border-t border-gray-200">
            <div>
              {currentStep > 1 && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setCurrentStep(currentStep - 1)}
                  disabled={loading}
                >
                  上一步
                </Button>
              )}
            </div>

            <div className="flex space-x-3">
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                disabled={loading}
              >
                取消
              </Button>

              {currentStep < 3 ? (
                <Button
                  type="button"
                  onClick={() => setCurrentStep(currentStep + 1)}
                  disabled={!isValid}
                >
                  下一步
                </Button>
              ) : (
                <Button
                  type="submit"
                  variant="primary"
                  loading={loading}
                  disabled={!isValid || !isDirty}
                >
                  更新策略
                </Button>
              )}
            </div>
          </div>
        </form>
      </div>
    </Modal>
  );
};

export default StrategyEditForm;