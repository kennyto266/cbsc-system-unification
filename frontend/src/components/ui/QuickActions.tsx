import React from 'react'
import { PlusIcon, PlayIcon, DocumentTextIcon, CogIcon } from '@heroicons/react/24/outline'

const actions = [
  {
    title: '创建策略',
    description: '使用可视化编辑器创建新的量化策略',
    icon: PlusIcon,
    color: 'blue',
    href: '/strategies/new',
  },
  {
    title: '运行回测',
    description: '测试策略在历史数据上的表现',
    icon: PlayIcon,
    color: 'green',
    href: '/backtest',
  },
  {
    title: '查看报告',
    description: '生成详细的策略分析报告',
    icon: DocumentTextIcon,
    color: 'purple',
    href: '/reports',
  },
  {
    title: '系统设置',
    description: '配置交易参数和风险控制',
    icon: CogIcon,
    color: 'yellow',
    href: '/settings',
  },
]

const colorClasses = {
  blue: 'bg-blue-50 text-blue-600 hover:bg-blue-100',
  green: 'bg-green-50 text-green-600 hover:bg-green-100',
  purple: 'bg-purple-50 text-purple-600 hover:bg-purple-100',
  yellow: 'bg-yellow-50 text-yellow-600 hover:bg-yellow-100',
}

export const QuickActions: React.FC = () => {
  return (
    <div className="card">
      <div className="card-header">
        <h2 className="text-lg font-semibold text-gray-900">快速操作</h2>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {actions.map((action) => (
          <a
            key={action.title}
            href={action.href}
            className={`p-4 rounded-lg transition-colors ${colorClasses[action.color as keyof typeof colorClasses]}`}
          >
            <action.icon className="w-8 h-8 mb-2" />
            <h3 className="font-medium text-gray-900">{action.title}</h3>
            <p className="mt-1 text-sm text-gray-600">{action.description}</p>
          </a>
        ))}
      </div>
    </div>
  )
}