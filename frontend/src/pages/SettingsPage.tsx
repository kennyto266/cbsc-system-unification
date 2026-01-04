import React, { useState } from 'react'
import {
  Settings as SettingsIcon,
  User,
  Bell,
  Shield,
  Palette,
  Globe,
  Database,
  Key,
  Save,
  Eye,
  EyeOff
} from 'lucide-react'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('general')
  const [saving, setSaving] = useState(false)

  const tabs = [
    { id: 'general', label: '通用設置', icon: SettingsIcon },
    { id: 'profile', label: '個人資料', icon: User },
    { id: 'notifications', label: '通知設置', icon: Bell },
    { id: 'security', label: '安全設置', icon: Shield },
    { id: 'appearance', label: '外觀', icon: Palette },
    { id: 'language', label: '語言與地區', icon: Globe },
    { id: 'api', label: 'API 配置', icon: Key },
    { id: 'data', label: '數據管理', icon: Database },
  ]

  const handleSave = async () => {
    setSaving(true)
    // Simulate save
    setTimeout(() => {
      setSaving(false)
    }, 1000)
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          系統設置
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          管理您的系統偏好設置和配置
        </p>
      </div>

      <div className="flex gap-6">
        {/* Sidebar */}
        <div className="w-64 flex-shrink-0">
          <Card className="p-2">
            <nav className="space-y-1">
              {tabs.map(tab => {
                const Icon = tab.icon
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {tab.label}
                  </button>
                )
              })}
            </nav>
          </Card>
        </div>

        {/* Content */}
        <div className="flex-1">
          <Card className="p-6">
            {activeTab === 'general' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  通用設置
                </h2>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      系統名稱
                    </label>
                    <input
                      type="text"
                      defaultValue="CBSC 量化交易策略管理系統"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      時區
                    </label>
                    <select className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white">
                      <option value="Asia/Hong_Kong">香港 (GMT+8)</option>
                      <option value="Asia/Shanghai">上海 (GMT+8)</option>
                      <option value="America/New_York">紐約 (GMT-5)</option>
                      <option value="Europe/London">倫敦 (GMT+0)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      日期格式
                    </label>
                    <select className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white">
                      <option value="YYYY/MM/DD">2026/01/04</option>
                      <option value="DD/MM/YYYY">04/01/2026</option>
                      <option value="MM/DD/YYYY">01/04/2026</option>
                    </select>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                        啟用自動保存
                      </h4>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        自動保存策略配置變更
                      </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" defaultChecked className="sr-only peer" />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'profile' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  個人資料
                </h2>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      用戶名
                    </label>
                    <input
                      type="text"
                      defaultValue="admin"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      郵箱
                    </label>
                    <input
                      type="email"
                      defaultValue="admin@cbsc.com"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      手機號碼
                    </label>
                    <input
                      type="tel"
                      defaultValue="+852 1234 5678"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                    />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'notifications' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  通知設置
                </h2>

                <div className="space-y-4">
                  {[
                    { label: '策略執行通知', desc: '當策略開始/停止/完成時通知' },
                    { label: '交易信號通知', desc: '接收到交易信號時通知' },
                    { label: '風險警告通知', desc: '觸發風險警告時通知' },
                    { label: '系統更新通知', desc: '系統更新和維護通知' },
                    { label: '電子郵件摘要', desc: '每日活動摘要郵件' },
                  ].map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between">
                      <div>
                        <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                          {item.label}
                        </h4>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {item.desc}
                        </p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" defaultChecked={idx < 3} className="sr-only peer" />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'security' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  安全設置
                </h2>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      當前密碼
                    </label>
                    <div className="relative">
                      <input
                        type="password"
                        className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                      />
                      <button className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600">
                        <Eye className="h-4 w-4" />
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      新密碼
                    </label>
                    <input
                      type="password"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      確認新密碼
                    </label>
                    <input
                      type="password"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                    />
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                        雙因子認證 (2FA)
                      </h4>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        增加帳戶安全性
                      </p>
                    </div>
                    <Button variant="outline" size="sm">
                      啟用
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'appearance' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  外觀設置
                </h2>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      主題
                    </label>
                    <div className="grid grid-cols-3 gap-3">
                      {[
                        { name: '淺色', mode: 'light' },
                        { name: '深色', mode: 'dark' },
                        { name: '自動', mode: 'auto' },
                      ].map(theme => (
                        <button
                          key={theme.mode}
                          className={`p-4 border-2 rounded-lg text-center transition-colors ${
                            theme.mode === 'auto'
                              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30'
                              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                          }`}
                        >
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {theme.name}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      字體大小
                    </label>
                    <select className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white">
                      <option value="small">小</option>
                      <option value="medium" selected>中</option>
                      <option value="large">大</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'language' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  語言與地區
                </h2>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      顯示語言
                    </label>
                    <select className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white">
                      <option value="zh-HK">繁體中文 (香港)</option>
                      <option value="zh-CN">簡體中文</option>
                      <option value="en-US">English (US)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      貨幣
                    </label>
                    <select className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white">
                      <option value="HKD">港幣 (HKD)</option>
                      <option value="CNY">人民幣 (CNY)</option>
                      <option value="USD">美元 (USD)</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'api' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  API 配置
                </h2>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      API 端點
                    </label>
                    <input
                      type="text"
                      defaultValue="http://localhost:3003"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      WebSocket 端點
                    </label>
                    <input
                      type="text"
                      defaultValue="ws://localhost:3007"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                    />
                  </div>

                  <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                      API 密鑰
                    </h4>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                        <div>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">
                            生產環境
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            已配置
                          </p>
                        </div>
                        <Button variant="outline" size="sm">
                          <Eye className="h-4 w-4 mr-1" />
                          查看
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'data' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  數據管理
                </h2>

                <div className="space-y-4">
                  <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                    <h4 className="text-sm font-medium text-yellow-900 dark:text-yellow-300 mb-1">
                      數據緩存
                    </h4>
                    <p className="text-xs text-yellow-800 dark:text-yellow-400 mb-3">
                      清理緩存可以釋放存儲空間，但可能會稍微影響性能
                    </p>
                    <Button variant="outline" size="sm">
                      清理緩存
                    </Button>
                  </div>

                  <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
                    <h4 className="text-sm font-medium text-red-900 dark:text-red-300 mb-1">
                      重置設置
                    </h4>
                    <p className="text-xs text-red-800 dark:text-red-400 mb-3">
                      將所有設置恢復為默認值（不可逆）
                    </p>
                    <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700">
                      重置設置
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* Save Button */}
            <div className="flex justify-end pt-6 mt-6 border-t border-gray-200 dark:border-gray-700">
              <Button onClick={handleSave} disabled={saving} className="flex items-center gap-2">
                <Save className="h-4 w-4" />
                {saving ? '保存中...' : '保存設置'}
              </Button>
            </div>
          </Card>

          {/* API Integration Notice */}
          <Card className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20">
            <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-300 mb-2">
              API 集成說明
            </h4>
            <p className="text-xs text-blue-800 dark:text-blue-400">
              此頁面將連接到以下 API 端點：
              GET /api/users/settings (獲取設置) ·
              PUT /api/users/settings (更新設置) ·
              POST /api/users/change-password (修改密碼)
              <br />
              當前為演示模式，實際部署時需要實現完整的 API 集成。
            </p>
          </Card>
        </div>
      </div>
    </div>
  )
}
