import React from 'react'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Link } from 'react-router-dom'
import {
  ArrowLeftIcon,
  SparklesIcon,
  StarIcon,
  ChartBarIcon,
  DocumentDuplicateIcon,
  CubeIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline'

const STRATEGY_TEMPLATES = [
  {
    id: 'rsi-dual',
    name: '雙RSI策略',
    category: '技術分析',
    description: '結合短期和長期RSI指標，捕捉超買超賣機會',
    complexity: '中等',
    expectedReturn: '+12-18%',
    risk: '中等',
    icon: <ChartBarIcon className="h-8 w-8" />,
    features: ['雙週期RSI', '動態止損', '趋势確認'],
  },
  {
    id: 'sentiment-momentum',
    name: '情緒動量策略',
    category: '多因子',
    description: '整合市場情緒指標與價格動量的雙因子策略',
    complexity: '高',
    expectedReturn: '+15-25%',
    risk: '中高',
    icon: <SparklesIcon className="h-8 w-8" />,
    features: ['情緒分析', '動量篩選', '風險平價'],
  },
  {
    id: 'cbsc-composite',
    name: 'CBSC綜合指標',
    category: 'CBSC專用',
    description: '基於CBSC數據的綜合技術指標策略',
    complexity: '中等',
    expectedReturn: '+10-20%',
    risk: '中等',
    icon: <StarIcon className="h-8 w-8" />,
    features: ['CBSC數據', '多指標', '自動優化'],
  },
  {
    id: 'arbitrage-stat',
    name: '統計套利策略',
    category: '套利',
    description: '利用價格統計特性的均值回歷套利策略',
    complexity: '高',
    expectedReturn: '+8-15%',
    risk: '低',
    icon: <CubeIcon className="h-8 w-8" />,
    features: ['統計分析', '均值回歸', '風險控制'],
  },
  {
    id: 'portfolio-opt',
    name: '投資組合優化',
    category: '資產管理',
    description: '基於現代投資組合理論的優化策略',
    complexity: '高',
    expectedReturn: '+10-16%',
    risk: '可調',
    icon: <DocumentDuplicateIcon className="h-8 w-8" />,
    features: ['馬科維茲', '風險平價', '再平衡'],
  },
  {
    id: 'trend-follow',
    name: '趨勢跟蹤策略',
    category: '技術分析',
    description: '識別並跟蹤市場趨勢的經典策略',
    complexity: '低',
    expectedReturn: '+5-15%',
    risk: '中等',
    icon: <ChartBarIcon className="h-8 w-8" />,
    features: ['移動平均', '趨勢確認', '倉位管理'],
  },
]

const StrategyTemplatesPage: React.FC = () => {
  return (
    <div className="space-y-6">
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
            策略模板
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            選擇預設策略模板快速開始
          </p>
        </div>
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {STRATEGY_TEMPLATES.map((template) => (
          <Card key={template.id} className="hover:shadow-lg transition-all cursor-pointer group">
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
                  {template.icon}
                </div>
                <span className="px-2 py-1 text-xs font-medium rounded bg-purple-100 text-purple-800">
                  {template.category}
                </span>
              </div>

              <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 group-hover:text-blue-600 transition-colors">
                {template.name}
              </h3>

              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                {template.description}
              </p>

              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500 dark:text-gray-400">複雜度</span>
                  <span className="font-medium text-gray-900 dark:text-white">{template.complexity}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500 dark:text-gray-400">預期收益</span>
                  <span className="font-medium text-green-600">{template.expectedReturn}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500 dark:text-gray-400">風險等級</span>
                  <span className="font-medium text-gray-900 dark:text-white">{template.risk}</span>
                </div>
              </div>

              <div className="border-t dark:border-gray-700 pt-4">
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">特性</div>
                <div className="flex flex-wrap gap-1">
                  {template.features.map((feature, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded"
                    >
                      {feature}
                    </span>
                  ))}
                </div>
              </div>

              <Link to="/strategies/create">
                <Button className="w-full mt-4">
                  使用此模板
                  <ArrowRightIcon className="h-4 w-4 ml-2" />
                </Button>
              </Link>
            </div>
          </Card>
        ))}
      </div>

      {/* API Note */}
      <Card className="p-4 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <div className="flex items-start gap-3">
          <DocumentDuplicateIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              <strong>模板來源：</strong> 這些模板來自 GET /api/strategies/templates API。
              每個模板都包含預設參數和配置，可以基於它們快速創建新策略。
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default StrategyTemplatesPage
