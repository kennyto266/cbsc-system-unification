/**
 * Market-Wide Optimization API Service
 */

import axios from 'axios';
import type {
  OptimizationConfig,
  StartOptimizationResponse,
  ProgressData,
  OptimizationResults
} from '../types/market-optimization';

const API_BASE = 'http://192.168.1.5:8003';

export const marketOptimizationApi = {
  /**
   * Start a new market-wide optimization
   */
  startOptimization: async (config: OptimizationConfig): Promise<StartOptimizationResponse> => {
    const response = await axios.post<StartOptimizationResponse>(
      `${API_BASE}/api/vectorbt/optimize-marketwide`,
      config
    );
    return response.data;
  },

  /**
   * Get optimization progress
   */
  getProgress: async (taskId: string): Promise<ProgressData> => {
    const response = await axios.get<ProgressData>(
      `${API_BASE}/api/vectorbt/optimize-marketwide/${taskId}/progress`
    );
    return response.data;
  },

  /**
   * Get final optimization results
   */
  getResults: async (taskId: string): Promise<OptimizationResults> => {
    const response = await axios.get<OptimizationResults>(
      `${API_BASE}/api/vectorbt/optimize-marketwide/${taskId}/results`
    );
    return response.data;
  },

  /**
   * Check API health
   */
  healthCheck: async (): Promise<{ status: string; vectorbt_available: boolean }> => {
    const response = await axios.get(`${API_BASE}/api/vectorbt/health`);
    return response.data;
  }
};

export default marketOptimizationApi;
