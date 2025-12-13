---
name: task-006-strategy-management-interface
status: open
created: 2025-12-13T09:33:34Z
updated: 2025-12-13T09:33:34Z
assignee: frontend-backend-team
phase: 2
estimated_hours: 120
priority: high
---

# Task #6: 策略管理界面

## 📋 任務描述
開發 CBSC Dashboard 的策略管理界面，包括策略列表與篩選、策略創建/編輯表單、策略性能分析頁面和批量操作功能，為用戶提供完整的策略生命週期管理工具。

## 🎯 具體要求

### 6.1 策略列表與篩選
- [ ] 策略列表表格（支持分頁、排序）
- [ ] 高級篩選器（按狀態、類型、績效等）
- [ ] 實時狀態指示器
- [ ] 快速操作按鈕（啟動/停止/編輯）
- [ ] 列表視圖/卡片視圖切換
- [ ] 列表配置保存

### 6.2 策略創建/編輯表單
- [ ] 多步驟表單嚮導
- [ ] 策略參數配置
- [ ] 代碼編輯器集成（Monaco Editor）
- [ ] 參數驗證和提示
- [ ] 表單草稿保存
- [ ] 策略模板系統

### 6.3 策略性能分析頁面
- [ ] 詳細績效指標展示
- [ ] 歷史回測結果
- [ ] 風險指標分析
- [ ] 收益率分布圖
- [ ] 回撤分析
- [ ] 績效對比工具

### 6.4 批量操作功能
- [ ] 多選操作接口
- [ ] 批量啟動/停止
- [ ] 批量參數更新
- [ ] 批量導出/導入
- [ ] 操作確認對話框
- [ ] 操作歷史記錄

## ✅ 驗收標準

1. **功能驗收**
   - [ ] 策略可以正常創建、編輯和刪除
   - [ ] 篩選和搜索功能準確無誤
   - [ ] 批量操作穩定可靠
   - [ ] 性能分析數據準確

2. **性能標準**
   - [ ] 列表加載時間 < 1 秒
   - [ ] 篩選響應時間 < 300ms
   - [ ] 表單提交時間 < 2 秒
   - [ ] 支持 1000+ 策略管理

3. **用戶體驗**
   - [ ] 操作流程直觀簡單
   - [ ] 錯誤提示清晰
   - [ ] 加載狀態明確
   - [ ] 快捷鍵支持

## 🔧 技術要求

