import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ReportExporter from '../ReportExporter';

// Mock export utilities
jest.mock('../utils/pdfGenerator', () => ({
  generatePDF: jest.fn(() => Promise.resolve('test-pdf-url'))
}));

jest.mock('../utils/excelGenerator', () => ({
  generateExcel: jest.fn(() => Promise.resolve('test-excel-url'))
}));

jest.mock('../utils/emailService', () => ({
  sendEmail: jest.fn(() => Promise.resolve({ success: true }))
}));

// Mock file-saver
jest.mock('file-saver', () => ({
  saveAs: jest.fn()
}));

describe('ReportExporter', () => {
  const mockReport = {
    id: 'test-report-1',
    strategyName: 'Interest Rate Strategy',
    strategy: {
      name: 'Interest Rate Differential',
      category: 'economic',
      parameters: {
        interestRateThreshold: 0.02,
        lookbackPeriod: 30
      }
    },
    period: {
      start: '2023-01-01',
      end: '2024-01-01',
      duration: 365
    },
    metrics: {
      totalReturn: 0.156,
      annualizedReturn: 0.156,
      maxDrawdown: -0.082,
      sharpeRatio: 1.45,
      sortinoRatio: 2.03,
      calmarRatio: 1.90,
      volatility: 0.145,
      winRate: 0.62,
      profitFactor: 1.85,
      averageWin: 1250.50,
      averageLoss: -675.30,
      totalTrades: 48,
      winningTrades: 30,
      losingTrades: 18
    },
    equityCurve: [],
    trades: [],
    generatedAt: '2024-01-02T10:00:00Z'
  };

  it('renders export modal correctly', () => {
    render(<ReportExporter report={mockReport} isOpen={true} onClose={() => {}} />);

    expect(screen.getByText('Export Report')).toBeInTheDocument();
    expect(screen.getByText('Select export format:')).toBeInTheDocument();
    expect(screen.getByText('PDF Report')).toBeInTheDocument();
    expect(screen.getByText('Excel Data')).toBeInTheDocument();
  });

  it('does not render when modal is closed', () => {
    render(<ReportExporter report={mockReport} isOpen={false} onClose={() => {}} />);

    expect(screen.queryByText('Export Report')).not.toBeInTheDocument();
  });

  it('shows available templates', () => {
    render(<ReportExporter report={mockReport} isOpen={true} onClose={() => {}} />);

    expect(screen.getByText('Report Template:')).toBeInTheDocument();
    expect(screen.getByText('Standard Professional')).toBeInTheDocument();
    expect(screen.getByText('Executive Summary')).toBeInTheDocument();
    expect(screen.getByText('Technical Analysis')).toBeInTheDocument();
  });

  it('allows template selection', async () => {
    render(<ReportExporter report={mockReport} isOpen={true} onClose={() => {}} />);

    const templateSelect = screen.getByDisplayValue('Standard Professional');
    fireEvent.change(templateSelect, { target: { value: 'executive' } });

    expect(screen.getByDisplayValue('Executive Summary')).toBeInTheDocument();
  });

  it('exports to PDF successfully', async () => {
    const { generatePDF } = require('../utils/pdfGenerator');
    const { saveAs } = require('file-saver');

    render(<ReportExporter report={mockReport} isOpen={true} onClose={() => {}} />);

    const pdfRadio = screen.getByLabelText('PDF Report');
    fireEvent.click(pdfRadio);

    const exportButton = screen.getByText('Export');
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(generatePDF).toHaveBeenCalledWith(mockReport, 'standard');
    });

    await waitFor(() => {
      expect(saveAs).toHaveBeenCalledWith('test-pdf-url', 'Interest_Rate_Strategy_Report.pdf');
    });
  });

  it('exports to Excel successfully', async () => {
    const { generateExcel } = require('../utils/excelGenerator');
    const { saveAs } = require('file-saver');

    render(<ReportExporter report={mockReport} isOpen={true} onClose={() => {}} />);

    const excelRadio = screen.getByLabelText('Excel Data');
    fireEvent.click(excelRadio);

    const exportButton = screen.getByText('Export');
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(generateExcel).toHaveBeenCalledWith(mockReport);
    });

    await waitFor(() => {
      expect(saveAs).toHaveBeenCalledWith('test-excel-url', 'Interest_Rate_Strategy_Report.xlsx');
    });
  });

  it('shows export progress', async () => {
    // Mock slow export
    const { generatePDF } = require('../utils/pdfGenerator');
    generatePDF.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));

    render(<ReportExporter report={mockReport} isOpen={true} onClose={() => {}} />);

    const pdfRadio = screen.getByLabelText('PDF Report');
    fireEvent.click(pdfRadio);

    const exportButton = screen.getByText('Export');
    fireEvent.click(exportButton);

    expect(screen.getByText('Exporting...')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('allows email delivery option', async () => {
    const { sendEmail } = require('../utils/emailService');

    render(<ReportExporter report={mockReport} isOpen={true} onClose={() => {}} />);

    const emailCheckbox = screen.getByLabelText('Email report');
    fireEvent.click(emailCheckbox);

    const emailInput = screen.getByPlaceholderText('Enter email address');
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });

    const exportButton = screen.getByText('Export');
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(sendEmail).toHaveBeenCalledWith({
        to: 'test@example.com',
        subject: 'Interest Rate Strategy Report',
        reportUrl: 'test-pdf-url'
      });
    });
  });

  it('validates email address', async () => {
    render(<ReportExporter report={mockReport} isOpen={true} onClose={() => {}} />);

    const emailCheckbox = screen.getByLabelText('Email report');
    fireEvent.click(emailCheckbox);

    const emailInput = screen.getByPlaceholderText('Enter email address');
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });

    const exportButton = screen.getByText('Export');
    fireEvent.click(exportButton);

    expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();
  });

  it('supports batch export', async () => {
    const mockReports = [mockReport, { ...mockReport, id: 'test-report-2', strategyName: 'Strategy 2' }];

    render(
      <ReportExporter
        reports={mockReports}
        isOpen={true}
        onClose={() => {}}
      />
    );

    expect(screen.getByText('Export 2 Reports')).toBeInTheDocument();
    expect(screen.getByText('Batch export options:')).toBeInTheDocument();

    const zipRadio = screen.getByLabelText('Zip Archive');
    fireEvent.click(zipRadio);

    const exportButton = screen.getByText('Export All');
    fireEvent.click(exportButton);

    // Should show progress for batch export
    await waitFor(() => {
      expect(screen.getByText('Processing 1 of 2...')).toBeInTheDocument();
    });
  });

  it('allows branding customization', () => {
    render(<ReportExporter report={mockReport} isOpen={true} onClose={() => {}} />);

    const brandingTab = screen.getByText('Branding');
    fireEvent.click(brandingTab);

    expect(screen.getByText('Company Name:')).toBeInTheDocument();
    expect(screen.getByText('Logo URL:')).toBeInTheDocument();
    expect(screen.getByText('Custom Colors:')).toBeInTheDocument();
  });

  it('shows export history', () => {
    const mockHistory = [
      { format: 'PDF', template: 'Standard', date: '2024-01-01', status: 'Completed' },
      { format: 'Excel', template: 'Technical', date: '2024-01-02', status: 'Processing' }
    ];

    render(<ReportExporter report={mockReport} isOpen={true} onClose={() => {}} exportHistory={mockHistory} />);

    const historyTab = screen.getByText('History');
    fireEvent.click(historyTab);

    expect(screen.getByText('Previous Exports')).toBeInTheDocument();
    expect(screen.getByText('PDF - Standard')).toBeInTheDocument();
    expect(screen.getByText('Excel - Technical')).toBeInTheDocument();
  });

  it('handles export errors gracefully', async () => {
    const { generatePDF } = require('../utils/pdfGenerator');
    generatePDF.mockRejectedValue(new Error('Export failed'));

    render(<ReportExporter report={mockReport} isOpen={true} onClose={() => {}} />);

    const pdfRadio = screen.getByLabelText('PDF Report');
    fireEvent.click(pdfRadio);

    const exportButton = screen.getByText('Export');
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(screen.getByText('Export failed: Export failed')).toBeInTheDocument();
    });
  });
});