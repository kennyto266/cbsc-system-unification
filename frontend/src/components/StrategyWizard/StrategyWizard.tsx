/**
 * Strategy Wizard Component
 * 策略配置嚮導組件
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useDispatch } from 'react-redux';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Alert } from '../ui/Alert';
import { WizardSteps, defaultWizardSteps } from './WizardSteps';
import { SmartSuggestions } from './SmartSuggestions';
import {
  createStrategy,
  updateStrategy,
  fetchStrategies
} from '../../store/strategies/strategySlice';
import { exportService } from '../../services/exportService';
import {
  Strategy,
  StrategyType,
  RiskTolerance,
  StrategyCreateRequest
} from '../../types/strategyTypes';

// Types
export interface WizardData {
  // Step 1: Basic Info
  name: string;
  description: string;
  strategy_type: StrategyType;
  parameters: Record<string, any>;

  // Step 2: Risk Configuration
  risk_tolerance: RiskTolerance;
  initial_capital: number;
  position_sizing: number;
  stop_loss?: number;
  take_profit?: number;

  // Step 3: Strategy Parameters
  custom_parameters: Record<string, any>;

  // Step 4: Data Source
  data_source: string;
  symbols: string[];
  start_date?: string;
  end_date?: string;
  timeframe: string;

  // Step 5: Confirmation
  is_active: boolean;
}

interface StrategyWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete?: (strategy: Strategy) => void;
  initialData?: Partial<WizardData>;
  initialDraft?: string;
  editMode?: boolean;
  strategyId?: string;
}

const INITIAL_WIZARD_DATA: WizardData = {
  name: '',
  description: '',
  strategy_type: StrategyType.TECHNICAL_INDICATORS,
  parameters: {},
  risk_tolerance: RiskTolerance.MEDIUM,
  initial_capital: 10000,
  position_sizing: 0.1,
  stop_loss: undefined,
  take_profit: undefined,
  custom_parameters: {},
  data_source: 'default',
  symbols: [],
  start_date: undefined,
  end_date: undefined,
  timeframe: '1d',
  is_active: true
};

export const StrategyWizard: React.FC<StrategyWizardProps> = ({
  isOpen,
  onClose,
  onComplete,
  initialData,
  initialDraft,
  editMode = false,
  strategyId
}) => {
  const dispatch = useDispatch();
  const [currentStep, setCurrentStep] = useState(1);
  const [wizardData, setWizardData] = useState<WizardData>(INITIAL_WIZARD_DATA);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [draftId, setDraftId] = useState<string | null>(null);
  const [showExitConfirm, setShowExitConfirm] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Use ref to track wizardData for auto-save without causing re-renders
  const wizardDataRef = React.useRef(wizardData);
  wizardDataRef.current = wizardData;

  // Load initial data
  useEffect(() => {
    if (isOpen) {
      if (initialDraft) {
        loadDraft(initialDraft);
      } else if (initialData) {
        setWizardData({ ...INITIAL_WIZARD_DATA, ...initialData });
      } else {
        setWizardData(INITIAL_WIZARD_DATA);
      }
      setCurrentStep(1);
      setErrors({});
      setHasChanges(false);
    }
  }, [isOpen, initialData, initialDraft]);

  // Auto-save draft - only depend on hasChanges and isOpen
  // Use ref to access current wizardData value without triggering re-render
  useEffect(() => {
    if (!isOpen || !hasChanges) return;

    const saveDraftTimeout = setTimeout(() => {
      // Use ref to get latest wizardData
      saveDraft(wizardDataRef.current);
    }, 3000); // Auto-save after 3 seconds of inactivity

    return () => clearTimeout(saveDraftTimeout);
  }, [hasChanges, isOpen]);

  // Load draft from storage
  const loadDraft = async (draftId: string) => {
    try {
      const draft = await exportService.loadDraft(draftId);
      if (draft) {
        setWizardData({ ...INITIAL_WIZARD_DATA, ...draft.data });
        setCurrentStep(draft.step || 1);
        setDraftId(draft.id);
      }
    } catch (error) {
      console.error('Failed to load draft:', error);
    }
  };

  // Save draft to storage
  const saveDraft = async (dataToSave: WizardData = wizardData) => {
    if (!hasChanges) return;

    try {
      setIsSaving(true);
      const draft = await exportService.saveDraft({
        id: draftId || undefined,
        name: dataToSave.name || '未命名草稿',
        step: currentStep,
        data: dataToSave,
        timestamp: new Date().toISOString()
      });

      setDraftId(draft.id);
      setHasChanges(false);
    } catch (error) {
      console.error('Failed to save draft:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // Update wizard data
  const updateData = useCallback((updates: Partial<WizardData>) => {
    setWizardData(prev => ({ ...prev, ...updates }));
    setHasChanges(true);
  }, []);

  // Validate current step - pure validation function, doesn't set errors
  const validateStep = useCallback((step: number): boolean => {
    switch (step) {
      case 1:
        if (!wizardData.name.trim() || !wizardData.description.trim()) {
          return false;
        }
        break;

      case 2:
        if (wizardData.initial_capital <= 0 ||
            wizardData.position_sizing <= 0 ||
            wizardData.position_sizing > 1 ||
            (wizardData.stop_loss && wizardData.stop_loss >= 0)) {
          return false;
        }
        break;

      case 4:
        if (wizardData.symbols.length === 0) {
          return false;
        }
        break;
    }

    return true;
  }, [wizardData]);

  // Set errors for current step - separate function to avoid re-render loop
  const setStepErrors = useCallback((step: number) => {
    const newErrors: Record<string, string> = {};

    switch (step) {
      case 1:
        if (!wizardData.name.trim()) {
          newErrors.name = '策略名稱不能為空';
        }
        if (!wizardData.description.trim()) {
          newErrors.description = '策略描述不能為空';
        }
        break;

      case 2:
        if (wizardData.initial_capital <= 0) {
          newErrors.initial_capital = '初始資金必須大於 0';
        }
        if (wizardData.position_sizing <= 0 || wizardData.position_sizing > 1) {
          newErrors.position_sizing = '倉位大小必須在 0 到 1 之間';
        }
        if (wizardData.stop_loss && wizardData.stop_loss >= 0) {
          newErrors.stop_loss = '止損必須是負數';
        }
        break;

      case 4:
        if (wizardData.symbols.length === 0) {
          newErrors.symbols = '請至少選擇一個交易標的';
        }
        break;
    }

    setErrors(newErrors);
  }, [wizardData]);

  // Handle step navigation
  const handleStepChange = async (newStep: number) => {
    // Validate current step before moving
    if (newStep > currentStep && !validateStep(currentStep)) {
      setStepErrors(currentStep);
      return;
    }

    // Save draft before changing steps
    if (hasChanges) {
      await saveDraft();
    }

    setCurrentStep(newStep);
  };

  // Handle next step
  const handleNext = () => {
    if (!validateStep(currentStep)) {
      setStepErrors(currentStep);
      return;
    }
    handleStepChange(currentStep + 1);
  };

  // Handle previous step
  const handlePrevious = () => {
    handleStepChange(currentStep - 1);
  };

  // Calculate completion percentage
  const calculateCompletion = useCallback(() => {
    const requiredFields = {
      1: ['name', 'description', 'strategy_type'],
      2: ['risk_tolerance', 'initial_capital', 'position_sizing'],
      3: [],
      4: ['data_source', 'symbols', 'timeframe'],
      5: []
    };

    let completed = 0;
    for (let step = 1; step <= 5; step++) {
      const fields = requiredFields[step as keyof typeof requiredFields];
      const isStepComplete = fields.every(field => {
        const value = wizardData[field as keyof WizardData];
        if (Array.isArray(value)) return value.length > 0;
        return value !== undefined && value !== '';
      });

      if (isStepComplete) completed++;
      if (step === currentStep && isStepComplete) break;
    }

    return Math.round((completed / 5) * 100);
  }, [wizardData, currentStep]);

  // Create steps with status
  const steps = defaultWizardSteps.map((step, index) => ({
    ...step,
    isCompleted: calculateCompletion() > (index + 1) * 20,
    isCurrent: currentStep === step.id,
    isAccessible: step.id <= currentStep || validateStep(step.id - 1)
  }));

  // Handle suggestion selection
  const handleSuggestionSelect = (suggestion: Partial<WizardData>) => {
    updateData(suggestion);
  };

  // Handle wizard completion
  const handleComplete = async () => {
    if (!validateStep(5)) return;

    try {
      setIsSaving(true);

      const strategyData: StrategyCreateRequest = {
        name: wizardData.name,
        description: wizardData.description,
        strategy_type: wizardData.strategy_type,
        parameters: {
          ...wizardData.parameters,
          ...wizardData.custom_parameters,
          risk_tolerance: wizardData.risk_tolerance,
          initial_capital: wizardData.initial_capital,
          position_sizing: wizardData.position_sizing,
          stop_loss: wizardData.stop_loss,
          take_profit: wizardData.take_profit,
          data_source: wizardData.data_source,
          symbols: wizardData.symbols,
          start_date: wizardData.start_date,
          end_date: wizardData.end_date,
          timeframe: wizardData.timeframe
        },
        metadata: {
          created_with_wizard: true,
          wizard_version: '1.0.0'
        }
      };

      let strategy: Strategy;
      if (editMode && strategyId) {
        strategy = await dispatch(updateStrategy({
          strategyId,
          updateRequest: strategyData
        })).unwrap();
      } else {
        strategy = await dispatch(createStrategy(strategyData)).unwrap();
      }

      // Delete draft if exists
      if (draftId) {
        await exportService.deleteDraft(draftId);
      }

      // Refresh strategies list
      dispatch(fetchStrategies({}));

      onComplete?.(strategy);
      onClose();
    } catch (error) {
      console.error('Failed to create strategy:', error);
      setErrors({ submit: '創建策略失敗，請重試' });
    } finally {
      setIsSaving(false);
    }
  };

  // Handle wizard exit
  const handleExit = () => {
    if (hasChanges) {
      setShowExitConfirm(true);
    } else {
      onClose();
    }
  };

  const confirmExit = async () => {
    if (draftId) {
      try {
        await exportService.deleteDraft(draftId);
      } catch (error) {
        console.error('Failed to delete draft:', error);
      }
    }
    onClose();
  };

  // Render step content
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <Step1BasicInfo
            data={wizardData}
            errors={errors}
            onChange={updateData}
            onSuggestionSelect={handleSuggestionSelect}
          />
        );
      case 2:
        return (
          <Step2RiskConfig
            data={wizardData}
            errors={errors}
            onChange={updateData}
          />
        );
      case 3:
        return (
          <Step3Parameters
            data={wizardData}
            errors={errors}
            onChange={updateData}
          />
        );
      case 4:
        return (
          <Step4DataSource
            data={wizardData}
            errors={errors}
            onChange={updateData}
          />
        );
      case 5:
        return (
          <Step5Confirmation
            data={wizardData}
            onEdit={(step) => handleStepChange(step)}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleExit}
      title={editMode ? '編輯策略' : '創建新策略'}
      size="full"
    >
      <div className="h-full flex flex-col">
        {/* Exit Confirmation Modal */}
        {showExitConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                確定要退出嗎？
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                您有未保存的更改。確定要退出而不保存嗎？
              </p>
              <div className="flex justify-end space-x-3">
                <Button
                  variant="outline"
                  onClick={() => setShowExitConfirm(false)}
                >
                  取消
                </Button>
                <Button
                  variant="danger"
                  onClick={confirmExit}
                >
                  確定退出
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Wizard Steps */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <WizardSteps
            steps={steps}
            currentStep={currentStep}
            onStepChange={handleStepChange}
            completionPercentage={calculateCompletion()}
          />

          {/* Error Alert */}
          {errors.submit && (
            <Alert
              variant="error"
              title="錯誤"
              description={errors.submit}
              className="mb-4"
            />
          )}

          {/* Step Content */}
          {renderStepContent()}
        </div>

        {/* Wizard Actions */}
        <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {currentStep > 1 && (
                <Button
                  variant="outline"
                  onClick={handlePrevious}
                  disabled={isSaving}
                >
                  上一步
                </Button>
              )}
            </div>

            <div className="flex items-center space-x-3">
              {/* Save Draft Button */}
              <Button
                variant="outline"
                onClick={saveDraft}
                disabled={!hasChanges || isSaving}
                loading={isSaving}
              >
                保存草稿
              </Button>

              {/* Next/Complete Button */}
              {currentStep < 5 ? (
                <Button
                  variant="primary"
                  onClick={handleNext}
                  disabled={isSaving}
                >
                  下一步
                </Button>
              ) : (
                <Button
                  variant="primary"
                  onClick={handleComplete}
                  disabled={isSaving}
                  loading={isSaving}
                >
                  創建策略
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
};

// Step Components
function Step1BasicInfo({
  data,
  errors,
  onChange,
  onSuggestionSelect
}: {
  data: WizardData;
  errors: Record<string, string>;
  onChange: (updates: Partial<WizardData>) => void;
  onSuggestionSelect: (suggestion: Partial<WizardData>) => void;
}) {
  return (
    <div className="space-y-6">
      {/* Smart Suggestions */}
      <SmartSuggestions
        onSuggestionSelect={onSuggestionSelect}
        currentStep={1}
      />

      {/* Basic Information Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            策略名稱 <span className="text-red-500">*</span>
          </label>
          <Input
            value={data.name}
            onChange={(e) => onChange({ name: e.target.value })}
            placeholder="例如：RSI 動量策略"
            errorText={errors.name}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            策略類型 <span className="text-red-500">*</span>
          </label>
          <select
            className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            value={data.strategy_type}
            onChange={(e) => onChange({ strategy_type: e.target.value as StrategyType })}
          >
            {Object.values(StrategyType).map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          策略描述 <span className="text-red-500">*</span>
        </label>
        <textarea
          rows={4}
          className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          value={data.description}
          onChange={(e) => onChange({ description: e.target.value })}
          placeholder="請描述策略的目標、適用場景和預期效果..."
        />
        {errors.description && (
          <p className="mt-1 text-sm text-red-600">{errors.description}</p>
        )}
      </div>
    </div>
  );
}

function Step2RiskConfig({
  data,
  errors,
  onChange
}: {
  data: WizardData;
  errors: Record<string, string>;
  onChange: (updates: Partial<WizardData>) => void;
}) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            風險承受度 <span className="text-red-500">*</span>
          </label>
          <select
            className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            value={data.risk_tolerance}
            onChange={(e) => onChange({ risk_tolerance: e.target.value as RiskTolerance })}
          >
            {Object.values(RiskTolerance).map((level) => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            初始資金 <span className="text-red-500">*</span>
          </label>
          <Input
            type="number"
            value={data.initial_capital}
            onChange={(e) => onChange({ initial_capital: parseFloat(e.target.value) || 0 })}
            placeholder="10000"
            errorText={errors.initial_capital}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            倉位大小 <span className="text-red-500">*</span>
          </label>
          <Input
            type="number"
            step="0.01"
            min="0"
            max="1"
            value={data.position_sizing}
            onChange={(e) => onChange({ position_sizing: parseFloat(e.target.value) || 0 })}
            placeholder="0.1 (10%)"
            errorText={errors.position_sizing}
          />
          <p className="mt-1 text-xs text-gray-500">
            每次交易使用的資金比例（0-1）
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            止損 (%)
          </label>
          <Input
            type="number"
            step="0.01"
            value={data.stop_loss || ''}
            onChange={(e) => onChange({
              stop_loss: e.target.value ? parseFloat(e.target.value) : undefined
            })}
            placeholder="-5"
            errorText={errors.stop_loss}
          />
          <p className="mt-1 text-xs text-gray-500">
            負數表示虧損百分比
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            止盈 (%)
          </label>
          <Input
            type="number"
            step="0.01"
            value={data.take_profit || ''}
            onChange={(e) => onChange({
              take_profit: e.target.value ? parseFloat(e.target.value) : undefined
            })}
            placeholder="10"
          />
          <p className="mt-1 text-xs text-gray-500">
            正數表示盈利百分比
          </p>
        </div>
      </div>
    </div>
  );
}

function Step3Parameters({
  data,
  errors,
  onChange
}: {
  data: WizardData;
  errors: Record<string, string>;
  onChange: (updates: Partial<WizardData>) => void;
}) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          自定義策略參數
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          根據您的策略類型，配置相應的參數。這些參數將影響策略的執行邏輯。
        </p>
      </div>

      {/* Dynamic parameter fields based on strategy type */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            參數名稱
          </label>
          <Input
            placeholder="例如：rsi_period"
            value={data.custom_parameters.parameter_name || ''}
            onChange={(e) => onChange({
              custom_parameters: {
                ...data.custom_parameters,
                parameter_name: e.target.value
              }
            })}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            參數值
          </label>
          <Input
            placeholder="例如：14"
            value={data.custom_parameters.parameter_value || ''}
            onChange={(e) => onChange({
              custom_parameters: {
                ...data.custom_parameters,
                parameter_value: e.target.value
              }
            })}
          />
        </div>
      </div>

      {/* Common parameters for different strategy types */}
      {data.strategy_type === StrategyType.TECHNICAL_INDICATORS && (
        <div className="space-y-4">
          <h4 className="text-md font-medium text-gray-800 dark:text-gray-200">
            技術指標參數
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="快速均線週期"
              type="number"
              placeholder="10"
              value={data.custom_parameters.fast_period || ''}
              onChange={(e) => onChange({
                custom_parameters: {
                  ...data.custom_parameters,
                  fast_period: parseInt(e.target.value) || undefined
                }
              })}
            />
            <Input
              label="慢速均線週期"
              type="number"
              placeholder="30"
              value={data.custom_parameters.slow_period || ''}
              onChange={(e) => onChange({
                custom_parameters: {
                  ...data.custom_parameters,
                  slow_period: parseInt(e.target.value) || undefined
                }
              })}
            />
          </div>
        </div>
      )}

      {data.strategy_type === StrategyType.MOMENTUM && (
        <div className="space-y-4">
          <h4 className="text-md font-medium text-gray-800 dark:text-gray-200">
            動量策略參數
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="回看期"
              type="number"
              placeholder="20"
              value={data.custom_parameters.lookback_period || ''}
              onChange={(e) => onChange({
                custom_parameters: {
                  ...data.custom_parameters,
                  lookback_period: parseInt(e.target.value) || undefined
                }
              })}
            />
            <Input
              label="動量閾值"
              type="number"
              step="0.01"
              placeholder="0.02"
              value={data.custom_parameters.momentum_threshold || ''}
              onChange={(e) => onChange({
                custom_parameters: {
                  ...data.custom_parameters,
                  momentum_threshold: parseFloat(e.target.value) || undefined
                }
              })}
            />
          </div>
        </div>
      )}
    </div>
  );
}

function Step4DataSource({
  data,
  errors,
  onChange
}: {
  data: WizardData;
  errors: Record<string, string>;
  onChange: (updates: Partial<WizardData>) => void;
}) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            數據源 <span className="text-red-500">*</span>
          </label>
          <select
            className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            value={data.data_source}
            onChange={(e) => onChange({ data_source: e.target.value })}
          >
            <option value="default">默認數據源</option>
            <option value="yahoo">Yahoo Finance</option>
            <option value="alpha">Alpha Vantage</option>
            <option value="polygon">Polygon.io</option>
            <option value="custom">自定義數據源</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            時間框架
          </label>
          <select
            className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            value={data.timeframe}
            onChange={(e) => onChange({ timeframe: e.target.value })}
          >
            <option value="1m">1 分鐘</option>
            <option value="5m">5 分鐘</option>
            <option value="15m">15 分鐘</option>
            <option value="1h">1 小時</option>
            <option value="1d">1 天</option>
            <option value="1w">1 週</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          交易標的 <span className="text-red-500">*</span>
        </label>
        <textarea
          rows={3}
          className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          value={data.symbols.join(', ')}
          onChange={(e) => onChange({
            symbols: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
          })}
          placeholder="例如：AAPL, MSFT, GOOGL (每個標的用逗號分隔)"
        />
        {errors.symbols && (
          <p className="mt-1 text-sm text-red-600">{errors.symbols}</p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            開始日期
          </label>
          <Input
            type="date"
            value={data.start_date || ''}
            onChange={(e) => onChange({ start_date: e.target.value })}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            結束日期
          </label>
          <Input
            type="date"
            value={data.end_date || ''}
            onChange={(e) => onChange({ end_date: e.target.value })}
          />
        </div>
      </div>
    </div>
  );
}

function Step5Confirmation({
  data,
  onEdit
}: {
  data: WizardData;
  onEdit: (step: number) => void;
}) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-TW', {
      style: 'currency',
      currency: 'TWD',
      minimumFractionDigits: 0
    }).format(value);
  };

  const formatPercentage = (value?: number) => {
    if (value === undefined) return '-';
    return `${value > 0 ? '+' : ''}${(value * 100).toFixed(2)}%`;
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          策略摘要
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          請仔細檢查您的策略配置。確認無誤後點擊"創建策略"完成設置。
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Basic Info Card */}
        <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-gray-900 dark:text-white">
              基本資訊
            </h4>
            <button
              onClick={() => onEdit(1)}
              className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
            >
              修改
            </button>
          </div>
          <dl className="space-y-2">
            <div>
              <dt className="text-xs text-gray-500 dark:text-gray-400">策略名稱</dt>
              <dd className="text-sm text-gray-900 dark:text-white">{data.name}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500 dark:text-gray-400">類型</dt>
              <dd className="text-sm text-gray-900 dark:text-white">{data.strategy_type}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500 dark:text-gray-400">描述</dt>
              <dd className="text-sm text-gray-900 dark:text-white">{data.description}</dd>
            </div>
          </dl>
        </div>

        {/* Risk Config Card */}
        <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-gray-900 dark:text-white">
              風險配置
            </h4>
            <button
              onClick={() => onEdit(2)}
              className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
            >
              修改
            </button>
          </div>
          <dl className="space-y-2">
            <div>
              <dt className="text-xs text-gray-500 dark:text-gray-400">風險承受度</dt>
              <dd className="text-sm text-gray-900 dark:text-white">{data.risk_tolerance}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500 dark:text-gray-400">初始資金</dt>
              <dd className="text-sm text-gray-900 dark:text-white">
                {formatCurrency(data.initial_capital)}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500 dark:text-gray-400">倉位大小</dt>
              <dd className="text-sm text-gray-900 dark:text-white">
                {(data.position_sizing * 100).toFixed(0)}%
              </dd>
            </div>
            {(data.stop_loss || data.take_profit) && (
              <div className="flex gap-4">
                {data.stop_loss && (
                  <div>
                    <dt className="text-xs text-gray-500 dark:text-gray-400">止損</dt>
                    <dd className="text-sm text-red-600">{formatPercentage(data.stop_loss)}</dd>
                  </div>
                )}
                {data.take_profit && (
                  <div>
                    <dt className="text-xs text-gray-500 dark:text-gray-400">止盈</dt>
                    <dd className="text-sm text-green-600">{formatPercentage(data.take_profit)}</dd>
                  </div>
                )}
              </div>
            )}
          </dl>
        </div>

        {/* Parameters Card */}
        <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-gray-900 dark:text-white">
              策略參數
            </h4>
            <button
              onClick={() => onEdit(3)}
              className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
            >
              修改
            </button>
          </div>
          <dl className="space-y-2">
            {Object.entries(data.custom_parameters).map(([key, value]) => (
              <div key={key}>
                <dt className="text-xs text-gray-500 dark:text-gray-400">{key}</dt>
                <dd className="text-sm text-gray-900 dark:text-white">{value}</dd>
              </div>
            ))}
            {Object.keys(data.custom_parameters).length === 0 && (
              <div className="text-sm text-gray-500 dark:text-gray-400">
                無自定義參數
              </div>
            )}
          </dl>
        </div>

        {/* Data Source Card */}
        <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-gray-900 dark:text-white">
              數據源設置
            </h4>
            <button
              onClick={() => onEdit(4)}
              className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
            >
              修改
            </button>
          </div>
          <dl className="space-y-2">
            <div>
              <dt className="text-xs text-gray-500 dark:text-gray-400">數據源</dt>
              <dd className="text-sm text-gray-900 dark:text-white">{data.data_source}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500 dark:text-gray-400">時間框架</dt>
              <dd className="text-sm text-gray-900 dark:text-white">{data.timeframe}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500 dark:text-gray-400">交易標的</dt>
              <dd className="text-sm text-gray-900 dark:text-white">
                {data.symbols.length > 0 ? data.symbols.join(', ') : '未設置'}
              </dd>
            </div>
            {(data.start_date || data.end_date) && (
              <div className="text-sm text-gray-900 dark:text-white">
                {data.start_date && `從 ${data.start_date}`}
                {data.start_date && data.end_date && ' '}
                {data.end_date && `到 ${data.end_date}`}
              </div>
            )}
          </dl>
        </div>
      </div>

      {/* Final Confirmation */}
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="text-sm text-blue-800 dark:text-blue-200">
            <p className="font-medium mb-1">創建確認</p>
            <p>點擊"創建策略"後，系統將根據以上配置創建新的交易策略。您可以隨時在策略管理頁面編輯或調整這些設置。</p>
          </div>
        </div>
      </div>
    </div>
  );
}