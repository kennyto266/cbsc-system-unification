# shadcn/ui 組件庫集成指南

## 概述

本項目已成功集成 shadcn/ui 組件庫，提供了一套基於 Radix UI 和 Tailwind CSS 的高質量、可訪問的 UI 組件。

## 已安裝的依賴

```bash
npm install @radix-ui/react-accordion \
            @radix-ui/react-avatar \
            @radix-ui/react-checkbox \
            @radix-ui/react-dialog \
            @radix-ui/react-label \
            @radix-ui/react-popover \
            @radix-ui/react-progress \
            @radix-ui/react-select \
            @radix-ui/react-slider \
            @radix-ui/react-slot \
            @radix-ui/react-switch \
            @radix-ui/react-tabs \
            @radix-ui/react-toggle \
            @radix-ui/react-icons \
            class-variance-authority \
            clsx \
            tailwind-merge \
            lucide-react \
            tailwindcss-animate
```

## 組件列表

### 基礎組件
- **Button** - 按鈕組件，支持多種變體和大小
- **Input** - 輸入框組件，支持錯誤狀態和幫助文本
- **Label** - 標籤組件，與表單元素配合使用
- **Badge** - 徽章組件，用於狀態標記
- **Checkbox** - 複選框組件

### 佈局組件
- **Card** - 卡片容器組件
  - CardHeader
  - CardTitle
  - CardDescription
  - CardContent
  - CardFooter

### 數據展示組件
- **Table** - 表格組件
  - TableHeader
  - TableBody
  - TableFooter
  - TableHead
  - TableRow
  - TableCell
  - TableCaption

### 表單組件
- **Select** - 下拉選擇組件
  - SelectTrigger
  - SelectValue
  - SelectContent
  - SelectItem
  - SelectGroup
  - SelectLabel

### 反饋組件
- **Alert** - 警告提示組件
  - AlertTitle
  - AlertDescription
- **Dialog** - 對話框組件
  - DialogTrigger
  - DialogContent
  - DialogHeader
  - DialogTitle
  - DialogDescription
  - DialogFooter
  - DialogClose
- **Toast** - 輕量級通知組件
  - ToastTitle
  - ToastDescription
  - ToastAction
- **useToast** - Toast 管理 Hook

### 導航組件
- **Tabs** - 標籤頁組件
  - TabsList
  - TabsTrigger
  - TabsContent

## 自定義主題

### CBSC 特定變體

我們為 CBSC 系統添加了特定的顏色變體：

#### Button 變體
- `cbsc` - CBSC 品牌漸變背景
- `cbscOutline` - CBSC 品牌邊框樣式
- `success` - 成功狀態
- `warning` - 警告狀態

#### Badge 變體
- `success` - 成功狀態
- `warning` - 警告狀態
- `info` - 信息狀態
- `error` - 錯誤狀態
- `successOutline` - 成功狀態邊框
- `warningOutline` - 警告狀態邊框
- `infoOutline` - 信息狀態邊框
- `errorOutline` - 錯誤狀態邊框

#### Alert 變體
- `success` - 成功提示
- `warning` - 警告提示
- `info` - 信息提示
- `destructive` - 錯誤提示

#### Toast 變體
- `success` - 成功通知
- `warning` - 警告通知
- `info` - 信息通知

## 使用示例

### 基本使用

```tsx
import { Button, Card, Input, Label } from '@/components/ui'

function MyComponent() {
  return (
    <Card className="p-6">
      <div className="space-y-4">
        <div>
          <Label htmlFor="email">郵箱地址</Label>
          <Input type="email" id="email" placeholder="輸入郵箱" />
        </div>
        <Button>提交</Button>
      </div>
    </Card>
  )
}
```

### 使用自定義變體

```tsx
// CBSC 品牌按鈕
<Button variant="cbsc">CBSC 操作</Button>

// 帶圖標的按鈕
<Button icon={<PlusIcon />} iconPosition="left">
  新增策略
</Button>

// 狀態徽章
<Badge variant="success">運行中</Badge>
<Badge variant="warning">警告</Badge>
```

