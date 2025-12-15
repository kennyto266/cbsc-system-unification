import { useState, useEffect, useCallback, useRef } from 'react';
import { api, apiClient } from '@/lib/api/client';
import { ApiResponse, PaginatedResponse, SearchParams } from '@/types';

interface UseApiOptions<T> {
  immediate?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  retry?: number;
  retryDelay?: number;
}

interface UsePaginatedApiOptions<T> extends UseApiOptions<PaginatedResponse<T>> {
  pageSize?: number;
}

interface State<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

interface PaginatedState<T> extends State<PaginatedResponse<T>> {
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

// Generic API hook for single requests
export function useApi<T = any>(
  url: string | null,
  options: UseApiOptions<T> = {}
) {
  const [state, setState] = useState<State<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const {
    immediate = true,
    onSuccess,
    onError,
    retry = 0,
    retryDelay = 1000,
  } = options;

  const retryCount = useRef(0);
  const abortControllerRef = useRef<AbortController | null>(null);

  const execute = useCallback(
    async (requestUrl?: string) => {
      const targetUrl = requestUrl || url;
      if (!targetUrl) return;

      // Cancel previous request if still pending
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      abortControllerRef.current = new AbortController();

      setState(prev => ({ ...prev, loading: true, error: null }));

      try {
        const data = await api.get<T>(targetUrl, {
          signal: abortControllerRef.current.signal,
        });

        setState({
          data,
          loading: false,
          error: null,
        });

        retryCount.current = 0;
        onSuccess?.(data);
      } catch (error) {
        const err = error as Error;

        // Retry logic
        if (retryCount.current < retry && err.name !== 'AbortError') {
          retryCount.current++;
          setTimeout(() => execute(targetUrl), retryDelay * retryCount.current);
          return;
        }

        setState({
          data: null,
          loading: false,
          error: err,
        });

        onError?.(err);
      }
    },
    [url, retry, retryDelay, onSuccess, onError]
  );

  useEffect(() => {
    if (immediate && url) {
      execute();
    }

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [immediate, url, execute]);

  return {
    ...state,
    execute,
    refetch: () => execute(),
    reset: () => setState({ data: null, loading: false, error: null }),
  };
}

// Paginated API hook
export function usePaginatedApi<T = any>(
  baseUrl: string,
  initialParams: SearchParams = {},
  options: UsePaginatedApiOptions<T> = {}
) {
  const [state, setState] = useState<PaginatedState<T>>({
    data: null,
    loading: false,
    error: null,
    pagination: {
      page: 1,
      limit: initialParams.limit || 20,
      total: 0,
      totalPages: 0,
    },
  });

  const [params, setParams] = useState<SearchParams>(initialParams);

  const {
    pageSize = 20,
    immediate = true,
    onSuccess,
    onError,
  } = options;

  const execute = useCallback(
    async (newParams?: SearchParams) => {
      const requestParams = { ...params, ...newParams };
      const queryString = new URLSearchParams({
        page: requestParams.page?.toString() || '1',
        limit: requestParams.limit?.toString() || pageSize.toString(),
        ...(requestParams.query && { q: requestParams.query }),
        ...(requestParams.sort && {
          sort: `${requestParams.sort.field}:${requestParams.sort.order}`,
        }),
        ...(requestParams.filters &&
          requestParams.filters.length > 0 && {
            filters: JSON.stringify(requestParams.filters),
          }),
      }).toString();

      setState(prev => ({ ...prev, loading: true, error: null }));

      try {
        const data = await api.get<PaginatedResponse<T>>(`${baseUrl}?${queryString}`);

        setState({
          data,
          loading: false,
          error: null,
          pagination: {
            page: data.pagination.page,
            limit: data.pagination.limit,
            total: data.pagination.total,
            totalPages: data.pagination.totalPages,
          },
        });

        onSuccess?.(data);
      } catch (error) {
        const err = error as Error;
        setState(prev => ({
          ...prev,
          loading: false,
          error: err,
        }));
        onError?.(err);
      }
    },
    [baseUrl, params, pageSize, onSuccess, onError]
  );

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [immediate, execute]);

  const setPage = (page: number) => {
    setParams(prev => ({ ...prev, page }));
  };

  const setLimit = (limit: number) => {
    setParams(prev => ({ ...prev, limit, page: 1 }));
  };

  const setFilters = (filters: SearchParams['filters']) => {
    setParams(prev => ({ ...prev, filters, page: 1 }));
  };

  const setSort = (field: string, order: 'asc' | 'desc') => {
    setParams(prev => ({
      ...prev,
      sort: { field, order },
      page: 1,
    }));
  };

  const setSearch = (query: string) => {
    setParams(prev => ({ ...prev, query, page: 1 }));
  };

  const reset = () => {
    setParams(initialParams);
    setState({
      data: null,
      loading: false,
      error: null,
      pagination: {
        page: 1,
        limit: pageSize,
        total: 0,
        totalPages: 0,
      },
    });
  };

  return {
    ...state,
    params,
    execute,
    refetch: () => execute(),
    setPage,
    setLimit,
    setFilters,
    setSort,
    setSearch,
    reset,
  };
}

// Mutation hook for POST/PUT/DELETE requests
export function useMutation<T = any, V = any>(
  url: string,
  method: 'POST' | 'PUT' | 'PATCH' | 'DELETE' = 'POST',
  options: UseApiOptions<T> = {}
) {
  const [state, setState] = useState<State<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const { onSuccess, onError } = options;

  const mutate = useCallback(
    async (data?: V) => {
      setState(prev => ({ ...prev, loading: true, error: null }));

      try {
        let result: T;

        switch (method) {
          case 'POST':
            result = await api.post<T>(url, data);
            break;
          case 'PUT':
            result = await api.put<T>(url, data);
            break;
          case 'PATCH':
            result = await api.patch<T>(url, data);
            break;
          case 'DELETE':
            result = await api.delete<T>(url);
            break;
        }

        setState({
          data: result,
          loading: false,
          error: null,
        });

        onSuccess?.(result);
        return result;
      } catch (error) {
        const err = error as Error;
        setState(prev => ({
          ...prev,
          loading: false,
          error: err,
        }));
        onError?.(err);
        throw err;
      }
    },
    [url, method, onSuccess, onError]
  );

  return {
    ...state,
    mutate,
    reset: () => setState({ data: null, loading: false, error: null }),
  };
}

// Debounced search hook
export function useDebouncedSearch<T = any>(
  url: string,
  delay: number = 300,
  options: UseApiOptions<T> = {}
) {
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [searchTerm, delay]);

