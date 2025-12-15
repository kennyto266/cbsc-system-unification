import React, { useState } from 'react';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  FormField,
  DataTable,
  Modal,
  useModal,
  ConfirmModal,
  FormModal,
  Alert,
  AlertBanner,
  useToast,
  toast,
} from '@/components/combined';
import { ShadcnButton as Button } from '@/components/ui/shadcn-button';
import { ShadcnCard as Card, CardContent, CardHeader, CardTitle } from '@/components/ui/shadcn-card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/shadcn-badge';
import { Edit, Trash, Plus, Search, Filter } from 'lucide-react';
import { ExtendedColumnDef } from './DataTable';

// 示例数据类型
interface Strategy {
  id: string;
  name: string;
  type: string;
  status: 'active' | 'inactive' | 'testing';
  performance: number;
  riskLevel: number;
  createdAt: string;
}

// 模拟数据
const mockStrategies: Strategy[] = [
  {
    id: '1',
    name: 'Momentum Master Pro',
    type: 'momentum',
    status: 'active',
    performance: 12.5,
    riskLevel: 75,
    createdAt: '2024-01-15',
  },
  {
    id: '2',
    name: 'Mean Reversion Alpha',
    type: 'mean_reversion',
    status: 'testing',
    performance: 8.3,
    riskLevel: 45,
    createdAt: '2024-01-10',
  },
  {
    id: '3',
    name: 'Arbitrage Hunter',
    type: 'arbitrage',
    status: 'active',
    performance: 5.7,
    riskLevel: 30,
    createdAt: '2024-01-05',
  },
  {
    id: '4',
    name: 'Trend Following X',
    type: 'trend_following',
    status: 'inactive',
    performance: -2.1,
    riskLevel: 60,
    createdAt: '2023-12-28',
  },
];

// 验证 schema
const formSchema = z.object({
  name: z.string().min(1, 'Strategy name is required'),
  type: z.enum(['momentum', 'mean_reversion', 'arbitrage', 'trend_following']),
  description: z.string().optional(),
  riskLevel: z.number().min(0).max(100),
  active: z.boolean(),
});

type FormData = z.infer<typeof formSchema>;

