import { useState, useMemo } from 'react'
import { useGetUsersQuery, useUpdateUserStatusMutation, useDeleteUserMutation } from '../../api/endpoints/userApi'
import type { User } from '../../types/auth'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'
import { Select } from '@/components/ui/select'
import type { SelectOption } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import {
  MoreHorizontal,
  Search,
  Plus,
  Trash2,
  Shield,
  ShieldOff,
  Mail,
  User as UserIcon,
  Calendar,
  Activity,
  Users,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { PageTemplate } from '../../components/layout/PageTemplate'

// Filter options
const STATUSES: SelectOption[] = [
  { value: 'all', label: '全部状态' },
  { value: 'active', label: '活跃' },
  { value: 'inactive', label: '未激活' },
]

const ROLES: SelectOption[] = [
  { value: 'all', label: '全部角色' },
  { value: 'admin', label: '管理员' },
  { value: 'user', label: '普通用户' },
  { value: 'analyst', label: '分析师' },
  { value: 'trader', label: '交易员' },
]

export default function UserList() {
  // State for filters and pagination
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [roleFilter, setRoleFilter] = useState('all')
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)

  // Query parameters
  const queryParams = useMemo(() => ({
    page,
    pageSize,
    search: searchQuery || undefined,
    status: statusFilter !== 'all' ? statusFilter : undefined,
    role: roleFilter !== 'all' ? roleFilter : undefined,
  }), [page, pageSize, searchQuery, statusFilter, roleFilter])

  // Fetch users
  const {
    data: usersData,
    isLoading: isLoadingUsers,
    error: usersError,
    refetch,
  } = useGetUsersQuery(queryParams)

  // Mutations
  const [updateUserStatus] = useUpdateUserStatusMutation()
  const [deleteUser] = useDeleteUserMutation()

  // Handlers
  const handleToggleStatus = async (user: User) => {
    const newStatus = user.status === 'active' ? 'inactive' : 'active'
    try {
      await updateUserStatus({ id: user.id, status: newStatus }).unwrap()
      refetch()
    } catch (error) {
      console.error('Failed to update user status:', error)
    }
  }

  const handleDeleteUser = async (userId: string) => {
    try {
      await deleteUser(userId).unwrap()
      refetch()
    } catch (error) {
      console.error('Failed to delete user:', error)
    }
  }

  const users = usersData?.items || []
  const total = usersData?.total || 0
  const totalPages = Math.ceil(total / pageSize)

  // Loading state
  if (isLoadingUsers) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  // Error state
  if (usersError) {
    return (
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <p className="text-destructive text-center">
            加载用户列表失败: {JSON.stringify(usersError)}
          </p>
          <div className="flex justify-center mt-4">
            <Button onClick={() => refetch()}>重试</Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <PageTemplate
      title="用户列表"
      description="管理系统用户、角色和权限"
      icon={Users}
      headerActions={
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          新建用户
        </Button>
      }
    >

      {/* Filters */}
      <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              placeholder="搜索用户名、邮箱..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                setPage(1) // Reset to first page on search
              }}
              className="pl-10 bg-slate-950/50 border-slate-800 text-slate-100 placeholder:text-slate-500 focus:border-cyan-500/50"
            />
          </div>

          {/* Status Filter */}
          <Select
            options={STATUSES}
            value={statusFilter}
            onChange={(value) => {
              setStatusFilter(value)
              setPage(1)
            }}
            placeholder="筛选状态"
            size="md"
            fullWidth={false}
            className="w-[180px]"
          />

          {/* Role Filter */}
          <Select
            options={ROLES}
            value={roleFilter}
            onChange={(value) => {
              setRoleFilter(value)
              setPage(1)
            }}
            placeholder="筛选角色"
            size="md"
            fullWidth={false}
            className="w-[180px]"
          />
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-slate-100">用户列表</h3>
          <p className="text-sm text-slate-400 mt-1">
            共 {total} 个用户，当前第 {page} 页，共 {totalPages} 页
          </p>
        </div>
        {users.length === 0 ? (
          <div className="text-center py-12">
            <UserIcon className="mx-auto h-12 w-12 text-slate-500 opacity-50" />
            <p className="mt-4 text-slate-400">没有找到用户</p>
          </div>
        ) : (
          <>
            <div className="rounded-md border border-slate-800/50">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-slate-800/50 border-slate-800/50">
                    <TableHead className="text-slate-100">用户</TableHead>
                    <TableHead className="text-slate-100">邮箱</TableHead>
                    <TableHead className="text-slate-100">状态</TableHead>
                    <TableHead className="text-slate-100">角色</TableHead>
                    <TableHead className="text-slate-100">注册时间</TableHead>
                    <TableHead className="text-slate-100">最后活动</TableHead>
                    <TableHead className="text-right text-slate-100">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((user) => (
                    <TableRow key={user.id} className="hover:bg-slate-800/30 border-slate-800/50">
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className="h-10 w-10 rounded-full bg-cyan-500/10 flex items-center justify-center">
                            <span className="text-sm font-medium text-cyan-400">
                              {user.username?.charAt(0).toUpperCase() || '?'}
                            </span>
                          </div>
                          <div>
                            <p className="font-medium text-slate-100">{user.username || '-'}</p>
                            <p className="text-sm text-slate-400">ID: {user.id}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Mail className="h-4 w-4 text-slate-400" />
                          <span className="text-slate-100">{user.email || '-'}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={user.status === 'active' ? 'default' : 'secondary'}
                          className={user.status === 'active'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                          }
                        >
                          {user.status === 'active' ? '活跃' : '未激活'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {user.roles && user.roles.length > 0 ? (
                            user.roles.map((role: string) => (
                              <Badge key={role} variant="outline" className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20">
                                {role}
                              </Badge>
                            ))
                          ) : (
                            <span className="text-slate-400 text-sm">-</span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 text-sm">
                          <Calendar className="h-4 w-4 text-slate-400" />
                          <span className="text-slate-100">
                            {user.createdAt ? formatDistanceToNow(new Date(user.createdAt), {
                              addSuffix: true,
                              locale: zhCN,
                            }) : '-'}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 text-sm">
                          <Activity className="h-4 w-4 text-slate-400" />
                          <span className="text-slate-100">
                            {user.lastLogin ? formatDistanceToNow(new Date(user.lastLogin), {
                              addSuffix: true,
                              locale: zhCN,
                            }) : '从未'}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="text-slate-100 hover:text-cyan-400">
                              <MoreHorizontal className="h-4 w-4" />
                              <span className="sr-only">打开菜单</span>
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="bg-slate-900 border-slate-800">
                            <DropdownMenuItem onClick={() => handleToggleStatus(user)} className="text-slate-100 hover:text-cyan-400">
                              {user.status === 'active' ? (
                                <>
                                  <ShieldOff className="mr-2 h-4 w-4" />
                                  禁用账户
                                </>
                              ) : (
                                <>
                                  <Shield className="mr-2 h-4 w-4" />
                                  启用账户
                                </>
                              )}
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <AlertDialog>
                              <AlertDialogTrigger asChild>
                                <DropdownMenuItem
                                  onSelect={(e) => e.preventDefault()}
                                  className="text-rose-400 focus:text-rose-400"
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  删除用户
                                </DropdownMenuItem>
                              </AlertDialogTrigger>
                              <AlertDialogContent className="bg-slate-900 border-slate-800">
                                <AlertDialogHeader>
                                  <AlertDialogTitle className="text-slate-100">确认删除用户</AlertDialogTitle>
                                  <AlertDialogDescription className="text-slate-400">
                                    您确定要删除用户 <strong>{user.username}</strong> 吗？
                                    此操作无法撤销。
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel className="text-slate-100">取消</AlertDialogCancel>
                                  <AlertDialogAction
                                    onClick={() => handleDeleteUser(user.id)}
                                    className="bg-rose-500 text-white hover:bg-rose-600"
                                  >
                                    删除
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-4">
                <p className="text-sm text-slate-400">
                  显示 {(page - 1) * pageSize + 1} 到 {Math.min(page * pageSize, total)} 条，共 {total} 条
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="border-slate-700 text-slate-100 hover:bg-slate-800"
                  >
                    上一页
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="border-slate-700 text-slate-100 hover:bg-slate-800"
                  >
                    下一页
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </PageTemplate>
  )
}
