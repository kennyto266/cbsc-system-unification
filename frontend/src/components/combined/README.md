# Square-UI + shadcn/ui 混合组件库

这是一个结合了 shadcn/ui 的强大功能和 Square-UI 美观的 CBSC 系统混合组件库。

## 组件概览

### 1. FormField - 增强表单字段

集成了各种输入类型的统一表单字段组件，支持 React Hook Form 集成。

#### 基本用法

```tsx
import { FormField } from '@/components/combined/FormField';
import { FormProvider, useForm } from 'react-hook-form';

function MyForm() {
  const methods = useForm({
    defaultValues: {
      username: '',
      email: '',
      password: '',
      strategy: '',
      riskLevel: [50],
      active: false,
      startDate: new Date(),
    },
  });

  const onSubmit = (data) => {
    console.log(data);
  };

  return (
    <FormProvider {...methods}>
      <form onSubmit={methods.handleSubmit(onSubmit)}>
        <FormField
          name="username"
          label="Username"
          placeholder="Enter your username"
          required
        />

        <FormField
          name="email"
          type="input"
          label="Email"
          placeholder="Enter your email"
          required
        />

        <FormField
          name="password"
          type="input"
          label="Password"
          inputProps={{ type: 'password' }}
          required
        />

        <FormField
          name="strategy"
          type="select"
          label="Strategy Type"
          options={[
            { value: 'momentum', label: 'Momentum' },
            { value: 'mean_reversion', label: 'Mean Reversion' },
            { value: 'arbitrage', label: 'Arbitrage' },
          ]}
          required
        />

        <FormField
          name="riskLevel"
          type="slider"
          label="Risk Level"
          sliderProps={{ min: 0, max: 100, step: 5 }}
        />

        <FormField
          name="active"
          type="switch"
          label="Enable notifications"
        />

        <FormField
          name="startDate"
          type="date"
          label="Start Date"
          placeholder="Pick a date"
        />
      </form>
    </FormProvider>
  );
}
```

#### 支持的字段类型

- `input` - 普通输入框
- `textarea` - 多行文本框
- `select` - 下拉选择框
- `multiselect` - 多选下拉框
- `checkbox` - 复选框
- `slider` - 滑块
- `switch` - 开关
- `date` - 日期选择器

### 2. DataTable - 增强数据表格

功能丰富的数据表格组件，支持排序、过滤、分页、选择等功能。

#### 基本用法

```tsx
import { DataTable, ExtendedColumnDef } from '@/components/combined/DataTable';
import { Badge } from '@/components/ui/shadcn-badge';
import { Button } from '@/components/ui/shadcn-button';
import { MoreHorizontal, Edit, Trash } from 'lucide-react';

// 定义列
const columns: ExtendedColumnDef<Strategy>[] = [
  {
    accessorKey: 'name',
    header: 'Strategy Name',
    cell: ({ getValue }) => (
      <div className="font-medium">{getValue()}</div>
    ),
  },
  {
    accessorKey: 'type',
    header: 'Type',
    cell: ({ getValue }) => (
      <Badge variant="secondary">{getValue()}</Badge>
    ),
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: ({ getValue }) => {
      const status = getValue();
      return (
        <Badge
          variant={
            status === 'active'
              ? 'default'
              : status === 'inactive'
              ? 'secondary'
              : 'outline'
          }
        >
          {status}
        </Badge>
      );
    },
  },
  {
    accessorKey: 'performance',
    header: 'Performance',
    cell: ({ getValue }) => {
      const value = getValue();
      return (
        <span className={value > 0 ? 'text-green-600' : 'text-red-600'}>
          {value > 0 ? '+' : ''}{value}%
        </span>
      );
    },
  },
];

// 定义数据
const data: Strategy[] = [
  {
    id: '1',
    name: 'Momentum Master',
    type: 'momentum',
    status: 'active',
    performance: 12.5,
  },
  // ...
];

function StrategyTable() {
  return (
    <DataTable
      columns={columns}
      data={data}
      searchable
      searchPlaceholder="Search strategies..."
      filterable
      filterColumns={[
        {
          id: 'type',
          title: 'Type',
          options: [
            { value: 'momentum', label: 'Momentum' },
            { value: 'mean_reversion', label: 'Mean Reversion' },
          ],
        },
        {
          id: 'status',
          title: 'Status',
          options: [
            { value: 'active', label: 'Active' },
            { value: 'inactive', label: 'Inactive' },
          ],
        },
      ]}
      selectable
      onSelectionChange={(selectedRows) => {
        console.log('Selected:', selectedRows);
      }}
      rowActions={(row) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Trash className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
      onRefresh={() => {
        console.log('Refreshing data...');
      }}
      onExport={() => {
        console.log('Exporting data...');
      }}
    />
  );
}
```

