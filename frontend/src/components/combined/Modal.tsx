import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { ShadcnButton as Button } from '@/components/ui/shadcn-button';
import { X, Maximize2, Minimize2 } from 'lucide-react';
import { cn } from '@/lib/utils';

// Modal Props 接口
export interface ModalProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  closable?: boolean;
  maskClosable?: boolean;
  showMaximize?: boolean;
  className?: string;
  contentClassName?: string;
}

// Modal 组件
export const Modal: React.FC<ModalProps> = ({
  open,
  onOpenChange,
  title,
  description,
  children,
  footer,
  size = 'md',
  closable = true,
  maskClosable = true,
  showMaximize = false,
  className,
  contentClassName,
}) => {
  const [maximized, setMaximized] = React.useState(false);

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-full mx-4',
  };

  const handleMaximizeToggle = () => {
    setMaximized(!maximized);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className={cn(
          'p-0',
          sizeClasses[size],
          maximized && 'w-full h-full max-w-none rounded-none',
          contentClassName
        )}
        onPointerDownOutside={(e) => {
          if (!maskClosable) {
            e.preventDefault();
          }
        }}
      >
        {/* Header */}
        {(title || closable || showMaximize) && (
          <DialogHeader className="flex flex-row items-center justify-between p-6 pb-4">
            <div className="flex-1">
              {title && <DialogTitle className="text-lg">{title}</DialogTitle>}
              {description && (
                <DialogDescription className="text-sm text-muted-foreground mt-1">
                  {description}
                </DialogDescription>
              )}
            </div>
            <div className="flex items-center space-x-1">
              {showMaximize && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={handleMaximizeToggle}
                >
                  {maximized ? (
                    <Minimize2 className="h-4 w-4" />
                  ) : (
                    <Maximize2 className="h-4 w-4" />
                  )}
                </Button>
              )}
              {closable && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={() => onOpenChange?.(false)}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          </DialogHeader>
        )}

        {/* Content */}
        <div className="px-6 py-4 flex-1 overflow-auto">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <DialogFooter className="px-6 py-4 border-t">
            {footer}
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
};

// ConfirmModal 组件 - 确认对话框
export interface ConfirmModalProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  title?: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'info' | 'success' | 'warning' | 'error';
  onConfirm?: () => void | Promise<void>;
  onCancel?: () => void;
  loading?: boolean;
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  open,
  onOpenChange,
  title = 'Confirm Action',
  description = 'Are you sure you want to proceed with this action?',
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  type = 'info',
  onConfirm,
  onCancel,
  loading = false,
}) => {
  const typeClasses = {
    info: 'text-blue-600',
    success: 'text-green-600',
    warning: 'text-yellow-600',
    error: 'text-red-600',
  };

  const typeIcons = {
    info: 'ℹ️',
    success: '✅',
    warning: '⚠️',
    error: '❌',
  };

  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title={title}
      size="sm"
      footer={
        <div className="flex justify-end space-x-2">
          <Button
            variant="outline"
            onClick={() => {
              onCancel?.();
              onOpenChange?.(false);
            }}
            disabled={loading}
          >
            {cancelText}
          </Button>
          <Button
            onClick={async () => {
              await onConfirm?.();
              onOpenChange?.(false);
            }}
            disabled={loading}
            className={typeClasses[type]}
          >
            {loading ? 'Loading...' : confirmText}
          </Button>
        </div>
      }
    >
      <div className="flex items-start space-x-3">
        <span className="text-2xl">{typeIcons[type]}</span>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
    </Modal>
  );
};

// InfoModal 组件 - 信息展示对话框
export interface InfoModalProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  showMaximize?: boolean;
}

export const InfoModal: React.FC<InfoModalProps> = ({
  open,
  onOpenChange,
  title,
  children,
  size = 'md',
  showMaximize = true,
}) => {
  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title={title}
      size={size}
      showMaximize={showMaximize}
      footer={
        <div className="flex justify-end">
          <Button onClick={() => onOpenChange?.(false)}>Close</Button>
        </div>
      }
    >
      {children}
    </Modal>
  );
};

// FormModal 组件 - 表单对话框
export interface FormModalProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  onSubmit?: () => void | Promise<void>;
  submitText?: string;
  cancelText?: string;
  loading?: boolean;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  disableSubmit?: boolean;
}

export const FormModal: React.FC<FormModalProps> = ({
  open,
  onOpenChange,
  title,
  description,
  children,
  onSubmit,
  submitText = 'Submit',
  cancelText = 'Cancel',
  loading = false,
  size = 'lg',
  disableSubmit = false,
}) => {
  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title={title}
      description={description}
      size={size}
      maskClosable={false}
      footer={
        <div className="flex justify-end space-x-2">
          <Button
            variant="outline"
            onClick={() => onOpenChange?.(false)}
            disabled={loading}
          >
            {cancelText}
          </Button>
          <Button
            onClick={onSubmit}
            disabled={loading || disableSubmit}
          >
            {loading ? 'Submitting...' : submitText}
          </Button>
        </div>
      }
    >
      {children}
    </Modal>
  );
};

// useModal Hook - 简化 Modal 的使用
export const useModal = (defaultOpen = false) => {
  const [open, setOpen] = React.useState(defaultOpen);

  return {
    open,
    setOpen,
    onOpenChange: setOpen,
    openModal: () => setOpen(true),
    closeModal: () => setOpen(false),
    toggleModal: () => setOpen(!open),
  };
};