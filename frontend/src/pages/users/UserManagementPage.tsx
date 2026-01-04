import React from 'react'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Link } from 'react-router-dom'
import {
  ArrowLeftIcon,
  UserGroupIcon,
  UserIcon,
  ShieldCheckIcon,
  ClockIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'

const UserManagementPage: React.FC = () => {
  // Mock statistics data
  const STATS = [
    {
      label: '總用戶數',
      value: '1,234',
      icon: <UserGroupIcon className="h-6 w-6" />,
      color: 'blue',
      change: '+12.5%',
    },
    {
      label: '活躍用戶',
      value: '856',
      icon: <UserIcon className="h-6 w-6" />,
      color: 'green',
      change: '+8.3%',
    },
    {
      label: '在線用戶',
      value: '127',
      icon: <ClockIcon className="h-6 w-6" />,
      color: 'purple',
      change: '實時',
    },
    {
      label: '管理員',
      value: '12',
      icon: <ShieldCheckIcon className="h-6 w-6" />,
      color: 'orange',
      change: '固定',
    },
  ]

  const RECENT_ACTIVITIES = [
    {
      id: 1,
      user: '張三',
      action: '創建了新策略',
      time: '5分鐘前',
      type: 'create',
    },
    {
      id: 2,
      user: '李四',
      action: '更新了個人資料',
      time: '15分鐘前',
      type: 'update',
    },
    {
      id: 3,
      user: '王五',
      action: '運行了回測',
      time: '30分鐘前',
      type: 'execute',
    },
    {
      id: 4,
      user: '趙六',
      action: '登錄系統',
      time: '1小時前',
      type: 'login',
    },
  ]

  const getActivityBadge = (type: string) => {
    const badges: Record<string, { color: string; label: string }> = {
      create: { color: 'green', label: '創建' },
      update: { color: 'blue', label: '更新' },
      execute: { color: 'purple', label: '執行' },
      login: { color: 'gray', label: '登錄' },
    }
    const badge = badges[type] || badges.login
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded bg-${badge.color}-100 text-${badge.color}-800`}>
        {badge.label}
      </span>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to="/">
          <Button variant="outline" size="sm">
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            返回首頁
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            用戶管理
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            管理系統用戶、權限和活動
          </p>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {STATS.map((stat) => (
          <Card key={stat.label} className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div className={`p-2 bg-${stat.color}-100 dark:bg-${stat.color}-900 rounded-lg`}>
                {stat.icon}
              </div>
              <span className={`text-xs font-medium ${
                stat.change.startsWith('+') ? 'text-green-600' : 'text-gray-600'
              }`}>
                {stat.change}
              </span>
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">
              {stat.label}
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {stat.value}
            </div>
          </Card>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          快速操作
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link to="/users/list">
            <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
                  <UserGroupIcon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                    用戶列表
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    查看和管理所有用戶
                  </p>
                </div>
              </div>
            </Card>
          </Link>

          <Link to="/users/roles">
            <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-lg">
                  <ShieldCheckIcon className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                    角色權限
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    配置角色和權限
                  </p>
                </div>
              </div>
            </Card>
          </Link>

          <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg">
                <ChartBarIcon className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  活動日誌
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  查看用戶活動記錄
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Recent Activities */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          最近活動
        </h2>
        <Card className="overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  用戶
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  操作
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  類型
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  時間
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              {RECENT_ACTIVITIES.map((activity) => (
                <tr key={activity.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      {activity.user}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-700 dark:text-gray-300">
                      {activity.action}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {getActivityBadge(activity.type)}
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {activity.time}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>

      {/* System Overview */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          系統概覽
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              用戶分佈
            </h3>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600 dark:text-gray-400">管理員</span>
                  <span className="font-medium text-gray-900 dark:text-white">12 (1%)</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div className="bg-orange-500 h-2 rounded-full" style={{ width: '1%' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600 dark:text-gray-400">高級用戶</span>
                  <span className="font-medium text-gray-900 dark:text-white">234 (19%)</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full" style={{ width: '19%' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600 dark:text-gray-400">普通用戶</span>
                  <span className="font-medium text-gray-900 dark:text-white">988 (80%)</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div className="bg-green-500 h-2 rounded-full" style={{ width: '80%' }} />
                </div>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              註冊趨勢
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">今日新增</span>
                <span className="font-medium text-green-600">+23</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">本周新增</span>
                <span className="font-medium text-blue-600">+156</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">本月新增</span>
                <span className="font-medium text-purple-600">+623</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">總增長率</span>
                <span className="font-medium text-gray-900 dark:text-white">+12.5%</span>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* API Note */}
      <Card className="p-4 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <div className="flex items-start gap-3">
          <UserGroupIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              <strong>API集成：</strong> 用戶管理功能將連接到以下API端點：
              GET /api/users (用戶列表), GET /api/users/{'{'}id{'}'} (用戶詳情), GET /api/roles (角色列表)。
              當前顯示模擬數據。實際部署時將從後端獲取真實數據。
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default UserManagementPage
