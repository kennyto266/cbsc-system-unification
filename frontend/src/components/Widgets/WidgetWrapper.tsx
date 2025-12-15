import React from 'react';
import { Rnd } from 'react-rnd';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import {
  Maximize2,
  Minimize2,
  Settings,
  X,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { Widget } from '../../types/widget';

interface WidgetWrapperProps {
  widget: Widget;
  children: React.ReactNode;
  isEditMode: boolean;
  onRemove: (id: string) => void;
  onToggleCollapse: (id: string) => void;
  onSettings: (id: string) => void;
}

export function WidgetWrapper({
  widget,
  children,
  isEditMode,
  onRemove,
  onToggleCollapse,
  onSettings
}: WidgetWrapperProps) {
  const [isFullscreen, setIsFullscreen] = React.useState(false);

  const handleRemove = () => {
    if (window.confirm('確定要刪除此小工具嗎？')) {
      onRemove(widget.id);
    }
  };

  return (
    <>
      {/* Regular widget view */}
      <Card
        className={`h-full transition-all duration-300 ${
          isEditMode ? 'ring-2 ring-blue-500' : ''
        } ${
          widget.isCollapsed ? 'h-auto' : ''
        }`}
        style={widget.config?.color ? {
          borderLeftColor: widget.config.color,
          borderLeftWidth: '4px'
        } : {}}
      >
        <CardHeader
          className="pb-2 cursor-move select-none"
          style={{
            padding: widget.isCollapsed ? '0.75rem' : undefined
          }}
        >
          <CardTitle className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <span className="text-lg">
                {widgetRegistry[widget.type]?.icon || '📦'}
              </span>
              <span>{widget.title}</span>
            </div>

            <div className="flex items-center gap-1">
              {/* Collapse/Expand button */}
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={() => onToggleCollapse(widget.id)}
              >
                {widget.isCollapsed ? (
                  <ChevronUp className="h-3 w-3" />
                ) : (
                  <ChevronDown className="h-3 w-3" />
                )}
              </Button>

              {/* Fullscreen button */}
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={() => setIsFullscreen(true)}
              >
                <Maximize2 className="h-3 w-3" />
              </Button>

              {/* Settings button */}
              {isEditMode && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0"
                  onClick={() => onSettings(widget.id)}
                >
                  <Settings className="h-3 w-3" />
                </Button>
              )}

              {/* Remove button - only in edit mode */}
              {isEditMode && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0 text-red-500 hover:text-red-700"
                  onClick={handleRemove}
                >
                  <X className="h-3 w-3" />
                </Button>
              )}
            </div>
          </CardTitle>
        </CardHeader>

        {/* Widget content */}
        {!widget.isCollapsed && (
          <CardContent className="pt-0">
            {children}
          </CardContent>
        )}

        {/* Drag handle overlay when in edit mode */}
        {isEditMode && (
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute bottom-2 right-2 pointer-events-auto">
              <div className="w-4 h-4 bg-blue-500 rounded-full opacity-50" />
            </div>
          </div>
        )}
      </Card>

      {/* Fullscreen modal */}
      {isFullscreen && (
        <div className="fixed inset-0 z-50 bg-background/95 backdrop-blur-sm">
          <div className="h-full flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">{widget.title}</h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsFullscreen(false)}
              >
                <Minimize2 className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex-1 p-4 overflow-auto">
              {children}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// Import widget registry at the bottom to avoid circular dependencies
import { widgetRegistry } from './WidgetRegistry';