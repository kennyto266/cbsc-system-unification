/**
 * Wizard Steps Component
 * 嚮導步驟組件
 */

import React from 'react';
import { CheckCircleIcon, ClockIcon } from '@heroicons/react/24/outline';

export interface WizardStep {
  id: number;
  title: string;
  description: string;
  isCompleted: boolean;
  isCurrent: boolean;
  isAccessible: boolean;
}

interface WizardStepsProps {
  steps: WizardStep[];
  currentStep: number;
  onStepChange: (step: number) => void;
  completionPercentage: number;
}

export const WizardSteps: React.FC<WizardStepsProps> = ({
  steps,
  currentStep,
  onStepChange,
  completionPercentage
}) => {
  return (
    <div className="mb-8">
      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            完成進度
          </span>
          <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
            {completionPercentage}%
          </span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            className="bg-blue-600 dark:bg-blue-400 h-2 rounded-full transition-all duration-300"
            style={{ width: `${completionPercentage}%` }}
          />
        </div>
      </div>

      {/* Step Navigation */}
      <nav aria-label="Progress">
        <ol className="flex items-center justify-between">
          {steps.map((step, stepIdx) => {
            const isCompleted = step.isCompleted;
            const isCurrent = step.isCurrent;
            const isAccessible = step.isAccessible;

            return (
              <li
                key={step.id}
                className={stepIdx !== steps.length - 1 ? 'flex-1' : ''}
              >
                <div
                  className={`
                    flex items-center
                    ${stepIdx !== steps.length - 1 ? 'pr-8 sm:pr-20' : ''}
                  `}
                >
                  <button
                    onClick={() => isAccessible && onStepChange(step.id)}
                    disabled={!isAccessible}
                    className={`
                      relative flex items-center justify-center w-10 h-10
                      rounded-full transition-all duration-200
                      ${isCompleted
                        ? 'bg-blue-600 dark:bg-blue-500 hover:bg-blue-700 dark:hover:bg-blue-600'
                        : isCurrent
                        ? 'bg-blue-100 dark:bg-blue-900 border-2 border-blue-600 dark:border-blue-400'
                        : isAccessible
                        ? 'bg-white dark:bg-gray-800 border-2 border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                        : 'bg-gray-100 dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 cursor-not-allowed'
                      }
                    `}
                    aria-current={isCurrent ? 'step' : undefined}
                  >
                    {isCompleted ? (
                      <CheckCircleIcon className="w-6 h-6 text-white" aria-hidden="true" />
                    ) : isCurrent ? (
                      <span className="text-blue-600 dark:text-blue-400 font-medium">
                        {step.id}
                      </span>
                    ) : (
                      <span className="text-gray-500 dark:text-gray-400">
                        {step.id}
                      </span>
                    )}
                  </button>

                  {/* Step Content */}
                  <div className="ml-4 min-w-0 flex-1 text-left">
                    <p
                      className={`
                        text-sm font-medium
                        ${isCompleted || isCurrent
                          ? 'text-blue-600 dark:text-blue-400'
                          : isAccessible
                          ? 'text-gray-900 dark:text-gray-100'
                          : 'text-gray-400 dark:text-gray-600'
                        }
                      `}
                    >
                      步驟 {step.id}: {step.title}
                    </p>
                    <p
                      className={`
                        text-xs mt-1
                        ${isCurrent
                          ? 'text-gray-600 dark:text-gray-400'
                          : 'text-gray-500 dark:text-gray-500'
                        }
                      `}
                    >
                      {step.description}
                    </p>
                  </div>

                  {/* Connecting Line */}
                  {stepIdx !== steps.length - 1 && (
                    <div
                      className={`
                        absolute top-5 left-10
                        w-full h-0.5
                        ${isCompleted
                          ? 'bg-blue-600 dark:bg-blue-400'
                          : 'bg-gray-300 dark:bg-gray-600'
                        }
                      `}
                      style={{ left: '2.5rem', right: '-2.5rem' }}
                    />
                  )}
                </div>
              </li>
            );
          })}
        </ol>
      </nav>

      {/* Current Step Details */}
      <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <div className="flex items-start space-x-3">
          <ClockIcon className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-blue-900 dark:text-blue-100">
              當前步驟: {steps[currentStep - 1]?.title}
            </h3>
            <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
              {steps[currentStep - 1]?.description}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Default step configuration
export const defaultWizardSteps: Omit<WizardStep, 'isCompleted' | 'isCurrent' | 'isAccessible'>[] = [
  {
    id: 1,
    title: '基本資訊',
    description: '設定策略名稱、類型和基本參數'
  },
  {
    id: 2,
    title: '風險配置',
    description: '設定風險承受度、止損止盈和資金管理'
  },
  {
    id: 3,
    title: '策略參數',
    description: '配置具體的策略執行參數'
  },
  {
    id: 4,
    title: '數據源設置',
    description: '選擇數據源和時間範圍'
  },
  {
    id: 5,
    title: '確認與創建',
    description: '檢查配置並創建策略'
  }
];