import React from 'react';
import { render, screen, waitFor, fireEvent, userEvent } from '../utils/testUtils';
import { rest } from 'msw';
import { server } from '../setup/server';

// Import components to test
import { StrategyList } from '../../components/strategies/StrategyList';
import { StrategyCard } from '../../components/strategies/StrategyCard';
import { StrategyForm } from '../../components/strategies/StrategyForm';
import { Dashboard } from '../../pages/Dashboard';

describe('Strategy Dashboard Integration Tests', () => {
  beforeEach(() => {
    integrationUtils.login();
  });

  describe('Strategy List Component', () => {
    test('should render strategy list with data from API', async () => {
      render(<StrategyList />);
      
      // Wait for strategies to load
      await waitFor(() => {
        expect(screen.getByText('Strategy 1-1')).toBeInTheDocument();
      });
      
      // Check if all expected strategies are rendered
      expect(screen.getAllByTestId(/strategy-card-/i)).toHaveLength(10);
    });

    test('should handle loading state', () => {
      // Mock slow API response
      server.use(
        rest.get('*/strategies', (req, res, ctx) => {
          return res(ctx.delay(1000));
        })
      );

      render(<StrategyList />);
      
      // Should show loading indicator
      expect(screen.getByTestId('strategies-loading')).toBeInTheDocument();
    });

    test('should handle error state', async () => {
      // Mock API error
      server.use(
        rest.get('*/strategies', (req, res, ctx) => {
          return res(
            ctx.status(500),
            ctx.json({
              success: false,
              error: 'Failed to fetch strategies',
            })
          );
        })
      );

      render(<StrategyList />);
      
      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument();
      });
    });

    test('should refresh strategy list', async () => {
      render(<StrategyList />);
      
      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('Strategy 1-1')).toBeInTheDocument();
      });
      
      // Click refresh button
      const refreshButton = screen.getByTestId('refresh-strategies');
      fireEvent.click(refreshButton);
      
      // Should show loading state again
      expect(screen.getByTestId('strategies-loading')).toBeInTheDocument();
    });

    test('should filter strategies', async () => {
      render(<StrategyList />);
      
      await waitFor(() => {
        expect(screen.getByText('Strategy 1-1')).toBeInTheDocument();
      });
      
      // Filter by status
      const statusFilter = screen.getByTestId('status-filter');
      fireEvent.change(statusFilter, { target: { value: 'active' } });
      
      // Wait for filtered results
      await waitFor(() => {
        const activeStrategies = screen.getAllByTestId(/strategy-card-/i);
        activeStrategies.forEach(card => {
          expect(card).toHaveTextContent('active');
        });
      });
    });
  });

  describe('Strategy Card Component', () => {
    test('should display strategy details correctly', async () => {
      const strategy = integration.createTestData.strategy();
      
      render(<StrategyCard strategy={strategy} />);
      
      expect(screen.getByText(strategy.name)).toBeInTheDocument();
      expect(screen.getByText(strategy.description)).toBeInTheDocument();
      expect(screen.getByTestId(`strategy-status-${strategy.status}`)).toBeInTheDocument();
      expect(screen.getByTestId('strategy-total-return')).toHaveTextContent('15%');
      expect(screen.getByTestId('strategy-sharpe-ratio')).toHaveTextContent('1.5');
    });

    test('should handle strategy activation/deactivation', async () => {
      const strategy = integration.createTestData.strategy({ status: 'inactive' });
      
      render(<StrategyCard strategy={strategy} />);
      
      const activateButton = screen.getByTestId('activate-strategy');
      fireEvent.click(activateButton);
      
      // Should show confirmation dialog
      expect(screen.getByTestId('confirm-dialog')).toBeInTheDocument();
      
      // Confirm activation
      const confirmButton = screen.getByTestId('confirm-activation');
      fireEvent.click(confirmButton);
      
      // Should update strategy status
      await waitFor(() => {
        expect(screen.getByTestId('strategy-status-active')).toBeInTheDocument();
      });
    });

    test('should navigate to strategy details', async () => {
      const strategy = integration.createTestData.strategy();
      
      render(<StrategyCard strategy={strategy} />);
      
      const detailsButton = screen.getByTestId('view-details');
      fireEvent.click(detailsButton);
      
      // Should navigate to strategy details page
      await waitFor(() => {
        expect(window.location.pathname).toBe(`/strategies/${strategy.id}`);
      });
    });

    test('should edit strategy inline', async () => {
      const strategy = integration.createTestData.strategy();
      
      render(<StrategyCard strategy={strategy} />);
      
      const editButton = screen.getByTestId('edit-strategy');
      fireEvent.click(editButton);
      
      // Should show edit form
      expect(screen.getByTestId('strategy-edit-form')).toBeInTheDocument();
      
      // Update strategy name
      const nameInput = screen.getByTestId('strategy-name-input');
      await userEvent.clear(nameInput);
      await userEvent.type(nameInput, 'Updated Strategy Name');
      
      // Save changes
      const saveButton = screen.getByTestId('save-changes');
      fireEvent.click(saveButton);
      
      // Should show updated name
      await waitFor(() => {
        expect(screen.getByText('Updated Strategy Name')).toBeInTheDocument();
      });
    });
  });

  describe('Strategy Form Component', () => {
    test('should create new strategy', async () => {
      render(<StrategyForm />);
      
      // Fill form fields
      const nameInput = screen.getByTestId('strategy-name');
      await userEvent.type(nameInput, 'New Test Strategy');
      
      const descriptionInput = screen.getByTestId('strategy-description');
      await userEvent.type(descriptionInput, 'Test strategy description');
      
      // Add symbols
      const symbolInput = screen.getByTestId('symbol-input');
      await userEvent.type(symbolInput, 'AAPL');
      fireEvent.click(screen.getByTestId('add-symbol'));
      
      // Set parameters
      const riskLevelInput = screen.getByTestId('risk-level');
      await userEvent.clear(riskLevelInput);
      await userEvent.type(riskLevelInput, '0.03');
      
      // Submit form
      const submitButton = screen.getByTestId('submit-strategy');
      fireEvent.click(submitButton);
      
      // Should show success message
      await waitFor(() => {
        expect(screen.getByText(/strategy created successfully/i)).toBeInTheDocument();
      });
    });

    test('should validate form inputs', async () => {
      render(<StrategyForm />);
      
      // Submit empty form
      const submitButton = screen.getByTestId('submit-strategy');
      fireEvent.click(submitButton);
      
      // Should show validation errors
      expect(screen.getByText(/name is required/i)).toBeInTheDocument();
      expect(screen.getByText(/at least one symbol is required/i)).toBeInTheDocument();
    });

    test('should handle duplicate symbols', async () => {
      render(<StrategyForm />);
      
      // Add the same symbol twice
      const symbolInput = screen.getByTestId('symbol-input');
      await userEvent.type(symbolInput, 'AAPL');
      fireEvent.click(screen.getByTestId('add-symbol'));
      
      await userEvent.clear(symbolInput);
      await userEvent.type(symbolInput, 'AAPL');
      fireEvent.click(screen.getByTestId('add-symbol'));
      
      // Should show error
      expect(screen.getByText(/symbol already added/i)).toBeInTheDocument();
    });
  });

  describe('Dashboard Integration', () => {
    test('should display overview statistics', async () => {
      render(<Dashboard />);
      
      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByTestId('total-strategies')).toBeInTheDocument();
        expect(screen.getByTestId('active-strategies')).toBeInTheDocument();
        expect(screen.getByTestId('portfolio-value')).toBeInTheDocument();
      });
    });

    test('should navigate between sections', async () => {
      render(<Dashboard />);
      
      // Navigate to strategies section
      const strategiesLink = screen.getByTestId('nav-strategies');
      fireEvent.click(strategiesLink);
      
      await waitFor(() => {
        expect(screen.getByTestId('strategies-section')).toBeInTheDocument();
      });
      
      // Navigate to portfolio section
      const portfolioLink = screen.getByTestId('nav-portfolio');
      fireEvent.click(portfolioLink);
      
      await waitFor(() => {
        expect(screen.getByTestId('portfolio-section')).toBeInTheDocument();
      });
    });

    test('should handle real-time updates', async () => {
      const mockWs = integrationUtils.createMockWebSocket();
      
      render(<Dashboard />);
      
      // Simulate WebSocket update
      const updateMessage = {
        type: 'portfolio_update',
        data: {
          total_value: 105000,
          change: 0.05,
        },
      };
      
      const onMessageCallback = mockWs.addEventListener.mock.calls.find(
        call => call[0] === 'message'
      )?.[1];
      
      if (onMessageCallback) {
        onMessageCallback({ data: JSON.stringify(updateMessage) });
      }
      
      // Should update displayed value
      await waitFor(() => {
        expect(screen.getByTestId('portfolio-value')).toHaveTextContent('$105,000');
      });
    });
  });

  describe('Responsive Design', () => {
    test('should adapt to mobile view', async () => {
      // Mock mobile viewport
      window.innerWidth = 375;
      window.dispatchEvent(new Event('resize'));
      
      render(<StrategyList />);
      
      await waitFor(() => {
        expect(screen.getByTestId('mobile-layout')).toBeInTheDocument();
      });
      
      // Check for mobile-specific elements
      expect(screen.getByTestId('mobile-menu')).toBeInTheDocument();
      expect(screen.getByTestId('strategy-cards-grid')).toHaveClass('grid-cols-1');
    });

    test('should adapt to tablet view', async () => {
      // Mock tablet viewport
      window.innerWidth = 768;
      window.dispatchEvent(new Event('resize'));
      
      render(<StrategyList />);
      
      await waitFor(() => {
        expect(screen.getByTestId('tablet-layout')).toBeInTheDocument();
      });
      
      // Check for tablet-specific layout
      expect(screen.getByTestId('strategy-cards-grid')).toHaveClass('grid-cols-2');
    });
  });

  describe('Accessibility', () => {
    test('should be keyboard navigable', async () => {
      render(<Dashboard />);
      
      // Tab through elements
      fireEvent.keyDown(document, { key: 'Tab' });
      
      // Focus should be on first interactive element
      const firstFocusable = screen.getByTestId('first-focusable');
      expect(firstFocusable).toHaveFocus();
      
      // Continue tabbing
      fireEvent.keyDown(document, { key: 'Tab' });
      
      const secondFocusable = screen.getByTestId('second-focusable');
      expect(secondFocusable).toHaveFocus();
    });

    test('should support screen readers', async () => {
      render(<StrategyCard strategy={integration.createTestData.strategy()} />);
      
      // Check for ARIA labels
      expect(screen.getByLabelText('Strategy name')).toBeInTheDocument();
      expect(screen.getByLabelText('Strategy status')).toBeInTheDocument();
      expect(screen.getByLabelText('Strategy performance')).toBeInTheDocument();
    });
  });
});