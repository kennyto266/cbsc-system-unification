import React from 'react'
import { ClockIcon, ArrowTrendingUpIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'

const activities = [
  {
    id: 1,
    type: 'success',
    title: '策略执行成功',
    description: '双均线策略买入 0700.HK',
    timestamp: '2 分钟前',
    icon: ArrowTrendingUpIcon,
  },
  {
    id: 2,
    type: 'warning',
    title: '风险提醒',
    description: '投资组合仓位超过 90%',
    timestamp: '15 分钟前',
    icon: ExclamationTriangleIcon,
  },
  {
    id: 3,
    type: 'info',
    title: '策略更新',
    description: 'RSI 策略参数已优化',
    timestamp: '1 小时前',
    icon: ClockIcon,
  },
  {
    id: 4,
    type: 'success',
    title: '收益创新高',
    description: '本月收益率达到 8.5%',
    timestamp: '2 小时前',
    icon: ArrowTrendingUpIcon,
  },
]

const typeStyles = {
  success: 'bg-green-50 text-green-600',
  warning: 'bg-yellow-50 text-yellow-600',
  info: 'bg-blue-50 text-blue-600',
}

export const RecentActivities: React.FC = () => {
  return (
    <div className="space-y-4">
      {activities.map((activity) => (
        <div key={activity.id} className="flex items-start space-x-3">
          <div className={`p-2 rounded-lg ${typeStyles[activity.type]}`}>
            <activity.icon className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900">{activity.title}</p>
            <p className="text-sm text-gray-500">{activity.description}</p>
            <p className="mt-1 text-xs text-gray-400">{activity.timestamp}</p>
          </div>
        </div>
      ))}

      <button className="w-full mt-4 text-sm text-blue-600 hover:text-blue-500 font-medium">
        查看全部活动
      </button>
    </div>
  )
}