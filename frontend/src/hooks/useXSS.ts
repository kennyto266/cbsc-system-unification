/**
 * useXSS Hook
 * React hook for XSS protection
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { xssProtection } from '../utils/security';

interface UseXSSOptions {
  validateOnType?: boolean;
  debounceMs?: number;
  maxLength?: number;
  allowedTags?: string[];
  customSanitizer?: (input: string) => string;
}

interface XSSState {
  input: string;
  sanitized: string;
  isValid: boolean;
  threats: string[];
  warnings: string[];
}

export const useXSS = (initialValue: string = '', options: UseXSSOptions = {}) => {
  const {
    validateOnType = false,
    debounceMs = 300,
    maxLength,
    allowedTags,
    customSanitizer
  } = options;

  const [state, setState] = useState<XSSState>({
    input: initialValue,
    sanitized: initialValue,
    isValid: true,
    threats: [],
    warnings: []
  });

  const debounceTimerRef = useRef<NodeJS.Timeout>();

  // Configure XSS protection if custom options provided
  useEffect(() => {
    if (allowedTags || customSanitizer) {
      const config: any = {};
      if (allowedTags) {
        config.ALLOWED_TAGS = allowedTags;
      }
      if (customSanitizer) {
        // Note: This would require extending XSSProtection class
        console.warn('Custom sanitizer not implemented in XSSProtection class');
      }
      // xssProtection.configure(config);
    }
  }, [allowedTags, customSanitizer]);

  const sanitize = useCallback((input: string): string => {
    let sanitized = xssProtection.sanitizeHTML(input);

    // Apply custom sanitizer if provided
    if (customSanitizer) {
      sanitized = customSanitizer(sanitized);
    }

    return sanitized;
  }, [customSanitizer]);

  const validate = useCallback((input: string): {
    isValid: boolean;
    threats: string[];
    warnings: string[];
  } => {
    const threats: string[] = [];
    const warnings: string[] = [];

    // Check length
    if (maxLength && input.length > maxLength) {
      warnings.push(`Input exceeds maximum length of ${maxLength}`);
    }

    // Check for dangerous patterns
    if (xssProtection.containsDangerousPatterns(input)) {
      threats.push('Dangerous HTML/JavaScript patterns detected');
    }

    // Check for suspicious URLs
    const urlRegex = /https?:\/\/[^\s]+/gi;
    const urls = input.match(urlRegex);
    if (urls) {
      urls.forEach(url => {
        if (!xssProtection.sanitizeURL(url)) {
          threats.push(`Suspicious URL detected: ${url}`);
        }
      });
    }

    return {
      isValid: threats.length === 0,
      threats,
      warnings
    };
  }, [maxLength]);

  const setInput = useCallback((newInput: string) => {
    setState(prevState => ({
      ...prevState,
      input: newInput
    }));

    if (validateOnType) {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }

      debounceTimerRef.current = setTimeout(() => {
        const sanitized = sanitize(newInput);
        const validation = validate(newInput);

        setState(prevState => ({
          ...prevState,
          sanitized,
          ...validation
        }));
      }, debounceMs);
    }
  }, [validateOnType, sanitize, validate, debounceMs]);

  const commitInput = useCallback(() => {
    const sanitized = sanitize(state.input);
    const validation = validate(state.input);

    setState(prevState => ({
      ...prevState,
      sanitized,
      ...validation
    }));
  }, [state.input, sanitize, validate]);

  const reset = useCallback(() => {
    setState({
      input: '',
      sanitized: '',
      isValid: true,
      threats: [],
      warnings: []
    });
  }, []);

  const clear = useCallback(() => {
    setState(prevState => ({
      ...prevState,
      input: '',
      sanitized: ''
    }));
  }, []);

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  return {
    ...state,
    setInput,
    commitInput,
    reset,
    clear
  };
};

// Hook for safe HTML rendering
export const useSafeHTML = (html: string, options?: {
  sanitize?: boolean;
  stripDangerous?: boolean;
}) => {
  const [safeHTML, setSafeHTML] = useState('');
  const [isSafe, setIsSafe] = useState(true);
  const [dangerDetected, setDangerDetected] = useState(false);

  useEffect(() => {
    if (!html) {
      setSafeHTML('');
      setIsSafe(true);
      setDangerDetected(false);
      return;
    }

    // Check for dangerous patterns
    const hasDanger = xssProtection.containsDangerousPatterns(html);
    setDangerDetected(hasDanger);

    // Sanitize if requested or if danger detected
    const shouldSanitize = options?.sanitize !== false || hasDanger;
    const sanitized = shouldSanitize ? xssProtection.sanitizeHTML(html) : html;

    setSafeHTML(sanitized);
    setIsSafe(!hasDanger);
  }, [html, options?.sanitize]);

  const createMarkup = () => ({ __html: safeHTML });

  return {
    safeHTML,
    isSafe,
    dangerDetected,
    createMarkup
  };
};

// Hook for monitoring XSS attempts
export const useXSSMonitor = () => {
  const [attempts, setAttempts] = useState<Array<{
    timestamp: number;
    type: string;
    content: string;
    blocked: boolean;
  }>>([]);

  const logAttempt = useCallback((type: string, content: string, blocked: boolean = true) => {
    const attempt = {
      timestamp: Date.now(),
      type,
      content: content.substring(0, 100), // Limit content length
      blocked
    };

    setAttempts(prev => {
      const newAttempts = [attempt, ...prev];
      // Keep only last 50 attempts
      return newAttempts.slice(0, 50);
    });
  }, []);

  const clearAttempts = useCallback(() => {
    setAttempts([]);
  }, []);

  const getThreatLevel = useCallback((): 'low' | 'medium' | 'high' => {
    const recentAttempts = attempts.filter(a =>
      Date.now() - a.timestamp < 300000 // Last 5 minutes
    );

    if (recentAttempts.length === 0) return 'low';
    if (recentAttempts.length < 5) return 'medium';
    return 'high';
  }, [attempts]);

  return {
    attempts,
    logAttempt,
    clearAttempts,
    getThreatLevel
  };
};

export default useXSS;