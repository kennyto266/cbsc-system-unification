/**
 * API Integration Layer Entry Point
 * Entry point for the unified API integration layer
 */

// Export API client
export { apiClient } from './client'

// Export API services
export * from './services/auth'
export * from './services/users'
export * from './services/strategies'
export * from './services/indicators'
export * from './services/market'
export * from './services/websocket'

// Export types
export * from './types/common'
export * from './types/auth'
export * from './types/strategies'
export * from './types/indicators'
export * from './types/market'

// Export utilities
export * from './utils/validation'
export * from './utils/transform'
export * from './utils/cache'

// Export configuration
export * from './config'

// Initialize API layer
export { initializeApi } from './init'