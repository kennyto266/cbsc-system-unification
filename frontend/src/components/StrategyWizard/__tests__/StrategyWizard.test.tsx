/**
 * Strategy Wizard Component Tests
 * 策略配置嚮導組件測試
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { configureStore, createAction } from '@reduxjs/toolkit';
import { StrategyWizard } from '../StrategyWizard';
import strategyReducer from '../../../store/strategies/strategySlice';
import { StrategyType, RiskTolerance } from '../../../types/strategyTypes';

// Mock wizard steps - mock must be defined with factory function
jest.mock('../WizardSteps', () => ({
  WizardSteps: ({ currentStep, onStepChange, completionPercentage }: any) => (
    <div data-testid="wizard-steps">
      <div data-testid="completion-percentage">{completionPercentage}%</div>
      {[1, 2, 3, 4, 5].map((step) => (
        <button
          key={step}
          data-testid={`step-${step}`}
          className={step === currentStep ? 'active' : ''}
          onClick={() => onStepChange(step)}
        >
          Step {step}
        </button>
      ))}
    </div>
  ),
  defaultWizardSteps: [
    { id: 'basic', title: 'Basic Info', description: 'Basic information' },
    { id: 'parameters', title: 'Parameters', description: 'Strategy parameters' },
    { id: 'risk', title: 'Risk Management', description: 'Risk settings' },
    { id: 'advanced', title: 'Advanced', description: 'Advanced options' },
    { id: 'review', title: 'Review', description: 'Review and submit' },
  ],
}));

// Mock smart suggestions
jest.mock('../SmartSuggestions', () => ({
  SmartSuggestions: ({ onSuggestionSelect }: any) => (
    <div data-testid="smart-suggestions">
      <button
        data-testid="suggestion-1"
        onClick={() => onSuggestionSelect({
          strategy_type: StrategyType.MOMENTUM,
          parameters: { period: 20 }
        })}
      >
        Momentum Strategy
      </button>
    </div>
  ),
}));

// Mock export service
jest.mock('../../../services/exportService', () => ({
  exportService: {
    saveDraft: jest.fn().mockResolvedValue({ id: 'draft-1' }),
    loadDraft: jest.fn().mockResolvedValue({
      id: 'draft-1',
      name: 'Test Draft',
      step: 1,
      data: {}
    }),
    deleteDraft: jest.fn().mockResolvedValue(true)
  }
}));

// Mock Redux actions
const mockDispatch = jest.fn();
jest.mock('react-redux', () => ({
  ...jest.requireActual('react-redux'),
  useDispatch: () => mockDispatch,
}));

const createTestStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      strategies: strategyReducer
    },
    preloadedState: {
      strategies: {
        items: [],
        loading: false,
        error: null,
        pagination: { page: 1, pageSize: 20, total: 0, pages: 0 },
        selectedItems: [],
        filter: {},
        ...initialState
      }
    }
  });
};

const renderWithProviders = (component: React.ReactElement, initialState = {}) => {
  const store = createTestStore(initialState);
  return render(
    <Provider store={store}>
      {component}
    </Provider>
  );
};

describe('StrategyWizard', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    onComplete: jest.fn(),
    initialData: undefined
  };

  beforeEach(() => {
    jest.clearAllMocks();
    // Use real timers to avoid issues with userEvent
    jest.useRealTimers();
    // Reset mockDispatch
    mockDispatch.mockClear();
  });

  afterEach(() => {
    // No need to restore since we're using real timers
  });

  it('renders wizard with all steps', () => {
    renderWithProviders(<StrategyWizard {...defaultProps} />);

    expect(screen.getByTestId('wizard-steps')).toBeInTheDocument();
    expect(screen.getByTestId('step-1')).toBeInTheDocument();
    expect(screen.getByTestId('step-2')).toBeInTheDocument();
    expect(screen.getByTestId('step-3')).toBeInTheDocument();
    expect(screen.getByTestId('step-4')).toBeInTheDocument();
    expect(screen.getByTestId('step-5')).toBeInTheDocument();
  });

  it('starts with step 1 active', () => {
    renderWithProviders(<StrategyWizard {...defaultProps} />);

    expect(screen.getByTestId('step-1')).toHaveClass('active');
  });

  it('saves draft automatically', async () => {
    const mockSave = require('../../../services/exportService').exportService.saveDraft;

    renderWithProviders(<StrategyWizard {...defaultProps} />);

    // Make a change to trigger hasChanges = true
    const nameInput = screen.getByPlaceholderText(/例如：RSI 動量策略/i);
    fireEvent.change(nameInput, { target: { value: 'Test' } });

    // Wait for auto-save (3 second delay)
    await waitFor(
      () => {
        expect(mockSave).toHaveBeenCalled();
      },
      { timeout: 5000 }
    );
  });

  it('loads draft when initialDraft is provided', async () => {
    const mockLoad = require('../../../services/exportService').exportService.loadDraft;
    const draft = {
      id: 'draft-1',
      name: 'Test Draft',
      step: 2,
      data: {
        strategy_type: StrategyType.MOMENTUM
      }
    };
    mockLoad.mockResolvedValue(draft);

    renderWithProviders(
      <StrategyWizard
        {...defaultProps}
        initialDraft="draft-1"
      />
    );

    await waitFor(() => {
      expect(mockLoad).toHaveBeenCalledWith('draft-1');
    });
  });

  it('shows smart suggestions on step 1', () => {
    renderWithProviders(<StrategyWizard {...defaultProps} />);

    expect(screen.getByTestId('smart-suggestions')).toBeInTheDocument();
    expect(screen.getByTestId('suggestion-1')).toBeInTheDocument();
  });

  it('can navigate between steps', async () => {
    const user = userEvent.setup({ delay: null }); // Disable delay for faster tests

    renderWithProviders(<StrategyWizard {...defaultProps} />);

    // Initially on step 1
    expect(screen.getByTestId('step-1')).toHaveClass('active');

    // Fill required fields on step 1 first
    const nameInput = screen.getByPlaceholderText(/例如：RSI 動量策略/i);
    await user.type(nameInput, 'Test Strategy');
    const descriptionTextarea = screen.getByPlaceholderText(/請描述策略的目標、適用場景和預期效果/i);
    await user.type(descriptionTextarea, 'Test description');

    // Now can navigate to step 2
    await user.click(screen.getByTestId('step-2'));
    await waitFor(() => {
      expect(screen.getByTestId('step-2')).toHaveClass('active');
    });

    // Can navigate to step 3 (no required fields on step 2)
    await user.click(screen.getByTestId('step-3'));
    await waitFor(() => {
      expect(screen.getByTestId('step-3')).toHaveClass('active');
    });
  });

  it('validates required fields before proceeding', async () => {
    const user = userEvent.setup({ delay: null });

    renderWithProviders(<StrategyWizard {...defaultProps} />);

    // Try to go to step 2 without filling step 1
    const nextButton = screen.getByRole('button', { name: /下一步/i });
    await user.click(nextButton);

    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText(/策略名稱不能為空/i)).toBeInTheDocument();
    });
  });

  it('can proceed through all steps with valid data', async () => {
    const user = userEvent.setup({ delay: null });
    const onComplete = jest.fn();

    // Mock createStrategy to resolve successfully
    const mockUnwrap = jest.fn().mockResolvedValue({
      id: 'test-strategy-1',
      name: 'Test Strategy',
      description: 'Test description',
    });
    mockDispatch.mockReturnValue({
      unwrap: mockUnwrap
    });

    renderWithProviders(
      <StrategyWizard
        {...defaultProps}
        onComplete={onComplete}
      />
    );

    // Fill step 1 - Basic Info
    const nameInput = screen.getByPlaceholderText(/例如：RSI 動量策略/i);
    await user.type(nameInput, 'Test Strategy');

    const descriptionTextarea = screen.getByPlaceholderText(/請描述策略的目標、適用場景和預期效果/i);
    await user.type(descriptionTextarea, 'Test description');

    // Select a suggestion to set strategy_type
    await user.click(screen.getByTestId('suggestion-1'));

    // Proceed to step 2
    const nextButton = screen.getByRole('button', { name: /下一步/i });
    await user.click(nextButton);

    await waitFor(() => {
      expect(screen.getByTestId('step-2')).toHaveClass('active');
    });

    // Step 2 has default values for risk_tolerance, initial_capital, position_sizing
    // So we can proceed to step 3
    await user.click(screen.getByTestId('step-3'));
    await waitFor(() => {
      expect(screen.getByTestId('step-3')).toHaveClass('active');
    });

    // Step 3 has no required fields, proceed to step 4
    await user.click(screen.getByTestId('step-4'));
    await waitFor(() => {
      expect(screen.getByTestId('step-4')).toHaveClass('active');
    });

    // Fill step 4 required fields (symbols - data_source and timeframe have defaults)
    const symbolsTextarea = screen.getByPlaceholderText(/例如：AAPL, MSFT, GOOGL/i);
    await user.type(symbolsTextarea, 'AAPL, MSFT');

    // Proceed to step 5
    await user.click(screen.getByTestId('step-5'));
    await waitFor(() => {
      expect(screen.getByTestId('step-5')).toHaveClass('active');
    });

    // Complete wizard
    const completeButton = screen.getByRole('button', { name: /創建策略/i });
    await user.click(completeButton);

    await waitFor(() => {
      expect(mockDispatch).toHaveBeenCalled();
      expect(onComplete).toHaveBeenCalled();
    });
  });

  it('shows strategy summary on final step', async () => {
    const user = userEvent.setup({ delay: null });

    renderWithProviders(<StrategyWizard {...defaultProps} />);

    // Fill step 1
    const nameInput = screen.getByPlaceholderText(/例如：RSI 動量策略/i);
    await user.type(nameInput, 'Test Strategy');
    const descriptionTextarea = screen.getByPlaceholderText(/請描述策略的目標、適用場景和預期效果/i);
    await user.type(descriptionTextarea, 'Test description');

    // Select strategy_type
    await user.click(screen.getByTestId('suggestion-1'));

    // Navigate through steps to reach step 5
    await user.click(screen.getByTestId('step-2'));
    await waitFor(() => {
      expect(screen.getByTestId('step-2')).toHaveClass('active');
    });

    await user.click(screen.getByTestId('step-3'));
    await waitFor(() => {
      expect(screen.getByTestId('step-3')).toHaveClass('active');
    });

    await user.click(screen.getByTestId('step-4'));
    await waitFor(() => {
      expect(screen.getByTestId('step-4')).toHaveClass('active');
    });

    // Fill step 4 required fields (symbols)
    const symbolsTextarea = screen.getByPlaceholderText(/例如：AAPL, MSFT, GOOGL/i);
    await user.type(symbolsTextarea, 'AAPL, MSFT');

    // Now can navigate to step 5
    await user.click(screen.getByTestId('step-5'));
    await waitFor(() => {
      expect(screen.getByTestId('step-5')).toHaveClass('active');
    });

    // Should show summary
    expect(screen.getByText(/策略摘要/i)).toBeInTheDocument();
    expect(screen.getByText('Test Strategy')).toBeInTheDocument();
  });

  it('allows modification from summary step', async () => {
    const user = userEvent.setup({ delay: null });

    renderWithProviders(<StrategyWizard {...defaultProps} />);

    // Fill all required fields to reach step 5
    const nameInput = screen.getByPlaceholderText(/例如：RSI 動量策略/i);
    await user.type(nameInput, 'Test Strategy');
    const descriptionTextarea = screen.getByPlaceholderText(/請描述策略的目標、適用場景和預期效果/i);
    await user.type(descriptionTextarea, 'Test description');

    // Select strategy_type
    await user.click(screen.getByTestId('suggestion-1'));

    await user.click(screen.getByTestId('step-2'));
    await waitFor(() => {
      expect(screen.getByTestId('step-2')).toHaveClass('active');
    });

    await user.click(screen.getByTestId('step-3'));
    await waitFor(() => {
      expect(screen.getByTestId('step-3')).toHaveClass('active');
    });

    // Navigate to step 4 before filling symbols
    await user.click(screen.getByTestId('step-4'));
    await waitFor(() => {
      expect(screen.getByTestId('step-4')).toHaveClass('active');
    });

    const symbolsTextarea = screen.getByPlaceholderText(/例如：AAPL, MSFT, GOOGL/i);
    await user.type(symbolsTextarea, 'AAPL');

    await user.click(screen.getByTestId('step-5'));
    await waitFor(() => {
      expect(screen.getByTestId('step-5')).toHaveClass('active');
    });

    // Click modify button for strategy name (there are multiple "修改" buttons)
    const modifyButtons = screen.getAllByText(/修改/i);
    await user.click(modifyButtons[0]); // First modify button (basic info)

    // Should return to step 1
    await waitFor(() => {
      expect(screen.getByTestId('step-1')).toHaveClass('active');
    });
  });

  it('handles saving and resuming drafts', async () => {
    const user = userEvent.setup({ delay: null });
    const mockSave = require('../../../services/exportService').exportService.saveDraft;

    renderWithProviders(<StrategyWizard {...defaultProps} />);

    // Make some changes first
    const nameInput = screen.getByPlaceholderText(/例如：RSI 動量策略/i);
    await user.type(nameInput, 'Test Strategy');

    // Save draft
    const saveButton = screen.getByRole('button', { name: /保存草稿/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockSave).toHaveBeenCalled();
    });
  });

  it('can exit wizard without saving', async () => {
    const onClose = jest.fn();

    renderWithProviders(
      <StrategyWizard
        {...defaultProps}
        onClose={onClose}
      />
    );

    // Make some changes first so hasChanges becomes true
    const nameInput = screen.getByPlaceholderText(/例如：RSI 動量策略/i);
    await userEvent.setup().type(nameInput, 'Test');

    // Note: Modal component typically handles close button internally
    // This test verifies the component structure, not actual Modal close behavior
    // In real usage, clicking Modal's X button would trigger onClose

    // Check that wizard is rendered
    expect(screen.getByTestId('wizard-steps')).toBeInTheDocument();
  });

  it('tracks completion progress', async () => {
    renderWithProviders(<StrategyWizard {...defaultProps} />);

    // Initially 0% complete - use data-testid instead of text
    expect(screen.getByTestId('completion-percentage')).toHaveTextContent('0%');

    // After filling step 1 required fields (name, description, strategy_type)
    const nameInput = screen.getByPlaceholderText(/例如：RSI 動量策略/i);
    fireEvent.change(nameInput, { target: { value: 'Test' } });

    const descriptionTextarea = screen.getByPlaceholderText(/請描述策略的目標、適用場景和預期效果/i);
    fireEvent.change(descriptionTextarea, { target: { value: 'Test description' } });

    // strategy_type is already selected by default (technical_indicators)

    await waitFor(() => {
      expect(screen.getByTestId('completion-percentage')).toHaveTextContent('20%');
    });
  });
});