### 策略列表組件
```typescript
// pages/strategies/StrategyList.tsx
interface StrategyListState {
  strategies: Strategy[];
  loading: boolean;
  pagination: {
    page: number;
    pageSize: number;
    total: number;
  };
  filters: StrategyFilters;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
  selectedIds: string[];
  viewMode: 'table' | 'card';
}

export const StrategyList: React.FC = () => {
  const [state, setState] = useState<StrategyListState>({
    strategies: [],
    loading: false,
    pagination: { page: 1, pageSize: 20, total: 0 },
    filters: {},
    sortBy: 'createdAt',
    sortOrder: 'desc',
    selectedIds: [],
    viewMode: 'table'
  });

  const { data, error, isLoading, refetch } = useQuery({
    queryKey: ['strategies', state.pagination, state.filters, state.sortBy, state.sortOrder],
    queryFn: fetchStrategies,
    keepPreviousData: true
  });

  const handleFilterChange = useCallback((newFilters: Partial<StrategyFilters>) => {
    setState(prev => ({
      ...prev,
      filters: { ...prev.filters, ...newFilters },
      pagination: { ...prev.pagination, page: 1 }
    }));
  }, []);

  const handleSort = useCallback((sortBy: string) => {
    setState(prev => ({
      ...prev,
      sortBy,
      sortOrder: prev.sortBy === sortBy && prev.sortOrder === 'asc' ? 'desc' : 'asc'
    }));
  }, []);

  const handleSelectionChange = useCallback((selectedIds: string[]) => {
    setState(prev => ({ ...prev, selectedIds }));
  }, []);

  const handleBatchOperation = useCallback(async (operation: BatchOperation) => {
    try {
      await executeBatchOperation(state.selectedIds, operation);
      refetch();
      setState(prev => ({ ...prev, selectedIds: [] }));
    } catch (error) {
      console.error('Batch operation failed:', error);
    }
  }, [state.selectedIds, refetch]);

  return (
    <div className="space-y-6">
      {/* 頁面標題和操作 */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">策略管理</h1>
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            onClick={() => setShowImportModal(true)}
          >
            <CloudArrowUpIcon className="h-5 w-5 mr-2" />
            導入策略
          </Button>
          <Button onClick={() => navigate('/strategies/new')}>
            <PlusIcon className="h-5 w-5 mr-2" />
            創建策略
          </Button>
        </div>
      </div>

      {/* 篩選器 */}
      <StrategyFilterPanel
        filters={state.filters}
        onFilterChange={handleFilterChange}
      />

      {/* 批量操作工具欄 */}
      {state.selectedIds.length > 0 && (
        <BatchOperationToolbar
          selectedCount={state.selectedIds.length}
          onOperation={handleBatchOperation}
        />
      )}

      {/* 視圖切換和分頁 */}
      <div className="flex justify-between items-center">
        <ViewModeToggle
          mode={state.viewMode}
          onModeChange={(mode) => setState(prev => ({ ...prev, viewMode: mode }))}
        />
        <Pagination
          page={state.pagination.page}
          pageSize={state.pagination.pageSize}
          total={data?.total || 0}
          onChange={(page, pageSize) => setState(prev => ({
            ...prev,
            pagination: { ...prev.pagination, page, pageSize }
          }))}
        />
      </div>

      {/* 策略列表 */}
      {isLoading ? (
        <StrategyListSkeleton />
      ) : state.viewMode === 'table' ? (
        <StrategyTable
          strategies={data?.items || []}
          selectedIds={state.selectedIds}
          onSelectionChange={handleSelectionChange}
          onSort={handleSort}
          sortBy={state.sortBy}
          sortOrder={state.sortOrder}
        />
      ) : (
        <StrategyCardGrid
          strategies={data?.items || []}
          selectedIds={state.selectedIds}
          onSelectionChange={handleSelectionChange}
        />
      )}
    </div>
  );
};
```

