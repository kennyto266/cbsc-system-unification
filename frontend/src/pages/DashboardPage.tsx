import React from 'react';
import { WidgetProvider } from '../contexts/WidgetContext';
import { WidgetGrid } from '../components/widgets/WidgetGrid';
import { WidgetManager } from '../components/widgets/WidgetManager';
import { Button } from '../components/ui/button';
import { Plus, GripVertical, Save } from 'lucide-react';

export default function DashboardPage() {
  return (
    <WidgetProvider>
      <div className="min-h-screen bg-background">
        {/* Header */}
        <header className="border-b bg-card">
          <div className="container mx-auto px-4 py-3">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold">策略管理儀表板</h1>
                <p className="text-sm text-muted-foreground">
                  自定義您的量化交易策略監控界面
                </p>
              </div>

              <div className="flex items-center gap-2">
                <WidgetManager>
                  <Button size="sm" className="gap-2">
                    <Plus className="h-4 w-4" />
                    添加小工具
                  </Button>
                </WidgetManager>
              </div>
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className="container mx-auto px-4 py-6">
          <div className="mb-4">
            <DashboardToolbar />
          </div>

          <WidgetGrid />
        </main>
      </div>
    </WidgetProvider>
  );
}

function DashboardToolbar() {
  const { state, toggleEditMode, saveLayout } = useWidgets();

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-semibold">
          {state.isEditMode ? '編輯模式' : '查看模式'}
        </h2>

        {state.isEditMode && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <GripVertical className="h-4 w-4" />
            <span>拖拽移動小工具</span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant={state.isEditMode ? 'default' : 'outline'}
          size="sm"
          onClick={toggleEditMode}
          className="gap-2"
        >
          <GripVertical className="h-4 w-4" />
          {state.isEditMode ? '完成編輯' : '編輯佈局'}
        </Button>

        {state.isEditMode && (
          <Button variant="outline" size="sm" onClick={saveLayout}>
            <Save className="h-4 w-4 mr-2" />
            保存佈局
          </Button>
        )}
      </div>
    </div>
  );
}