#### 功能特性

- ✅ 排序
- ✅ 全局搜索
- ✅ 列过滤
- ✅ 行选择
- ✅ 分页
- ✅ 行操作
- ✅ 刷新
- ✅ 导出
- ✅ 响应式设计

### 3. Modal - 增强模态框

灵活的模态框组件，支持多种预设和自定义配置。

#### 基本用法

```tsx
import { Modal, useModal, ConfirmModal, FormModal, InfoModal } from '@/components/combined/Modal';

// 自定义模态框
function CustomModalExample() {
  const { open, setOpen } = useModal();

  return (
    <div>
      <Button onClick={() => setOpen(true)}>Open Modal</Button>
      <Modal
        open={open}
        onOpenChange={setOpen}
        title="Custom Modal"
        description="This is a custom modal with content"
        size="lg"
        showMaximize
      >
        <p>Modal content goes here...</p>
      </Modal>
    </div>
  );
}

// 确认对话框
function ConfirmExample() {
  const { open, setOpen } = useModal();

  return (
    <div>
      <Button variant="destructive" onClick={() => setOpen(true)}>
        Delete Item
      </Button>
      <ConfirmModal
        open={open}
        onOpenChange={setOpen}
        title="Delete Confirmation"
        description="Are you sure you want to delete this item? This action cannot be undone."
        type="error"
        onConfirm={() => {
          console.log('Item deleted');
        }}
      />
    </div>
  );
}

// 表单模态框
function FormModalExample() {
  const { open, setOpen } = useModal();

  return (
    <div>
      <Button onClick={() => setOpen(true)}>Add New Strategy</Button>
      <FormModal
        open={open}
        onOpenChange={setOpen}
        title="Create New Strategy"
        description="Fill in the details to create a new trading strategy"
        onSubmit={(data) => {
          console.log('Form submitted:', data);
        }}
      >
        <StrategyForm />
      </FormModal>
    </div>
  );
}
```

#### 模态框类型

- `Modal` - 基础模态框
- `ConfirmModal` - 确认对话框
- `InfoModal` - 信息展示对话框
- `FormModal` - 表单对话框

### 4. Alert - 增强提醒

多功能的提醒组件，支持 Alert 和 Toast 两种形式。

#### Alert 用法

```tsx
import { Alert, AlertBanner, InlineAlert } from '@/components/combined/Alert';

function AlertsExample() {
  return (
    <div className="space-y-4">
      {/* 基础提醒 */}
      <Alert variant="info" title="Information">
        This is an informational message.
      </Alert>

      <Alert variant="success" title="Success!">
        Your action was completed successfully.
      </Alert>

      <Alert variant="warning" title="Warning">
        Please review your input before proceeding.
      </Alert>

      <Alert variant="error" title="Error" closable>
        Something went wrong. Please try again.
      </Alert>

      {/* 页面横幅 */}
      <AlertBanner
        variant="warning"
        showIcon
        actions={
          <Button size="sm">Learn More</Button>
        }
      >
        System maintenance scheduled for tonight at 10 PM.
      </AlertBanner>

      {/* 内联提醒 */}
      <InlineAlert variant="info">
        Tips: You can use keyboard shortcuts to navigate faster.
      </InlineAlert>
    </div>
  );
}
```

#### Toast 用法

```tsx
import { useToast, toast, ToastContainer } from '@/components/combined/Alert';

function ToastExample() {
  const { toast } = useToast();

  const showToasts = () => {
    // 基础用法
    toast({
      title: 'Success',
      description: 'Your changes have been saved.',
      variant: 'success',
    });

    // 带操作的 Toast
    toast({
      title: 'New Update Available',
      description: 'Version 2.0 is ready to install.',
      action: (
        <ToastAction onClick={() => console.log('Update clicked')}>
          Update Now
        </ToastAction>
      ),
    });

    // 快捷方法
    toast.info('This is an info message');
    toast.success('Operation completed successfully');
    toast.warning('Please check your inputs');
    toast.error('Something went wrong');
  };

  return (
    <div>
      <Button onClick={showToasts}>Show Toasts</Button>
      <ToastContainer />
    </div>
  );
}
```

