/**
 * Global Type Declarations
 * Extensions to global objects and window interface
 */

declare global {
  interface Window {
    // Google Analytics
    gtag?: (command: string, targetId: string, config?: Record<string, any>) => void

    // Additional global properties can be added here
    dataLayer?: any[]

    // WebSocket connections
    websocketConnection?: WebSocket

    // Other global properties
    [key: string]: any
  }

  namespace NodeJS {
    interface ProcessEnv {
      NODE_ENV: 'development' | 'production' | 'test'
      [key: string]: string | undefined
    }
  }
}

export {}
