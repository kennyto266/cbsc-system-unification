/**
 * ErrorBoundary.tsx - React Error Boundary
 *
 * Catches JavaScript errors anywhere in the component tree,
 * logs those errors, and displays a fallback UI.
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error Boundary Component
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log the full error details to console
    console.error('=== ERROR BOUNDARY CAUGHT ===');
    console.error('Error:', error);
    console.error('Error Message:', error.message);
    console.error('Error Stack:', error.stack);
    console.error('Component Stack:', errorInfo.componentStack);
    console.error('Error Info:', errorInfo);

    // Also log to window for visibility
    (window as any).__lastError = {
      error,
      errorInfo,
      timestamp: new Date().toISOString(),
    };
  }

  render(): ReactNode {
    if (this.state.hasError) {
      // Custom fallback UI
      return (
        <div style={{ padding: '20px', backgroundColor: '#fee', border: '1px solid #f00' }}>
          <h1>Something went wrong.</h1>
          <h2>Error Details:</h2>
          <pre style={{ whiteSpace: 'pre-wrap', backgroundColor: '#fff', padding: '10px' }}>
            {this.state.error?.toString()}
          </pre>
          <h3>Stack Trace:</h3>
          <pre style={{ whiteSpace: 'pre-wrap', backgroundColor: '#fff', padding: '10px', maxHeight: '400px', overflow: 'auto' }}>
            {this.state.error?.stack}
          </pre>
          <h3>Component Stack:</h3>
          <pre style={{ whiteSpace: 'pre-wrap', backgroundColor: '#fff', padding: '10px', maxHeight: '200px', overflow: 'auto' }}>
            {this.state.errorInfo?.componentStack}
          </pre>
          <button onClick={() => window.location.reload()}>Reload Page</button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