## 样式主题

组件库基于 Square-UI 的紫色主题，并完全支持暗黑模式。

### CSS 变量

```css
:root {
  --cbsc-primary: 262.1 83.3% 57.8%;
  --cbsc-primary-hover: 262.1 83.3% 50%;
  --cbsc-secondary: 210 40% 96.1%;
  --cbsc-accent: 210 40% 94%;

  --cbsc-bg-primary: 0 0% 100%;
  --cbsc-bg-secondary: 210 40% 98%;
  --cbsc-bg-tertiary: 210 40% 96%;

  --cbsc-text-primary: 222.2 84% 4.9%;
  --cbsc-text-secondary: 215.4 16.3% 46.9%;
  --cbsc-text-muted: 210 40% 60%;

  --cbsc-border-primary: 214.3 31.8% 91.4%;
  --cbsc-border-secondary: 214.3 31.8% 85%;
  --cbsc-border-focus: hsl(var(--cbsc-primary));
}
```

## 最佳实践

### 1. 表单验证

结合 `react-hook-form` 和 `zod` 进行表单验证：

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { userSchemas } from '@/lib/validations';

const schema = userSchemas.register;

function UserRegistrationForm() {
  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
    },
  });

  return (
    <FormProvider {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <FormField
          name="username"
          label="Username"
          required
        />
        {/* 其他字段... */}
      </form>
    </FormProvider>
  );
}
```

### 2. 数据表格

使用 TypeScript 定义数据类型：

```tsx
interface Strategy {
  id: string;
  name: string;
  type: 'momentum' | 'mean_reversion' | 'arbitrage';
  status: 'active' | 'inactive' | 'testing';
  performance: number;
  createdAt: Date;
}

const columns: ExtendedColumnDef<Strategy>[] = [
  // ...
];
```

### 3. 模态框管理

使用 `useModal` hook 管理模态框状态：

```tsx
function ComplexModalExample() {
  const createModal = useModal();
  const editModal = useModal();
  const deleteModal = useModal();

  return (
    <>
      <Button onClick={createModal.openModal}>Create</Button>
      <Button onClick={editModal.openModal}>Edit</Button>
      <Button onClick={deleteModal.openModal}>Delete</Button>

      <Modal open={createModal.open} onOpenChange={createModal.setOpen}>
        {/* Create form */}
      </Modal>

      <Modal open={editModal.open} onOpenChange={editModal.setOpen}>
        {/* Edit form */}
      </Modal>

      <ConfirmModal
        open={deleteModal.open}
        onOpenChange={deleteModal.setOpen}
        onConfirm={handleDelete}
      />
    </>
  );
}
```

## 依赖关系

确保已安装以下依赖：

```json
{
  "dependencies": {
    "@radix-ui/react-accordion": "^1.1.2",
    "@radix-ui/react-avatar": "^1.0.4",
    "@radix-ui/react-checkbox": "^1.0.4",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-label": "^2.0.2",
    "@radix-ui/react-popover": "^1.0.7",
    "@radix-ui/react-progress": "^1.0.3",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-slider": "^1.1.2",
    "@radix-ui/react-slot": "^1.0.2",
    "@radix-ui/react-switch": "^1.0.3",
    "@radix-ui/react-tabs": "^1.0.4",
    "@tanstack/react-table": "^8.11.8",
    "@hookform/resolvers": "^3.3.4",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "lucide-react": "^0.312.0",
    "react-day-picker": "^8.10.0",
    "react-hook-form": "^7.49.3",
    "tailwind-merge": "^2.2.2",
    "zod": "^3.22.4"
  }
}
```

## 贡献指南

1. 遵循 Square-UI 的设计规范
2. 保持组件的一致性和可复用性
3. 添加适当的 TypeScript 类型
4. 编写清晰的文档和示例
5. 确保所有组件支持暗黑模式
6. 测试所有交互和边缘情况