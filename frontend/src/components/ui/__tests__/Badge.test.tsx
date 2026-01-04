import React from 'react'
import { render, screen, cleanup } from '@testing-library/react'
import { Badge } from '../Badge'
import type { BadgeProps } from '../Badge'

describe('Badge Component', () => {
  // Helper function to render Badge with props
  const renderBadge = (props: Partial<BadgeProps> = {}) => {
    const defaultProps: BadgeProps = {
      children: 'Test Badge'
    }
    return render(<Badge {...defaultProps} {...props} />)
  }

  afterEach(() => {
    cleanup()
  })

  // Basic rendering tests
  describe('Rendering', () => {
    test('renders with default props', () => {
      renderBadge()

      const badge = screen.getByText('Test Badge')
      expect(badge).toBeInTheDocument()
      expect(badge.tagName).toBe('SPAN')
      expect(badge).toHaveClass(
        'inline-flex',
        'items-center',
        'font-medium',
        'bg-primary-100',
        'text-primary-800',
        'px-2.5',
        'py-0.5',
        'text-sm',
        'rounded-full'
      )
    })

    test('renders with custom className', () => {
      renderBadge({ className: 'custom-badge' })

      const badge = screen.getByText('Test Badge')
      expect(badge).toHaveClass('custom-badge')
    })

    test('renders with different content types', () => {
      const contents = [
        'Text Badge',
        123,
        <span key="complex">Complex Content</span>,
        <>
          <span key="1">Multi</span>
          <span key="2">Part</span>
        </>
      ]

      contents.forEach((content, index) => {
        const { unmount } = renderBadge({
          children: content,
          'data-testid': `badge-${index}`
        })

        const badge = screen.getByTestId(`badge-${index}`)
        expect(badge).toBeInTheDocument()
        unmount()
      })
    })

    test('renders as React element with additional props', () => {
      renderBadge({
        id: 'test-badge',
        'data-value': 'custom-data',
        role: 'status'
      })

      const badge = screen.getByText('Test Badge')
      expect(badge).toHaveAttribute('id', 'test-badge')
      expect(badge).toHaveAttribute('data-value', 'custom-data')
      expect(badge).toHaveAttribute('role', 'status')
    })
  })

  // Variant tests
  describe('Variants', () => {
    test('renders all variant types correctly', () => {
      const variants: BadgeProps['variant'][] = [
        'primary',
        'success',
        'warning',
        'error',
        'neutral'
      ]

      variants.forEach(variant => {
        const { unmount } = renderBadge({
          variant,
          children: `${variant} Badge`,
          'data-testid': `badge-${variant}`
        })

        const badge = screen.getByTestId(`badge-${variant}`)
        expect(badge).toBeInTheDocument()
        expect(badge).toHaveClass(`bg-${variant}-100`, `text-${variant}-800`)
        unmount()
      })
    })

    test('applies correct variant styles', () => {
      const variantClasses = {
        primary: ['bg-primary-100', 'text-primary-800'],
        success: ['bg-success-100', 'text-success-800'],
        warning: ['bg-warning-100', 'text-warning-800'],
        error: ['bg-error-100', 'text-error-800'],
        neutral: ['bg-neutral-100', 'text-neutral-800']
      }

      Object.entries(variantClasses).forEach(([variant, expectedClasses]) => {
        const { unmount } = renderBadge({
          variant: variant as BadgeProps['variant'],
          children: `${variant} Badge`
        })

        const badge = screen.getByText(`${variant} Badge`)
        expectedClasses.forEach(className => {
          expect(badge).toHaveClass(className)
        })
        unmount()
      })
    })
  })

  // Size tests
  describe('Sizes', () => {
    test('renders all size variants correctly', () => {
      const sizes: BadgeProps['size'][] = ['xs', 'sm', 'md', 'lg']
      const sizeClasses = {
        xs: ['px-1.5', 'py-0.5', 'text-xs'],
        sm: ['px-2', 'py-0.5', 'text-xs'],
        md: ['px-2.5', 'py-0.5', 'text-sm'],
        lg: ['px-3', 'py-1', 'text-sm']
      }

      sizes.forEach(size => {
        const { unmount } = renderBadge({
          size,
          children: `${size} Badge`,
          'data-testid': `badge-${size}`
        })

        const badge = screen.getByTestId(`badge-${size}`)
        expect(badge).toBeInTheDocument()

        const expectedClasses = sizeClasses[size]
        expectedClasses.forEach(className => {
          expect(badge).toHaveClass(className)
        })

        unmount()
      })
    })

    test('maintains variant classes with different sizes', () => {
      const { unmount } = renderBadge({
        variant: 'success',
        size: 'lg',
        children: 'Large Success Badge'
      })

      const badge = screen.getByText('Large Success Badge')
      expect(badge).toHaveClass(
        'bg-success-100',
        'text-success-800',
        'px-3',
        'py-1',
        'text-sm'
      )

      unmount()
    })
  })

  // Rounded prop tests
  describe('Rounded prop', () => {
    test('renders with rounded corners by default', () => {
      renderBadge()

      const badge = screen.getByText('Test Badge')
      expect(badge).toHaveClass('rounded-full')
    })

    test('renders with rounded when rounded prop is true', () => {
      renderBadge({ rounded: true })

      const badge = screen.getByText('Test Badge')
      expect(badge).toHaveClass('rounded-full')
      expect(badge).not.toHaveClass('rounded-md')
    })

    test('renders with medium rounded when rounded prop is false', () => {
      renderBadge({ rounded: false })

      const badge = screen.getByText('Test Badge')
      expect(badge).toHaveClass('rounded-md')
      expect(badge).not.toHaveClass('rounded-full')
    })
  })

  // HTML attribute tests
  describe('HTML attributes', () => {
    test('passes through all HTML attributes', () => {
      renderBadge({
        id: 'my-badge',
        role: 'status',
        'aria-label': 'Status Badge',
        title: 'Badge tooltip',
        style: { cursor: 'pointer' },
        onClick: jest.fn()
      })

      const badge = screen.getByText('Test Badge')
      expect(badge).toHaveAttribute('id', 'my-badge')
      expect(badge).toHaveAttribute('role', 'status')
      expect(badge).toHaveAttribute('aria-label', 'Status Badge')
      expect(badge).toHaveAttribute('title', 'Badge tooltip')
    })

    test('applies custom styles', () => {
      renderBadge({
        style: {
          backgroundColor: 'red',
          color: 'white',
          fontWeight: 'bold'
        }
      })

      const badge = screen.getByText('Test Badge')
      expect(badge).toBeInTheDocument()
      expect(badge).toHaveAttribute('style')
      // Style properties are applied via inline styles
      expect(badge.style.backgroundColor).toBe('red')
      expect(badge.style.color).toBe('white')
      expect(badge.style.fontWeight).toBe('bold')
    })
  })

  // Accessibility tests
  describe('Accessibility', () => {
    test('supports ARIA attributes', () => {
      renderBadge({
        role: 'status',
        'aria-live': 'polite',
        'aria-atomic': 'true'
      })

      const badge = screen.getByText('Test Badge')
      expect(badge).toHaveAttribute('role', 'status')
      expect(badge).toHaveAttribute('aria-live', 'polite')
      expect(badge).toHaveAttribute('aria-atomic', 'true')
    })

    test('supports ARIA labeling', () => {
      renderBadge({
        'aria-label': 'New notifications',
        children: '5'
      })

      const badge = screen.getByText('5')
      expect(badge).toHaveAttribute('aria-label', 'New notifications')
    })

    test('supports ARIA describedby', () => {
      renderBadge({
        'aria-describedby': 'badge-description',
        children: 'Status'
      })

      const badge = screen.getByText('Status')
      expect(badge).toHaveAttribute('aria-describedby', 'badge-description')
    })
  })

  // Integration tests
  describe('Integration', () => {
    test('works inside other components', () => {
      render(
        <div className="flex items-center space-x-2">
          <span>Notifications:</span>
          <Badge variant="error" size="sm">3</Badge>
        </div>
      )

      expect(screen.getByText('Notifications:')).toBeInTheDocument()
      const badge = screen.getByText('3')
      expect(badge).toHaveClass(
        'bg-error-100',
        'text-error-800',
        'px-2',
        'py-0.5',
        'text-xs'
      )
    })

    test('works as status indicator', () => {
      const statuses = [
        { variant: 'success' as const, label: 'Online', color: 'green' },
        { variant: 'error' as const, label: 'Offline', color: 'red' },
        { variant: 'warning' as const, label: 'Away', color: 'yellow' }
      ]

      render(
        <div>
          {statuses.map(status => (
            <div key={status.label} className="flex items-center space-x-2">
              <Badge
                variant={status.variant}
                size="xs"
                rounded
                data-testid={`status-${status.label}`}
              >
                ●
              </Badge>
              <span>{status.label}</span>
            </div>
          ))}
        </div>
      )

      statuses.forEach(status => {
        const statusBadge = screen.getByTestId(`status-${status.label}`)
        expect(statusBadge).toBeInTheDocument()
        expect(statusBadge).toHaveClass(`bg-${status.variant}-100`)
      })
    })

    test('works for notification count', () => {
      render(
        <button className="relative">
          <span>Inbox</span>
          <Badge
            variant="error"
            size="xs"
            className="absolute -top-1 -right-1"
            data-testid="notification-badge"
          >
            99+
          </Badge>
        </button>
      )

      const badge = screen.getByTestId('notification-badge')
      expect(badge).toHaveTextContent('99+')
      expect(badge).toHaveClass('absolute', '-top-1', '-right-1')
    })
  })

  // Edge cases
  describe('Edge cases', () => {
    test('renders with empty content', () => {
      const { container } = renderBadge({ children: '' })

      // Use querySelector to avoid multiple empty text matches
      const badge = container.querySelector('span')
      expect(badge).toBeInTheDocument()
      expect(badge).toHaveClass('inline-flex', 'items-center')
    })

    test('renders with null children', () => {
      renderBadge({ children: null })

      const badge = document.querySelector('span')
      expect(badge).toBeInTheDocument()
      expect(badge?.textContent).toBe('')
    })

    test('renders with undefined children', () => {
      renderBadge({ children: undefined })

      const badge = document.querySelector('span')
      expect(badge).toBeInTheDocument()
      expect(badge?.textContent).toBe('')
    })

    test('handles very long content', () => {
      const longText = 'This is a very long badge text that might overflow'
      renderBadge({ children: longText })

      const badge = screen.getByText(longText)
      expect(badge).toBeInTheDocument()
      expect(badge).toHaveClass('inline-flex', 'items-center', 'font-medium')
    })
  })

  // Performance tests
  describe('Performance', () => {
    test('renders many badges efficiently', () => {
      const count = 100
      render(
        <div data-testid="badge-container">
          {Array.from({ length: count }, (_, i) => (
            <Badge
              key={i}
              variant={i % 2 === 0 ? 'primary' : 'success'}
              size="sm"
            >
              Badge {i}
            </Badge>
          ))}
        </div>
      )

      const container = screen.getByTestId('badge-container')
      expect(container.children.length).toBe(count)
    })
  })
})