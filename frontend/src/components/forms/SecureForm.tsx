/**
 * SecureForm Component
 * Secure form with built-in CSRF protection and input validation
 */

import React, { useState, useRef, useEffect } from 'react';
import { csrfProtection, inputValidator, ValidationSchema, sanitizeInput } from '../../utils/security';

interface SecureFormProps {
  onSubmit: (data: any) => void | Promise<void>;
  schema?: ValidationSchema;
  className?: string;
  children: React.ReactNode;
  method?: 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  action?: string;
  encryptFields?: string[];
}

export const SecureForm: React.FC<SecureFormProps> = ({
  onSubmit,
  schema,
  className,
  children,
  method = 'POST',
  action,
  encryptFields = []
}) => {
  const formRef = useRef<HTMLFormElement>(null);
  const [errors, setErrors] = useState<{ [field: string]: string }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [sanitizedData, setSanitizedData] = useState<any>({});

  // Add CSRF token to form
  useEffect(() => {
    if (formRef.current) {
      // Check if CSRF token already exists
      let csrfInput = formRef.current.querySelector('input[name="_csrf"]') as HTMLInputElement;

      if (!csrfInput) {
        // Create and add CSRF token input
        csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = '_csrf';
        csrfInput.value = csrfProtection.getToken();
        formRef.current.appendChild(csrfInput);
      } else {
        // Update existing token
        csrfInput.value = csrfProtection.getToken();
      }
    }
  }, []);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setErrors({});

    try {
      // Collect form data
      const formData = new FormData(formRef.current!);
      const data: any = {};

      // Convert FormData to object
      formData.forEach((value, key) => {
        if (key !== '_csrf') {
          data[key] = value;
        }
      });

      // Validate against schema if provided
      let validatedData = data;
      if (schema) {
        const validation = inputValidator.validateSchema(data, schema);
        if (!validation.valid) {
          setErrors(validation.errors);
          setIsSubmitting(false);
          return;
        }
        validatedData = validation.sanitized;
      }

      // Sanitize all inputs
      const sanitized: any = {};
      for (const [key, value] of Object.entries(validatedData)) {
        if (typeof value === 'string') {
          sanitized[key] = sanitizeInput(value);
        } else {
          sanitized[key] = value;
        }
      }

      // Encrypt sensitive fields if specified
      if (encryptFields.length > 0) {
        // Note: This would require encryption utility to be initialized
        // For demonstration purposes only
        console.warn('Encryption of fields is not implemented in this example');
      }

      setSanitizedData(sanitized);

      // Submit data
      await onSubmit(sanitized);
    } catch (error) {
      console.error('Form submission error:', error);
      setErrors({ _form: 'Submission failed. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form
      ref={formRef}
      onSubmit={handleSubmit}
      method={method}
      action={action}
      className={className}
      noValidate
    >
      {children}
      {errors._form && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{errors._form}</p>
        </div>
      )}
    </form>
  );
};

// Secure input field component
export const SecureInput: React.FC<{
  name: string;
  type?: string;
  label?: string;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  error?: string;
  required?: boolean;
  className?: string;
  maxLength?: number;
  pattern?: string;
  validateOnChange?: boolean;
  validation?: (value: string) => string | null;
}> = ({
  name,
  type = 'text',
  label,
  placeholder,
  value,
  onChange,
  error,
  required,
  className,
  maxLength,
  pattern,
  validateOnChange,
  validation
}) => {
  const [internalValue, setInternalValue] = useState(value || '');
  const [internalError, setInternalError] = useState<string | null>(null);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.value;

    // Update internal state
    setInternalValue(newValue);

    // Validate on change if enabled
    if (validateOnChange && validation) {
      const error = validation(newValue);
      setInternalError(error);
    }

    // Call parent onChange
    if (onChange) {
      onChange(newValue);
    }
  };

  const handleBlur = () => {
    // Validate on blur
    if (validation) {
      const error = validation(internalValue);
      setInternalError(error);
    }
  };

  const displayError = error || internalError;

  return (
    <div className={className}>
      {label && (
        <label htmlFor={name} className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <input
        type={type}
        id={name}
        name={name}
        value={value !== undefined ? value : internalValue}
        onChange={handleChange}
        onBlur={handleBlur}
        placeholder={placeholder}
        required={required}
        maxLength={maxLength}
        pattern={pattern}
        className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
          displayError
            ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
            : 'border-gray-300'
        }`}
        autoComplete={type === 'password' ? 'new-password' : 'off'}
      />
      {displayError && (
        <p className="mt-1 text-sm text-red-600">{displayError}</p>
      )}
    </div>
  );
};

// Secure textarea component
export const SecureTextarea: React.FC<{
  name: string;
  label?: string;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  error?: string;
  required?: boolean;
  className?: string;
  maxLength?: number;
  rows?: number;
  sanitize?: boolean;
}> = ({
  name,
  label,
  placeholder,
  value,
  onChange,
  error,
  required,
  className,
  maxLength,
  rows = 3,
  sanitize: shouldSanitize = true
}) => {
  const [internalValue, setInternalValue] = useState(value || '');
  const [charCount, setCharCount] = useState(0);

  const handleChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    let newValue = event.target.value;

    // Sanitize input if enabled
    if (shouldSanitize) {
      newValue = sanitizeInput(newValue);
    }

    setInternalValue(newValue);
    setCharCount(newValue.length);

    if (onChange) {
      onChange(newValue);
    }
  };

  return (
    <div className={className}>
      {label && (
        <label htmlFor={name} className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <textarea
        id={name}
        name={name}
        value={value !== undefined ? value : internalValue}
        onChange={handleChange}
        placeholder={placeholder}
        required={required}
        maxLength={maxLength}
        rows={rows}
        className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none ${
          error
            ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
            : 'border-gray-300'
        }`}
      />
      {maxLength && (
        <p className={`mt-1 text-xs ${
          charCount > maxLength * 0.9 ? 'text-red-600' : 'text-gray-500'
        }`}>
          {charCount}/{maxLength}
        </p>
      )}
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
};

// Form error summary component
export const FormErrorSummary: React.FC<{
  errors: { [field: string]: string };
  className?: string;
}> = ({ errors, className }) => {
  const errorCount = Object.keys(errors).length;

  if (errorCount === 0) {
    return null;
  }

  return (
    <div className={`mb-4 p-4 bg-red-50 border border-red-200 rounded-md ${className}`}>
      <h3 className="text-sm font-medium text-red-800 mb-2">
        Please fix the following error{errorCount > 1 ? 's' : ''}:
      </h3>
      <ul className="list-disc list-inside space-y-1">
        {Object.entries(errors).map(([field, message]) => (
          <li key={field} className="text-sm text-red-700">
            {message}
          </li>
        ))}
      </ul>
    </div>
  );
};

// Success message component
export const FormSuccess: React.FC<{
  message: string;
  onDismiss?: () => void;
  className?: string;
}> = ({ message, onDismiss, className }) => {
  if (!message) {
    return null;
  }

  return (
    <div className={`mb-4 p-4 bg-green-50 border border-green-200 rounded-md ${className}`}>
      <div className="flex items-center justify-between">
        <p className="text-sm text-green-700">{message}</p>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="ml-4 text-green-500 hover:text-green-700"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};

export default SecureForm;