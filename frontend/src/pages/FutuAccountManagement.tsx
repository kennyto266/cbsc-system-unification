import React, { useState, useEffect } from 'react'
import {
  Settings,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertCircle,
  Plus,
  Trash2,
  Eye,
  EyeOff,
  TrendingUp,
  DollarSign,
  Activity
} from 'lucide-react'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'

interface FutuAccount {
  id: string
  name: string
  host: string
  port: number
  username?: string
  envId?: string
  tradeEnv: number // 1=實盤, 2=模擬
  status: 'connected' | 'disconnected' | 'error'
  lastSync?: string
  accounts: {
    accountId: string
    accountType: string // 'stock'|'future'|'cfd'
    currency: string
    cash: number
    availableFunds: number
    marketValue: number
    totalAssets: number
    power: number // 購買力
  }[]
}

export default function FutuAccountManagement() {
  const [accounts, setAccounts] = useState<FutuAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [showPassword, setShowPassword] = useState<Record<string, boolean>>({})
  const [newAccountModal, setNewAccountModal] = useState(false)

  useEffect(() => {
    loadAccounts()
  }, [])

  const loadAccounts = async () => {
    setLoading(true)
    try {
      // TODO: Replace with actual API call
      // const response = await fetch('/api/futu/accounts')
      // const data = await response.json()

      // Mock data for now
      setAccounts([
        {
          id: 'futu-001',
          name: '主要實盤帳戶',
          host: '127.0.0.1',
          port: 11111,
          username: 'user123',
          envId: 'test',
          tradeEnv: 2,
          status: 'connected',
          lastSync: new Date().toISOString(),
          accounts: [
            {
              accountId: 'HK1234567',
              accountType: 'stock',
              currency: 'HKD',
              cash: 500000.00,
              availableFunds: 450000.00,
              marketValue: 50000.00,
              totalAssets: 550000.00,
              power: 900000.00
            },
            {
              accountId: 'US1234567',
              accountType: 'stock',
              currency: 'USD',
              cash: 10000.00,
              availableFunds: 9500.00,
              marketValue: 500.00,
              totalAssets: 10500.00,
              power: 19000.00
            }
          ]
        },
        {
          id: 'futu-002',
          name: '測試帳戶',
          host: '127.0.0.1',
          port: 11112,
          username: 'testuser',
          tradeEnv: 2,
          status: 'disconnected',
          accounts: []
        }
      ])
    } catch (error) {
      console.error('Failed to load Futu accounts:', error)
    } finally {
      setLoading(false)
    }
  }

  const testConnection = async (accountId: string) => {
    try {
      // TODO: Replace with actual API call
      // await fetch(`/api/futu/accounts/${accountId}/test`, { method: 'POST' })

      setAccounts(accounts.map(acc =>
        acc.id === accountId
          ? { ...acc, status: 'connected', lastSync: new Date().toISOString() }
          : acc
      ))
    } catch (error) {
      console.error('Connection test failed:', error)
      setAccounts(accounts.map(acc =>
        acc.id === accountId
          ? { ...acc, status: 'error' }
          : acc
      ))
    }
  }

  const deleteAccount = async (accountId: string) => {
    if (!confirm('確定要刪除此帳戶配置嗎？')) return

    try {
      // TODO: Replace with actual API call
      // await fetch(`/api/futu/accounts/${accountId}`, { method: 'DELETE' })

      setAccounts(accounts.filter(acc => acc.id !== accountId))
    } catch (error) {
      console.error('Failed to delete account:', error)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'disconnected':
        return <XCircle className="h-5 w-5 text-gray-400" />
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      default:
        return <Activity className="h-5 w-5 text-gray-400" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'connected': return '已連接'
      case 'disconnected': return '未連接'
      case 'error': return '連接錯誤'
      default: return '未知'
    }
  }

  const getTradeEnvText = (env: number) => {
    return env === 1 ? '實盤' : '模擬'
  }

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('zh-HK', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2
    }).format(amount)
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Futu 牛牛帳戶管理
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          管理 Futu NiuNi 牛牛交易帳戶連接和配置
        </p>
      </div>

      {/* Action Bar */}
      <div className="flex items-center justify-between mb-6">
        <Button
          onClick={() => setNewAccountModal(true)}
          className="flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          添加帳戶
        </Button>
        <Button
          variant="outline"
          onClick={loadAccounts}
          className="flex items-center gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          刷新
        </Button>
      </div>

      {/* Accounts List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : accounts.length === 0 ? (
        <Card className="p-12 text-center">
          <Settings className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            尚未配置任何帳戶
          </h3>
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            點擊「添加帳戶」按鈕來配置您的第一個 Futu 牛牛帳戶
          </p>
        </Card>
      ) : (
        <div className="space-y-6">
          {accounts.map(account => (
            <Card key={account.id} className="p-6">
              {/* Account Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  {getStatusIcon(account.status)}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {account.name}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {account.host}:{account.port} · {getTradeEnvText(account.tradeEnv)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => testConnection(account.id)}
                  >
                    測試連接
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteAccount(account.id)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {/* Connection Info */}
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 mb-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">用戶名:</span>
                    <span className="ml-2 font-medium text-gray-900 dark:text-white">
                      {account.username || 'N/A'}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">狀態:</span>
                    <span className="ml-2 font-medium text-gray-900 dark:text-white">
                      {getStatusText(account.status)}
                    </span>
                  </div>
                  {account.lastSync && (
                    <div className="col-span-2">
                      <span className="text-gray-500 dark:text-gray-400">最後同步:</span>
                      <span className="ml-2 font-medium text-gray-900 dark:text-white">
                        {new Date(account.lastSync).toLocaleString('zh-HK')}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Sub-accounts */}
              {account.accounts && account.accounts.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                    子帳戶明細
                  </h4>
                  <div className="space-y-3">
                    {account.accounts.map((subAcc) => (
                      <div
                        key={subAcc.accountId}
                        className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4"
                      >
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <span className="font-medium text-gray-900 dark:text-white">
                              {subAcc.accountId}
                            </span>
                            <span className="ml-2 text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded">
                              {subAcc.accountType.toUpperCase()}
                            </span>
                          </div>
                          <span className="text-sm font-semibold text-gray-900 dark:text-white">
                            {subAcc.currency}
                          </span>
                        </div>

                        {/* Account Metrics */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="flex items-center gap-2">
                            <DollarSign className="h-4 w-4 text-green-600" />
                            <div>
                              <p className="text-xs text-gray-500 dark:text-gray-400">現金</p>
                              <p className="text-sm font-semibold text-gray-900 dark:text-white">
                                {formatCurrency(subAcc.cash, subAcc.currency)}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <TrendingUp className="h-4 w-4 text-blue-600" />
                            <div>
                              <p className="text-xs text-gray-500 dark:text-gray-400">市值</p>
                              <p className="text-sm font-semibold text-gray-900 dark:text-white">
                                {formatCurrency(subAcc.marketValue, subAcc.currency)}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Activity className="h-4 w-4 text-purple-600" />
                            <div>
                              <p className="text-xs text-gray-500 dark:text-gray-400">總資產</p>
                              <p className="text-sm font-semibold text-gray-900 dark:text-white">
                                {formatCurrency(subAcc.totalAssets, subAcc.currency)}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Settings className="h-4 w-4 text-orange-600" />
                            <div>
                              <p className="text-xs text-gray-500 dark:text-gray-400">購買力</p>
                              <p className="text-sm font-semibold text-gray-900 dark:text-white">
                                {formatCurrency(subAcc.power, subAcc.currency)}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* API Integration Notice */}
      <Card className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20">
        <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-300 mb-2">
          API 集成說明
        </h4>
        <p className="text-xs text-blue-800 dark:text-blue-400">
          此頁面將連接到以下 API 端點：
          GET /api/futu/accounts (獲取帳戶列表) ·
          POST /api/futu/accounts/test (測試連接) ·
          DELETE /api/futu/accounts/{'{id}'} (刪除帳戶) ·
          GET /api/futu/accounts/{'{id}'}/balance (查詢餘額)
          <br />
          當前顯示模擬數據。實際部署時需要實現完整的 API 集成。
        </p>
      </Card>
    </div>
  )
}
