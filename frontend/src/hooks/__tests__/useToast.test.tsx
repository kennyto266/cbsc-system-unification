/**
 * useToast Hook Tests
 *
 * Comprehensive tests for the useToast hook including
 * toast management, auto-removal, and global state synchronization.
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals';
import { useToast } from '../useToast';

describe('useToast', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('should initialize with empty toasts', () => {
    const { result } = renderHook(() => useToast());

    expect(result.current.toasts).toEqual([]);
    expect(typeof result.current.toast).toBe('function');
    expect(typeof result.current.dismiss).toBe('function');
    expect(typeof result.current.dismissAll).toBe('function');
  });

  it('should add a toast with generated ID', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.toast({
        type: 'success',
        description: 'Test message',
      });
    });

    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0]).toMatchObject({
      type: 'success',
      description: 'Test message',
      duration: 5000,
    });
    expect(typeof result.current.toasts[0].id).toBe('string');
    expect(result.current.toasts[0].id.length).toBeGreaterThan(0);
  });

  it('should add a toast with custom duration', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.toast({
        type: 'error',
        description: 'Error message',
        duration: 10000,
      });
    });

    expect(result.current.toasts[0].duration).toBe(10000);
  });

  it('should remove a toast by ID', () => {
    const { result } = renderHook(() => useToast());

    // Add a toast
    act(() => {
      result.current.toast({
        type: 'info',
        description: 'Info message',
      });
    });

    expect(result.current.toasts).toHaveLength(1);

    // Get the toast ID
    const toastId = result.current.toasts[0].id;

    // Remove the toast
    act(() => {
      result.current.dismiss(toastId);
    });

    expect(result.current.toasts).toEqual([]);
  });

  it('should clear all toasts', () => {
    const { result } = renderHook(() => useToast());

    // Add multiple toasts
    act(() => {
      result.current.toast({ type: 'success', description: 'Success 1' });
      result.current.toast({ type: 'error', description: 'Error 1' });
      result.current.toast({ type: 'warning', description: 'Warning 1' });
    });

    expect(result.current.toasts).toHaveLength(3);

    // Clear all
    act(() => {
      result.current.dismissAll();
    });

    expect(result.current.toasts).toEqual([]);
  });

  it('should auto-remove toast after duration', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.toast({
        type: 'success',
        description: 'Auto-remove message',
        duration: 1000,
      });
    });

    expect(result.current.toasts).toHaveLength(1);

    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(1000);
    });

    expect(result.current.toasts).toEqual([]);
  });

  it('should not auto-remove toast with duration 0', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.toast({
        type: 'error',
        description: 'Persistent message',
        duration: 0,
      });
    });

    expect(result.current.toasts).toHaveLength(1);

    // Fast-forward time significantly
    act(() => {
      jest.advanceTimersByTime(10000);
    });

    // Toast should still be there
    expect(result.current.toasts).toHaveLength(1);
  });

  it('should handle all toast types correctly', () => {
    const { result } = renderHook(() => useToast());
    const toastTypes: Array<'success' | 'error' | 'warning' | 'info'> = [
      'success',
      'error',
      'warning',
      'info',
    ];

    toastTypes.forEach((type) => {
      act(() => {
        result.current.toast({
          type,
          description: `${type} message`,
        });
      });
    });

    expect(result.current.toasts).toHaveLength(4);
    result.current.toasts.forEach((toast, index) => {
      expect(toast.type).toBe(toastTypes[index]);
    });
  });

  it('should generate unique IDs for each toast', () => {
    const { result } = renderHook(() => useToast());
    const ids = new Set<string>();

    // Add multiple toasts
    for (let i = 0; i < 10; i++) {
      act(() => {
        result.current.toast({
          type: 'info',
          description: `Message ${i}`,
        });
      });
      ids.add(result.current.toasts[i].id);
    }

    expect(ids.size).toBe(10);
  });

  it('should handle removing non-existent toast gracefully', () => {
    const { result } = renderHook(() => useToast());

    // Try to remove toast that doesn't exist
    act(() => {
      result.current.dismiss('non-existent-id');
    });

    // Should not throw error
    expect(result.current.toasts).toEqual([]);
  });

  it('should handle multiple auto-removal timers correctly', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.toast({
        type: 'success',
        description: 'Toast 1',
        duration: 1000,
      });
      result.current.toast({
        type: 'error',
        description: 'Toast 2',
        duration: 2000,
      });
    });

    expect(result.current.toasts).toHaveLength(2);

    // First toast should be removed after 1000ms
    act(() => {
      jest.advanceTimersByTime(1000);
    });

    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0].description).toBe('Toast 2');

    // Second toast should be removed after another 1000ms
    act(() => {
      jest.advanceTimersByTime(1000);
    });

    expect(result.current.toasts).toEqual([]);
  });

  it('should support title field', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.toast({
        type: 'success',
        title: 'Success Title',
        description: 'Test message',
      });
    });

    expect(result.current.toasts[0].title).toBe('Success Title');
    expect(result.current.toasts[0].description).toBe('Test message');
  });
});
