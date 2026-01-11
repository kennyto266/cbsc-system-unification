import React from 'react'

/**
 * Footer - Application footer component
 */
export const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="bg-card border-t border-border py-4 px-6">
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <div className="flex items-center space-x-4">
          <span>© {currentYear} CBSC Quantitative Trading System</span>
          <span>•</span>
          <span>Version 1.0.0</span>
        </div>

        <div className="flex items-center space-x-4">
          <a
            href="/docs"
            className="hover:text-foreground transition-colors"
          >
            Documentation
          </a>
          <a
            href="/support"
            className="hover:text-foreground transition-colors"
          >
            Support
          </a>
          <a
            href="/privacy"
            className="hover:text-foreground transition-colors"
          >
            Privacy Policy
          </a>
        </div>
      </div>
    </footer>
  )
}

export default Footer