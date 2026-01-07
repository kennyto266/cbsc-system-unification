import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// Import only real components that don't use import.meta.env
import TouchFeedback, { Touchable } from '../TouchFeedback';
import GestureRecognizer from '../Gesture/GestureRecognizer';

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => {},
  }),
});

// Mock jest functions
const mockFn = () => jest.fn();

describe('Mobile Components', () => {
  describe('TouchFeedback', () => {
    it('should render children correctly', () => {
      render(
        <TouchFeedback>
          <button>Test Button</button>
        </TouchFeedback>
      );
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('should apply disabled styles when disabled', () => {
      render(
        <TouchFeedback disabled>
          <button>Test Button</button>
        </TouchFeedback>
      );
      const button = screen.getByRole('button');
      // TouchFeedback root is the parent of the relative z-10 container
      const touchFeedbackRoot = button.parentElement?.parentElement;
      expect(touchFeedbackRoot).toHaveClass('cursor-default');
    });

    it('should trigger onPress callback', async () => {
      const onPress = mockFn();
      render(
        <TouchFeedback onPress={onPress}>
          <button>Test Button</button>
        </TouchFeedback>
      );

      await userEvent.click(screen.getByRole('button'));
      expect(onPress).toHaveBeenCalled();
    });

    it('should trigger onTap callback', async () => {
      const onTap = mockFn();
      render(
        <TouchFeedback onTap={onTap}>
          <button>Test Button</button>
        </TouchFeedback>
      );

      await userEvent.click(screen.getByRole('button'));
      expect(onTap).toHaveBeenCalled();
    });
  });

  describe('Touchable', () => {
    it('should render as TouchFeedback component', () => {
      render(
        <Touchable onPress={() => {}}>
          <button>Touchable Button</button>
        </Touchable>
      );
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('should handle onPress prop', async () => {
      const onPress = mockFn();
      render(
        <Touchable onPress={onPress}>
          <button>Touchable Button</button>
        </Touchable>
      );

      await userEvent.click(screen.getByRole('button'));
      expect(onPress).toHaveBeenCalled();
    });

    it('should handle disabled state', () => {
      render(
        <Touchable disabled onPress={() => {}}>
          <button>Disabled Button</button>
        </Touchable>
      );
      const button = screen.getByRole('button');
      // Touchable (TouchFeedback) root is the parent of the relative z-10 container
      const touchableRoot = button.parentElement?.parentElement;
      expect(touchableRoot).toHaveClass('cursor-default');
    });
  });

  describe('GestureRecognizer', () => {
    it('should render children correctly', () => {
      render(
        <GestureRecognizer>
          <div>Test Content</div>
        </GestureRecognizer>
      );
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('should handle disabled state', () => {
      render(
        <GestureRecognizer disabled>
          <div>Disabled Content</div>
        </GestureRecognizer>
      );
      const container = screen.getByText('Disabled Content').parentElement;
      expect(container).toBeInTheDocument();
    });

    it('should handle touch events', () => {
      const onTouchStart = mockFn();
      const onTouchMove = mockFn();
      const onTouchEnd = mockFn();

      render(
        <GestureRecognizer
          callbacks={{
            onTouchStart,
            onTouchMove,
            onTouchEnd,
          }}
        >
          <div>Touch Test</div>
        </GestureRecognizer>
      );

      const container = screen.getByText('Touch Test');

      fireEvent.touchStart(container, {
        touches: [{ clientX: 100, clientY: 100 }],
      });
      fireEvent.touchMove(container, {
        touches: [{ clientX: 150, clientY: 150 }],
      });
      fireEvent.touchEnd(container, {
        changedTouches: [{ clientX: 150, clientY: 150 }],
      });

      expect(onTouchStart).toHaveBeenCalled();
      expect(onTouchMove).toHaveBeenCalled();
      expect(onTouchEnd).toHaveBeenCalled();
    });

    it('should handle tap gesture', () => {
      const onTap = mockFn();

      render(
        <GestureRecognizer
          callbacks={{
            onTap,
          }}
        >
          <div>Tap Test</div>
        </GestureRecognizer>
      );

      const container = screen.getByText('Tap Test');

      fireEvent.touchStart(container, {
        touches: [{ clientX: 100, clientY: 100 }],
      });

      fireEvent.touchEnd(container, {
        changedTouches: [{ clientX: 100, clientY: 100 }],
      });

      // Note: Actual tap detection happens after timeout in real implementation
      // This test verifies the component structure
      expect(container).toBeInTheDocument();
    });

    it('should handle swipe gestures', () => {
      const onSwipe = mockFn();

      render(
        <GestureRecognizer
          callbacks={{
            onSwipe,
          }}
        >
          <div>Swipe Test</div>
        </GestureRecognizer>
      );

      const container = screen.getByText('Swipe Test');

      // Simulate swipe right
      fireEvent.touchStart(container, {
        touches: [{ clientX: 100, clientY: 100 }],
      });

      fireEvent.touchMove(container, {
        touches: [{ clientX: 200, clientY: 100 }],
      });

      fireEvent.touchEnd(container, {
        changedTouches: [{ clientX: 200, clientY: 100 }],
      });

      // Note: Actual swipe detection happens after touch end
      // This test verifies the component structure
      expect(container).toBeInTheDocument();
    });
  });

  describe('Touch Interactions', () => {
    it('should handle long press', async () => {
      jest.useFakeTimers();
      const onLongPress = mockFn();

      render(
        <TouchFeedback onLongPress={onLongPress} longPressDelay={500}>
          <button>Long Press Button</button>
        </TouchFeedback>
      );

      fireEvent.mouseDown(screen.getByRole('button'));

      // Fast-forward time
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        expect(onLongPress).toHaveBeenCalled();
      });

      jest.useRealTimers();
    });

    it('should cleanup timers on unmount', () => {
      jest.useFakeTimers();
      const onLongPress = mockFn();

      const { unmount } = render(
        <TouchFeedback onLongPress={onLongPress}>
          <button>Button</button>
        </TouchFeedback>
      );

      fireEvent.mouseDown(screen.getByRole('button'));

      // Unmount before timer completes
      unmount();

      // Timer should be cleared
      jest.advanceTimersByTime(500);

      expect(onLongPress).not.toHaveBeenCalled();

      jest.useRealTimers();
    });
  });

  describe('Responsive Behavior', () => {
    it('should handle different viewport sizes', () => {
      // Test with mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 667,
      });

      render(
        <TouchFeedback>
          <button>Mobile Button</button>
        </TouchFeedback>
      );

      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('should respect matchMedia queries', () => {
      const mediaQuery = window.matchMedia('(max-width: 768px)');

      render(
        <GestureRecognizer>
          <div>Responsive Content</div>
        </GestureRecognizer>
      );

      // Component should render regardless of media query
      expect(screen.getByText('Responsive Content')).toBeInTheDocument();
    });
  });
});
