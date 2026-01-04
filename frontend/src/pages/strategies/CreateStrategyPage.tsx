import React, { useState } from 'react'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Link, useNavigate } from 'react-router-dom'
import {
  ArrowLeftIcon,
  CheckIcon,
  SparklesIcon,
  StarIcon,
  ChartBarIcon,
  ClockIcon
} from '@heroicons/react/24/outline'

const CreateStrategyPage: React.FC = () => {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: 'technical',
    riskLevel: 'medium',
    initialCapital: 100000,
  })

  const STRATEGY_TEMPLATES = [
    {
      id: 'rsi',
      name: 'RSI策略',
      icon: <ChartBarIcon className="h-6 w-6" />,
      description: '基於相對強弱指標的技術分析策略',
      category: 'technical',
    },
    {
      id: 'momentum',
      name: '動量策略',
      icon: <SparklesIcon className="h-6 w-6" />,
      description: '追蹤市場趨勢的動量交易策略',
      category: 'technical',
    },
    {
      id: 'sentiment',
      name: '情緒策略',
      icon: <StarIcon className="h-6 w-6" />,
      description: '基於市場情緒指標的策略',
      category: 'fundamental',
    },
    {
      id: 'arbitrage',
      name: '套利策略',
      icon: <ClockIcon className="h-6 w-6" />,
      description: '跨市場套利交易策略',
      category: 'quant',
    },
  ]

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // TODO: Connect to POST /api/personal-strategies/strategies
    console.log('Creating strategy:', formData)
    alert('策略創建成功！')
    navigate('/strategies/list')
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to="/strategies/list">
          <Button variant="outline" size="sm">
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            返回列表
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            創建新策略
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            選擇策略模板並配置參數
          </p>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center justify-center gap-4 py-4">
        {[1, 2, 3].map((s) => (
          <React.Fragment key={s}>
            <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
              step >= s
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
            }`}>
              {step >= s ? <CheckIcon className="h-5 w-5" /> : s}
            </div>
            {s < 3 && (
              <div className={`flex-1 h-1 ${step > s ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'}`} />
            )}
          </React.Fragment>
        ))}
      </div>

      {step === 1 && (
        <>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            選擇策略類型
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {STRATEGY_TEMPLATES.map((template) => (
              <div
                key={template.id}
                role="button"
                tabIndex={0}
                className="p-6 rounded-lg border border-gray-200 bg-white shadow-sm cursor-pointer hover:shadow-lg transition-shadow border-2 border-transparent hover:border-blue-500"
                onClick={() => {
                  setFormData({ ...formData, category: template.category })
                  setStep(2)
                }}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    setFormData({ ...formData, category: template.category })
                    setStep(2)
                  }
                }}
              >
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
                    {template.icon}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">
                      {template.name}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {template.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {step === 2 && (
        <>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            配置策略參數
          </h2>
          <Card className="p-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  策略名稱 *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                  placeholder="輸入策略名稱"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  策略描述
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                  placeholder="描述策略的投資理念和目標"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    風險等級
                  </label>
                  <select
                    value={formData.riskLevel}
                    onChange={(e) => setFormData({ ...formData, riskLevel: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                  >
                    <option value="low">低風險</option>
                    <option value="medium">中等風險</option>
                    <option value="high">高風險</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    初始資本
                  </label>
                  <input
                    type="number"
                    value={formData.initialCapital}
                    onChange={(e) => setFormData({ ...formData, initialCapital: Number(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                    placeholder="100000"
                  />
                </div>
              </div>

              <div className="flex gap-4 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setStep(1)}
                  className="flex-1"
                >
                  上一步
                </Button>
                <Button
                  type="submit"
                  className="flex-1"
                >
                  創建策略
                </Button>
              </div>
            </form>
          </Card>
        </>
      )}

      {/* API Note */}
      <Card className="p-4 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <div className="flex items-start gap-3">
          <SparklesIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              <strong>API集成：</strong> 此頁面將連接到 POST /api/personal-strategies/strategies
              創建新策略。當前為演示模式，實際部署時需要實現完整的表單驗證和API調用。
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default CreateStrategyPage