// 组件示例
export const ComponentExamples: React.FC = () => {
  const { toast } = useToast();
  const createModal = useModal();
  const deleteModal = useModal<{ id: string; name: string }>();
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);

  // 表单方法
  const formMethods = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
      type: 'momentum',
      description: '',
      riskLevel: 50,
      active: false,
    },
  });

  // 数据表格列定义
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
        <Badge variant="secondary" className="capitalize">
          {getValue().replace('_', ' ')}
        </Badge>
      ),
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ getValue }) => {
        const status = getValue() as string;
        const statusConfig = {
          active: { variant: 'default' as const, label: 'Active' },
          testing: { variant: 'secondary' as const, label: 'Testing' },
          inactive: { variant: 'outline' as const, label: 'Inactive' },
        };
        const config = statusConfig[status as keyof typeof statusConfig];
        return <Badge variant={config.variant}>{config.label}</Badge>;
      },
    },
    {
      accessorKey: 'performance',
      header: 'Performance',
      cell: ({ getValue }) => {
        const value = getValue() as number;
        return (
          <span className={value > 0 ? 'text-green-600' : 'text-red-600'}>
            {value > 0 ? '+' : ''}{value}%
          </span>
        );
      },
    },
    {
      accessorKey: 'riskLevel',
      header: 'Risk Level',
      cell: ({ getValue }) => {
        const value = getValue() as number;
        const riskColor = value > 70 ? 'text-red-600' : value > 40 ? 'text-yellow-600' : 'text-green-600';
        return <span className={riskColor}>{value}%</span>;
      },
    },
  ];

  // 处理删除
  const handleDelete = () => {
    if (deleteModal.data) {
      toast({
        title: 'Strategy Deleted',
        description: `${deleteModal.data.name} has been removed`,
        variant: 'success',
      });
      deleteModal.closeModal();
    }
  };

  // 处理创建
  const handleCreateStrategy = (data: FormData) => {
    toast({
      title: 'Strategy Created',
      description: `${data.name} has been successfully created`,
      variant: 'success',
    });
    createModal.closeModal();
    formMethods.reset();
  };

  // 处理表格操作
  const handleTableAction = (action: string, strategy: Strategy) => {
    if (action === 'edit') {
      setSelectedStrategy(strategy);
      formMethods.reset({
        name: strategy.name,
        type: strategy.type as any,
        description: '',
        riskLevel: strategy.riskLevel,
        active: strategy.status === 'active',
      });
      createModal.openModal();
    } else if (action === 'delete') {
      deleteModal.setData({ id: strategy.id, name: strategy.name });
      deleteModal.openModal();
    }
  };

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold mb-2">Component Examples</h1>
        <p className="text-muted-foreground">
          Examples of Square-UI + shadcn/ui combined components
        </p>
      </div>

      <Tabs defaultValue="table" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="table">Data Table</TabsTrigger>
          <TabsTrigger value="forms">Forms</TabsTrigger>
          <TabsTrigger value="modals">Modals</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
        </TabsList>

        {/* Data Table 示例 */}
        <TabsContent value="table">
          <Card>
            <CardHeader>
              <CardTitle>Strategy Management</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={columns}
                data={mockStrategies}
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
                      { value: 'arbitrage', label: 'Arbitrage' },
                      { value: 'trend_following', label: 'Trend Following' },
                    ],
                  },
                  {
                    id: 'status',
                    title: 'Status',
                    options: [
                      { value: 'active', label: 'Active' },
                      { value: 'testing', label: 'Testing' },
                      { value: 'inactive', label: 'Inactive' },
                    ],
                  },
                ]}
                selectable
                onSelectionChange={(rows) => {
                  console.log('Selected rows:', rows);
                }}
                rowActions={(row) => (
                  <div className="flex space-x-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleTableAction('edit', row)}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleTableAction('delete', row)}
                    >
                      <Trash className="h-4 w-4" />
                    </Button>
                  </div>
                )}
                onRefresh={() => {
                  toast({
                    title: 'Refreshed',
                    description: 'Data has been refreshed',
                    variant: 'info',
                  });
                }}
                onExport={() => {
                  toast({
                    title: 'Exporting',
                    description: 'Preparing data export...',
                    variant: 'info',
                  });
                }}
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Forms 示例 */}
        <TabsContent value="forms">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Create Strategy Form</CardTitle>
              </CardHeader>
              <CardContent>
                <FormProvider {...formMethods}>
                  <form
                    onSubmit={formMethods.handleSubmit(handleCreateStrategy)}
                    className="space-y-4"
                  >
                    <FormField
                      name="name"
                      label="Strategy Name"
                      placeholder="Enter strategy name"
                      required
                    />

                    <FormField
                      name="type"
                      type="select"
                      label="Strategy Type"
                      options={[
                        { value: 'momentum', label: 'Momentum' },
                        { value: 'mean_reversion', label: 'Mean Reversion' },
                        { value: 'arbitrage', label: 'Arbitrage' },
                        { value: 'trend_following', label: 'Trend Following' },
                      ]}
                      required
                    />

                    <FormField
                      name="description"
                      type="textarea"
                      label="Description"
                      placeholder="Describe your strategy"
                    />

                    <FormField
                      name="riskLevel"
                      type="slider"
                      label="Risk Level"
                      sliderProps={{ min: 0, max: 100, step: 5 }}
                      helperText="Higher risk may lead to higher returns"
                    />

                    <FormField
                      name="active"
                      type="switch"
                      label="Enable Strategy"
                    />

                    <div className="flex space-x-2">
                      <Button type="submit" className="flex-1">
                        Create Strategy
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => formMethods.reset()}
                      >
                        Reset
                      </Button>
                    </div>
                  </form>
                </FormProvider>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Form Field Examples</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium mb-2">Input Types</h4>
                  <div className="space-y-2">
                    <FormField
                      name="example1"
                      placeholder="Text input"
                      label="Text Input"
                    />
                    <FormField
                      name="example2"
                      label="Email Input"
                      type="input"
                      inputProps={{ type: 'email' }}
                      placeholder="email@example.com"
                    />
                    <FormField
                      name="example3"
                      label="Number Input"
                      type="input"
                      inputProps={{ type: 'number' }}
                      placeholder="12345"
                    />
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-medium mb-2">Other Fields</h4>
                  <div className="space-y-2">
                    <FormField
                      name="example4"
                      type="checkbox"
                      label="I agree to the terms and conditions"
                      checkboxProps={{ label: 'Accept Terms' }}
                    />
                    <FormField
                      name="example5"
                      type="date"
                      label="Select Date"
                      placeholder="Pick a date"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Modals 示例 */}
        <TabsContent value="modals">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Modal Triggers</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button onClick={createModal.openModal} className="w-full">
                  <Plus className="mr-2 h-4 w-4" />
                  Open Form Modal
                </Button>

                <Button
                  variant="outline"
                  onClick={() =>
                    toast.info('This is a toast notification example')
                  }
                  className="w-full"
                >
                  Show Toast
                </Button>

                <Button
                  variant="secondary"
                  onClick={() => {
                    setSelectedStrategy(null);
                    formMethods.reset();
                    createModal.openModal();
                  }}
                  className="w-full"
                >
                  New Strategy Modal
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Modal Info</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  Click the buttons to see different modal examples:
                </p>
                <ul className="space-y-2 text-sm">
                  <li>• Form Modal - For creating/editing data</li>
                  <li>• Confirm Modal - For confirming actions</li>
                  <li>• Info Modal - For displaying information</li>
                  <li>• Custom Modal - Fully customizable</li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Alerts 示例 */}
        <TabsContent value="alerts">
          <div className="space-y-4">
            <AlertBanner
              variant="info"
              showIcon
              actions={
                <Button size="sm" variant="outline">
                  Learn More
                </Button>
              }
            >
              Welcome to the CBSC Strategy Management System! Get started by creating your first strategy.
            </AlertBanner>

            <div className="grid gap-4 lg:grid-cols-2">
              <div className="space-y-3">
                <h4 className="text-sm font-medium">Alert Variants</h4>
                <Alert variant="info" title="Information">
                  This is an informational message about the system status.
                </Alert>
                <Alert variant="success" title="Success">
                  Your strategy has been successfully created and is now active.
                </Alert>
                <Alert variant="warning" title="Warning" closable>
                  High volatility detected. Please review your risk settings.
                </Alert>
                <Alert variant="error" title="Error" closable>
                  Failed to save changes. Please check your connection and try again.
                </Alert>
              </div>

              <div className="space-y-3">
                <h4 className="text-sm font-medium">Toast Examples</h4>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => toast.info('Info toast message')}
                  >
                    Info
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => toast.success('Success!')}
                  >
                    Success
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => toast.warning('Warning!')}
                  >
                    Warning
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => toast.error('Error occurred')}
                  >
                    Error
                  </Button>
                </div>

                <div className="pt-2">
                  <h5 className="text-xs font-medium mb-2">Inline Alerts</h5>
                  <div className="space-y-2">
                    <Alert variant="info" className="py-2">
                      <span className="text-xs">
                        Tip: Use keyboard shortcuts for faster navigation
                      </span>
                    </Alert>
                    <Alert variant="warning" className="py-2">
                      <span className="text-xs">
                        Please save your changes before leaving this page
                      </span>
                    </Alert>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {/* Modals */}
      <FormModal
        open={createModal.open}
        onOpenChange={createModal.setOpen}
        title={selectedStrategy ? 'Edit Strategy' : 'Create Strategy'}
        description={selectedStrategy ? 'Update your strategy details' : 'Fill in the details to create a new strategy'}
        onSubmit={formMethods.handleSubmit(handleCreateStrategy)}
        submitText={selectedStrategy ? 'Update' : 'Create'}
      >
        <div className="space-y-4">
          <FormField
            name="name"
            label="Strategy Name"
            placeholder="Enter strategy name"
            required
          />
          <FormField
            name="type"
            type="select"
            label="Strategy Type"
            options={[
              { value: 'momentum', label: 'Momentum' },
              { value: 'mean_reversion', label: 'Mean Reversion' },
              { value: 'arbitrage', label: 'Arbitrage' },
              { value: 'trend_following', label: 'Trend Following' },
            ]}
            required
          />
          <FormField
            name="description"
            type="textarea"
            label="Description"
            placeholder="Describe your strategy"
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
            label="Enable Strategy"
          />
        </div>
      </FormModal>

      <ConfirmModal
        open={deleteModal.open}
        onOpenChange={deleteModal.setOpen}
        title="Delete Strategy"
        description={`Are you sure you want to delete "${deleteModal.data?.name}"? This action cannot be undone.`}
        type="error"
        onConfirm={handleDelete}
      />
    </div>
  );
};