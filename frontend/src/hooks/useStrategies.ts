/**
 * Strategies Hooks
 * 策略管理相關的 Hooks
 */

import { useDispatch, useSelector } from 'react-redux';
import { useEffect } from 'react';

import {
  fetchStrategies,
  fetchStrategy,
  createStrategy,
  updateStrategy,
  deleteStrategy,
  executeStrategy,
  fetchStrategyPerformance,
  clearError,
  setFilter,
  clearFilter,
  toggleStrategySelection,
  clearSelection,
  selectAllStrategies
} from '../store/strategies/strategySlice';

import {
  selectStrategies,
  selectCurrentStrategy,
  selectStrategiesLoading,
  selectStrategiesError,
  selectStrategiesPagination,
  selectConfigs,
  selectPerformance,
  selectPerformanceLoading,
  selectFilter,
  selectSelectedStrategies
} from '../store/strategies/strategySlice';

import { Strategy, StrategyCreateRequest, StrategyUpdateRequest, StrategyListOptions } from '../types/strategyTypes';

/**
 * Hook for strategies management
 * 策略管理 Hook
 */
export const useStrategies = (options?: StrategyListOptions) => {
  const dispatch = useDispatch();

  // Selectors
  const strategies = useSelector(selectStrategies);
  const loading = useSelector(selectStrategiesLoading);
  const error = useSelector(selectStrategiesError);
  const pagination = useSelector(selectStrategiesPagination);
  const filter = useSelector(selectFilter);
  const selectedStrategies = useSelector(selectSelectedStrategies);

  // Actions
  const loadStrategies = (loadOptions?: StrategyListOptions) => {
    dispatch(fetchStrategies(loadOptions || options));
  };

  const clearErrorMessage = () => {
    dispatch(clearError());
  };

  const updateFilter = (newFilter: any) => {
    dispatch(setFilter(newFilter));
  };

  const clearAllFilters = () => {
    dispatch(clearFilter());
  };

  const toggleSelection = (strategyId: string) => {
    dispatch(toggleStrategySelection(strategyId));
  };

  const clearAllSelections = () => {
    dispatch(clearSelection());
  };

  const selectAll = () => {
    dispatch(selectAllStrategies());
  };

  // Auto load strategies
  useEffect(() => {
    if (options) {
      loadStrategies(options);
    }
  }, [JSON.stringify(options), JSON.stringify(filter)]);

  return {
    // Data
    strategies,
    loading,
    error,
    pagination,
    filter,
    selectedStrategies,

    // Actions
    loadStrategies,
    clearError: clearErrorMessage,
    updateFilter,
    clearAllFilters,
    toggleSelection,
    clearAllSelections,
    selectAll
  };
};

/**
 * Hook for single strategy operations
 * 單個策略操作 Hook
 */
export const useStrategy = (strategyId?: string) => {
  const dispatch = useDispatch();

  // Selectors
  const strategy = useSelector(selectCurrentStrategy);
  const loading = useSelector(selectStrategiesLoading);
  const error = useSelector(selectStrategiesError);

  // Actions
  const loadStrategy = (id: string) => {
    dispatch(fetchStrategy(id));
  };

  const createNewStrategy = async (data: StrategyCreateRequest) => {
    return dispatch(createStrategy(data)).unwrap();
  };

  const updateExistingStrategy = async (id: string, data: StrategyUpdateRequest) => {
    return dispatch(updateStrategy({ id, data })).unwrap();
  };

  const deleteExistingStrategy = async (id: string) => {
    return dispatch(deleteStrategy(id)).unwrap();
  };

  const executeExistingStrategy = async (id: string, executionRequest: any) => {
    return dispatch(executeStrategy({ strategyId: id, executionRequest })).unwrap();
  };

  // Auto load strategy when ID changes
  useEffect(() => {
    if (strategyId) {
      loadStrategy(strategyId);
    }
  }, [strategyId]);

  return {
    // Data
    strategy,
    loading,
    error,

    // Actions
    loadStrategy,
    createStrategy: createNewStrategy,
    updateStrategy: updateExistingStrategy,
    deleteStrategy: deleteExistingStrategy,
    executeStrategy: executeExistingStrategy
  };
};

/**
 * Hook for strategy performance data
 * 策略性能數據 Hook
 */
export const useStrategyPerformance = (strategyId: string, timeRange?: string) => {
  const dispatch = useDispatch();

  // Selectors
  const performance = useSelector(selectPerformance);
  const loading = useSelector(selectPerformanceLoading);

  // Actions
  const loadPerformance = (id: string, options?: { timeRange?: string }) => {
    dispatch(fetchStrategyPerformance({
      strategyId: id,
      timeRange: options?.timeRange || timeRange
    }));
  };

  // Auto load performance data
  useEffect(() => {
    if (strategyId) {
      loadPerformance(strategyId, { timeRange });
    }
  }, [strategyId, timeRange]);

  return {
    performance,
    loading,
    loadPerformance
  };
};

/**
 * Hook for strategy configurations
 * 策略配置 Hook
 */
export const useStrategyConfigs = (strategyId: string) => {
  const dispatch = useDispatch();

  // Selectors
  const configs = useSelector(selectConfigs);
  const loading = useSelector(selectStrategiesLoading);

  // Actions
  const loadConfigs = (id: string) => {
    dispatch(fetchStrategyConfigs({ strategy_id: id }));
  };

  // Auto load configs
  useEffect(() => {
    if (strategyId) {
      loadConfigs(strategyId);
    }
  }, [strategyId]);

  return {
    configs,
    loading,
    loadConfigs
  };
};

export default {
  useStrategies,
  useStrategy,
  useStrategyPerformance,
  useStrategyConfigs
};