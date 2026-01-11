import React from 'react';
import { WidgetProvider, useWidgets } from '../contexts/WidgetContext';
import { WidgetGrid } from '../components/widgets/WidgetGrid';
import { WidgetManager } from '../components/widgets/WidgetManager';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Plus, GripVertical, Save, Grid3X3, Settings, Layers } from 'lucide-react';

export default function WidgetDashboardDemo() {
  return (
    <WidgetProvider>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        {/* Header */}
        <header className="border-b bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm sticky top-0 z-30">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <Grid3X3 className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold">響應式網格小工具系統</h1>
                  <p className="text-sm text-muted-foreground">
                    任務 #64: Responsive Grid Widget Management
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Badge variant="secondary" className="hidden sm:flex">
                  <Layers className="h-3 w-3 mr-1" />
                  拖拽調整
                </Badge>
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
          {/* Toolbar */}
          <div className="mb-6">
            <DashboardToolbar />
          </div>

          {/* Features card */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <GripVertical className="h-4 w-4" />
                  拖拽排序
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <p className="text-sm text-muted-foreground">
                  在編輯模式下，可以自由拖拽小工具重新排列佈局，支持實時預覽
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Settings className="h-4 w-4" />
                  響應式調整
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <p className="text-sm text-muted-foreground">
                  小工具會根據屏幕大小自動調整，支持桌面、平板和手機端
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Save className="h-4 w-4" />
                  本地存儲
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <p className="text-sm text-muted-foreground">
                  佈局自動保存到瀏覽器本地存儲，刷新頁面後自動恢復
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Widget Grid */}
          <div className="bg-white dark:bg-slate-900 rounded-lg shadow-sm border p-4">
            <WidgetGrid />
          </div>
        </main>

        {/* Footer */}
        <footer className="mt-12 py-6 border-t bg-white/50 dark:bg-slate-900/50">
          <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
            <p>使用 React Grid Layout 構建的響應式小工具管理系統</p>
          </div>
        </footer>
      </div>
    </WidgetProvider>
  );
}

function DashboardToolbar() {
  const { state, toggleEditMode } = useWidgets();

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-semibold">
              {state.isEditMode ? (
                <span className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                  編輯模式
                </span>
              ) : (
                '查看模式'
              )}
            </h2>

            {state.isEditMode && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <GripVertical className="h-4 w-4" />
                <span className="hidden sm:inline">
                  拖拽移動小工具，拖拽右下角調整大小
                </span>
              </div>
            )}

            <Badge variant="outline" className="hidden md:flex">
              {state.widgets.length} 個小工具
            </Badge>
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

            {!state.isEditMode && state.widgets.length === 0 && (
              <WidgetManager>
                <Button size="sm" variant="outline" className="gap-2">
                  <Plus className="h-4 w-4" />
                  開始添加
                </Button>
              </WidgetManager>
            )}
          </div>
        </div>

        {/* Quick tips */}
        {state.isEditMode && (
          <div className="mt-3 pt-3 border-t text-xs text-muted-foreground space-y-1">
            <div>• 點擊小工具右上角的 X 刪除小工具</div>
            <div>• 點擊折疊圖標最小化小工具</div>
            <div>• 點擊全屏圖標查看小工具詳細內容</div>
            <div>• 所有更改會自動保存到本地存儲</div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}