import { useState, useCallback } from 'react';
import React from 'react';

// Toast 接口定义
export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
}

// useToast Hook 返回类型
interface UseToastReturn {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  clearAllToasts: () => void;
}

// Toast 供应商组件
interface ToastProviderProps {
  children: React.ReactNode;
}

// 全局 Toast 状态
let globalToasts: Toast[] = [];
let globalListeners: (() => void)[] = [];

// 更新通知
const notifyListeners = () => {
  globalListeners.forEach(listener => listener());
};

// useToast Hook
export const useToast = (): UseToastReturn => {
  const [, forceUpdate] = useState({});

  const updateToasts = useCallback(() => {
    forceUpdate({});
  }, []);

  // 注册监听器
  useState(() => {
    globalListeners.push(updateToasts);
    return () => {
      globalListeners = globalListeners.filter(l => l !== updateToasts);
    };
  });

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newToast: Toast = {
      ...toast,
      id,
      duration: toast.duration ?? 3000
    };

    globalToasts.push(newToast);
    notifyListeners();

    // 自动移除
    if (newToast.duration && newToast.duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, newToast.duration);
    }
  }, []);

  const removeToast = useCallback((id: string) => {
    globalToasts = globalToasts.filter(t => t.id !== id);
    notifyListeners();
  }, []);

  const clearAllToasts = useCallback(() => {
    globalToasts = [];
    notifyListeners();
  }, []);

  return {
    toasts: globalToasts,
    addToast,
    removeToast,
    clearAllToasts
  };
};

// Toast 组件
export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useToast();

  const getToastStyles = (type: Toast['type']) => {
    switch (type) {
      case 'success':
        return 'bg-green-500';
      case 'error':
        return 'bg-red-500';
      case 'warning':
        return 'bg-yellow-500';
      case 'info':
        return 'bg-blue-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getToastIcon = (type: Toast['type']) => {
    switch (type) {
      case 'success':
        return (
          <span className="w-5 h-5 flex items-center justify-center text-white font-bold">OK</span>
        );
      case 'error':
        return (
          <span className="w-5 h-5 flex items-center justify-center text-white font-bold">X</span>
        );
      case 'warning':
        return (
          <span className="w-5 h-5 flex items-center justify-center text-white font-bold">!</span>
        );
      case 'info':
        return (
          <span className="w-5 h-5 flex items-center justify-center text-white font-bold">i</span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`${getToastStyles(toast.type)} text-white px-4 py-3 rounded-lg shadow-lg flex items-center space-x-3 min-w-[300px] max-w-md transform transition-all duration-300 ease-in-out`}
        >
          <div className="flex-shrink-0">
            {getToastIcon(toast.type)}
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium">{toast.message}</p>
          </div>
          <button
            onClick={() => removeToast(toast.id)}
            className="flex-shrink-0 text-white hover:text-gray-200 transition-colors"
            aria-label="Close toast"
          >
            <span className="w-4 h-4 flex items-center justify-center text-white font-bold">×</span>
          </button>
        </div>
      ))}
    </div>
  );
};