import React, { useState } from 'react'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Link } from 'react-router-dom'
import {
  ArrowLeftIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  ShieldCheckIcon,
  KeyIcon,
  CheckIcon
} from '@heroicons/react/24/outline'

// Mock role data
const MOCK_ROLES = [
  {
    id: '1',
    name: 'admin',
    displayName: '系統管理員',
    description: '擁有所有系統權限',
    permissions: [
      'users.create',
      'users.read',
      'users.update',
      'users.delete',
      'strategies.create',
      'strategies.read',
      'strategies.update',
      'strategies.delete',
      'strategies.execute',
      'system.manage',
      'reports.view',
    ],
    userCount: 3,
    isSystemRole: true,
    createdAt: '2025-01-01',
  },
  {
    id: '2',
    name: 'premium',
    displayName: '高級用戶',
    description: '可以使用所有策略功能',
    permissions: [
      'strategies.create',
      'strategies.read',
      'strategies.update',
      'strategies.execute',
      'reports.view',
    ],
    userCount: 12,
    isSystemRole: false,
    createdAt: '2025-02-15',
  },
  {
    id: '3',
    name: 'user',
    displayName: '普通用戶',
    description: '基本用戶權限',
    permissions: [
      'strategies.read',
      'strategies.execute',
    ],
    userCount: 45,
    isSystemRole: false,
    createdAt: '2025-01-01',
  },
  {
    id: '4',
    name: 'viewer',
    displayName: '訪客',
    description: '只讀權限',
    permissions: [
      'strategies.read',
    ],
    userCount: 8,
    isSystemRole: false,
    createdAt: '2025-03-20',
  },
]

// Permission categories
const PERMISSION_CATEGORIES = {
  users: { label: '用戶管理', icon: '👥' },
  strategies: { label: '策略管理', icon: '📊' },
  system: { label: '系統管理', icon: '⚙️' },
  reports: { label: '報告查看', icon: '📈' },
}

const RolePermissionsPage: React.FC = () => {
  const [roles] = useState(MOCK_ROLES)
  const [selectedRole, setSelectedRole] = useState(MOCK_ROLES[0])

  const groupPermissions = (permissions: string[]) => {
    const grouped: Record<string, string[]> = {}
    permissions.forEach(perm => {
      const [category] = perm.split('.')
      if (!grouped[category]) {
        grouped[category] = []
      }
      grouped[category].push(perm)
    })
    return grouped
  }

  const hasPermission = (role: typeof MOCK_ROLES[0], permission: string) => {
    return role.permissions.includes(permission)
  }

  const getAllPermissions = () => {
    return [
      'users.create',
      'users.read',
      'users.update',
      'users.delete',
      'strategies.create',
      'strategies.read',
      'strategies.update',
      'strategies.delete',
      'strategies.execute',
      'system.manage',
      'reports.view',
    ]
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            角色權限管理
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            配置系統角色和權限
          </p>
        </div>
        <div className="flex gap-3">
          <Button>
            <PlusIcon className="h-5 w-5 mr-2" />
            添加角色
          </Button>
        </div>
      </div>

      {/* Back Button */}
      <Link to="/users">
        <Button variant="outline" size="sm">
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          返回用戶管理
        </Button>
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Role List */}
        <div className="lg:col-span-1">
          <Card className="p-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              角色列表 ({roles.length})
            </h2>
            <div className="space-y-2">
              {roles.map((role) => (
                <div
                  key={role.id}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    selectedRole.id === role.id
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                  onClick={() => setSelectedRole(role)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <ShieldCheckIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                      <div>
                        <div className="font-medium text-gray-900 dark:text-white">
                          {role.displayName}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          @{role.name}
                        </div>
                      </div>
                    </div>
                    {role.isSystemRole && (
                      <span className="px-2 py-1 text-xs bg-orange-100 text-orange-800 rounded">
                        系統
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    {role.description}
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                    <span>{role.permissions.length} 個權限</span>
                    <span>{role.userCount} 個用戶</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Permission Details */}
        <div className="lg:col-span-2">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {selectedRole.displayName}
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {selectedRole.description}
                </p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm">
                  <PencilIcon className="h-4 w-4 mr-2" />
                  編輯
                </Button>
                {!selectedRole.isSystemRole && (
                  <Button variant="outline" size="sm" className="text-red-600">
                    <TrashIcon className="h-4 w-4 mr-2" />
                    刪除
                  </Button>
                )}
              </div>
            </div>

            {/* Role Info */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <Card className="p-4 bg-gray-50 dark:bg-gray-800">
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">角色名稱</div>
                <div className="font-medium text-gray-900 dark:text-white">@{selectedRole.name}</div>
              </Card>
              <Card className="p-4 bg-gray-50 dark:bg-gray-800">
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">用戶數量</div>
                <div className="font-medium text-gray-900 dark:text-white">{selectedRole.userCount}</div>
              </Card>
              <Card className="p-4 bg-gray-50 dark:bg-gray-800">
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">權限數量</div>
                <div className="font-medium text-gray-900 dark:text-white">{selectedRole.permissions.length}</div>
              </Card>
            </div>

            {/* Permissions Matrix */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                權限配置
              </h3>
              <div className="space-y-4">
                {Object.entries(PERMISSION_CATEGORIES).map(([category, info]) => {
                  const categoryPerms = getAllPermissions().filter(p => p.startsWith(category))
                  return (
                    <div key={category} className="border dark:border-gray-700 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-xl">{info.icon}</span>
                        <h4 className="font-medium text-gray-900 dark:text-white">
                          {info.label}
                        </h4>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                        {categoryPerms.map((perm) => {
                          const [, action] = perm.split('.')
                          const hasIt = hasPermission(selectedRole, perm)
                          return (
                            <div
                              key={perm}
                              className={`flex items-center gap-2 p-2 rounded ${
                                hasIt
                                  ? 'bg-green-50 dark:bg-green-900/20'
                                  : 'bg-gray-50 dark:bg-gray-800'
                              }`}
                            >
                              {hasIt ? (
                                <CheckIcon className="h-4 w-4 text-green-600 dark:text-green-400" />
                              ) : (
                                <div className="h-4 w-4" />
                              )}
                              <span className={`text-sm ${
                                hasIt
                                  ? 'text-green-700 dark:text-green-300'
                                  : 'text-gray-600 dark:text-gray-400'
                              }`}>
                                {action}
                              </span>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Users with this role */}
            <div className="mt-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                擁有此角色的用戶 ({selectedRole.userCount})
              </h3>
              <Card className="p-4">
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <KeyIcon className="h-12 w-12 mx-auto mb-2" />
                  <p>用戶列表將在此處顯示</p>
                  <p className="text-sm mt-1">實際部署時將從API獲取真實數據</p>
                </div>
              </Card>
            </div>
          </Card>
        </div>
      </div>

      {/* API Note */}
      <Card className="p-4 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <div className="flex items-start gap-3">
          <ShieldCheckIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              <strong>API集成：</strong> 角色權限管理將連接到以下API端點：
              GET /api/roles (角色列表), GET /api/roles/{'{'}id{'}'} (角色詳情), PUT /api/roles/{'{'}id{'}'} (更新角色),
              GET /api/permissions (權限列表)。當前顯示模擬數據。
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default RolePermissionsPage
