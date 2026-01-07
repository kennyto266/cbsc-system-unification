/**
 * Data Exporter Component Tests
 * 數據導出組件測試
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// Mock export service
jest.mock('../../../services/exportService', () => ({
  exportService: {
    exportData: jest.fn().mockResolvedValue(new Blob(['test data'])),
    generateShareLink: jest.fn().mockResolvedValue('https://example.com/shared/abc123'),
    getTemplates: jest.fn().mockReturnValue([
      {
        id: 'template-1',
        name: 'Standard Report',
        description: 'Standard strategy report',
        isDefault: true
      }
    ])
  },
  downloadFile: jest.fn().mockResolvedValue(undefined),
  exportBatchData: jest.fn().mockResolvedValue(undefined),
}));

// Mock UI components
jest.mock('../../ui/Modal', () => ({
  Modal: ({ children, isOpen, onClose, title }: any) =>
    isOpen ? (
      <div data-testid="modal">
        <h2 data-testid="modal-title">{title}</h2>
        <div data-testid="modal-content">{children}</div>
        <button onClick={onClose} data-testid="close-modal">Close</button>
      </div>
    ) : null
}));

jest.mock('../../ui/Button', () => ({
  Button: ({ children, onClick, disabled, ...props }: any) => (
    <button onClick={onClick} disabled={disabled} data-button-type={props.type || 'button'}>
      {children}
    </button>
  )
}));

jest.mock('../../ui/Input', () => ({
  Input: ({ label, error, ...props }: any) => (
    <div>
      <label>{label}</label>
      <input aria-label={label} {...props} />
      {error && <span data-testid="input-error">{error}</span>}
    </div>
  )
}));

jest.mock('../../ui/Alert', () => ({
  Alert: ({ children, type, variant, title, description }: any) => {
    const alertType = type || variant || 'info';
    return (
      <div data-testid={`alert-${alertType}`} role="alert">
        {title && <div data-testid="alert-title">{title}</div>}
        {description && <div data-testid="alert-description">{description}</div>}
        {children}
      </div>
    );
  }
}));

jest.mock('../../ui/Loading', () => ({
  Loading: () => <div data-testid="loading">Loading...</div>
}));

jest.mock('../../ui/CustomTabs', () => ({
  CustomTabs: ({ children, value, onChange }: any) => (
    <div data-testid="tabs">
      {React.Children.map(children, (child: any) => {
        if (child.type.name === 'TabPanel') {
          return React.cloneElement(child, { active: child.props.value === value });
        }
        return child;
      })}
    </div>
  ),
  TabPanel: ({ children, value, active, onClick }: any) => (
    <button
      data-testid={`tab-${value}`}
      aria-selected={active}
      onClick={onClick}
    >
      {children}
    </button>
  )
}));

// Mock heroicons
jest.mock('@heroicons/react/24/outline', () => ({
  ArrowDownTrayIcon: () => <div data-testid="download-icon" />,
  ShareIcon: () => <div data-testid="share-icon" />,
  DocumentIcon: () => <div data-testid="document-icon" />,
  TableIcon: () => <div data-testid="table-icon" />,
  PhotoIcon: () => <div data-testid="photo-icon" />,
  ClipboardDocumentIcon: () => <div data-testid="clipboard-icon" />,
  ClockIcon: () => <div data-testid="clock-icon" />,
  ShieldCheckIcon: () => <div data-testid="shield-icon" />,
}));

// Import component after mocks
const { DataExporter } = require('../DataExporter');

const mockData = {
  strategy: {
    id: 'strategy-1',
    name: 'Test Strategy',
    performance: {
      total_return: 0.15,
      sharpe_ratio: 1.2,
      max_drawdown: -0.05
    }
  },
  backtest: {
    trades: [
      { symbol: 'AAPL', profit: 100, date: '2024-01-01' },
      { symbol: 'MSFT', profit: -50, date: '2024-01-02' }
    ]
  }
};

describe('DataExporter', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    data: mockData,
    title: 'Test Export'
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render export modal when open', () => {
    render(<DataExporter {...defaultProps} />);

    expect(screen.getByTestId('modal')).toBeInTheDocument();
    // Check for the actual modal title that the component renders
    expect(screen.getByTestId('modal-title')).toBeInTheDocument();
  });

  it('should not render when closed', () => {
    render(<DataExporter {...defaultProps} isOpen={false} />);

    expect(screen.queryByTestId('modal')).not.toBeInTheDocument();
  });

  it('should call onClose when close button clicked', () => {
    const onClose = jest.fn();
    render(<DataExporter {...defaultProps} onClose={onClose} />);

    fireEvent.click(screen.getByTestId('close-modal'));

    expect(onClose).toHaveBeenCalled();
  });

  it('should render export format options', () => {
    render(<DataExporter {...defaultProps} />);

    // Should have format selection radio buttons
    const csvRadio = screen.getByLabelText(/CSV/i) || screen.getAllByRole('radio').find(r => r.value === 'csv');
    expect(csvRadio).toBeInTheDocument();
  });

  it('should have filename input', () => {
    render(<DataExporter {...defaultProps} />);

    const filenameInput = screen.getByPlaceholderText(/文件名稱/i) || screen.getByRole('textbox');
    expect(filenameInput).toBeInTheDocument();
  });

  it('should call export service when export button clicked', async () => {
    const user = userEvent.setup();
    const mockExport = require('../../../services/exportService').exportService.exportData;

    render(<DataExporter {...defaultProps} />);

    // Set filename
    const filenameInput = screen.getByPlaceholderText(/文件名稱/i) || screen.getByRole('textbox');
    await user.type(filenameInput, 'test-export');

    // Click export button - filter to avoid selecting title buttons
    const buttons = screen.getAllByRole('button');
    const exportButton = buttons.find(btn => btn.textContent?.match(/導出/));
    await user.click(exportButton!);

    await waitFor(() => {
      expect(mockExport).toHaveBeenCalled();
    });
  });

  it('should handle export errors gracefully', async () => {
    const user = userEvent.setup();
    const mockExport = require('../../../services/exportService').exportService.exportData;
    mockExport.mockRejectedValueOnce(new Error('導出失敗'));

    render(<DataExporter {...defaultProps} />);

    const filenameInput = screen.getByPlaceholderText(/文件名稱/i) || screen.getByRole('textbox');
    await user.type(filenameInput, 'test-export');

    // Filter to avoid selecting title buttons
    const buttons = screen.getAllByRole('button');
    const exportButton = buttons.find(btn => btn.textContent?.match(/導出/));
    await user.click(exportButton!);

    await waitFor(() => {
      // Check for error in the input-error element that our mock renders
      expect(screen.getByTestId('input-error')).toBeInTheDocument();
      expect(screen.getByTestId('input-error')).toHaveTextContent('導出失敗');
    });
  });

  it('should show loading state during export', async () => {
    const user = userEvent.setup();
    const mockExport = require('../../../services/exportService').exportService.exportData;
    // Make export take longer
    mockExport.mockImplementationOnce(() => new Promise(() => {}));

    render(<DataExporter {...defaultProps} />);

    const filenameInput = screen.getByPlaceholderText(/文件名稱/i) || screen.getByRole('textbox');
    await user.type(filenameInput, 'test-export');

    // Filter to find export button
    const buttons = screen.getAllByRole('button');
    const exportButton = buttons.find(btn => btn.textContent?.match(/導出$/));
    await user.click(exportButton!);

    await waitFor(() => {
      // Check that button shows loading state text
      const loadingButton = screen.getByRole('button', { name: /導出中/i });
      expect(loadingButton).toBeInTheDocument();
      // Button should be disabled during export
      expect(loadingButton).toBeDisabled();
    });
  });
});
