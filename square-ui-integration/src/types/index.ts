// Re-export all types
export * from './api'
export * from './auth'
export * from './strategy'
export * from './market'
export * from './user'
export * from './common'

// Global type declarations
declare global {
  interface Window {
    __APP_VERSION__?: string
  }
}