/** @type {import('jest').Config} */
module.exports = {
  // Test environment
  testEnvironment: 'jsdom',

  // Setup files
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],

  // Ensure DOM is properly set up
  testEnvironmentOptions: {
    url: 'http://localhost:3000',
  },

  // Module file extensions
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],

  // Module name mapping for absolute imports
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@hooks/(.*)$': '<rootDir>/src/hooks/$1',
    '^@types/(.*)$': '<rootDir>/src/types/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1',
    '^@api/(.*)$': '<rootDir>/src/api/$1',
    '^@store/(.*)$': '<rootDir>/src/store/$1',
    '^@services/(.*)$': '<rootDir>/src/services/$1',
    '^@contexts/(.*)$': '<rootDir>/src/contexts/$1',
    '^@pages/(.*)$': '<rootDir>/src/pages/$1',
    '^@styles/(.*)$': '<rootDir>/src/styles/$1',
    '^@shared/(.*)$': '<rootDir>/src/shared/$1',
    '^@config/(.*)$': '<rootDir>/src/config/$1',
    // Asset file mocking
    '\\.(css|less|scss|sass)$': '<rootDir>/config/jest/cssTransform.js',
    '\\.(jpg|jpeg|png|gif|svg|ico)$': '<rootDir>/src/__mocks__/fileMock.js',
  },

  // Transform patterns
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', {
      tsconfig: {
        jsx: 'react-jsx',
        esModuleInterop: true,
        allowSyntheticDefaultImports: true,
      },
    }],
    '^.+\\.(js|jsx)$': 'babel-jest',
    '^.+\\.(css|less|scss|sass)$': '<rootDir>/config/jest/cssTransform.js',
  },

  // Test match patterns
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{ts,tsx,js,jsx}',
    '<rootDir>/src/**/*.{test,spec}.{ts,tsx,js,jsx}',
  ],

  // Coverage configuration
  collectCoverageFrom: [
    'src/**/*.{ts,tsx,js,jsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{ts,tsx}',
    '!src/**/index.ts',
    '!src/setupTests.ts',
    '!src/main.tsx',
    '!src/vite-env.d.ts',
    '!src/test/**/*',
    '!src/utils/**/*',
    '!src/types/**/*',
    '!src/views/**/*',
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html', 'json'],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },

  // Ignore patterns
  testPathIgnorePatterns: [
    '/node_modules/',
    '/coverage/',
    '/dist/',
    '/build/',
    '/src/test/',
    '/src/utils/',
    '/src/types/',
    '/src/views/',
  ],

  // Mock configurations
  clearMocks: true,
  restoreMocks: true,
  resetMocks: true,

  // Test timeout
  testTimeout: 30000,

  // Verbose output
  verbose: false,

  // Globals for import.meta.env support
  globals: {
    'import.meta': {
      env: {
        VITE_API_BASE_URL: 'http://localhost:3007',
        VITE_WS_BASE_URL: 'ws://localhost:3007',
        VITE_API_TIMEOUT: '30000',
        VITE_ENABLE_MOCKING: 'false',
        VITE_LOG_LEVEL: 'info',
        DEV: false,
        MODE: 'test',
        PROD: false,
      },
    },
  },
}