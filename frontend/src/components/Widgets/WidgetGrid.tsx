import React, { useRef, useCallback } from 'react';
import { Responsive, WidthProvider, Layout } from 'react-grid-layout';
import { useWidgets } from '../../contexts/WidgetContext';
import { WidgetWrapper } from './WidgetWrapper';
import { StrategyOverviewWidget } from './widgets/StrategyOverviewWidget';
import { PerformanceChartWidget } from './widgets/PerformanceChartWidget';
import { MarketMonitorWidget } from './widgets/MarketMonitorWidget';
import { TradingListWidget } from './widgets/TradingListWidget';
import { NotificationCenterWidget } from './widgets/NotificationCenterWidget';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

const ResponsiveGridLayout = WidthProvider(Responsive);

interface WidgetGridProps {
  className?: string;
}

export function WidgetGrid({ className }: WidgetGridProps) {
  const { state, updateWidget, removeWidget, toggleEditMode } = useWidgets();
  const gridRef = useRef<Responsive>(null);

  // Handle layout change
  const handleLayoutChange = useCallback(
    (layout: Layout[], allLayouts: Record<string, Layout[]>) => {
      // Update layouts in context
      if (state.dispatch) {
        state.dispatch({
          type: 'UPDATE_LAYOUT',
          payload: allLayouts as any,
        });
      }
    },
    [state.dispatch]
  );

  // Render widget based on type
  const renderWidget = useCallback((widgetId: string) => {
    const widget = state.widgets.find(w => w.id === widgetId);
    if (!widget) return null;

    const onRemove = (id: string) => removeWidget(id);
    const onToggleCollapse = (id: string) =>
      updateWidget(id, { isCollapsed: !widget.isCollapsed });
    const onSettings = (id: string) => {
      // TODO: Open settings modal
      console.log('Settings for widget:', id);
    };

    const widgetContent = () => {
      switch (widget.type) {
        case 'strategy-overview':
          return <StrategyOverviewWidget widget={widget} />;
        case 'performance-chart':
          return <PerformanceChartWidget widget={widget} />;
        case 'market-monitor':
          return <MarketMonitorWidget widget={widget} />;
        case 'trading-list':
          return <TradingListWidget widget={widget} />;
        case 'notification-center':
          return <NotificationCenterWidget widget={widget} />;
        default:
          return (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              未知的小工具類型
            </div>
          );
      }
    };

    return (
      <div key={widgetId} className="h-full">
        <WidgetWrapper
          widget={widget}
          isEditMode={state.isEditMode}
          onRemove={onRemove}
          onToggleCollapse={onToggleCollapse}
          onSettings={onSettings}
        >
          {widgetContent()}
        </WidgetWrapper>
      </div>
    );
  }, [state.widgets, state.isEditMode, removeWidget, updateWidget]);

  // Prepare breakpoints
  const breakpoints = {
    lg: 1200,
    md: 996,
    sm: 768,
    xs: 480,
    xxs: 0,
  };

  // Prepare columns for each breakpoint
  const cols = {
    lg: 12,
    md: 10,
    sm: 6,
    xs: 4,
    xxs: 2,
  };

  return (
    <div className={`w-full ${className}`}>
      <ResponsiveGridLayout
        ref={gridRef}
        className="layout"
        layouts={state.layouts}
        breakpoints={breakpoints}
        cols={cols}
        rowHeight={60}
        margin={[16, 16]}
        containerPadding={[16, 16]}
        isDraggable={state.isEditMode}
        isResizable={state.isEditMode}
        compactType="vertical"
        preventCollision={false}
        onLayoutChange={handleLayoutChange}
        useCSSTransforms={true}
        // Performance optimizations
        measureBeforeMount={true}
        resizeHandles={['se']}
        resizeHandle={
          state.isEditMode ? (
            <div className="absolute bottom-0 right-0 w-4 h-4 bg-blue-500 cursor-se-resize opacity-75 rounded-tl-lg" />
          ) : null
        }
      >
        {state.widgets.map(widget => widget.id)}
      </ResponsiveGridLayout>

      {/* Render widgets separately to optimize performance */}
      {state.widgets.map(widget => (
        <div key={widget.id} style={{ display: 'none' }}>
          {renderWidget(widget.id)}
        </div>
      ))}

      {/* In edit mode, show placeholder for empty spots */}
      {state.isEditMode && (
        <div className="fixed bottom-4 right-4 z-40">
          <div className="bg-blue-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
            <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
            <span className="text-sm">編輯模式</span>
            <button
              onClick={toggleEditMode}
              className="ml-2 text-white/80 hover:text-white"
            >
              完成
            </button>
          </div>
        </div>
      )}
    </div>
  );
}