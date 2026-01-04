/**
 * Strategy Wizard Component Tests
 * 策略配置嚮導組件測試
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { StrategyWizard } from '../StrategyWizard';
import { strategySlice } from '../../../store/strategies/strategySlice';
import { StrategyType, RiskTolerance } from '../../../types/strategyTypes';

// Mock wizard steps
jest.mock('../WizardSteps', () => ({
  WizardSteps: ({ currentStep, onStepChange }: any) => (
    <div data-testid="wizard-steps">
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

const createTestStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      strategies: strategySlice.reducer
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

    // Wait for auto-save
    await waitFor(() => {
      expect(mockSave).toHaveBeenCalled();
    }, { timeout: 2000 });
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
    const user = userEvent.setup();

    renderWithProviders(<StrategyWizard {...defaultProps} />);

    // Initially on step 1
    expect(screen.getByTestId('step-1')).toHaveClass('active');

    // Click step 2
    await user.click(screen.getByTestId('step-2'));
    expect(screen.getByTestId('step-2')).toHaveClass('active');

    // Click step 3
    await user.click(screen.getByTestId('step-3'));
    expect(screen.getByTestId('step-3')).toHaveClass('active');
  });

  it('validates required fields before proceeding', async () => {
    const user = userEvent.setup();

    renderWithProviders(<StrategyWizard {...defaultProps} />);

    // Try to go to step 2 without filling step 1
    const nextButton = screen.getByRole('button', { name: /下一步/i });
    await user.click(nextButton);

    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText(/請填寫所有必填欄位/i)).toBeInTheDocument();
    });
  });

  it('can proceed through all steps with valid data', async () => {
    const user = userEvent.setup();
    const onComplete = jest.fn();

    renderWithProviders(
      <StrategyWizard
        {...defaultProps}
        onComplete={onComplete}
      />
    );

    // Fill step 1 - Basic Info
    const nameInput = screen.getByLabelText(/策略名稱/i);
    await user.type(nameInput, 'Test Strategy');

    // Select a suggestion
    await user.click(screen.getByTestId('suggestion-1'));

    // Proceed to step 2
    const nextButton = screen.getByRole('button', { name: /下一步/i });
    await user.click(nextButton);

    // Should be on step 2
    expect(screen.getByTestId('step-2')).toHaveClass('active');

    // Fill all remaining steps
    for (let i = 3; i <= 5; i++) {
      await user.click(screen.getByTestId(`step-${i}`));
      expect(screen.getByTestId(`step-${i}`)).toHaveClass('active');
    }

    // Complete wizard
    const completeButton = screen.getByRole('button', { name: /完成/i });
    await user.click(completeButton);

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalledWith({
        name: 'Test Strategy',
        strategy_type: StrategyType.MOMENTUM,
        parameters: { period: 20 }
      });
    });
  });

  it('shows strategy summary on final step', async () => {
    const user = userEvent.setup();

    renderWithProviders(<StrategyWizard {...defaultProps} />);

    // Fill and navigate to final step
    const nameInput = screen.getByLabelText(/策略名稱/i);
    await user.type(nameInput, 'Test Strategy');
    await user.click(screen.getByTestId('step-5'));

    // Should show summary
    expect(screen.getByText(/策略摘要/i)).toBeInTheDocument();
    expect(screen.getByText('Test Strategy')).toBeInTheDocument();
  });

  it('allows modification from summary step', async () => {
    const user = userEvent.setup();

    renderWithProviders(<StrategyWizard {...defaultProps} />);

    // Navigate to summary step
    await user.click(screen.getByTestId('step-5'));

    // Click modify button for strategy name
    const modifyButton = screen.getByText(/修改名稱/i);
    await user.click(modifyButton);

    // Should return to step 1
    expect(screen.getByTestId('step-1')).toHaveClass('active');
  });

  it('handles saving and resuming drafts', async () => {
    const user = userEvent.setup();
    const mockSave = require('../../../services/exportService').exportService.saveDraft;

    renderWithProviders(<StrategyWizard {...defaultProps} />);

    // Save draft
    const saveButton = screen.getByRole('button', { name: /保存草稿/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockSave).toHaveBeenCalled();
    });

    // Should show save confirmation
    expect(screen.getByText(/草稿已保存/i)).toBeInTheDocument();
  });

  it('can exit wizard without saving', async () => {
    const onClose = jest.fn();
    const user = userEvent.setup();

    renderWithProviders(
      <StrategyWizard
        {...defaultProps}
        onClose={onClose}
      />
    );

    // Click exit without saving
    const exitButton = screen.getByRole('button', { name: /退出/i });
    await user.click(exitButton);

    // Should show confirmation dialog
    expect(screen.getByText(/確定要退出嗎？/i)).toBeInTheDocument();

    // Confirm exit
    const confirmButton = screen.getByRole('button', { name: /確定退出/i });
    await user.click(confirmButton);

    expect(onClose).toHaveBeenCalled();
  });

  it('tracks completion progress', async () => {
    renderWithProviders(<StrategyWizard {...defaultProps} />);

    // Initially 0% complete
    expect(screen.getByText('0%')).toBeInTheDocument();

    // After filling step 1
    const nameInput = screen.getByLabelText(/策略名稱/i);
    fireEvent.change(nameInput, { target: { value: 'Test' } });

    await waitFor(() => {
      expect(screen.getByText('20%')).toBeInTheDocument();
    });
  });
});