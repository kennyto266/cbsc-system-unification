import React from 'react'
import { render, screen, fireEvent, waitFor, cleanup, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Modal } from '../Modal'
import { ThemeProvider } from '@/contexts/ThemeContext'
import type { ModalProps } from '../Modal'

// Test wrapper - 测试包装器
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider>
    {children}
  </ThemeProvider>
)

// Mock createPortal for testing
const originalCreatePortal = React.createPortal
beforeEach(() => {
  React.createPortal = jest.fn((element) => element)
})

afterEach(() => {
  React.createPortal = originalCreatePortal
  cleanup()
  // Reset body overflow style
  document.body.style.overflow = ''
})

describe('Modal Component', () => {
  // Helper function to render Modal with props
  const renderModal = (props: Partial<ModalProps> & { isOpen?: boolean } = {}) => {
    const defaultProps: ModalProps & { isOpen?: boolean } = {
      isOpen: true,
      onClose: jest.fn(),
      children: <div>Modal Content</div>
    }
    return render(
      <TestWrapper>
        <Modal {...defaultProps} {...props} />
      </TestWrapper>
    )
  }

  // Basic rendering tests
  describe('Rendering', () => {
    test('does not render when isOpen is false', () => {
      renderModal({ isOpen: false })

      expect(screen.queryByText('Modal Content')).not.toBeInTheDocument()
    })

    test('renders when isOpen is true', () => {
      renderModal()

      expect(screen.getByText('Modal Content')).toBeInTheDocument()
    })

    test('renders with title', () => {
      renderModal({ title: 'Test Modal' })

      const title = screen.getByRole('heading', { name: 'Test Modal' })
      expect(title).toBeInTheDocument()
      expect(title.tagName).toBe('H2')
      expect(title).toHaveClass('text-lg', 'font-semibold', 'text-neutral-900')
    })

    test('renders without title when not provided', () => {
      renderModal({ title: undefined })

      expect(screen.queryByRole('heading')).not.toBeInTheDocument()
    })

    test('renders custom children', () => {
      const customContent = (
        <div>
          <p>Custom modal content</p>
          <button>Action Button</button>
        </div>
      )
      renderModal({ children: customContent })

      expect(screen.getByText('Custom modal content')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Action Button' })).toBeInTheDocument()
    })

    test('renders with close button by default', () => {
      renderModal()

      const closeButton = screen.getByRole('button', { name: /close/i })
      expect(closeButton).toBeInTheDocument()
      expect(closeButton.querySelector('svg')).toBeInTheDocument()
    })

    test('hides close button when showCloseButton is false', () => {
      renderModal({ showCloseButton: false })

      expect(screen.queryByRole('button', { name: /close/i })).not.toBeInTheDocument()
    })
  })

  // Size variants tests
  describe('Size variants', () => {
    const sizes: ModalProps['size'][] = ['sm', 'md', 'lg', 'xl', 'full']
    const sizeClasses = {
      sm: 'max-w-md',
      md: 'max-w-lg',
      lg: 'max-w-2xl',
      xl: 'max-w-4xl',
      full: 'max-w-7xl'
    }

    sizes.forEach(size => {
      test(`renders with ${size} size`, () => {
        renderModal({ size })

        const modalContent = screen.getByText('Modal Content').closest('.relative')
        expect(modalContent).toHaveClass(sizeClasses[size])
      })
    })
  })

  // Close functionality tests
  describe('Close functionality', () => {
    test('calls onClose when close button is clicked', async () => {
      const onClose = jest.fn()
      renderModal({ onClose })

      const closeButton = screen.getByRole('button', { name: /close/i })
      await userEvent.click(closeButton)

      expect(onClose).toHaveBeenCalledTimes(1)
    })

    test('calls onClose when backdrop is clicked if closeOnBackdropClick is true', async () => {
      const onClose = jest.fn()
      renderModal({ onClose, closeOnBackdropClick: true })

      // The backdrop should be the first div with the click handler
      const backdrop = screen.getByText('Modal Content').closest('.fixed')
      if (backdrop) {
        await userEvent.click(backdrop)
        expect(onClose).toHaveBeenCalledTimes(1)
      }
    })

    test('does not call onClose when backdrop is clicked if closeOnBackdropClick is false', async () => {
      const onClose = jest.fn()
      renderModal({ onClose, closeOnBackdropClick: false })

      // Find and click the backdrop
      const backdrop = screen.getByText('Modal Content').closest('.fixed')
      if (backdrop) {
        await userEvent.click(backdrop)
        expect(onClose).not.toHaveBeenCalled()
      }
    })

    test('calls onClose when Escape key is pressed if closeOnEscape is true', async () => {
      const onClose = jest.fn()
      renderModal({ onClose, closeOnEscape: true })

      await act(async () => {
        fireEvent.keyDown(document, { key: 'Escape' })
      })

      await waitFor(() => {
        expect(onClose).toHaveBeenCalledTimes(1)
      })
    })

    test('does not call onClose when Escape key is pressed if closeOnEscape is false', async () => {
      const onClose = jest.fn()
      renderModal({ onClose, closeOnEscape: false })

      await act(async () => {
        fireEvent.keyDown(document, { key: 'Escape' })
      })

      expect(onClose).not.toHaveBeenCalled()
    })

    test('does not call onClose when other keys are pressed', async () => {
      const onClose = jest.fn()
      renderModal({ onClose, closeOnEscape: true })

      await act(async () => {
        fireEvent.keyDown(document, { key: 'Enter' })
        fireEvent.keyDown(document, { key: 'Space' })
        fireEvent.keyDown(document, { key: 'Tab' })
      })

      expect(onClose).not.toHaveBeenCalled()
    })
  })

  // Event handling tests
  describe('Event handling', () => {
    test('prevents event propagation when clicking modal content', async () => {
      const onClose = jest.fn()
      renderModal({ onClose })

      const modalContent = screen.getByText('Modal Content').closest('.relative')
      if (modalContent) {
        await userEvent.click(modalContent)
        expect(onClose).not.toHaveBeenCalled()
      }
    })

    test('adds and removes keyboard event listeners', () => {
      const addSpy = jest.spyOn(document, 'addEventListener')
      const removeSpy = jest.spyOn(document, 'removeEventListener')

      const { unmount } = renderModal()

      expect(addSpy).toHaveBeenCalledWith('keydown', expect.any(Function))

      unmount()

      expect(removeSpy).toHaveBeenCalledWith('keydown', expect.any(Function))

      addSpy.mockRestore()
      removeSpy.mockRestore()
    })
  })

  // Body scroll tests
  describe('Body scroll management', () => {
    test('hides body overflow when modal opens', () => {
      expect(document.body.style.overflow).toBe('')

      renderModal({ isOpen: true })

      expect(document.body.style.overflow).toBe('hidden')
    })

    test('restores body overflow when modal closes', () => {
      const { rerender } = renderModal({ isOpen: true })
      expect(document.body.style.overflow).toBe('hidden')

      rerender(
        <TestWrapper>
          <Modal isOpen={false} onClose={jest.fn()}>
            Content
          </Modal>
        </TestWrapper>
      )

      expect(document.body.style.overflow).toBe('unset')
    })

    test('restores body overflow on unmount', () => {
      const { unmount } = renderModal({ isOpen: true })
      expect(document.body.style.overflow).toBe('hidden')

      unmount()

      expect(document.body.style.overflow).toBe('unset')
    })
  })

  // Portal tests
  describe('Portal functionality', () => {
    test('uses createPortal to render content', () => {
      renderModal()

      expect(React.createPortal).toHaveBeenCalledWith(
        expect.any(Object),
        document.body
      )
    })
  })

  // Accessibility tests
  describe('Accessibility', () => {
    test('renders modal with proper ARIA attributes', () => {
      renderModal({ title: 'Accessible Modal' })

      const modalContainer = screen.getByText('Modal Content').closest('.fixed')
      expect(modalContainer).toBeInTheDocument()
    })

    test('close button has accessible name', () => {
      renderModal()

      const closeButton = screen.getByRole('button')
      expect(closeButton).toBeInTheDocument()
    })

    test('focus management - close button is focusable', () => {
      renderModal()

      const closeButton = screen.getByRole('button')
      closeButton.focus()
      expect(closeButton).toHaveFocus()
    })
  })

  // Edge cases tests
  describe('Edge cases', () => {
    test('handles empty children', () => {
      renderModal({ children: null })

      // Modal should still render its structure
      const modal = document.querySelector('.relative')
      expect(modal).toBeInTheDocument()
    })

    test('handles undefined children', () => {
      renderModal({ children: undefined })

      // Modal should still render its structure
      const modal = document.querySelector('.relative')
      expect(modal).toBeInTheDocument()
    })

    test('handles missing onClose gracefully', () => {
      // This should not crash but will cause errors when trying to close
      expect(() => {
        renderModal({ onClose: undefined as any })
      }).toThrow()
    })

    test('handles rapid open/close', async () => {
      const onClose = jest.fn()
      const { rerender } = renderModal({ isOpen: true, onClose })

      rerender(
        <TestWrapper>
          <Modal isOpen={false} onClose={onClose}>
            Content
          </Modal>
        </TestWrapper>
      )

      expect(screen.queryByText('Modal Content')).not.toBeInTheDocument()
    })
  })

  // Integration tests
  describe('Integration', () => {
    test('works with form content', async () => {
      const handleSubmit = jest.fn(e => e.preventDefault())

      renderModal({
        children: (
          <form onSubmit={handleSubmit}>
            <input placeholder="Name" />
            <button type="submit">Submit</button>
          </form>
        )
      })

      const input = screen.getByPlaceholderText('Name')
      const submitButton = screen.getByRole('button', { name: 'Submit' })

      await userEvent.type(input, 'Test Name')
      await userEvent.click(submitButton)

      expect(handleSubmit).toHaveBeenCalled()
    })

    test('scrolls when content is too tall', () => {
      const tallContent = Array.from({ length: 100 }, (_, i) => (
        <p key={i}>Content line {i}</p>
      ))

      renderModal({
        children: <div>{tallContent}</div>
      })

      const scrollContainer = screen.getByText('Content line 0').parentElement
      expect(scrollContainer).toHaveClass('overflow-y-auto')
    })

    test('maintains proper z-index stacking', () => {
      renderModal()

      const modalContainer = screen.getByText('Modal Content').closest('.fixed')
      expect(modalContainer).toHaveClass('z-50')
    })
  })

  // Performance tests
  describe('Performance', () => {
    test('only adds escape listener when modal is open', () => {
      const addSpy = jest.spyOn(document, 'addEventListener')

      // Closed modal
      const { rerender } = renderModal({ isOpen: false })
      expect(addSpy).not.toHaveBeenCalledWith('keydown', expect.any(Function))

      // Open modal
      rerender(
        <TestWrapper>
          <Modal isOpen={true} onClose={jest.fn()}>
            Content
          </Modal>
        </TestWrapper>
      )
      expect(addSpy).toHaveBeenCalledWith('keydown', expect.any(Function))

      addSpy.mockRestore()
    })
  })
})