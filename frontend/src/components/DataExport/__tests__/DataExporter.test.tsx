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
  Modal: ({ children, isOpen, onClose }: any) =>
    isOpen ? (
      <div data-testid="modal">
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
  Input: ({ label, ...props }: any) => (
    <div>
      <label>{label}</label>
      <input aria-label={label} {...props} />
    </div>
  )
}));

jest.mock('../../ui/Alert', () => ({
  Alert: ({ children, type }: any) => (
    <div data-testid={`alert-${type}`} role="alert">
      {children}
    </div>
  )
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
    expect(screen.getByText('Test Export')).toBeInTheDocument();
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

    const filenameInput = screen.getByLabelText(/文件名稱/i);
    expect(filenameInput).toBeInTheDocument();
  });

  it('should call export service when export button clicked', async () => {
    const user = userEvent.setup();
    const mockExport = require('../../../services/exportService').exportService.exportData;

    render(<DataExporter {...defaultProps} />);

    // Set filename
    const filenameInput = screen.getByLabelText(/文件名稱/i);
    await user.type(filenameInput, 'test-export');

    // Click export button
    const exportButton = screen.getByRole('button', { name: /導出/i });
    await user.click(exportButton);

    await waitFor(() => {
      expect(mockExport).toHaveBeenCalled();
    });
  });

  it('should handle export errors gracefully', async () => {
    const user = userEvent.setup();
    const mockExport = require('../../../services/exportService').exportService.exportData;
    mockExport.mockRejectedValueOnce(new Error('Export failed'));

    render(<DataExporter {...defaultProps} />);

    const filenameInput = screen.getByLabelText(/文件名稱/i);
    await user.type(filenameInput, 'test-export');

    const exportButton = screen.getByRole('button', { name: /導出/i });
    await user.click(exportButton);

    await waitFor(() => {
      expect(screen.getByText(/導出失敗/i)).toBeInTheDocument();
    });
  });

  it('should show loading state during export', async () => {
    const user = userEvent.setup();
    const mockExport = require('../../../services/exportService').exportService.exportData;
    // Make export take longer
    mockExport.mockImplementationOnce(() => new Promise(() => {}));

    render(<DataExporter {...defaultProps} />);

    const filenameInput = screen.getByLabelText(/文件名稱/i);
    await user.type(filenameInput, 'test-export');

    const exportButton = screen.getByRole('button', { name: /導出/i });
    await user.click(exportButton);

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toBeInTheDocument();
    });
  });
});
