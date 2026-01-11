import React, { createContext, useContext, useState, useCallback } from 'react';

interface LoadingState {
  global: boolean;
  charts: boolean;
  strategies: boolean;
  refetch: boolean;
}

interface LoadingContextType {
  loading: LoadingState;
  setLoading: (component: keyof LoadingState, value: boolean) => void;
  showLoading: (component?: keyof LoadingState) => void;
  hideLoading: (component?: keyof LoadingState) => void;
  isLoading: (component?: keyof LoadingState) => boolean;
}

const LoadingContext = createContext<LoadingContextType | undefined>(undefined);

export const LoadingProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [loading, setLoadingState] = useState<LoadingState>({
    global: false,
    charts: false,
    strategies: false,
    refetch: false
  });

  const setLoading = useCallback((component: keyof LoadingState, value: boolean) => {
    setLoadingState(prev => ({ ...prev, [component]: value }));
  }, []);

  const showLoading = useCallback((component: keyof LoadingState = 'global') => {
    setLoading(component, true);
  }, [setLoading]);

  const hideLoading = useCallback((component: keyof LoadingState = 'global') => {
    setLoading(component, false);
  }, [setLoading]);

  const isLoading = useCallback((component: keyof LoadingState = 'global'): boolean => {
    if (component === 'global') {
      return loading.global || loading.charts || loading.strategies || loading.refetch;
    }
    return loading[component];
  }, [loading]);

  return (
    <LoadingContext.Provider value={{
      loading,
      setLoading,
      showLoading,
      hideLoading,
      isLoading
    }}>
      {children}
    </LoadingContext.Provider>
  );
};

export const useLoading = (): LoadingContextType => {
  const context = useContext(LoadingContext);
  if (!context) {
    throw new Error('useLoading must be used within a LoadingProvider');
  }
  return context;
};

// Global Loading Overlay Component
export const LoadingOverlay: React.FC<{
  show?: boolean;
  message?: string;
  transparent?: boolean;
}> = ({ show, message = '載入中...', transparent = false }) => {
  const { isLoading } = useLoading();
  const shouldShow = show !== undefined ? show : isLoading();

  if (!shouldShow) return null;

  return (
    <div className={`fixed inset-0 z-50 flex items-center justify-center ${
      transparent ? 'bg-black bg-opacity-30' : 'bg-white bg-opacity-90'
    } backdrop-blur-sm`}>
      <div className="flex flex-col items-center space-y-4">
        <div className="relative">
          <div className="w-12 h-12 border-4 border-blue-200 rounded-full animate-spin"></div>
          <div className="absolute top-0 left-0 w-12 h-12 border-4 border-blue-600 rounded-full animate-spin border-t-transparent"></div>
        </div>
        <p className="text-gray-700 font-medium">{message}</p>
      </div>
    </div>
  );
};

// Component-specific loading indicators
export const ChartLoadingIndicator: React.FC<{ show?: boolean }> = ({ show }) => {
  const { isLoading } = useLoading();
  const shouldShow = show !== undefined ? show : isLoading('charts');

  if (!shouldShow) return null;

  return (
    <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 z-10">
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 border-2 border-blue-200 rounded-full animate-spin"></div>
        <div className="w-8 h-8 border-2 border-blue-600 rounded-full animate-spin border-t-transparent absolute"></div>
        <span className="text-sm text-gray-600 ml-12">更新圖表...</span>
      </div>
    </div>
  );
};

export const StrategyLoadingIndicator: React.FC<{ show?: boolean }> = ({ show }) => {
  const { isLoading } = useLoading();
  const shouldShow = show !== undefined ? show : isLoading('strategies');

  if (!shouldShow) return null;

  return (
    <div className="flex items-center justify-center py-8">
      <div className="flex items-center space-x-3">
        <div className="w-6 h-6 border-2 border-gray-200 rounded-full animate-spin"></div>
        <div className="w-6 h-6 border-2 border-gray-600 rounded-full animate-spin border-t-transparent absolute"></div>
        <span className="text-sm text-gray-600 ml-10">載入策略資料...</span>
      </div>
    </div>
  );
};

export const RefetchLoadingIndicator: React.FC<{
  show?: boolean;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
}> = ({ show, position = 'top-right' }) => {
  const { isLoading } = useLoading();
  const shouldShow = show !== undefined ? show : isLoading('refetch');

  if (!shouldShow) return null;

  const positionClasses = {
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4'
  };

  return (
    <div className={`fixed ${positionClasses[position]} z-40 flex items-center space-x-2 bg-white rounded-lg shadow-lg px-4 py-2`}>
      <div className="w-4 h-4 border border-blue-200 rounded-full animate-spin"></div>
      <div className="w-4 h-4 border border-blue-600 rounded-full animate-spin border-t-transparent absolute"></div>
      <span className="text-sm text-gray-700 ml-8">更新中...</span>
    </div>
  );
};

// Skeleton loaders for different content types
export const StrategyCardSkeleton: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6 animate-pulse">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <div className="h-5 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
        <div className="h-6 bg-gray-200 rounded w-20"></div>
      </div>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="h-4 bg-gray-200 rounded w-full mb-1"></div>
          <div className="h-6 bg-gray-200 rounded w-3/4"></div>
        </div>
        <div>
          <div className="h-4 bg-gray-200 rounded w-full mb-1"></div>
          <div className="h-6 bg-gray-200 rounded w-3/4"></div>
        </div>
      </div>
      <div className="h-10 bg-gray-200 rounded"></div>
    </div>
  );
};

export const ChartSkeleton: React.FC<{ height?: number }> = ({ height = 300 }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm p-4 animate-pulse">
      <div className="flex justify-between items-center mb-4">
        <div className="h-5 bg-gray-200 rounded w-1/3"></div>
        <div className="flex space-x-2">
          <div className="h-8 bg-gray-200 rounded w-20"></div>
          <div className="h-8 bg-gray-200 rounded w-20"></div>
        </div>
      </div>
      <div className="relative" style={{ height: `${height}px` }}>
        <div className="absolute inset-0 bg-gray-100 rounded"></div>
        <div className="absolute bottom-0 left-0 right-0 h-20 bg-gray-200 rounded-b"></div>
        <div className="absolute top-0 bottom-20 left-8 w-1 bg-gray-200"></div>
        <div className="absolute top-0 bottom-20 right-8 w-1 bg-gray-200"></div>
      </div>
    </div>
  );
};

export const PerformanceSummarySkeleton: React.FC = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="bg-white rounded-lg shadow-sm p-6 animate-pulse">
          <div className="flex items-center justify-between mb-2">
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
          </div>
          <div className="h-8 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-full"></div>
        </div>
      ))}
    </div>
  );
};

export default LoadingOverlay;