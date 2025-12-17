// Strategy management hooks
export { useStrategies } from './useStrategies'
export { useBatchOperation } from './useBatchOperation'
export { useStrategyDetail } from './useStrategyDetail'
export { useBacktest } from './useBacktest'
export { useStrategyExecution } from './useStrategyExecution'

// Re-export types for convenience
export type {
  UseStrategiesOptions,
  UseStrategiesReturn,
} from './useStrategies'

export type {
  BatchOperationOptions,
} from './useBatchOperation'

export type {
  UseStrategyDetailOptions,
} from './useStrategyDetail'

export type {
  UseBacktestOptions,
} from './useBacktest'

export type {
  UseStrategyExecutionOptions,
  ManualOrderParams,
} from './useStrategyExecution'