### 策略編輯器組件
```typescript
// components/strategies/StrategyEditor.tsx
interface StrategyEditorProps {
  strategy?: Strategy;
  onSave: (strategy: StrategyData) => Promise<void>;
  onCancel: () => void;
}

export const StrategyEditor: React.FC<StrategyEditorProps> = ({
  strategy,
  onSave,
  onCancel
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [formData, setFormData] = useState<StrategyFormData>(getDefaultFormData(strategy));
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const steps = [
    { id: 'basic', title: '基本信息', icon: DocumentTextIcon },
    { id: 'params', title: '參數配置', icon: CogIcon },
    { id: 'code', title: '策略代碼', icon: CodeBracketIcon },
    { id: 'risk', title: '風險控制', icon: ShieldCheckIcon },
    { id: 'review', title: '確認提交', icon: CheckCircleIcon }
  ];

  const handleStepChange = (step: number) => {
    if (validateCurrentStep()) {
      setActiveStep(step);
    }
  };

  const validateCurrentStep = (): boolean => {
    const currentStepId = steps[activeStep].id;
    const validationErrors = validateStep(formData, currentStepId);

    setErrors(validationErrors);
    return Object.keys(validationErrors).length === 0;
  };

  const handleNext = () => {
    if (validateCurrentStep() && activeStep < steps.length - 1) {
      setActiveStep(prev => prev + 1);
    }
  };

  const handlePrevious = () => {
    if (activeStep > 0) {
      setActiveStep(prev => prev - 1);
    }
  };

  const handleSave = async () => {
    if (!validateCurrentStep()) return;

    setIsSaving(true);
    try {
      await onSave(formData);
      setHasUnsavedChanges(false);
    } catch (error) {
      console.error('Save failed:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const renderStepContent = () => {
    switch (steps[activeStep].id) {
      case 'basic':
        return <BasicInfoStep formData={formData} onChange={setFormData} errors={errors} />;
      case 'params':
        return <ParametersStep formData={formData} onChange={setFormData} errors={errors} />;
      case 'code':
        return <CodeStep formData={formData} onChange={setFormData} errors={errors} />;
      case 'risk':
        return <RiskControlStep formData={formData} onChange={setFormData} errors={errors} />;
      case 'review':
        return <ReviewStep formData={formData} />;
      default:
        return null;
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* 步驟指示器 */}
      <StepIndicator
        steps={steps}
        activeStep={activeStep}
        onStepClick={handleStepChange}
      />

      {/* 表單內容 */}
      <div className="mt-8 bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        {renderStepContent()}
      </div>

      {/* 操作按鈕 */}
      <div className="mt-6 flex justify-between">
        <Button
          variant="outline"
          onClick={activeStep === 0 ? onCancel : handlePrevious}
          disabled={isSaving}
        >
          {activeStep === 0 ? '取消' : '上一步'}
        </Button>

        <div className="flex space-x-3">
          {hasUnsavedChanges && (
            <Button
              variant="outline"
              onClick={() => saveDraft(formData)}
            >
              保存草稿
            </Button>
          )}

          {activeStep < steps.length - 1 ? (
            <Button onClick={handleNext}>
              下一步
              <ArrowRightIcon className="h-5 w-5 ml-2" />
            </Button>
          ) : (
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ? '保存中...' : '保存策略'}
            </Button>
          )}
        </div>
      </div>

      {/* 離開確認 */}
      <UnsavedChangesDialog
        open={hasUnsavedChanges}
        onConfirm={() => {
          setHasUnsavedChanges(false);
          onCancel();
        }}
        onCancel={() => {}}
      />
    </div>
  );
};

// 代碼編輯器步驟
const CodeStep: React.FC<CodeStepProps> = ({ formData, onChange, errors }) => {
  const editorRef = useRef<any>(null);

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor;

    // 配置 TypeScript 支持
    monaco.languages.typescript.typescriptDefaults.setCompilerOptions({
      target: monaco.languages.typescript.ScriptTarget.ES2020,
      allowNonTsExtensions: true,
      moduleResolution: monaco.languages.typescript.ModuleResolutionKind.NodeJs,
      module: monaco.languages.typescript.ModuleKind.CommonJS,
      noEmit: true,
      esModuleInterop: true,
      jsx: monaco.languages.typescript.JsxEmit.React,
      reactNamespace: 'React',
      allowJs: true,
      typeRoots: ['node_modules/@types']
    });

    // 添加策略 API 類型定義
    monaco.languages.typescript.typescriptDefaults.addExtraLib(`
      declare module StrategyAPI {
        export interface MarketData {
          symbol: string;
          price: number;
          volume: number;
          timestamp: Date;
        }

        export function buy(symbol: string, quantity: number): Promise<TradeResult>;
        export function sell(symbol: string, quantity: number): Promise<TradeResult>;
        export function getMarketData(symbol: string): Promise<MarketData>;
      }
    `);
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          策略代碼
        </label>
        <div className="border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
          <MonacoEditor
            height="400px"
            language="typescript"
            theme={useTheme().mode === 'dark' ? 'vs-dark' : 'vs-light'}
            value={formData.code}
            onChange={(value) => onChange({ ...formData, code: value || '' })}
            onMount={handleEditorDidMount}
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              wordWrap: 'on',
              automaticLayout: true,
              scrollBeyondLastLine: false,
              suggestOnTriggerCharacters: true,
              quickSuggestions: true
            }}
          />
        </div>
        {errors.code && (
          <p className="mt-2 text-sm text-red-600">{errors.code}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            策略類型
          </label>
          <Select
            value={formData.type}
            onChange={(value) => onChange({ ...formData, type: value })}
          >
            <SelectItem value="trend">趨勢策略</SelectItem>
            <SelectItem value="arbitrage">套利策略</SelectItem>
            <SelectItem value="marketMaking">做市策略</SelectItem>
            <SelectItem value="meanReversion">均值回歸</SelectItem>
            <SelectItem value="custom">自定義</SelectItem>
          </Select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            交易所
          </label>
          <Select
            value={formData.exchange}
            onChange={(value) => onChange({ ...formData, exchange: value })}
          >
            <SelectItem value="binance">Binance</SelectItem>
            <SelectItem value="huobi">Huobi</SelectItem>
            <SelectItem value="okex">OKEx</SelectItem>
            <SelectItem value="coinbase">Coinbase</SelectItem>
          </Select>
        </div>
      </div>
    </div>
  );
};
```

