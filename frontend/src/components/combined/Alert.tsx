import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { AlertCircle, CheckCircle, Info, X, AlertTriangle } from 'lucide-react';

// Alert 变体样式
const alertVariants = cva(
  'relative w-full rounded-lg border p-4 transition-all',
  {
    variants: {
      variant: {
        default: 'bg-background text-foreground border-border',
        info: 'border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-800 dark:bg-blue-950 dark:text-blue-200',
        success: 'border-green-200 bg-green-50 text-green-800 dark:border-green-800 dark:bg-green-950 dark:text-green-200',
        warning: 'border-yellow-200 bg-yellow-50 text-yellow-800 dark:border-yellow-800 dark:bg-yellow-950 dark:text-yellow-200',
        error: 'border-red-200 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

// Alert Props 接口
export interface AlertProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof alertVariants> {
  title?: string;
  icon?: React.ReactNode;
  closable?: boolean;
  onClose?: () => void;
}

// Alert 组件
export const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant, title, children, icon, closable = false, onClose, ...props }, ref) => {
    const defaultIcons = {
      info: <Info className="h-4 w-4" />,
      success: <CheckCircle className="h-4 w-4" />,
      warning: <AlertTriangle className="h-4 w-4" />,
      error: <AlertCircle className="h-4 w-4" />,
      default: <Info className="h-4 w-4" />,
    };

    return (
      <div
        ref={ref}
        role="alert"
        className={cn(alertVariants({ variant }), className)}
        {...props}
      >
        <div className="flex items-start gap-3">
          {icon || defaultIcons[variant || 'default']}
          <div className="flex-1 min-w-0">
            {title && <h5 className="font-medium mb-1">{title}</h5>}
            {children && <div className="text-sm">{children}</div>}
          </div>
          {closable && (
            <button
              onClick={onClose}
              className="inline-flex items-center justify-center rounded-md p-1 hover:bg-black/10 dark:hover:bg-white/10 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    );
  }
);
Alert.displayName = 'Alert';

// Toast 相关类型和组件
export interface ToastProps {
  id?: string;
  title?: string;
  description?: string;
  variant?: 'info' | 'success' | 'warning' | 'error';
  duration?: number;
  action?: React.ReactNode;
  onDismiss?: () => void;
}

export interface ToastActionProps {
  altText?: string;
  onClick: () => void;
  children: React.ReactNode;
}

export const ToastAction: React.FC<ToastActionProps> = ({ altText, onClick, children }) => {
  return (
    <button
      onClick={onClick}
      aria-label={altText}
      className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background bg-primary text-primary-foreground hover:bg-primary/90 h-8 px-3"
    >
      {children}
    </button>
  );
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <>{children}</>;
};

export const ToastViewport: React.FC = () => {
  return (
    <div
      className="fixed top-0 z-[100] flex max-h-screen w-full flex-col-reverse p-4 sm:bottom-0 sm:right-0 sm:top-auto sm:flex-col md:max-w-[420px]"
      id="toast-viewport"
    />
  );
};

// Toast 组件
export const Toast: React.FC<ToastProps> = ({
  id,
  title,
  description,
  variant = 'info',
  duration = 5000,
  action,
  onDismiss,
}) => {
  React.useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onDismiss?.();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [duration, onDismiss]);

  return (
    <div
      className={cn(
        'group pointer-events-auto relative flex w-full items-center justify-between space-x-4 overflow-hidden rounded-md border p-6 pr-8 shadow-lg transition-all data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-80 data-[state=closed]:slide-out-to-right-full data-[state=open]:slide-in-from-top-full data-[state=open]:sm:slide-in-from-bottom-full',
        {
          'border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-800 dark:bg-blue-950 dark:text-blue-200':
            variant === 'info',
          'border-green-200 bg-green-50 text-green-800 dark:border-green-800 dark:bg-green-950 dark:text-green-200':
            variant === 'success',
          'border-yellow-200 bg-yellow-50 text-yellow-800 dark:border-yellow-800 dark:bg-yellow-950 dark:text-yellow-200':
            variant === 'warning',
          'border-red-200 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200':
            variant === 'error',
        }
      )}
      data-state="open"
    >
      <div className="grid gap-1">
        {title && <div className="text-sm font-semibold">{title}</div>}
        {description && <div className="text-sm opacity-90">{description}</div>}
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
      <button
        onClick={onDismiss}
        className="absolute right-2 top-2 rounded-md p-1 text-foreground/50 opacity-0 transition-opacity hover:text-foreground focus:opacity-100 focus:outline-none focus:ring-2 group-hover:opacity-100"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
};

// Toast Hook
export const useToast = () => {
  const [toasts, setToasts] = React.useState<ToastProps[]>([]);

  const toast = React.useCallback(
    ({ ...props }: Omit<ToastProps, 'id' | 'onDismiss'>) => {
      const id = Math.random().toString(36).substr(2, 9);
      const newToast = { ...props, id };

      setToasts((prev) => [...prev, newToast]);

      return {
        id,
        dismiss: () => {
          setToasts((prev) => prev.filter((t) => t.id !== id));
        },
      };
    },
    []
  );

  const dismiss = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const dismissAll = React.useCallback(() => {
    setToasts([]);
  }, []);

  return {
    toast,
    dismiss,
    dismissAll,
    toasts,
  };
};

// 预设的 Toast 函数
export const toast = {
  info: (message: string, options?: Partial<Omit<ToastProps, 'variant' | 'description'>>) => {
    return { message, variant: 'info' as const, ...options };
  },
  success: (message: string, options?: Partial<Omit<ToastProps, 'variant' | 'description'>>) => {
    return { message, variant: 'success' as const, ...options };
  },
  warning: (message: string, options?: Partial<Omit<ToastProps, 'variant' | 'description'>>) => {
    return { message, variant: 'warning' as const, ...options };
  },
  error: (message: string, options?: Partial<Omit<ToastProps, 'variant' | 'description'>>) => {
    return { message, variant: 'error' as const, ...options };
  },
};

// ToastContainer 组件 - 显示所有 Toast
export const ToastContainer: React.FC = () => {
  const { toasts, dismiss } = useToast();

  return (
    <ToastProvider>
      <ToastViewport>
        {toasts.map((toastProps) => (
          <Toast
            key={toastProps.id}
            {...toastProps}
            onDismiss={() => dismiss(toastProps.id!)}
          />
        ))}
      </ToastViewport>
    </ToastProvider>
  );
};

// AlertBanner 组件 - 页面级提醒
export interface AlertBannerProps extends Omit<AlertProps, 'title' | 'closable'> {
  showIcon?: boolean;
  actions?: React.ReactNode;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({
  showIcon = true,
  actions,
  children,
  ...props
}) => {
  return (
    <Alert
      {...props}
      className={cn('border-l-4', props.className)}
      icon={showIcon ? props.icon : undefined}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">{children}</div>
        {actions && <div className="ml-4">{actions}</div>}
      </div>
    </Alert>
  );
};

// InlineAlert 组件 - 内联提醒
export const InlineAlert: React.FC<Omit<AlertProps, 'title' | 'closable'>> = ({
  children,
  variant,
  icon,
  ...props
}) => {
  return (
    <Alert
      variant={variant}
      icon={icon}
      className={cn('py-2', props.className)}
      {...props}
    >
      <span className="text-xs">{children}</span>
    </Alert>
  );
};