  const searchUrl = debouncedSearchTerm ? `${url}?q=${encodeURIComponent(debouncedSearchTerm)}` : null;
  const searchResults = useApi<T>(searchUrl, options);

  return {
    ...searchResults,
    searchTerm,
    setSearchTerm,
    debouncedSearchTerm,
  };
}

// Real-time data hook with WebSocket
export function useRealTimeApi<T = any>(
  url: string,
  wsUrl: string,
  options: UseApiOptions<T> = {}
) {
  const [state, setState] = useState<State<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
      reconnectAttempts.current = 0;
    };

    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setState({
          data,
          loading: false,
          error: null,
        });
        options.onSuccess?.(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setState(prev => ({
        ...prev,
        error: new Error('WebSocket connection error'),
      }));
    };

    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected');
      if (reconnectAttempts.current < maxReconnectAttempts) {
        reconnectAttempts.current++;
        setTimeout(connectWebSocket, 1000 * Math.pow(2, reconnectAttempts.current));
      }
    };
  }, [wsUrl, options]);

  useEffect(() => {
    // Initial data fetch
    if (url) {
      api.get<T>(url).then(data => {
        setState({
          data,
          loading: false,
          error: null,
        });
      });
    }

    // Connect WebSocket
    connectWebSocket();

    return () => {
      wsRef.current?.close();
    };
  }, [url, connectWebSocket]);

  return {
    ...state,
    reconnect: () => connectWebSocket(),
  };
}