### Redux 狀態管理
```typescript
// store/slices/strategiesSlice.ts
export interface StrategiesState {
  strategies: Record<string, Strategy>;
  list: {
    ids: string[];
    loading: boolean;
    error: string | null;
    filters: StrategyFilters;
    pagination: PaginationState;
    sort: SortState;
  };
  editor: {
    currentStrategy: Strategy | null;
    isEditing: boolean;
    hasUnsavedChanges: boolean;
    validationErrors: Record<string, string>;
  };
  operations: {
    selectedIds: string[];
    batchOperation: BatchOperation | null;
    isProcessing: boolean;
  };
}

export const strategiesSlice = createSlice({
  name: 'strategies',
  initialState,
  reducers: {
    // 列表管理
    setStrategies: (state, action) => {
      const strategies = action.payload;
      state.strategies = keyBy(strategies, 'id');
      state.list.ids = strategies.map(s => s.id);
    },
    addStrategy: (state, action) => {
      const strategy = action.payload;
      state.strategies[strategy.id] = strategy;
      state.list.ids.unshift(strategy.id);
    },
    updateStrategy: (state, action) => {
      const { id, updates } = action.payload;
      if (state.strategies[id]) {
        state.strategies[id] = { ...state.strategies[id], ...updates };
      }
    },
    deleteStrategy: (state, action) => {
      const id = action.payload;
      delete state.strategies[id];
      state.list.ids = state.list.ids.filter(sid => sid !== id);
    },
    setFilters: (state, action) => {
      state.list.filters = { ...state.list.filters, ...action.payload };
    },
    setSort: (state, action) => {
      state.list.sort = { ...state.list.sort, ...action.payload };
    },
    // 編輯器管理
    startEditing: (state, action) => {
      state.editor.currentStrategy = action.payload;
      state.editor.isEditing = true;
      state.editor.hasUnsavedChanges = false;
      state.editor.validationErrors = {};
    },
    updateEditingStrategy: (state, action) => {
      state.editor.hasUnsavedChanges = true;
      if (state.editor.currentStrategy) {
        state.editor.currentStrategy = {
          ...state.editor.currentStrategy,
          ...action.payload
        };
      }
    },
    setValidationErrors: (state, action) => {
      state.editor.validationErrors = action.payload;
    },
    // 批量操作
    selectStrategies: (state, action) => {
      state.operations.selectedIds = action.payload;
    },
    toggleStrategySelection: (state, action) => {
      const id = action.payload;
      const index = state.operations.selectedIds.indexOf(id);
      if (index > -1) {
        state.operations.selectedIds.splice(index, 1);
      } else {
        state.operations.selectedIds.push(id);
      }
    },
    setBatchOperation: (state, action) => {
      state.operations.batchOperation = action.payload;
    },
    clearSelection: (state) => {
      state.operations.selectedIds = [];
    }
  }
});

// RTK Query API
export const strategiesApi = createApi({
  reducerPath: 'strategiesApi',
  baseQuery: fetchBaseQuery({
    baseUrl: '/api/strategies',
    prepareHeaders: (headers, { getState }) => {
      const token = (getState() as RootState).auth.token;
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    }
  }),
  tagTypes: ['Strategy'],
  endpoints: (builder) => ({
    getStrategies: builder.query<StrategiesResponse, StrategiesQuery>({
      query: (params) => ({
        url: '',
        params
      }),
      providesTags: ['Strategy']
    }),
    getStrategy: builder.query<Strategy, string>({
      query: (id) => `/${id}`,
      providesTags: (result, error, id) => [{ type: 'Strategy', id }]
    }),
    createStrategy: builder.mutation<Strategy, CreateStrategyRequest>({
      query: (strategy) => ({
        url: '',
        method: 'POST',
        body: strategy
      }),
      invalidatesTags: ['Strategy']
    }),
    updateStrategy: builder.mutation<Strategy, UpdateStrategyRequest>({
      query: ({ id, ...patch }) => ({
        url: `/${id}`,
        method: 'PATCH',
        body: patch
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Strategy', id }]
    }),
    deleteStrategy: builder.mutation<void, string>({
      query: (id) => ({
        url: `/${id}`,
        method: 'DELETE'
      }),
      invalidatesTags: ['Strategy']
    }),
    executeBatchOperation: builder.mutation<void, BatchOperationRequest>({
      query: ({ operation, ids }) => ({
        url: '/batch',
        method: 'POST',
        body: { operation, ids }
      }),
      invalidatesTags: ['Strategy']
    })
  })
});
```

