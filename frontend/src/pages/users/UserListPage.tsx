import React, { useState } from 'react'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Link } from 'react-router-dom'
import {
  ArrowLeftIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  PencilIcon,
  TrashIcon,
  ShieldCheckIcon,
  UserIcon,
  CheckIcon,
  XIcon
} from '@heroicons/react/24/outline'

// Mock user data
const MOCK_USERS = [
  {
    id: '1',
    username: 'admin',
    email: 'admin@cbsc.com',
    fullName: '系統管理員',
    role: 'admin',
    status: 'active',
    lastLogin: '2025-12-05 10:30',
    createdAt: '2025-01-01',
  },
  {
    id: '2',
    username: 'zhangsan',
    email: 'zhangsan@example.com',
    fullName: '張三',
    role: 'user',
    status: 'active',
    lastLogin: '2025-12-05 09:15',
    createdAt: '2025-03-15',
  },
  {
    id: '3',
    username: 'lisi',
    email: 'lisi@example.com',
    fullName: '李四',
    role: 'premium',
    status: 'active',
    lastLogin: '2025-12-04 16:45',
    createdAt: '2025-05-20',
  },
  {
    id: '4',
    username: 'wangwu',
    email: 'wangwu@example.com',
    fullName: '王五',
    role: 'user',
    status: 'inactive',
    lastLogin: '2025-11-20 14:20',
    createdAt: '2025-06-10',
  },
  {
    id: '5',
    username: 'zhaoliu',
    email: 'zhaoliu@example.com',
    fullName: '趙六',
    role: 'user',
    status: 'active',
    lastLogin: '2025-12-05 08:30',
    createdAt: '2025-08-05',
  },
]

const STATUS_CONFIG = {
  active: { label: '活躍', color: 'green' },
  inactive: { label: '未激活', color: 'gray' },
  suspended: { label: '已停用', color: 'red' },
}

const ROLE_CONFIG = {
  admin: { label: '管理員', color: 'orange' },
  premium: { label: '高級用戶', color: 'blue' },
  user: { label: '普通用戶', color: 'gray' },
}

const UserListPage: React.FC = () => {
  const [users] = useState(MOCK_USERS)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedRole, setSelectedRole] = useState('')
  const [selectedStatus, setSelectedStatus] = useState('')

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.fullName.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesRole = !selectedRole || user.role === selectedRole
    const matchesStatus = !selectedStatus || user.status === selectedStatus
    return matchesSearch && matchesRole && matchesStatus
  })

  const getStatusBadge = (status: string) => {
    const config = STATUS_CONFIG[status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.inactive
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full bg-${config.color}-100 text-${config.color}-800`}>
        {config.label}
      </span>
    )
  }

  const getRoleBadge = (role: string) => {
    const config = ROLE_CONFIG[role as keyof typeof ROLE_CONFIG] || ROLE_CONFIG.user
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full bg-${config.color}-100 text-${config.color}-800`}>
        {config.label}
      </span>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            用戶列表
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            管理系統中的所有用戶
          </p>
        </div>
        <div className="flex gap-3">
          <Button>
            <PlusIcon className="h-5 w-5 mr-2" />
            添加用戶
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

      {/* Search and Filters */}
      <Card className="p-4">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="搜索用戶名、郵箱或姓名..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
            />
          </div>
          <select
            value={selectedRole}
            onChange={(e) => setSelectedRole(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
          >
            <option value="">所有角色</option>
            <option value="admin">管理員</option>
            <option value="premium">高級用戶</option>
            <option value="user">普通用戶</option>
          </select>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
          >
            <option value="">所有狀態</option>
            <option value="active">活躍</option>
            <option value="inactive">未激活</option>
            <option value="suspended">已停用</option>
          </select>
        </div>
      </Card>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">總用戶數</div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{users.length}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">活躍用戶</div>
          <div className="text-2xl font-bold text-green-600 mt-1">
            {users.filter(u => u.status === 'active').length}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">管理員</div>
          <div className="text-2xl font-bold text-orange-600 mt-1">
            {users.filter(u => u.role === 'admin').length}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">高級用戶</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">
            {users.filter(u => u.role === 'premium').length}
          </div>
        </Card>
      </div>

      {/* User List */}
      <Card className="overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">用戶</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">郵箱</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">角色</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">狀態</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">最後登錄</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">操作</th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
            {filteredUsers.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                <td className="px-6 py-4">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                      <UserIcon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {user.fullName}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        @{user.username}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-900 dark:text-white">
                    {user.email}
                  </div>
                </td>
                <td className="px-6 py-4">
                  {getRoleBadge(user.role)}
                </td>
                <td className="px-6 py-4">
                  {getStatusBadge(user.status)}
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    {user.lastLogin}
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex gap-2">
                    <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded" title="編輯">
                      <PencilIcon className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                    </button>
                    <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded" title="權限">
                      <ShieldCheckIcon className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                    </button>
                    <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded" title="刪除">
                      <TrashIcon className="h-4 w-4 text-red-600 dark:text-red-400" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredUsers.length === 0 && (
          <div className="text-center py-12">
            <UserIcon className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500 dark:text-gray-400">沒有找到匹配的用戶</p>
          </div>
        )}
      </Card>

      {/* Pagination */}
      {filteredUsers.length > 0 && (
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600 dark:text-gray-400">
              顯示 1-{filteredUsers.length} 條，共 {users.length} 條
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" disabled>
                上一頁
              </Button>
              <Button variant="outline" size="sm" disabled>
                下一頁
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* API Note */}
      <Card className="p-4 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <div className="flex items-start gap-3">
          <UserIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              <strong>API集成：</strong> 此頁面將連接到 GET /api/users API。
              當前顯示模擬數據。登錄後將顯示真實的用戶數據，並支持完整的CRUD操作。
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default UserListPage
