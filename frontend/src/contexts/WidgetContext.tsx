import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { Widget, Layout, Layouts, WidgetLayout, GridConfig } from '../types/widget';

// Widget actions
type WidgetAction =
  | { type: 'ADD_WIDGET'; payload: Widget }
  | { type: 'REMOVE_WIDGET'; payload: string }
  | { type: 'UPDATE_WIDGET'; payload: { id: string; updates: Partial<Widget> } }
  | { type: 'UPDATE_LAYOUT'; payload: Layouts }
  | { type: 'TOGGLE_EDIT_MODE' }
  | { type: 'RESET_LAYOUT' }
  | { type: 'LOAD_LAYOUT'; payload: { widgets: Widget[]; layouts: Layouts } };

// State interface
interface WidgetState {
  widgets: Widget[];
  layouts: Layouts;
  isEditMode: boolean;
  gridConfig: GridConfig;
}

// Initial grid configuration
const initialGridConfig: GridConfig = {
  cols: { lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 },
  rowHeight: 60,
  margin: [16, 16],
  containerPadding: [16, 16],
  isDraggable: false,
  isResizable: false,
  compactType: 'vertical',
};

// Get saved layouts from localStorage
const getSavedLayouts = (): Layouts => {
  const saved = localStorage.getItem('dashboard-layouts');
  if (saved) {
    try {
      return JSON.parse(saved);
    } catch (e) {
      console.error('Error parsing saved layouts:', e);
    }
  }

  // Return default layouts
  return {
    lg: [],
    md: [],
    sm: [],
    xs: [],
    xxs: [],
  };
};

// Get saved widgets from localStorage
const getSavedWidgets = (): Widget[] => {
  const saved = localStorage.getItem('dashboard-widgets');
  if (saved) {
    try {
      return JSON.parse(saved);
    } catch (e) {
      console.error('Error parsing saved widgets:', e);
    }
  }

  return [];
};

// Initial state
const initialState: WidgetState = {
  widgets: getSavedWidgets(),
  layouts: getSavedLayouts(),
  isEditMode: false,
  gridConfig: initialGridConfig,
};

// Reducer function
function widgetReducer(state: WidgetState, action: WidgetAction): WidgetState {
  switch (action.type) {
    case 'ADD_WIDGET': {
      const newWidget = action.payload;
      const newWidgets = [...state.widgets, newWidget];

      // Add layout items for each breakpoint
      const newLayouts = { ...state.layouts };
      const breakpoints = ['lg', 'md', 'sm', 'xs', 'xxs'] as const;

      breakpoints.forEach(bp => {
        const defaultSize = getDefaultWidgetSize(newWidget.type, bp);
        const layoutItem = {
          i: newWidget.id,
          x: 0,
          y: Infinity, // Place at bottom
          w: defaultSize.w,
          h: defaultSize.h,
          minW: 2,
          minH: 2,
        };
        newLayouts[bp] = [...newLayouts[bp], layoutItem];
      });

      return {
        ...state,
        widgets: newWidgets,
        layouts: newLayouts,
      };
    }

    case 'REMOVE_WIDGET': {
      const widgetId = action.payload;
      const newWidgets = state.widgets.filter(w => w.id !== widgetId);

      // Remove from layouts
      const newLayouts = { ...state.layouts };
      const breakpoints = ['lg', 'md', 'sm', 'xs', 'xxs'] as const;

      breakpoints.forEach(bp => {
        newLayouts[bp] = newLayouts[bp].filter(l => l.i !== widgetId);
      });

      return {
        ...state,
        widgets: newWidgets,
        layouts: newLayouts,
      };
    }

    case 'UPDATE_WIDGET':
      return {
        ...state,
        widgets: state.widgets.map(w =>
          w.id === action.payload.id
            ? { ...w, ...action.payload.updates }
            : w
        ),
      };

    case 'UPDATE_LAYOUT':
      return {
        ...state,
        layouts: action.payload,
      };

    case 'TOGGLE_EDIT_MODE':
      return {
        ...state,
        isEditMode: !state.isEditMode,
        gridConfig: {
          ...state.gridConfig,
          isDraggable: !state.isEditMode,
          isResizable: !state.isEditMode,
        },
      };

    case 'RESET_LAYOUT':
      return {
        ...state,
        layouts: getSavedLayouts(),
        widgets: getSavedWidgets(),
      };

    case 'LOAD_LAYOUT':
      return {
        ...state,
        widgets: action.payload.widgets,
        layouts: action.payload.layouts,
      };

    default:
      return state;
  }
}

// Helper function to get default widget size for breakpoint
function getDefaultWidgetSize(type: string, breakpoint: string): { w: number; h: number } {
  const baseSizes: Record<string, { w: number; h: number }> = {
    'strategy-overview': { w: 4, h: 3 },
    'performance-chart': { w: 8, h: 4 },
    'market-monitor': { w: 6, h: 4 },
    'trading-list': { w: 6, h: 5 },
    'notification-center': { w: 4, h: 3 },
    'custom': { w: 4, h: 3 },
  };

  const base = baseSizes[type] || baseSizes['custom'];

  // Adjust for breakpoint
  const multiplier = {
    lg: 1,
    md: 0.8,
    sm: 0.6,
    xs: 0.5,
    xxs: 0.4,
  }[breakpoint] || 1;

  return {
    w: Math.max(2, Math.round(base.w * multiplier)),
    h: Math.max(2, Math.round(base.h * multiplier)),
  };
}

// Create context
const WidgetContext = createContext<{
  state: WidgetState;
  dispatch: React.Dispatch<WidgetAction>;
  addWidget: (widget: Omit<Widget, 'id'>) => void;
  removeWidget: (id: string) => void;
  updateWidget: (id: string, updates: Partial<Widget>) => void;
  toggleEditMode: () => void;
  saveLayout: () => void;
} | null>(null);

// Context provider
export function WidgetProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(widgetReducer, initialState);

  // Save to localStorage when state changes
  useEffect(() => {
    if (state.widgets.length > 0) {
      localStorage.setItem('dashboard-widgets', JSON.stringify(state.widgets));
      localStorage.setItem('dashboard-layouts', JSON.stringify(state.layouts));
    }
  }, [state.widgets, state.layouts]);

  const addWidget = (widget: Omit<Widget, 'id'>) => {
    const newWidget: Widget = {
      ...widget,
      id: `widget-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    };
    dispatch({ type: 'ADD_WIDGET', payload: newWidget });
  };

  const removeWidget = (id: string) => {
    dispatch({ type: 'REMOVE_WIDGET', payload: id });
  };

  const updateWidget = (id: string, updates: Partial<Widget>) => {
    dispatch({ type: 'UPDATE_WIDGET', payload: { id, updates } });
  };

  const toggleEditMode = () => {
    dispatch({ type: 'TOGGLE_EDIT_MODE' });
  };

  const saveLayout = () => {
    // Layouts are already saved automatically
    console.log('Layout saved');
  };

  return (
    <WidgetContext.Provider
      value={{
        state,
        dispatch,
        addWidget,
        removeWidget,
        updateWidget,
        toggleEditMode,
        saveLayout,
      }}
    >
      {children}
    </WidgetContext.Provider>
  );
}

// Hook to use widget context
export function useWidgets() {
  const context = useContext(WidgetContext);
  if (!context) {
    throw new Error('useWidgets must be used within a WidgetProvider');
  }
  return context;
}