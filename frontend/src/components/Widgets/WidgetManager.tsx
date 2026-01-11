import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { ScrollArea } from '../ui/scroll-area';
import { useWidgets } from '../../contexts/WidgetContext';
import { widgetRegistry, getWidgetCategories } from './WidgetRegistry';
import { Plus, Settings, Download, Upload } from 'lucide-react';

interface WidgetManagerProps {
  children: React.ReactNode;
}

export function WidgetManager({ children }: WidgetManagerProps) {
  const { addWidget, state } = useWidgets();
  const [isOpen, setIsOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const categories = getWidgetCategories();

  const handleAddWidget = (type: string) => {
    const widgetConfig = widgetRegistry[type];
    if (widgetConfig) {
      addWidget({
        type: widgetConfig.type as any,
        title: widgetConfig.title,
        config: {
          color: undefined,
          refreshInterval: 5,
        },
      });
      setIsOpen(false);
    }
  };

  const exportLayout = () => {
    const layoutData = {
      widgets: state.widgets,
      layouts: state.layouts,
      timestamp: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(layoutData, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dashboard-layout-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const importLayout = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const layoutData = JSON.parse(e.target?.result as string);
          if (layoutData.widgets && layoutData.layouts) {
            state.dispatch?.({
              type: 'LOAD_LAYOUT',
              payload: {
                widgets: layoutData.widgets,
                layouts: layoutData.layouts,
              },
            });
            setIsSettingsOpen(false);
          }
        } catch (error) {
          console.error('Error importing layout:', error);
          alert('導入佈局失敗，請檢查文件格式');
        }
      };
      reader.readAsText(file);
    }
  };

  return (
    <>
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogTrigger asChild>
          {children}
        </DialogTrigger>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>添加小工具</DialogTitle>
          </DialogHeader>

          <div className="flex gap-4">
            {/* Category filter */}
            <div className="w-48 space-y-2">
              <div className="font-medium text-sm">分類</div>
              <Button
                variant={selectedCategory === 'all' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setSelectedCategory('all')}
                className="w-full justify-start"
              >
                全部 ({Object.keys(widgetRegistry).length})
              </Button>
              {categories.map(category => {
                const count = Object.values(widgetRegistry).filter(
                  w => w.category === category
                ).length;
                return (
                  <Button
                    key={category}
                    variant={selectedCategory === category ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setSelectedCategory(category)}
                    className="w-full justify-start"
                  >
                    {category} ({count})
                  </Button>
                );
              })}
            </div>

            {/* Widget list */}
            <ScrollArea className="flex-1">
              <div className="grid grid-cols-2 gap-3 pr-4">
                {Object.entries(widgetRegistry)
                  .filter(
                    ([_, config]) =>
                      selectedCategory === 'all' || config.category === selectedCategory
                  )
                  .map(([key, config]) => (
                    <Card
                      key={key}
                      className="p-4 cursor-pointer hover:shadow-md transition-shadow"
                      onClick={() => handleAddWidget(key)}
                    >
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-2xl">{config.icon}</span>
                        <div className="flex-1">
                          <h3 className="font-medium">{config.title}</h3>
                          {config.category && (
                            <Badge variant="secondary" className="text-xs">
                              {config.category}
                            </Badge>
                          )}
                        </div>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        尺寸: {config.defaultSize.w} × {config.defaultSize.h}
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full mt-3"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAddWidget(key);
                        }}
                      >
                        <Plus className="h-3 w-3 mr-1" />
                        添加
                      </Button>
                    </Card>
                  ))}
              </div>
            </ScrollArea>
          </div>
        </DialogContent>
      </Dialog>

      {/* Settings dialog */}
      <Dialog open={isSettingsOpen} onOpenChange={setIsSettingsOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>佈局設置</DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div className="text-sm text-muted-foreground">
              當前佈局包含 {state.widgets.length} 個小工具
            </div>

            <div className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={exportLayout}
              >
                <Download className="h-4 w-4 mr-2" />
                導出佈局
              </Button>

              <div>
                <input
                  type="file"
                  accept=".json"
                  onChange={importLayout}
                  className="hidden"
                  id="import-layout"
                />
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => document.getElementById('import-layout')?.click()}
                >
                  <Upload className="h-4 w-4 mr-2" />
                  導入佈局
                </Button>
              </div>

              <Button
                variant="destructive"
                className="w-full justify-start"
                onClick={() => {
                  if (window.confirm('確定要重置佈局嗎？這將清除所有小工具。')) {
                    state.dispatch?.({ type: 'RESET_LAYOUT' });
                    setIsSettingsOpen(false);
                  }
                }}
              >
                重置佈局
              </Button>
            </div>

            <div className="text-xs text-muted-foreground pt-2 border-t">
              <div>網格配置：</div>
              <div>• 大屏幕: 12 列</div>
              <div>• 中等屏幕: 10 列</div>
              <div>• 小屏幕: 6 列</div>
              <div>• 手機: 4 列</div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Floating action button for settings */}
      <div className="fixed bottom-4 left-4 z-40">
        <Dialog open={isSettingsOpen} onOpenChange={setIsSettingsOpen}>
          <DialogTrigger asChild>
            <Button size="sm" variant="outline" className="shadow-lg">
              <Settings className="h-4 w-4" />
            </Button>
          </DialogTrigger>
        </Dialog>
      </div>
    </>
  );
}