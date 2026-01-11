import React from 'react';
import { useController, useFormContext } from 'react-hook-form';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { Label } from '@/components/ui/label';
import { ShadcnInput as Input } from '@/components/ui/shadcn-input';
import { Textarea } from '@/components/ui/textarea';
import { ShadcnSelect as Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/shadcn-select';
import { Checkbox } from '@/components/ui/checkbox';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { CalendarIcon } from 'lucide-react';
import { format } from 'date-fns';

// FormField 变体样式
const formFieldVariants = cva(
  'space-y-2',
  {
    variants: {
      layout: {
        default: 'flex flex-col',
        inline: 'flex items-center space-x-2',
        horizontal: 'grid grid-cols-2 gap-4',
      },
      size: {
        sm: 'text-sm',
        md: 'text-base',
        lg: 'text-lg',
      },
    },
    defaultVariants: {
      layout: 'default',
      size: 'md',
    },
  }
);

export interface FormFieldProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'size'>,
  VariantProps<typeof formFieldVariants> {
  name: string;
  label?: string;
  type?: 'input' | 'textarea' | 'select' | 'checkbox' | 'slider' | 'switch' | 'date' | 'multiselect';
  placeholder?: string;
  options?: Array<{ value: string; label: string }>;
  helperText?: string;
  required?: boolean;
  disabled?: boolean;
  inputProps?: React.InputHTMLAttributes<HTMLInputElement>;
  textareaProps?: React.TextareaHTMLAttributes<HTMLTextAreaElement>;
  selectProps?: any;
  checkboxProps?: any;
  sliderProps?: any;
  switchProps?: any;
  dateProps?: any;
}

export const FormField: React.FC<FormFieldProps> = ({
  name,
  label,
  type = 'input',
  placeholder,
  options = [],
  helperText,
  required = false,
  disabled = false,
  layout,
  size,
  className,
  inputProps,
  textareaProps,
  selectProps,
  checkboxProps,
  sliderProps,
  switchProps,
  dateProps,
  ...props
}) => {
  const { control } = useFormContext();
  const {
    field,
    fieldState: { error },
  } = useController({ name, control });

  const renderField = () => {
    switch (type) {
      case 'textarea':
        return (
          <Textarea
            {...field}
            placeholder={placeholder}
            disabled={disabled}
            {...textareaProps}
            className={cn(
              error && 'border-destructive focus-visible:ring-destructive',
              textareaProps?.className
            )}
          />
        );

      case 'select':
        return (
          <Select
            value={field.value}
            onValueChange={field.onChange}
            disabled={disabled}
            {...selectProps}
          >
            <SelectTrigger className={cn(error && 'border-destructive', selectProps?.className)}>
              <SelectValue placeholder={placeholder} />
            </SelectTrigger>
            <SelectContent>
              {options.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      case 'multiselect':
        return (
          <Select
            value={field.value?.[0] || ''}
            onValueChange={(value) => {
              const currentValues = field.value || [];
              if (currentValues.includes(value)) {
                field.onChange(currentValues.filter((v: string) => v !== value));
              } else {
                field.onChange([...currentValues, value]);
              }
            }}
            disabled={disabled}
            {...selectProps}
          >
            <SelectTrigger className={cn(error && 'border-destructive', selectProps?.className)}>
              <SelectValue placeholder={placeholder || 'Select options...'} />
            </SelectTrigger>
            <SelectContent>
              {options.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      checked={field.value?.includes(option.value)}
                      readOnly
                    />
                    <span>{option.label}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      case 'checkbox':
        return (
          <div className="flex items-center space-x-2">
            <Checkbox
              checked={field.value}
              onCheckedChange={field.onChange}
              disabled={disabled}
              id={name}
              {...checkboxProps}
            />
            <Label htmlFor={name} className="text-sm font-normal">
              {checkboxProps?.label || label}
            </Label>
          </div>
        );

      case 'slider':
        return (
          <Slider
            value={field.value ? [field.value] : [0]}
            onValueChange={([value]) => field.onChange(value)}
            disabled={disabled}
            max={sliderProps?.max || 100}
            min={sliderProps?.min || 0}
            step={sliderProps?.step || 1}
            {...sliderProps}
          />
        );

      case 'switch':
        return (
          <Switch
            checked={field.value}
            onCheckedChange={field.onChange}
            disabled={disabled}
            {...switchProps}
          />
        );

      case 'date':
        return (
          <Popover>
            <PopoverTrigger asChild>
              <button
                type="button"
                className={cn(
                  'w-full h-10 px-3 py-2 text-sm border rounded-md',
                  'bg-background hover:bg-accent',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                  'disabled:cursor-not-allowed disabled:opacity-50',
                  error && 'border-destructive focus-visible:ring-destructive',
                  dateProps?.className
                )}
                disabled={disabled}
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {field.value ? format(new Date(field.value), 'PPP') : placeholder || 'Pick a date'}
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0">
              <Calendar
                mode="single"
                selected={field.value ? new Date(field.value) : undefined}
                onSelect={(date) => field.onChange(date)}
                disabled={disabled}
                {...dateProps}
              />
            </PopoverContent>
          </Popover>
        );

      default:
        return (
          <Input
            {...field}
            type={type === 'input' ? inputProps?.type || 'text' : type}
            placeholder={placeholder}
            disabled={disabled}
            {...inputProps}
            className={cn(
              error && 'border-destructive focus-visible:ring-destructive',
              inputProps?.className
            )}
          />
        );
    }
  };

  return (
    <div className={cn(formFieldVariants({ layout, size, className }))} {...props}>
      {type !== 'checkbox' && label && (
        <Label
          htmlFor={type === 'checkbox' ? undefined : name}
          className={cn(
            'text-sm font-medium leading-none',
            error && 'text-destructive'
          )}
        >
          {label}
          {required && <span className="text-destructive ml-1">*</span>}
        </Label>
      )}

      {renderField()}

      {error && (
        <p className="text-xs text-destructive">{error.message}</p>
      )}

      {helperText && !error && (
        <p className="text-xs text-muted-foreground">{helperText}</p>
      )}
    </div>
  );
};

// FormSection 组件 - 用于组织表单字段
export interface FormSectionProps {
  title?: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}

export const FormSection: React.FC<FormSectionProps> = ({
  title,
  description,
  children,
  className
}) => {
  return (
    <div className={cn('space-y-4', className)}>
      {title && (
        <div>
          <h3 className="text-lg font-medium">{title}</h3>
          {description && (
            <p className="text-sm text-muted-foreground mt-1">{description}</p>
          )}
        </div>
      )}
      <div className="space-y-4">{children}</div>
    </div>
  );
};

// FormActions 组件 - 用于表单底部按钮
export interface FormActionsProps {
  children: React.ReactNode;
  align?: 'left' | 'center' | 'right' | 'space-between';
  className?: string;
}

export const FormActions: React.FC<FormActionsProps> = ({
  children,
  align = 'right',
  className
}) => {
  const alignClasses = {
    left: 'justify-start',
    center: 'justify-center',
    right: 'justify-end',
    'space-between': 'justify-between',
  };

  return (
    <div className={cn('flex gap-2', alignClasses[align], className)}>
      {children}
    </div>
  );
};