import { useState, useMemo } from 'react'
import {
  useGetRolesQuery,
  useCreateRoleMutation,
  useUpdateRoleMutation,
  useDeleteRoleMutation,
  useGetPermissionsQuery,
} from '../../api/endpoints/userApi'
import type { Role, Permission } from '../../types/auth'
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
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
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
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'
import {
  MoreHorizontal,
  Plus,
  Trash2,
  Edit,
  Shield,
  ShieldCheck,
  Key,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

export default function RoleManagement() {
  const [searchQuery, setSearchQuery] = useState('')
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [selectedRole, setSelectedRole] = useState<Role | null>(null)

  // Form state
  const [roleName, setRoleName] = useState('')
  const [roleDescription, setRoleDescription] = useState('')
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([])

  // Queries
  const {
    data: rolesData,
    isLoading: isLoadingRoles,
    error: rolesError,
    refetch: refetchRoles,
  } = useGetRolesQuery({ search: searchQuery || undefined })

  const { data: permissions = [] } = useGetPermissionsQuery()

  // Mutations
  const [createRole] = useCreateRoleMutation()
  const [updateRole] = useUpdateRoleMutation()
  const [deleteRole] = useDeleteRoleMutation()

  const roles = rolesData?.items || []

  // Handlers
  const handleCreateRole = async () => {
    try {
      await createRole({
        name: roleName,
        description: roleDescription,
        permissions: selectedPermissions,
      }).unwrap()
      setCreateDialogOpen(false)
      setRoleName('')
      setRoleDescription('')
      setSelectedPermissions([])
      refetchRoles()
    } catch (error) {
      console.error('Failed to create role:', error)
    }
  }

  const handleEditRole = async () => {
    if (!selectedRole) return
    try {
      await updateRole({
        id: selectedRole.id,
        data: {
          name: roleName,
          description: roleDescription,
          permissions: selectedPermissions,
        },
      }).unwrap()
      setEditDialogOpen(false)
      setSelectedRole(null)
      setRoleName('')
      setRoleDescription('')
      setSelectedPermissions([])
      refetchRoles()
    } catch (error) {
      console.error('Failed to update role:', error)
    }
  }

  const handleDeleteRole = async (roleId: string) => {
    try {
      await deleteRole(roleId).unwrap()
      refetchRoles()
    } catch (error) {
      console.error('Failed to delete role:', error)
    }
  }

  const openEditDialog = (role: Role) => {
    setSelectedRole(role)
    setRoleName(role.name)
    setRoleDescription(role.description || '')
    setSelectedPermissions(role.permissions || [])
    setEditDialogOpen(true)
  }

  const togglePermission = (permissionId: string) => {
    setSelectedPermissions(prev =>
      prev.includes(permissionId)
        ? prev.filter(p => p !== permissionId)
        : [...prev, permissionId]
    )
  }

  // Group permissions by resource
  const permissionsByResource = useMemo(() => {
    const grouped: Record<string, Permission[]> = {}
    permissions.forEach((permission: Permission) => {
      const resource = permission.resource || 'other'
      if (!grouped[resource]) {
        grouped[resource] = []
      }
      grouped[resource].push(permission)
    })
    return grouped
  }, [permissions])

  // Loading state
  if (isLoadingRoles) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  // Error state
  if (rolesError) {
    return (
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <p className="text-destructive text-center">
            加载角色列表失败: {JSON.stringify(rolesError)}
          </p>
          <div className="flex justify-center mt-4">
            <Button onClick={() => refetchRoles()}>重试</Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">角色权限管理</h1>
          <p className="text-muted-foreground mt-1">
            管理系统角色和权限配置
          </p>
        </div>
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              新建角色
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>创建新角色</DialogTitle>
              <DialogDescription>
                创建新的系统角色并分配相应的权限
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="role-name">角色名称 *</Label>
                <Input
                  id="role-name"
                  placeholder="例如：trader, analyst, admin"
                  value={roleName}
                  onChange={(e) => setRoleName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="role-description">角色描述</Label>
                <Textarea
                  id="role-description"
                  placeholder="描述该角色的职责和用途"
                  value={roleDescription}
                  onChange={(e) => setRoleDescription(e.target.value)}
                  rows={3}
                />
              </div>
              <div className="space-y-2">
                <Label>权限配置</Label>
                <div className="border rounded-md p-4 max-h-60 overflow-y-auto space-y-4">
                  {Object.entries(permissionsByResource).map(([resource, perms]) => (
                    <div key={resource}>
                      <p className="text-sm font-medium mb-2 capitalize">{resource}</p>
                      <div className="grid grid-cols-2 gap-2">
                        {perms.map((permission) => (
                          <div
                            key={permission.id}
                            className="flex items-center space-x-2 text-sm"
                          >
                            <input
                              type="checkbox"
                              id={`perm-${permission.id}`}
                              checked={selectedPermissions.includes(permission.id)}
                              onChange={() => togglePermission(permission.id)}
                              className="rounded"
                            />
                            <label
                              htmlFor={`perm-${permission.id}`}
                              className="cursor-pointer select-none"
                            >
                              {permission.action}
                            </label>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                取消
              </Button>
              <Button onClick={handleCreateRole} disabled={!roleName}>
                创建
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative max-w-md">
            <ShieldCheck className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="搜索角色名称..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Roles Table */}
      <Card>
        <CardHeader>
          <CardTitle>角色列表</CardTitle>
          <CardDescription>
            共 {roles.length} 个角色
          </CardDescription>
        </CardHeader>
        <CardContent>
          {roles.length === 0 ? (
            <div className="text-center py-12">
              <Shield className="mx-auto h-12 w-12 text-muted-foreground opacity-50" />
              <p className="mt-4 text-muted-foreground">没有找到角色</p>
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>角色</TableHead>
                    <TableHead>描述</TableHead>
                    <TableHead>权限数量</TableHead>
                    <TableHead>创建时间</TableHead>
                    <TableHead className="text-right">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {roles.map((role) => (
                    <TableRow key={role.id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                            <Shield className="h-5 w-5 text-primary" />
                          </div>
                          <div>
                            <p className="font-medium">{role.name}</p>
                            <p className="text-sm text-muted-foreground">ID: {role.id}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <p className="text-sm">{role.description || '-'}</p>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">
                          <Key className="mr-1 h-3 w-3" />
                          {role.permissions?.length || 0} 个权限
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <p className="text-sm text-muted-foreground">
                          {role.createdAt ? formatDistanceToNow(new Date(role.createdAt), {
                            addSuffix: true,
                            locale: zhCN,
                          }) : '-'}
                        </p>
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                              <span className="sr-only">打开菜单</span>
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => openEditDialog(role)}>
                              <Edit className="mr-2 h-4 w-4" />
                              编辑角色
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <AlertDialog>
                              <AlertDialogTrigger asChild>
                                <DropdownMenuItem
                                  onSelect={(e) => e.preventDefault()}
                                  className="text-destructive focus:text-destructive"
                                  disabled={role.isSystemRole}
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  删除角色
                                </DropdownMenuItem>
                              </AlertDialogTrigger>
                              <AlertDialogContent>
                                <AlertDialogHeader>
                                  <AlertDialogTitle>确认删除角色</AlertDialogTitle>
                                  <AlertDialogDescription>
                                    您确定要删除角色 <strong>{role.name}</strong> 吗？
                                    {role.isSystemRole && ' 此角色为系统角色，无法删除。'}
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>取消</AlertDialogCancel>
                                  <AlertDialogAction
                                    onClick={() => handleDeleteRole(role.id)}
                                    disabled={role.isSystemRole}
                                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
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
          )}
        </CardContent>
      </Card>

      {/* Edit Role Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>编辑角色</DialogTitle>
            <DialogDescription>
              修改角色信息和权限配置
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-role-name">角色名称 *</Label>
              <Input
                id="edit-role-name"
                value={roleName}
                onChange={(e) => setRoleName(e.target.value)}
                disabled={selectedRole?.isSystemRole}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-role-description">角色描述</Label>
              <Textarea
                id="edit-role-description"
                value={roleDescription}
                onChange={(e) => setRoleDescription(e.target.value)}
                rows={3}
              />
            </div>
            <div className="space-y-2">
              <Label>权限配置</Label>
              <div className="border rounded-md p-4 max-h-60 overflow-y-auto space-y-4">
                {Object.entries(permissionsByResource).map(([resource, perms]) => (
                  <div key={resource}>
                    <p className="text-sm font-medium mb-2 capitalize">{resource}</p>
                    <div className="grid grid-cols-2 gap-2">
                      {perms.map((permission) => (
                        <div
                          key={permission.id}
                          className="flex items-center space-x-2 text-sm"
                        >
                          <input
                            type="checkbox"
                            id={`edit-perm-${permission.id}`}
                            checked={selectedPermissions.includes(permission.id)}
                            onChange={() => togglePermission(permission.id)}
                            className="rounded"
                          />
                          <label
                            htmlFor={`edit-perm-${permission.id}`}
                            className="cursor-pointer select-none"
                          >
                            {permission.action}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleEditRole} disabled={!roleName}>
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
