/**
 * API Configuration
 *
 * Centralized API configuration for the CBSC Trading System frontend.
 * This module provides the base URL, headers, and utility functions for API calls.
 */

// Helper to get env vars safely in both Jest and Vite
const getEnvVar = (key: string, defaultValue: string): string => {
  if (typeof process !== 'undefined' && process.env?.[key]) {
    return process.env[key];
  }
  try {
    const metaEnv = (0, eval)('typeof import.meta !== "undefined" ? import.meta.env : undefined');
    if (metaEnv?.[key]) return metaEnv[key];
  } catch {
    // Fall through
  }
  return defaultValue;
};

// Get API base URL from environment variables
const API_BASE_URL = getEnvVar('VITE_API_BASE_URL', '/api');
const WS_BASE_URL = getEnvVar('VITE_WS_BASE_URL', 'ws://localhost:3004/ws');

// Feature flags
const ENABLE_WEBSOCKET = getEnvVar('VITE_ENABLE_WEBSOCKET', 'true') !== 'false';
const ENABLE_REALTIME = getEnvVar('VITE_ENABLE_REALTIME', 'true') !== 'false';

/**
 * Build a full API URL for the given endpoint
 */
export const buildApiUrl = (endpoint: string): string => {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  const cleanBaseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
  return `${cleanBaseUrl}/${cleanEndpoint}`;
};

/**
 * Get authentication token from localStorage
 */
export const getAuthToken = (): string | null => {
  return localStorage.getItem('auth_token') || localStorage.getItem('token');
};

/**
 * Set authentication token in localStorage
 */
export const setAuthToken = (token: string): void => {
  localStorage.setItem('auth_token', token);
};

/**
 * Set both access and refresh tokens in localStorage
 */
export const setAuthTokens = (accessToken: string, refreshToken: string): void => {
  localStorage.setItem('auth_token', accessToken);
  localStorage.setItem('refresh_token', refreshToken);
};

/**
 * Get refresh token from localStorage
 */
export const getRefreshToken = (): string | null => {
  return localStorage.getItem('refresh_token');
};

/**
 * Remove authentication token from localStorage
 */
export const removeAuthToken = (): void => {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('token');
  localStorage.removeItem('refresh_token');
};

/**
 * Default headers for API requests
 */
export const getDefaultHeaders = () => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return headers;
};

/**
 * WebSocket channels
 */
export const WS_CHANNELS = {
  STRATEGY_PERFORMANCE: 'strategy_performance',
  MARKET_DATA: 'market_data',
  HIBOR_RATES: 'hibor_rates',
  CBSC_CONTRACTS: 'cbsc_contracts',
} as const;

/**
 * Export base URLs for use in RTK Query baseQuery
 */
export { API_BASE_URL, WS_BASE_URL, ENABLE_WEBSOCKET, ENABLE_REALTIME };