## 📊 預估工作量
| 子任務 | 預估時間 | 負責人 |
|--------|----------|--------|
| 策略列表實現 | 32小時 | 前端工程師 A |
| 篩選和搜索 | 16小時 | 前端工程師 B |
| 策略編輯器 | 32小時 | 前端工程師 A |
| 性能分析頁面 | 24小時 | 前端工程師 B |
| 批量操作功能 | 16小時 | 前端工程師 A |
| **總計** | **120小時** | |

## 🔗 依賴關係
- 前置任務：Task #4 (Dashboard主界面), Task #5 (實時數據可視化)
- 後續任務：Task #8 (報告生成系統)

## 📝 注意事項
1. 實現策略配置的版本控制
2. 考慮策略模板和繼承機制
3. 實現策略測試和調試工具
4. 處理大量策略的性能優化
5. 確保策略代碼的安全性檢查

## 🧪 測試要求
```typescript
// components/strategies/__tests__/StrategyEditor.test.tsx
describe('StrategyEditor', () => {
  test('renders all steps correctly', () => {
    render(<StrategyEditor onSave={jest.fn()} onCancel={jest.fn()} />);

    expect(screen.getByText('基本信息')).toBeInTheDocument();
    expect(screen.getByText('參數配置')).toBeInTheDocument();
    expect(screen.getByText('策略代碼')).toBeInTheDocument();
    expect(screen.getByText('風險控制')).toBeInTheDocument();
    expect(screen.getByText('確認提交')).toBeInTheDocument();
  });

  test('validates form before proceeding', async () => {
    render(<StrategyEditor onSave={jest.fn()} onCancel={jest.fn()} />);

    // 嘗試進入下一步而不填寫必填字段
    fireEvent.click(screen.getByText('下一步'));

    await waitFor(() => {
      expect(screen.getByText('策略名稱不能為空')).toBeInTheDocument();
    });
  });

  test('saves strategy successfully', async () => {
    const onSave = jest.fn().mockResolvedValue(undefined);
    render(<StrategyEditor onSave={onSave} onCancel={jest.fn()} />);

    // 填寫所有步驟
    fillBasicInfo();
    fillParameters();
    fillCode();
    fillRiskControl();

    // 保存
    fireEvent.click(screen.getByText('保存策略'));

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith(expect.objectContaining({
        name: 'Test Strategy',
        type: 'trend'
      }));
    });
  });

  test('handles unsaved changes warning', () => {
    render(<StrategyEditor onSave={jest.fn()} onCancel={jest.fn()} />);

    // 修改表單
    fireEvent.change(screen.getByLabelText('策略名稱'), {
      target: { value: 'Modified Strategy' }
    });

    // 嘗試取消
    fireEvent.click(screen.getByText('取消'));

    expect(screen.getByText('您有未保存的更改')).toBeInTheDocument();
  });
});
```

## 📚 相關文檔
- [Monaco Editor 文檔](https://microsoft.github.io/monaco-editor/)
- [React Hook Form 文檔](https://react-hook-form.com/)
- [Redux Toolkit 文檔](https://redux-toolkit.js.org/)
- [React Table v7 文檔](https://react-table.tanstack.com/)
- [React Virtualized 文檔](https://github.com/bvaughn/react-virtualized)