/**
 * useCSRF Hook
 * React hook for CSRF protection
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { csrfProtection } from '../utils/security';

interface CSRFState {
  token: string;
  isInitialized: boolean;
  lastRotation: number;
  rotationEnabled: boolean;
}

export const useCSRF = (options?: {
  autoRotate?: boolean;
  rotationInterval?: number;
}) => {
  const {
    autoRotate = true,
    rotationInterval = 3600000 // 1 hour
  } = options || {};

  const [state, setState] = useState<CSRFState>({
    token: '',
    isInitialized: false,
    lastRotation: 0,
    rotationEnabled: autoRotate
  });

  const rotationTimerRef = useRef<NodeJS.Timeout>();

  // Initialize CSRF protection
  useEffect(() => {
    const token = csrfProtection.getToken();
    setState({
      token,
      isInitialized: true,
      lastRotation: Date.now(),
      rotationEnabled: autoRotate
    });

    // Set up rotation timer if enabled
    if (autoRotate) {
      rotationTimerRef.current = setInterval(() => {
        rotateToken();
      }, rotationInterval);
    }

    return () => {
      if (rotationTimerRef.current) {
        clearInterval(rotationTimerRef.current);
      }
    };
  }, [autoRotate, rotationInterval]);

  const rotateToken = useCallback(() => {
    csrfProtection.rotateToken();
    const newToken = csrfProtection.getToken();
    setState(prev => ({
      ...prev,
      token: newToken,
      lastRotation: Date.now()
    }));
  }, []);

  const getToken = useCallback(() => {
    return csrfProtection.getToken();
  }, []);

  const validateToken = useCallback((token: string) => {
    return csrfProtection.validateToken(token);
  }, []);

  const addToHeaders = useCallback((headers: Record<string, string> = {}) => {
    return csrfProtection.addTokenToHeaders(headers);
  }, []);

  const addToFormData = useCallback((formData: FormData) => {
    csrfProtection.addTokenToFormData(formData);
  }, []);

  const fetchWithCSRF = useCallback(async (url: string, options: RequestInit = {}) => {
    return csrfProtection.fetchWithCSRF(url, options);
  }, []);

  const enableRotation = useCallback(() => {
    if (!rotationTimerRef.current) {
      rotationTimerRef.current = setInterval(() => {
        rotateToken();
      }, rotationInterval);
    }
    setState(prev => ({ ...prev, rotationEnabled: true }));
  }, [rotateToken, rotationInterval]);

  const disableRotation = useCallback(() => {
    if (rotationTimerRef.current) {
      clearInterval(rotationTimerRef.current);
      rotationTimerRef.current = undefined;
    }
    setState(prev => ({ ...prev, rotationEnabled: false }));
  }, []);

  return {
    ...state,
    rotateToken,
    getToken,
    validateToken,
    addToHeaders,
    addToFormData,
    fetchWithCSRF,
    enableRotation,
    disableRotation
  };
};

// Hook for CSRF-aware API calls
export const useSecureAPI = (baseURL: string, options?: {
  defaultHeaders?: Record<string, string>;
  timeout?: number;
}) => {
  const { getToken, addToHeaders, fetchWithCSRF } = useCSRF();
  const { defaultHeaders = {}, timeout = 30000 } = options || {};

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const abortControllerRef = useRef<AbortController>();

  const request = useCallback(async (
    endpoint: string,
    options: RequestInit = {}
  ) => {
    // Cancel previous request if still pending
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();

    setLoading(true);
    setError(null);

    try {
      const url = endpoint.startsWith('http') ? endpoint : `${baseURL}${endpoint}`;
      const headers = addToHeaders({
        'Content-Type': 'application/json',
        ...defaultHeaders,
        ...options.headers
      });

      const response = await fetchWithCSRF(url, {
        ...options,
        headers,
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (err) {
      if (err instanceof Error) {
        if (err.name === 'AbortError') {
          console.log('Request aborted');
          return null;
        }
        setError(err);
      } else {
        setError(new Error('Unknown error occurred'));
      }
      throw err;
    } finally {
      setLoading(false);
    }
  }, [baseURL, defaultHeaders, addToHeaders, fetchWithCSRF]);

  const get = useCallback((endpoint: string, options?: RequestInit) => {
    return request(endpoint, { ...options, method: 'GET' });
  }, [request]);

  const post = useCallback((endpoint: string, data?: any, options?: RequestInit) => {
    return request(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined
    });
  }, [request]);

  const put = useCallback((endpoint: string, data?: any, options?: RequestInit) => {
    return request(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined
    });
  }, [request]);

  const patch = useCallback((endpoint: string, data?: any, options?: RequestInit) => {
    return request(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined
    });
  }, [request]);

  const del = useCallback((endpoint: string, options?: RequestInit) => {
    return request(endpoint, { ...options, method: 'DELETE' });
  }, [request]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    loading,
    error,
    request,
    get,
    post,
    put,
    patch,
    delete: del
  };
};

// Hook for form submission with CSRF protection
export const useSecureForm = <T = any>(options?: {
  onSubmit?: (data: T) => void | Promise<void>;
  onSuccess?: (data: any) => void;
  onError?: (error: Error) => void;
}) => {
  const { onSubmit, onSuccess, onError } = options || {};
  const { getToken, addToFormData } = useCSRF();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<Error | null>(null);

  const submit = useCallback(async (data: T) => {
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      // Add CSRF token to data
      const dataWithToken = {
        ...data,
        _csrf: getToken()
      };

      // Call submit handler
      const result = await onSubmit?.(dataWithToken);

      // Call success handler
      if (onSuccess) {
        onSuccess(result);
      }

      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Submission failed');
      setSubmitError(error);

      if (onError) {
        onError(error);
      }

      throw error;
    } finally {
      setIsSubmitting(false);
    }
  }, [getToken, onSubmit, onSuccess, onError]);

  const submitWithFormData = useCallback(async (formData: FormData) => {
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      // Add CSRF token to FormData
      addToFormData(formData);

      // Call submit handler
      const result = await onSubmit?.(formData as any);

      // Call success handler
      if (onSuccess) {
        onSuccess(result);
      }

      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Submission failed');
      setSubmitError(error);

      if (onError) {
        onError(error);
      }

      throw error;
    } finally {
      setIsSubmitting(false);
    }
  }, [addToFormData, onSubmit, onSuccess, onError]);

  return {
    isSubmitting,
    submitError,
    submit,
    submitWithFormData
  };
};

export default useCSRF;