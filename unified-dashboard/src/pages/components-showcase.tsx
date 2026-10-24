import React, { useState } from 'react'
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
  Input,
  Label,
  Badge,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Checkbox,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Alert,
  AlertDescription,
  AlertTitle,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  useToast,
} from '@/components/ui'
import { Toaster } from '@/components/ui/toaster'

const ComponentShowcase = () => {
  const [selectedValue, setSelectedValue] = useState('')
  const [isChecked, setIsChecked] = useState(false)
  const { toast } = useToast()

  const showToast = (variant: 'default' | 'success' | 'warning' | 'error') => {
    const titles = {
      default: '通知',
      success: '成功',
      warning: '警告',
      error: '错误'
    }
    const descriptions = {
      default: '这是一条默认通知消息',
      success: '操作已成功完成！',
      warning: '请注意：此操作可能存在风险',
      error: '操作失败，请重试'
    }

    toast({
      title: titles[variant],
      description: descriptions[variant],
      variant: variant === 'error' ? 'destructive' : variant,
    })
  }

  return (
    <div className="container mx-auto py-8 px-4 space-y-8">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gradient-primary">shadcn/ui 組件庫展示</h1>
        <p className="text-lg text-gray-600">基於 Radix UI 和 Tailwind CSS 的現代化組件系統</p>
      </div>

      {/* Toast Container */}
      <Toaster />

      {/* Tabs for different component categories */}
      <Tabs defaultValue="basic" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="basic">基礎組件</TabsTrigger>
          <TabsTrigger value="forms">表單組件</TabsTrigger>
          <TabsTrigger value="feedback">反饋組件</TabsTrigger>
          <TabsTrigger value="display">數據展示</TabsTrigger>
        </TabsList>

        {/* Basic Components */}
        <TabsContent value="basic" className="space-y-6">
          {/* Buttons */}
          <Card>
            <CardHeader>
              <CardTitle>按鈕 (Button)</CardTitle>
              <CardDescription>各種樣式和大小的按鈕組件</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-3">
                <Button>默認按鈕</Button>
                <Button variant="secondary">次要按鈕</Button>
                <Button variant="outline">邊框按鈕</Button>
                <Button variant="ghost">幽靈按鈕</Button>
                <Button variant="destructive">危險按鈕</Button>
              </div>
              <div className="flex flex-wrap gap-3">
                <Button variant="cbsc">CBSC 漸變</Button>
                <Button variant="success">成功</Button>
                <Button variant="warning">警告</Button>
              </div>
              <div className="flex flex-wrap gap-3 items-center">
                <Button size="sm">小號</Button>
                <Button size="default">默認</Button>
                <Button size="lg">大號</Button>
                <Button size="icon">📦</Button>
              </div>
            </CardContent>
          </Card>

          {/* Badges */}
          <Card>
            <CardHeader>
              <CardTitle>徽章 (Badge)</CardTitle>
              <CardDescription>用於標記狀態或分類的徽章組件</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-3">
                <Badge>默認</Badge>
                <Badge variant="secondary">次要</Badge>
                <Badge variant="outline">邊框</Badge>
                <Badge variant="destructive">危險</Badge>
              </div>
              <div className="flex flex-wrap gap-3">
                <Badge variant="success">成功</Badge>
                <Badge variant="warning">警告</Badge>
                <Badge variant="info">信息</Badge>
              </div>
              <div className="flex flex-wrap gap-3">
                <Badge size="sm">小號</Badge>
                <Badge size="default">默認</Badge>
                <Badge size="lg">大號</Badge>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Form Components */}
        <TabsContent value="forms" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>輸入框 (Input)</CardTitle>
              <CardDescription>各種類型的輸入框組件</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid w-full max-w-sm items-center gap-1.5">
                <Label htmlFor="email">郵箱地址</Label>
                <Input type="email" id="email" placeholder="輸入您的郵箱" />
              </div>
              <div className="grid w-full max-w-sm items-center gap-1.5">
                <Label htmlFor="password">密碼</Label>
                <Input type="password" id="password" placeholder="輸入密碼" />
              </div>
              <div className="grid w-full max-w-sm items-center gap-1.5">
                <Label htmlFor="error">錯誤狀態</Label>
                <Input id="error" placeholder="輸入內容" helperText="此字段是必需的" error />
              </div>
            </CardContent>
          </Card>

          {/* Select and Checkbox */}
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>選擇器 (Select)</CardTitle>
                <CardDescription>下拉選擇組件</CardDescription>
              </CardHeader>
              <CardContent>
                <Select value={selectedValue} onValueChange={setSelectedValue}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="選擇一個選項" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="option1">選項 1</SelectItem>
                    <SelectItem value="option2">選項 2</SelectItem>
                    <SelectItem value="option3">選項 3</SelectItem>
                    <SelectItem value="option4">選項 4</SelectItem>
                  </SelectContent>
                </Select>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>複選框 (Checkbox)</CardTitle>
                <CardDescription>複選框組件</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="terms"
                    checked={isChecked}
                    onCheckedChange={(checked) => setIsChecked(checked as boolean)}
                  />
                  <Label htmlFor="terms" className="text-sm">
                    我同意條款和條件
                  </Label>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Feedback Components */}
        <TabsContent value="feedback" className="space-y-6">
          {/* Alerts */}
          <Card>
            <CardHeader>
              <CardTitle>警告提示 (Alert)</CardTitle>
              <CardDescription>用於顯示重要信息的提示組件</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Alert>
                <AlertTitle>默認提示</AlertTitle>
                <AlertDescription>
                  這是一條默認類型的提示信息。
                </AlertDescription>
              </Alert>
              <Alert variant="success">
                <AlertTitle>成功</AlertTitle>
                <AlertDescription>
                  操作已成功完成！數據已保存。
                </AlertDescription>
              </Alert>
              <Alert variant="warning">
                <AlertTitle>警告</AlertTitle>
                <AlertDescription>
                  請注意：此操作可能會影響其他數據。
                </AlertDescription>
              </Alert>
              <Alert variant="destructive">
                <AlertTitle>錯誤</AlertTitle>
                <AlertDescription>
                  操作失敗！請檢查您的輸入並重試。
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>

          {/* Dialog */}
          <Card>
            <CardHeader>
              <CardTitle>對話框 (Dialog)</CardTitle>
              <CardDescription>模態對話框組件</CardDescription>
            </CardHeader>
            <CardContent>
              <Dialog>
                <DialogTrigger asChild>
                  <Button>打開對話框</Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>確認操作</DialogTitle>
                    <DialogDescription>
                      您確定要執行此操作嗎？此操作無法撤銷。
                    </DialogDescription>
                  </DialogHeader>
                  <DialogFooter>
                    <Button variant="outline">取消</Button>
                    <Button>確認</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </CardContent>
          </Card>

          {/* Toast Notifications */}
          <Card>
            <CardHeader>
              <CardTitle>通知 (Toast)</CardTitle>
              <CardDescription>輕量級通知消息</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-3">
                <Button onClick={() => showToast('default')}>默認通知</Button>
                <Button onClick={() => showToast('success')}>成功通知</Button>
                <Button onClick={() => showToast('warning')}>警告通知</Button>
                <Button onClick={() => showToast('error')}>錯誤通知</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Data Display Components */}
        <TabsContent value="display" className="space-y-6">
          {/* Table */}
          <Card>
            <CardHeader>
              <CardTitle>表格 (Table)</CardTitle>
              <CardDescription>數據表格展示組件</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>策略名稱</TableHead>
                    <TableHead>類型</TableHead>
                    <TableHead>狀態</TableHead>
                    <TableHead>收益率</TableHead>
                    <TableHead>風險等級</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-medium">量化Alpha策略</TableCell>
                    <TableCell>股票</TableCell>
                    <TableCell><Badge variant="success">運行中</Badge></TableCell>
                    <TableCell>24.5%</TableCell>
                    <TableCell><Badge variant="warning">中高</Badge></TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">套利策略V2</TableCell>
                    <TableCell>期權</TableCell>
                    <TableCell><Badge variant="success">運行中</Badge></TableCell>
                    <TableCell>18.3%</TableCell>
                    <TableCell><Badge>低</Badge></TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">動量策略</TableCell>
                    <TableCell>期貨</TableCell>
                    <TableCell><Badge variant="destructive">已停止</Badge></TableCell>
                    <TableCell>-5.2%</TableCell>
                    <TableCell><Badge variant="destructive">高</Badge></TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default ComponentShowcase