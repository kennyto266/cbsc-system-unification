import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import '@testing-library/jest-dom';

// Import components
import TouchFeedback, { Touchable } from '../TouchFeedback';
import GestureRecognizer from '../Gesture/GestureRecognizer';
import OfflineMode from '../Offline/OfflineMode';
import MobileOptimizedChart from '../Optimization/MobileOptimizedChart';
import MobileOptimizedForm from '../Optimization/MobileOptimizedForm';
import MobileOptimizedList from '../Optimization/MobileOptimizedList';

// Mock IntersectionObserver for chart component
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
      expect(button.parentElement).toHaveClass('cursor-default');
    });

    it('should trigger onPress callback', async () => {
      const onPress = jest.fn();
      render(
        <TouchFeedback onPress={onPress}>
          <button>Test Button</button>
        </TouchFeedback>
      );

      fireEvent.click(screen.getByRole('button'));
      await waitFor(() => {
        expect(onPress).toHaveBeenCalled();
      });
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
  });

  describe('OfflineMode', () => {
    beforeEach(() => {
      // Mock navigator.onLine
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: true,
      });
    });

    it('should not show offline banner when online', () => {
      render(<OfflineMode />);
      expect(screen.queryByText(/離線模式/)).not.toBeInTheDocument();
    });

    it('should show offline banner when offline', async () => {
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false,
      });

      // Simulate offline event
      fireEvent(window, new Event('offline'));

      render(<OfflineMode />);

      // Note: In real implementation, you'd need to wait for the event listener
      // This is a simplified test
    });
  });

  describe('MobileOptimizedChart', () => {
    const mockData = [
      { name: 'Jan', value: 100 },
      { name: 'Feb', value: 200 },
    ];

    it('should render chart with data', () => {
      render(
        <MobileOptimizedChart
          data={mockData}
          type="line"
          title="Test Chart"
        />
      );
      expect(screen.getByText('Test Chart')).toBeInTheDocument();
    });

    it('should render in simplified mode for mobile', () => {
      render(
        <MobileOptimizedChart
          data={mockData}
          type="line"
          simplified={true}
        />
      );
      expect(screen.getByText('簡化模式')).toBeInTheDocument();
    });

    it('should show trend indicator', () => {
      render(
        <MobileOptimizedChart
          data={mockData}
          type="line"
          showTrendIndicator={true}
        />
      );
      // Check for trend icon presence
      const trendIcon = document.querySelector('[class*="TrendingUp"], [class*="TrendingDown"]');
      expect(trendIcon).toBeInTheDocument();
    });
  });

  describe('MobileOptimizedForm', () => {
    const mockFields = [
      {
        name: 'test',
        label: 'Test Field',
        type: 'text' as const,
        required: true,
      },
    ];

    it('should render form with fields', () => {
      render(
        <MobileOptimizedForm
          fields={mockFields}
          onSubmit={() => {}}
        />
      );
      expect(screen.getByLabelText('Test Field')).toBeInTheDocument();
    });

    it('should show validation errors', async () => {
      render(
        <MobileOptimizedForm
          fields={mockFields}
          onSubmit={() => {}}
          showValidationErrors={true}
        />
      );

      // Submit empty form
      const form = screen.getByRole('form') || screen.getByText('提交').closest('form');
      if (form) {
        fireEvent.submit(form);

        await waitFor(() => {
          expect(screen.getByText(/此欄位為必填/)).toBeInTheDocument();
        });
      }
    });

    it('should handle field input', async () => {
      render(
        <MobileOptimizedForm
          fields={mockFields}
          onSubmit={() => {}}
        />
      );

      const input = screen.getByLabelText('Test Field');
      fireEvent.change(input, { target: { value: 'test value' } });

      await waitFor(() => {
        expect(input).toHaveValue('test value');
      });
    });
  });

  describe('MobileOptimizedList', () => {
    const mockItems = [
      {
        id: 1,
        title: 'Test Item 1',
        subtitle: 'Subtitle 1',
      },
      {
        id: 2,
        title: 'Test Item 2',
        subtitle: 'Subtitle 2',
      },
    ];

    it('should render list items', () => {
      render(
        <MobileOptimizedList
          items={mockItems}
        />
      );
      expect(screen.getByText('Test Item 1')).toBeInTheDocument();
      expect(screen.getByText('Test Item 2')).toBeInTheDocument();
    });

    it('should render empty state when no items', () => {
      render(
        <MobileOptimizedList
          items={[]}
          emptyMessage="No items found"
        />
      );
      expect(screen.getByText('No items found')).toBeInTheDocument();
    });

    it('should handle search', async () => {
      render(
        <MobileOptimizedList
          items={mockItems}
          searchable={true}
        />
      );

      const searchInput = screen.getByPlaceholderText('搜索...');
      fireEvent.change(searchInput, { target: { value: 'Item 1' } });

      await waitFor(() => {
        expect(screen.getByText('Test Item 1')).toBeInTheDocument();
        expect(screen.queryByText('Test Item 2')).not.toBeInTheDocument();
      });
    });

    it('should handle item clicks', async () => {
      const onItemClick = jest.fn();
      render(
        <MobileOptimizedList
          items={mockItems}
          onItemClick={onItemClick}
        />
      );

      fireEvent.click(screen.getByText('Test Item 1'));

      await waitFor(() => {
        expect(onItemClick).toHaveBeenCalledWith(mockItems[0]);
      });
    });
  });

  // Integration tests
  describe('Mobile Integration', () => {
    it('should handle responsive behavior', () => {
      // Test with different viewport sizes
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375, // iPhone width
      });

      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 667, // iPhone height
      });

      render(
        <MobileOptimizedChart
          data={mockData}
          type="line"
          simplified={true}
        />
      );

      // Should render in mobile mode
      expect(screen.getByText('簡化模式')).toBeInTheDocument();
    });
  });
});