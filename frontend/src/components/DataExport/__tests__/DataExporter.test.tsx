/**
 * Data Exporter Component Tests
 * 數據導出組件測試
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DataExporter } from '../DataExporter';
import { ExportFormat } from '../../../services/exportService';

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
  downloadFile: jest.fn().mockResolvedValue(undefined)
}));

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

  it('renders export modal with format options', () => {
    render(<DataExporter {...defaultProps} />);

    expect(screen.getByText('導出數據')).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /CSV/i })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /JSON/i })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /PDF/i })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /PNG/i })).toBeInTheDocument();
  });

  it('defaults to CSV format', () => {
    render(<DataExporter {...defaultProps} />);

    const csvRadio = screen.getByRole('radio', { name: /CSV/i });
    expect(csvRadio).toBeChecked();
  });

  it('shows format-specific options', async () => {
    const user = userEvent.setup();
    render(<DataExporter {...defaultProps} />);

    // Select PDF format
    const pdfRadio = screen.getByRole('radio', { name: /PDF/i });
    await user.click(pdfRadio);

    // Should show PDF options
    expect(screen.getByText('包含元數據')).toBeInTheDocument();
    expect(screen.getByText('使用模板')).toBeInTheDocument();
  });

  it('validates file name before export', async () => {
    const user = userEvent.setup();
    render(<DataExporter {...defaultProps} />);

    // Clear file name
    const filenameInput = screen.getByLabelText(/文件名稱/i);
    await user.clear(filenameInput);

    // Try to export
    const exportButton = screen.getByRole('button', { name: /導出/i });
    await user.click(exportButton);

    // Should show error
    expect(screen.getByText(/文件名稱不能為空/i)).toBeInTheDocument();
  });

  it('exports data with selected format', async () => {
    const user = userEvent.setup();
    const mockExport = require('../../../services/exportService').exportService.exportData;

    render(<DataExporter {...defaultProps} />);

    // Set filename
    const filenameInput = screen.getByLabelText(/文件名稱/i);
    await user.type(filenameInput, 'test-export');

    // Click export
    const exportButton = screen.getByRole('button', { name: /導出/i });
    await user.click(exportButton);

    await waitFor(() => {
      expect(mockExport).toHaveBeenCalledWith(
        mockData,
        'csv',
        expect.any(Object)
      );
    });

    // Should trigger download
    const mockDownload = require('../../../services/exportService').downloadFile;
    expect(mockDownload).toHaveBeenCalled();
  });

  it('generates share link when share tab is selected', async () => {
    const user = userEvent.setup();
    const mockGenerateLink = require('../../../services/exportService').exportService.generateShareLink;

    render(<DataExporter {...defaultProps} />);

    // Switch to share tab
    const shareTab = screen.getByRole('tab', { name: /分享/i });
    await user.click(shareTab);

    // Generate share link
    const shareButton = screen.getByRole('button', { name: /生成分享鏈接/i });
    await user.click(shareButton);

    await waitFor(() => {
      expect(mockGenerateLink).toHaveBeenCalled();
    });

    // Should show generated link
    expect(screen.getByDisplayValue('https://example.com/shared/abc123')).toBeInTheDocument();
  });

  it('allows copying share link', async () => {
    const user = userEvent.setup();
    // Mock navigator.clipboard.writeText
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn().mockResolvedValue(undefined)
      }
    });

    render(<DataExporter {...defaultProps} />);

    // Switch to share tab
    const shareTab = screen.getByRole('tab', { name: /分享/i });
    await user.click(shareTab);

    // Generate share link
    const shareButton = screen.getByRole('button', { name: /生成分享鏈接/i });
    await user.click(shareButton);

    // Copy link
    const copyButton = screen.getByRole('button', { name: /複製鏈接/i });
    await user.click(copyButton);

    // Should show success message
    await waitFor(() => {
      expect(screen.getByText(/鏈接已複製到剪貼板/i)).toBeInTheDocument();
    });
  });

  it('handles custom template selection', async () => {
    const user = userEvent.setup();

    render(<DataExporter {...defaultProps} />);

    // Select PDF format
    const pdfRadio = screen.getByRole('radio', { name: /PDF/i });
    await user.click(pdfRadio);

    // Select custom template
    const templateSelect = screen.getByLabelText(/選擇模板/i);
    await user.selectOptions(templateSelect, 'template-1');

    // Export with template
    const filenameInput = screen.getByLabelText(/文件名稱/i);
    await user.type(filenameInput, 'test-export');

    const exportButton = screen.getByRole('button', { name: /導出/i });
    await user.click(exportButton);

    const mockExport = require('../../../services/exportService').exportService.exportData;
    await waitFor(() => {
      expect(mockExport).toHaveBeenCalledWith(
        mockData,
        'pdf',
        expect.objectContaining({
          template: 'template-1'
        })
      );
    });
  });

  it('handles batch export for large datasets', async () => {
    const user = userEvent.setup();
    const largeData = {
      trades: Array.from({ length: 2000 }, (_, i) => ({
        id: i,
        symbol: 'AAPL',
        price: 150 + i
      }))
    };

    render(
      <DataExporter
        {...defaultProps}
        data={largeData}
      />
    );

    // Should show batch warning
    expect(screen.getByText(/數據量較大，將分批處理/i)).toBeInTheDocument();

    // Proceed with export
    const filenameInput = screen.getByLabelText(/文件名稱/i);
    await user.type(filenameInput, 'large-export');

    const exportButton = screen.getByRole('button', { name: /導出/i });
    await user.click(exportButton);

    // Should show progress
    await waitFor(() => {
      expect(screen.getByText(/導出進度/i)).toBeInTheDocument();
    });
  });

  it('handles export errors gracefully', async () => {
    const user = userEvent.setup();
    const mockExport = require('../../../services/exportService').exportService.exportData;
    mockExport.mockRejectedValue(new Error('Export failed'));

    render(<DataExporter {...defaultProps} />);

    const filenameInput = screen.getByLabelText(/文件名稱/i);
    await user.type(filenameInput, 'test-export');

    const exportButton = screen.getByRole('button', { name: /導出/i });
    await user.click(exportButton);

    await waitFor(() => {
      expect(screen.getByText(/導出失敗/i)).toBeInTheDocument();
    });
  });

  it('allows setting share link expiration', async () => {
    const user = userEvent.setup();
    const mockGenerateLink = require('../../../services/exportService').exportService.generateShareLink;

    render(<DataExporter {...defaultProps} />);

    // Switch to share tab
    const shareTab = screen.getByRole('tab', { name: /分享/i });
    await user.click(shareTab);

    // Set expiration
    const expiresSelect = screen.getByLabelText(/鏈接有效期/i);
    await user.selectOptions(expiresSelect, '7');

    // Generate share link
    const shareButton = screen.getByRole('button', { name: /生成分享鏈接/i });
    await user.click(shareButton);

    await waitFor(() => {
      expect(mockGenerateLink).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          expiresAt: expect.any(Date)
        })
      );
    });
  });
});