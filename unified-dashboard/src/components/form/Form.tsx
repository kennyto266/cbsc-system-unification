import React, { createContext, useContext, forwardRef } from 'react'
import { cn } from '@/utils/cn'

interface FormContextType {
  disabled?: boolean
  readonly?: boolean
}

const FormContext = createContext<FormContextType>({})

export interface FormProps extends React.FormHTMLAttributes<HTMLFormElement> {
  disabled?: boolean
  readonly?: boolean
}

const Form = forwardRef<HTMLFormElement, FormProps>(
  ({ className, disabled = false, readonly = false, children, ...props }, ref) => {
    return (
      <FormContext.Provider value={{ disabled, readonly }}>
        <form
          ref={ref}
          className={cn('space-y-4', className)}
          {...props}
        >
          {children}
        </form>
      </FormContext.Provider>
    )
  }
)

Form.displayName = 'Form'

export interface FormFieldProps extends React.HTMLAttributes<HTMLDivElement> {
  label?: string
  required?: boolean
  error?: string
  helperText?: string
}

const FormField = forwardRef<HTMLDivElement, FormFieldProps>(
  ({ className, label, required = false, error, helperText, children, ...props }, ref) => {
    const { disabled } = useContext(FormContext)

    return (
      <div ref={ref} className={cn('space-y-2', className)} {...props}>
        {label && (
          <label className={cn(
            'text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70',
            disabled && 'opacity-50'
          )}>
            {label}
            {required && <span className="text-error-500 ml-1">*</span>}
          </label>
        )}

        <div className={cn(disabled && 'opacity-50')}>
          {children}
        </div>

        {error && (
          <p className="text-xs text-error-600">
            {error}
          </p>
        )}

        {helperText && !error && (
          <p className="text-xs text-gray-500">
            {helperText}
          </p>
        )}
      </div>
    )
  }
)

FormField.displayName = 'FormField'

export interface FormLabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {}

const FormLabel = forwardRef<HTMLLabelElement, FormLabelProps>(
  ({ className, ...props }, ref) => {
    const { disabled } = useContext(FormContext)

    return (
      <label
        ref={ref}
        className={cn(
          'text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70',
          disabled && 'opacity-50',
          className
        )}
        {...props}
      />
    )
  }
)

FormLabel.displayName = 'FormLabel'

export interface FormControlProps extends React.HTMLAttributes<HTMLDivElement> {}

const FormControl = forwardRef<HTMLDivElement, FormControlProps>(
  ({ className, ...props }, ref) => {
    const { disabled } = useContext(FormContext)

    return (
      <div
        ref={ref}
        className={cn(disabled && 'opacity-50', className)}
        {...props}
      />
    )
  }
)

FormControl.displayName = 'FormControl'

export interface FormDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {}

const FormDescription = forwardRef<HTMLParagraphElement, FormDescriptionProps>(
  ({ className, ...props }, ref) => {
    return (
      <p
        ref={ref}
        className={cn('text-xs text-gray-500', className)}
        {...props}
      />
    )
  }
)

FormDescription.displayName = 'FormDescription'

export interface FormMessageProps extends React.HTMLAttributes<HTMLParagraphElement> {
  variant?: 'error' | 'success' | 'warning'
}

const FormMessage = forwardRef<HTMLParagraphElement, FormMessageProps>(
  ({ className, variant = 'error', children, ...props }, ref) => {
    if (!children) return null

    const variantClasses = {
      error: 'text-error-600',
      success: 'text-success-600',
      warning: 'text-warning-600',
    }

    return (
      <p
        ref={ref}
        className={cn('text-xs', variantClasses[variant], className)}
        {...props}
      >
        {children}
      </p>
    )
  }
)

FormMessage.displayName = 'FormMessage'

export interface FormItemProps extends React.HTMLAttributes<HTMLDivElement> {}

const FormItem = forwardRef<HTMLDivElement, FormItemProps>(
  ({ className, ...props }, ref) => {
    return (
      <div ref={ref} className={cn('space-y-2', className)} {...props} />
    )
  }
)

FormItem.displayName = 'FormItem'

export {
  Form,
  FormField,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
  FormItem,
  FormContext,
}