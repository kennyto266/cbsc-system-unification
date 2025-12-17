/**
 * Component Showcase Page
 * 展示shadcn/ui組件在CBSC系統中的應用
 */

import React, { useState } from 'react'
import {
  Button,
  TradingButton,
  ActionButton,
  Card,
  MetricCard,
  TradingCard,
  StrategyCard,
  Input,
  Label,
  Badge,
  Select,
  Checkbox,
  Alert,
  Tabs,
  Toast,
  useToast,
} from '@/components/ui'
import { TrendingUp, TrendingDown, Minus, Plus, Edit, Trash2, Eye } from 'lucide-react'

const ComponentShowcase: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState('buttons')
  const [isChecked, setIsChecked] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const [selectValue, setSelectValue] = useState('')
  const { toast } = useToast()

  const showToast = () => {
    toast({
      title: "操作成功",
      description: "這是一個Toast通知示例",
    })
  }

  return (
    <div className="container mx-auto p-6 space-y-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-2">CBSC UI組件展示</h1>
        <p className="text-gray-600">基於shadcn/ui的量化交易系統組件庫</p>
      </div>

      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="buttons">按鈕組件</TabsTrigger>
          <TabsTrigger value="cards">卡片組件</TabsTrigger>
          <TabsTrigger value="forms">表單組件</TabsTrigger>
          <TabsTrigger value="feedback">反饋組件</TabsTrigger>
        </TabsList>

        {/* Button Components */}
        <TabsContent value="buttons" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>標準按鈕</CardTitle>
              <CardDescription>基礎的shadcn/ui按鈕變體</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                <Button variant="default">默認</Button>
                <Button variant="secondary">次要</Button>
                <Button variant="outline">邊框</Button>
                <Button variant="ghost">幽靈</Button>
                <Button variant="link">鏈接</Button>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button variant="success">成功</Button>
                <Button variant="danger">危險</Button>
                <Button variant="warning">警告</Button>
                <Button variant="info">信息</Button>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button variant="bullish">看漲</Button>
                <Button variant="bearish">看跌</Button>
                <Button variant="neutral">中性</Button>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button loading>加載中...</Button>
                <Button icon={<Plus />} iconPosition="left">
                  添加
                </Button>
                <Button icon={<Edit />} iconPosition="right">
                  編輯
                </Button>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button size="xs">超小</Button>
                <Button size="sm">小</Button>
                <Button size="default">默認</Button>
                <Button size="lg">大</Button>
                <Button size="xl">超大</Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>交易按鈕</CardTitle>
              <CardDescription>專為金融交易設計的按鈕預設</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                <TradingButton.Buy />
                <TradingButton.Sell />
                <TradingButton.Hold />
                <TradingButton.Buy icon={<TrendingUp size={16} />} />
                <TradingButton.Sell icon={<TrendingDown size={16} />} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>操作按鈕</CardTitle>
              <CardDescription>常見的系統操作按鈕</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                <ActionButton.Create />
                <ActionButton.Edit />
                <ActionButton.Delete />
                <ActionButton.View />
                <ActionButton.Create icon={<Plus size={16} />} />
                <ActionButton.Edit icon={<Edit size={16} />} />
                <ActionButton.Delete icon={<Trash2 size={16} />} />
                <ActionButton.View icon={<Eye size={16} />} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Card Components */}
        <TabsContent value="cards" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <MetricCard
              title="總資產"
              value="HK$1,234,567"
              change={2.34}
              changeType="increase"
              icon={<TrendingUp className="h-4 w-4 text-green-600" />}
            />

            <MetricCard
              title="今日盈虧"
              value="HK$-12,345"
              change={-1.23}
              changeType="decrease"
              icon={<TrendingDown className="h-4 w-4 text-red-600" />}
            />

            <MetricCard
              title="勝率"
              value="68.5%"
              change={5.2}
              changeType="increase"
              icon={<Minus className="h-4 w-4 text-blue-600" />}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <TradingCard
              symbol="AAPL"
              price={178.45}
              change={2.35}
              changePercent={1.33}
              volume="45.2M"
            />

            <TradingCard
              symbol="TSLA"
              price={245.67}
              change={-3.21}
              changePercent={-1.29}
              volume="82.1M"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <StrategyCard
              name="RSI均值回歸"
              status="active"
              performance={{
                totalReturn: 15.4,
                winRate: 68.2,
                maxDrawdown: -8.3,
              }}
              lastRun="2024-12-17T10:30:00Z"
            />

            <StrategyCard
              name="移動平均線突破"
              status="paused"
              performance={{
                totalReturn: 8.7,
                winRate: 62.1,
                maxDrawdown: -12.5,
              }}
              lastRun="2024-12-16T15:45:00Z"
            />

            <StrategyCard
              name="布林帶策略"
              status="stopped"
              performance={{
                totalReturn: -3.2,
                winRate: 45.8,
                maxDrawdown: -18.7,
              }}
              lastRun="2024-12-15T09:20:00Z"
            />
          </div>
        </TabsContent>

        {/* Form Components */}
        <TabsContent value="forms" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>表單組件</CardTitle>
              <CardDescription>輸入、選擇和驗證組件</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="input">文本輸入</Label>
                  <Input
                    id="input"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="請輸入內容..."
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="select">下拉選擇</Label>
                  <Select value={selectValue} onValueChange={setSelectValue}>
                    <option value="">請選擇</option>
                    <option value="option1">選項1</option>
                    <option value="option2">選項2</option>
                    <option value="option3">選項3</option>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">密碼輸入</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="請輸入密碼..."
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">郵箱輸入</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="請輸入郵箱..."
                  />
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="checkbox"
                  checked={isChecked}
                  onCheckedChange={(checked) => setIsChecked(checked as boolean)}
                />
                <Label htmlFor="checkbox">我同意條款和條件</Label>
              </div>

              <div className="flex gap-2">
                <Button onClick={showToast}>提交</Button>
                <Button variant="outline">重置</Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>標籤和徽章</CardTitle>
              <CardDescription>狀態指示和分類標籤</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                <Badge>默認</Badge>
                <Badge variant="secondary">次要</Badge>
                <Badge variant="outline">邊框</Badge>
                <Badge variant="success">成功</Badge>
                <Badge variant="danger">危險</Badge>
                <Badge variant="warning">警告</Badge>
                <Badge variant="info">信息</Badge>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Feedback Components */}
        <TabsContent value="feedback" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>警報組件</CardTitle>
              <CardDescription>用於顯示重要信息和警告</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Alert>
                <AlertTitle>信息提示</AlertTitle>
                <AlertDescription>
                  這是一個一般性的信息提示，用於向用戶傳達有用的信息。
                </AlertDescription>
              </Alert>

              <Alert variant="warning">
                <AlertTitle>警告</AlertTitle>
                <AlertDescription>
                  這是一個警告信息，提示用戶注意潛在的問題或風險。
                </AlertDescription>
              </Alert>

              <Alert variant="success">
                <AlertTitle>成功</AlertTitle>
                <AlertDescription>
                  操作成功完成！您的更改已保存。
                </AlertDescription>
              </Alert>

              <Alert variant="danger">
                <AlertTitle>錯誤</AlertTitle>
                <AlertDescription>
                  發生錯誤！請檢查您的輸入並重試。
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Toast通知</CardTitle>
              <CardDescription>臨時的消息通知</CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={showToast}>顯示Toast通知</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default ComponentShowcase