import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import {
  User,
  Bell,
  Palette,
  Shield,
  Globe,
  Key,
  Monitor,
  Mail,
  Smartphone,
  Save,
  Check,
} from 'lucide-react'

export default function Settings() {
  const [saved, setSaved] = useState(false)

  // Mock user data
  const [userData, setUserData] = useState({
    username: 'admin',
    email: 'admin@cbsc.com',
    fullName: 'System Administrator',
    phone: '+86 138****8888',
  })

  // Mock notification settings
  const [notifications, setNotifications] = useState({
    emailAlerts: true,
    pushNotifications: false,
    weeklyReport: true,
    riskAlerts: true,
    systemUpdates: true,
  })

  // Mock appearance settings
  const [appearance, setAppearance] = useState({
    theme: 'dark',
    language: 'zh-CN',
    timezone: 'Asia/Shanghai',
    compactMode: false,
  })

  // Mock security settings
  const [security, setSecurity] = useState({
    twoFactor: true,
    loginAlert: true,
    sessionTimeout: '30',
    ipWhitelist: false,
  })

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-white mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
          系統設置
        </h1>
        <p className="text-slate-400">管理您的帳戶、偏好和系統配置</p>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        {/* Tab Navigation */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-1 inline-flex">
          <TabsList className="bg-transparent border-0 gap-1">
            <TabsTrigger
              value="profile"
              className="data-[state=active]:bg-slate-800 data-[state=active]:text-white text-slate-400"
            >
              <User className="mr-2 h-4 w-4" />
              個人資料
            </TabsTrigger>
            <TabsTrigger
              value="notifications"
              className="data-[state=active]:bg-slate-800 data-[state=active]:text-white text-slate-400"
            >
              <Bell className="mr-2 h-4 w-4" />
              通知設置
            </TabsTrigger>
            <TabsTrigger
              value="appearance"
              className="data-[state=active]:bg-slate-800 data-[state=active]:text-white text-slate-400"
            >
              <Palette className="mr-2 h-4 w-4" />
              外觀設置
            </TabsTrigger>
            <TabsTrigger
              value="security"
              className="data-[state=active]:bg-slate-800 data-[state=active]:text-white text-slate-400"
            >
              <Shield className="mr-2 h-4 w-4" />
              安全設置
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Profile Settings */}
        <TabsContent value="profile">
          <Card className="bg-slate-900/50 border-slate-800 max-w-3xl">
            <CardHeader>
              <CardTitle className="text-white">個人資料</CardTitle>
              <CardDescription className="text-slate-400">
                更新您的個人信息和聯繫方式
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center gap-6 pb-6 border-b border-slate-800">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                  <span className="text-2xl font-bold text-white">A</span>
                </div>
                <div>
                  <Button variant="outline" size="sm" className="border-slate-700 text-slate-300">
                    更換頭像
                  </Button>
                  <p className="text-xs text-slate-500 mt-2">支持 JPG, PNG 格式，最大 2MB</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="username" className="text-slate-300">用戶名</Label>
                  <Input
                    id="username"
                    value={userData.username}
                    onChange={(e) => setUserData({ ...userData, username: e.target.value })}
                    className="bg-slate-800 border-slate-700 text-white"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email" className="text-slate-300">電子郵件</Label>
                  <Input
                    id="email"
                    type="email"
                    value={userData.email}
                    onChange={(e) => setUserData({ ...userData, email: e.target.value })}
                    className="bg-slate-800 border-slate-700 text-white"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="fullName" className="text-slate-300">全名</Label>
                  <Input
                    id="fullName"
                    value={userData.fullName}
                    onChange={(e) => setUserData({ ...userData, fullName: e.target.value })}
                    className="bg-slate-800 border-slate-700 text-white"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="phone" className="text-slate-300">手機號碼</Label>
                  <Input
                    id="phone"
                    value={userData.phone}
                    onChange={(e) => setUserData({ ...userData, phone: e.target.value })}
                    className="bg-slate-800 border-slate-700 text-white"
                  />
                </div>
              </div>

              <div className="pt-4 flex justify-end">
                <Button onClick={handleSave} className="bg-blue-600 hover:bg-blue-700">
                  {saved ? (
                    <>
                      <Check className="mr-2 h-4 w-4" />
                      已保存
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" />
                      保存更改
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notification Settings */}
        <TabsContent value="notifications">
          <Card className="bg-slate-900/50 border-slate-800 max-w-3xl">
            <CardHeader>
              <CardTitle className="text-white">通知設置</CardTitle>
              <CardDescription className="text-slate-400">
                選擇您希望接收通知的方式
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-slate-300 flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  郵件通知
                </h3>

                <div className="space-y-4 pl-6">
                  <div className="flex items-center justify-between py-3 border-b border-slate-800">
                    <div>
                      <p className="text-white font-medium">風險警報郵件</p>
                      <p className="text-sm text-slate-500">當風險指標超過閾值時發送郵件</p>
                    </div>
                    <Switch
                      checked={notifications.emailAlerts}
                      onCheckedChange={(checked) => setNotifications({ ...notifications, emailAlerts: checked })}
                    />
                  </div>

                  <div className="flex items-center justify-between py-3 border-b border-slate-800">
                    <div>
                      <p className="text-white font-medium">每週報告</p>
                      <p className="text-sm text-slate-500">每週發送投資組合績效報告</p>
                    </div>
                    <Switch
                      checked={notifications.weeklyReport}
                      onCheckedChange={(checked) => setNotifications({ ...notifications, weeklyReport: checked })}
                    />
                  </div>

                  <div className="flex items-center justify-between py-3">
                    <div>
                      <p className="text-white font-medium">系統更新通知</p>
                      <p className="text-sm text-slate-500">接收系統更新和維護通知</p>
                    </div>
                    <Switch
                      checked={notifications.systemUpdates}
                      onCheckedChange={(checked) => setNotifications({ ...notifications, systemUpdates: checked })}
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-sm font-medium text-slate-300 flex items-center gap-2">
                  <Smartphone className="h-4 w-4" />
                  推送通知
                </h3>

                <div className="space-y-4 pl-6">
                  <div className="flex items-center justify-between py-3 border-b border-slate-800">
                    <div>
                      <p className="text-white font-medium">啟用推送通知</p>
                      <p className="text-sm text-slate-500">在瀏覽器中接收即時通知</p>
                    </div>
                    <Switch
                      checked={notifications.pushNotifications}
                      onCheckedChange={(checked) => setNotifications({ ...notifications, pushNotifications: checked })}
                    />
                  </div>

                  <div className="flex items-center justify-between py-3">
                    <div>
                      <p className="text-white font-medium">風險警報推送</p>
                      <p className="text-sm text-slate-500">緊急風險警報的即時推送</p>
                    </div>
                    <Switch
                      checked={notifications.riskAlerts}
                      onCheckedChange={(checked) => setNotifications({ ...notifications, riskAlerts: checked })}
                    />
                  </div>
                </div>
              </div>

              <div className="pt-4 flex justify-end">
                <Button onClick={handleSave} className="bg-blue-600 hover:bg-blue-700">
                  {saved ? (
                    <>
                      <Check className="mr-2 h-4 w-4" />
                      已保存
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" />
                      保存更改
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Appearance Settings */}
        <TabsContent value="appearance">
          <Card className="bg-slate-900/50 border-slate-800 max-w-3xl">
            <CardHeader>
              <CardTitle className="text-white">外觀設置</CardTitle>
              <CardDescription className="text-slate-400">
                自定義系統外觀和語言
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-slate-300 flex items-center gap-2">
                  <Monitor className="h-4 w-4" />
                  主題設置
                </h3>

                <div className="grid grid-cols-3 gap-4">
                  {(['dark', 'light', 'auto'] as const).map((theme) => (
                    <button
                      key={theme}
                      onClick={() => setAppearance({ ...appearance, theme })}
                      className={`p-4 rounded-lg border-2 transition-all ${
                        appearance.theme === theme
                          ? 'border-blue-500 bg-blue-500/10'
                          : 'border-slate-700 hover:border-slate-600'
                      }`}
                    >
                      <div className="aspect-video rounded bg-slate-800 mb-2 overflow-hidden">
                        <div className={`w-full h-full ${
                          theme === 'dark' ? 'bg-slate-900' :
                          theme === 'light' ? 'bg-white' :
                          'bg-gradient-to-r from-slate-900 to-white'
                        }`} />
                      </div>
                      <p className="text-sm text-white">
                        {theme === 'dark' && '深色模式'}
                        {theme === 'light' && '淺色模式'}
                        {theme === 'auto' && '自動'}
                      </p>
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-sm font-medium text-slate-300 flex items-center gap-2">
                  <Globe className="h-4 w-4" />
                  語言和地區
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="language" className="text-slate-300">語言</Label>
                    <select
                      id="language"
                      value={appearance.language}
                      onChange={(e) => setAppearance({ ...appearance, language: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                    >
                      <option value="zh-CN">簡體中文</option>
                      <option value="zh-TW">繁體中文</option>
                      <option value="en-US">English</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="timezone" className="text-slate-300">時區</Label>
                    <select
                      id="timezone"
                      value={appearance.timezone}
                      onChange={(e) => setAppearance({ ...appearance, timezone: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                    >
                      <option value="Asia/Shanghai">中國標準時間 (UTC+8)</option>
                      <option value="Asia/Hong_Kong">香港時間 (UTC+8)</option>
                      <option value="UTC">協調世界時 (UTC)</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between py-3 border-t border-slate-800">
                <div>
                  <p className="text-white font-medium">緊湊模式</p>
                  <p className="text-sm text-slate-500">減小間距以顯示更多內容</p>
                </div>
                <Switch
                  checked={appearance.compactMode}
                  onCheckedChange={(checked) => setAppearance({ ...appearance, compactMode: checked })}
                />
              </div>

              <div className="pt-4 flex justify-end">
                <Button onClick={handleSave} className="bg-blue-600 hover:bg-blue-700">
                  {saved ? (
                    <>
                      <Check className="mr-2 h-4 w-4" />
                      已保存
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" />
                      保存更改
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Settings */}
        <TabsContent value="security">
          <Card className="bg-slate-900/50 border-slate-800 max-w-3xl">
            <CardHeader>
              <CardTitle className="text-white">安全設置</CardTitle>
              <CardDescription className="text-slate-400">
                管理帳戶安全和訪問控制
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-slate-300 flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  兩步驗證
                </h3>

                <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <p className="text-white font-medium">兩步驗證</p>
                        <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">
                          已啟用
                        </Badge>
                      </div>
                      <p className="text-sm text-slate-500">使用身份驗證器應用保護您的帳戶</p>
                    </div>
                    <Button variant="outline" size="sm" className="border-slate-700 text-slate-300">
                      管理
                    </Button>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-sm font-medium text-slate-300 flex items-center gap-2">
                  <Key className="h-4 w-4" />
                  密碼和會話
                </h3>

                <div className="space-y-4">
                  <div className="flex items-center justify-between py-3 border-b border-slate-800">
                    <div>
                      <p className="text-white font-medium">修改密碼</p>
                      <p className="text-sm text-slate-500">定期更換密碼以保護帳戶安全</p>
                    </div>
                    <Button variant="outline" size="sm" className="border-slate-700 text-slate-300">
                      修改
                    </Button>
                  </div>

                  <div className="flex items-center justify-between py-3 border-b border-slate-800">
                    <div>
                      <p className="text-white font-medium">會話超時</p>
                      <p className="text-sm text-slate-500">自動登出前的空閒時間</p>
                    </div>
                    <select
                      value={security.sessionTimeout}
                      onChange={(e) => setSecurity({ ...security, sessionTimeout: e.target.value })}
                      className="px-3 py-1 bg-slate-800 border border-slate-700 rounded-md text-white text-sm"
                    >
                      <option value="15">15 分鐘</option>
                      <option value="30">30 分鐘</option>
                      <option value="60">1 小時</option>
                      <option value="120">2 小時</option>
                    </select>
                  </div>

                  <div className="flex items-center justify-between py-3 border-b border-slate-800">
                    <div>
                      <p className="text-white font-medium">登入警報</p>
                      <p className="text-sm text-slate-500">新設備登入時發送郵件通知</p>
                    </div>
                    <Switch
                      checked={security.loginAlert}
                      onCheckedChange={(checked) => setSecurity({ ...security, loginAlert: checked })}
                    />
                  </div>

                  <div className="flex items-center justify-between py-3">
                    <div>
                      <p className="text-white font-medium">IP 白名單</p>
                      <p className="text-sm text-slate-500">僅允許特定 IP 地址訪問</p>
                    </div>
                    <Switch
                      checked={security.ipWhitelist}
                      onCheckedChange={(checked) => setSecurity({ ...security, ipWhitelist: checked })}
                    />
                  </div>
                </div>
              </div>

              <div className="pt-4 flex justify-end">
                <Button onClick={handleSave} className="bg-blue-600 hover:bg-blue-700">
                  {saved ? (
                    <>
                      <Check className="mr-2 h-4 w-4" />
                      已保存
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" />
                      保存更改
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