### 使用 Toast 通知

```tsx
import { useToast } from '@/components/ui/use-toast'

function MyComponent() {
  const { toast } = useToast()

  const handleSuccess = () => {
    toast({
      title: "操作成功",
      description: "策略已成功創建",
      variant: "success",
    })
  }

  return <Button onClick={handleSuccess}>創建策略</Button>
}
```

### 使用對話框

```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui'

function DeleteDialog() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="destructive">刪除</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>確認刪除</DialogTitle>
        </DialogHeader>
        <p>此操作無法撤銷，確定要刪除嗎？</p>
        <div className="flex justify-end gap-2 mt-4">
          <Button variant="outline">取消</Button>
          <Button variant="destructive">確認刪除</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
```

## 組件展示頁面

訪問 `/components-showcase` 路由可以查看所有可用的 shadcn/ui 組件及其使用示例。

## 自定義主題配置

### 修改顏色

在 `tailwind.config.js` 中自定義顏色：

```js
module.exports = {
  theme: {
    extend: {
      colors: {
        // 添加自定義顏色
        brand: {
          50: '#f0f4ff',
          500: '#667eea',
          900: '#3c366b',
        }
      }
    }
  }
}
```

### 添加新的組件變體

使用 `class-variance-authority` 添加新變體：

```tsx
import { cva } from "class-variance-authority"

const buttonVariants = cva(
  "base-styles",
  {
    variants: {
      variant: {
        // 添加新變體
        gradient: "bg-gradient-to-r from-purple-500 to-pink-500 text-white",
      }
    }
  }
)
```

## 無障礙支持

所有基於 Radix UI 的組件都內置了完整的無障礙支持，包括：

- 鍵盤導航
- 屏幕閱讀器支持
- ARIA 屬性
- 焦點管理

## 遷移指南

如果需要從現有組件遷移到 shadcn/ui：

1. 導入新的組件：
   ```tsx
   // 舊的
   import { OldButton } from '@/components/old-button'

   // 新的
   import { Button } from '@/components/ui'
   ```

2. 更新屬性：
   ```tsx
   // 舊的
   <OldButton primary large onClick={handleClick}>
     按鈕
   </OldButton>

   // 新的
   <Button variant="default" size="lg" onClick={handleClick}>
     按鈕
   </Button>
   ```

3. 更新樣式（如需要）：
   - shadcn/ui 使用 CSS 變量，可以通過修改 `:root` 選擇器來自定義主題

## 最佳實踐

1. **保持一致性** - 使用預定義的變體而不是自定義樣式
2. **合組使用** - 將相關的組件（如 Label 和 Input）一起使用
3. **響應式設計** - 使用 Tailwind CSS 的響應式修飾符
4. **無障礙性** - 利用組件的內置無障礙功能
5. **性能優化** - 使用動態導入減少包大小

## 故障排除

### 常見問題

1. **樣式不生效**
   - 確保 `tailwind.config.js` 配置正確
   - 檢查是否導入了 `@tailwind` 指令

2. **TypeScript 錯誤**
   - 確保 `tsconfig.json` 包含正確的路徑映射
   - 檢查是否安裝了所有必要的類型包

3. **動畫不流暢**
   - 確保安裝了 `tailwindcss-animate`
   - 檢查 `tailwind.config.js` 中的動畫配置

## 更新與維護

要更新 shadcn/ui 組件：

```bash
# 更新依賴
npm update @radix-ui/react-*

# 更新特定組件
npx shadcn-ui@latest add [component-name]
```

## 資源鏈接

- [shadcn/ui 官方文檔](https://ui.shadcn.com/)
- [Radix UI 文檔](https://www.radix-ui.com/)
- [Tailwind CSS 文檔](https://tailwindcss.com/docs)
- [Class Variance Authority](https://cva.style/docs)