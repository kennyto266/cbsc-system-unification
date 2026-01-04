import React, { useState, useEffect } from 'react';
import {
  XMarkIcon,
  DocumentArrowDownIcon,
  DocumentIcon,
  ShareIcon,
  AtSymbolIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  CalendarIcon,
  Cog6ToothIcon,
  PhotoIcon,
  SwatchIcon
} from '@heroicons/react/24/outline';
import { PDF_TEMPLATES, generatePDF, generatePDFWithCharts } from './utils/pdfGenerator';
import { EXCEL_TEMPLATES, generateExcel, generateBatchExcel } from './utils/excelGenerator';
import {
  EMAIL_TEMPLATES,
  sendReportEmail,
  sendMultipleEmails,
  isValidEmail
} from './utils/emailService';
import { saveAs } from 'file-saver';

export interface EconomicBacktestReport {
  id: string;
  strategyName: string;
  strategy: {
    name: string;
    parameters: Record<string, any>;
    category: string;
  };
  period: {
    start: string;
    end: string;
    duration: number;
  };
  metrics: {
    totalReturn: number;
    annualizedReturn: number;
    maxDrawdown: number;
    sharpeRatio: number;
    sortinoRatio: number;
    calmarRatio: number;
    volatility: number;
    winRate: number;
    profitFactor: number;
    averageWin: number;
    averageLoss: number;
    totalTrades: number;
    winningTrades: number;
    losingTrades: number;
  };
  economicData?: any;
  strategyComparison?: any[];
  contributionBreakdown?: any[];
  equityCurve?: any[];
  trades?: any[];
  generatedAt: string;
}

interface ReportExporterProps {
  report?: EconomicBacktestReport;
  reports?: EconomicBacktestReport[];
  isOpen: boolean;
  onClose: () => void;
  exportHistory?: Array<{
    format: string;
    template: string;
    date: string;
    status: 'Completed' | 'Processing' | 'Failed';
  }>;
}

interface BrandingOptions {
  companyName?: string;
  logoUrl?: string;
  primaryColor?: string;
  secondaryColor?: string;
  fontFamily?: string;
}

const ReportExporter: React.FC<ReportExporterProps> = ({
  report,
  reports,
  isOpen,
  onClose,
  exportHistory = []
}) => {
  const [activeTab, setActiveTab] = useState<'export' | 'branding' | 'history'>('export');
  const [exportFormat, setExportFormat] = useState<'pdf' | 'excel'>('pdf');
  const [selectedTemplate, setSelectedTemplate] = useState('standard');
  const [includeCharts, setIncludeCharts] = useState(true);
  const [emailReport, setEmailReport] = useState(false);
  const [emailAddresses, setEmailAddresses] = useState('');
  const [emailTemplate, setEmailTemplate] = useState('standard');
  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [exportStatus, setExportStatus] = useState<'idle' | 'processing' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [branding, setBranding] = useState<BrandingOptions>({
    companyName: '',
    logoUrl: '',
    primaryColor: '#3B82F6',
    secondaryColor: '#10B981',
    fontFamily: 'Inter'
  });

  const isBatchExport = reports && reports.length > 1;
  const currentReports = isBatchExport ? reports : (report ? [report] : []);

  useEffect(() => {
    if (isOpen) {
      // Reset state when modal opens
      setActiveTab('export');
      setExportFormat('pdf');
      setSelectedTemplate('standard');
      setIncludeCharts(true);
      setEmailReport(false);
      setEmailAddresses('');
      setEmailTemplate('standard');
      setIsExporting(false);
      setExportProgress(0);
      setExportStatus('idle');
      setErrorMessage('');
    }
  }, [isOpen]);

  const handleExport = async () => {
    if (!currentReports || currentReports.length === 0) return;

    setIsExporting(true);
    setExportStatus('processing');
    setExportProgress(0);

    try {
      if (isBatchExport) {
        // Batch export
        const totalReports = currentReports.length;
        const exportedUrls: string[] = [];

        for (let i = 0; i < totalReports; i++) {
          const currentReport = currentReports[i];
          setExportProgress((i / totalReports) * 50);

          let exportUrl: string;
          if (exportFormat === 'pdf') {
            exportUrl = await generatePDF(currentReport, selectedTemplate, branding);
          } else {
            exportUrl = await generateExcel(currentReport, selectedTemplate, branding);
          }

          exportedUrls.push(exportUrl);
        }

        setExportProgress(50);

        // Create ZIP archive (in a real implementation, you would use JSZip)
        if (exportFormat === 'pdf') {
          const batchPdfUrl = await generatePDF(currentReports[0], selectedTemplate, branding);
          saveAs(batchPdfUrl, `Strategy_Reports_Batch_${new Date().toISOString().split('T')[0]}.pdf`);
        } else {
          const batchExcelUrl = await generateBatchExcel(currentReports, selectedTemplate);
          saveAs(batchExcelUrl, `Strategy_Reports_Batch_${new Date().toISOString().split('T')[0]}.xlsx`);
        }

        setExportProgress(100);
      } else {
        // Single report export
        const currentReport = currentReports[0];

        if (exportFormat === 'pdf') {
          setExportProgress(25);
          let pdfUrl: string;

          if (includeCharts && document.querySelectorAll('#performance-chart, #correlation-chart').length > 0) {
            const chartIds = ['performance-chart', 'correlation-chart', 'contribution-chart'];
            pdfUrl = await generatePDFWithCharts(currentReport, chartIds, selectedTemplate);
          } else {
            pdfUrl = await generatePDF(currentReport, selectedTemplate, branding);
          }

          setExportProgress(75);

          // Download the PDF
          saveAs(pdfUrl, `${currentReport.strategyName}_Report_${new Date().toISOString().split('T')[0]}.pdf`);

          setExportProgress(100);
        } else {
          setExportProgress(25);
          const excelUrl = await generateExcel(currentReport, selectedTemplate, branding);
          setExportProgress(75);

          // Download the Excel file
          saveAs(excelUrl, `${currentReport.strategyName}_Report_${new Date().toISOString().split('T')[0]}.xlsx`);

          setExportProgress(100);
        }

        // Send email if requested
        if (emailReport && emailAddresses) {
          const recipients = emailAddresses.split(',').map(e => e.trim()).filter(e => e);
          const validEmails = recipients.filter(isValidEmail);

          if (validEmails.length === 0) {
            throw new Error('No valid email addresses provided');
          }

          setExportProgress(90);

          const reportUrl = exportFormat === 'pdf'
            ? URL.createObjectURL(new Blob(['PDF content'], { type: 'application/pdf' }))
            : URL.createObjectURL(new Blob(['Excel content'], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }));

          for (const email of validEmails) {
            await sendReportEmail(currentReport, email, emailTemplate, reportUrl, exportFormat);
          }
        }
      }

      setExportStatus('success');
      setTimeout(() => {
        onClose();
      }, 2000);
    } catch (error: any) {
      console.error('Export failed:', error);
      setExportStatus('error');
      setErrorMessage(error.message || 'Export failed. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  const handleEmailValidation = () => {
    if (!emailReport) return true;

    const emails = emailAddresses.split(',').map(e => e.trim()).filter(e => e);
    const validEmails = emails.filter(isValidEmail);

    return validEmails.length > 0;
  };

  const renderExportTab = () => (
    <div className="space-y-6">
      {/* Export Format */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">Export Format</label>
        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={() => setExportFormat('pdf')}
            className={`p-4 border rounded-lg flex items-center space-x-3 transition-colors ${
              exportFormat === 'pdf'
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <DocumentIcon className="w-6 h-6" />
            <div className="text-left">
              <p className="font-medium">PDF Report</p>
              <p className="text-sm opacity-75">Professional formatted report</p>
            </div>
          </button>
          <button
            onClick={() => setExportFormat('excel')}
            className={`p-4 border rounded-lg flex items-center space-x-3 transition-colors ${
              exportFormat === 'excel'
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <DocumentArrowDownIcon className="w-6 h-6" />
            <div className="text-left">
              <p className="font-medium">Excel Data</p>
              <p className="text-sm opacity-75">Raw data and calculations</p>
            </div>
          </button>
        </div>
      </div>

      {/* Template Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Report Template
        </label>
        <select
          value={selectedTemplate}
          onChange={(e) => setSelectedTemplate(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        >
          {(exportFormat === 'pdf' ? PDF_TEMPLATES : EXCEL_TEMPLATES).map(template => (
            <option key={template.id} value={template.id}>
              {template.name}
            </option>
          ))}
        </select>
      </div>

      {/* Include Charts (PDF only) */}
      {exportFormat === 'pdf' && !isBatchExport && (
        <div className="flex items-center">
          <input
            type="checkbox"
            id="include-charts"
            checked={includeCharts}
            onChange={(e) => setIncludeCharts(e.target.checked)}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="include-charts" className="ml-2 text-sm text-gray-700">
            Include charts and graphs
          </label>
        </div>
      )}

      {/* Email Options */}
      <div>
        <div className="flex items-center mb-3">
          <input
            type="checkbox"
            id="email-report"
            checked={emailReport}
            onChange={(e) => setEmailReport(e.target.checked)}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="email-report" className="ml-2 text-sm font-medium text-gray-700">
            Email report
          </label>
        </div>

        {emailReport && (
          <div className="space-y-3 pl-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email addresses (comma-separated)
              </label>
              <input
                type="text"
                value={emailAddresses}
                onChange={(e) => setEmailAddresses(e.target.value)}
                placeholder="john@example.com, jane@example.com"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email template
              </label>
              <select
                value={emailTemplate}
                onChange={(e) => setEmailTemplate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                {EMAIL_TEMPLATES.map(template => (
                  <option key={template.id} value={template.id}>
                    {template.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Batch Export Options */}
      {isBatchExport && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-blue-800 mb-2">Batch Export Options</h3>
          <p className="text-sm text-blue-700">
            Exporting {currentReports.length} reports as a single file.
            {exportFormat === 'excel' ? ' Each report will be a separate sheet in the Excel file.' : ''}
          </p>
        </div>
      )}

      {/* Export Button */}
      <div className="flex justify-end">
        <button
          onClick={handleExport}
          disabled={isExporting || !handleEmailValidation()}
          className={`px-6 py-3 rounded-md font-medium transition-colors flex items-center space-x-2 ${
            isExporting || !handleEmailValidation()
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {isExporting ? (
            <>
              <ClockIcon className="w-5 h-5 animate-spin" />
              <span>Exporting... {Math.round(exportProgress)}%</span>
            </>
          ) : (
            <>
              <DocumentArrowDownIcon className="w-5 h-5" />
              <span>{isBatchExport ? 'Export All' : 'Export Report'}</span>
            </>
          )}
        </button>
      </div>

      {/* Progress Bar */}
      {isExporting && (
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${exportProgress}%` }}
          />
        </div>
      )}

      {/* Status Messages */}
      {exportStatus === 'success' && (
        <div className="flex items-center p-3 bg-green-50 border border-green-200 rounded-lg">
          <CheckCircleIcon className="w-5 h-5 text-green-600 mr-2" />
          <p className="text-sm text-green-800">
            Report exported successfully!
            {emailReport && ' Email has been sent.'}
          </p>
        </div>
      )}

      {exportStatus === 'error' && (
        <div className="flex items-center p-3 bg-red-50 border border-red-200 rounded-lg">
          <ExclamationCircleIcon className="w-5 h-5 text-red-600 mr-2" />
          <p className="text-sm text-red-800">Export failed: {errorMessage}</p>
        </div>
      )}
    </div>
  );

  const renderBrandingTab = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-medium text-gray-900">Customize Branding</h3>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Company Name
        </label>
        <input
          type="text"
          value={branding.companyName}
          onChange={(e) => setBranding({ ...branding, companyName: e.target.value })}
          placeholder="Your Company"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Logo URL
        </label>
        <input
          type="url"
          value={branding.logoUrl}
          onChange={(e) => setBranding({ ...branding, logoUrl: e.target.value })}
          placeholder="https://example.com/logo.png"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Primary Color
          </label>
          <input
            type="color"
            value={branding.primaryColor}
            onChange={(e) => setBranding({ ...branding, primaryColor: e.target.value })}
            className="h-10 w-full"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Secondary Color
          </label>
          <input
            type="color"
            value={branding.secondaryColor}
            onChange={(e) => setBranding({ ...branding, secondaryColor: e.target.value })}
            className="h-10 w-full"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Font Family
        </label>
        <select
          value={branding.fontFamily}
          onChange={(e) => setBranding({ ...branding, fontFamily: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="Inter">Inter</option>
          <option value="Arial">Arial</option>
          <option value="Helvetica">Helvetica</option>
          <option value="Times New Roman">Times New Roman</option>
          <option value="Georgia">Georgia</option>
        </select>
      </div>

      {/* Preview */}
      <div className="border-t pt-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Preview</h4>
        <div className="border rounded-lg p-4" style={{ fontFamily: branding.fontFamily }}>
          <div className="flex items-center space-x-3 mb-3">
            {branding.logoUrl && (
              <img src={branding.logoUrl} alt="Logo" className="h-8" />
            )}
            <h5 className="text-lg font-bold" style={{ color: branding.primaryColor }}>
              {branding.companyName || 'Your Company'}
            </h5>
          </div>
          <p className="text-sm text-gray-600">
            Sample report header with custom branding applied
          </p>
        </div>
      </div>
    </div>
  );

  const renderHistoryTab = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-medium text-gray-900">Previous Exports</h3>

      {exportHistory.length === 0 ? (
        <p className="text-sm text-gray-500 text-center py-8">
          No export history available
        </p>
      ) : (
        <div className="space-y-2">
          {exportHistory.map((item, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
            >
              <div className="flex items-center space-x-3">
                <CalendarIcon className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {item.format} - {item.template}
                  </p>
                  <p className="text-xs text-gray-500">{item.date}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  item.status === 'Completed'
                    ? 'bg-green-100 text-green-800'
                    : item.status === 'Processing'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {item.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            Export {isBatchExport ? `${currentReports.length} Reports` : 'Report'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b">
          <nav className="flex -mb-px">
            {[
              { id: 'export', label: 'Export', icon: DocumentArrowDownIcon },
              { id: 'branding', label: 'Branding', icon: SwatchIcon },
              { id: 'history', label: 'History', icon: ClockIcon }
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 px-6 py-3 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Content */}
        <div className="p-6">
          {activeTab === 'export' && renderExportTab()}
          {activeTab === 'branding' && renderBrandingTab()}
          {activeTab === 'history' && renderHistoryTab()}
        </div>
      </div>
    </div>
  );
};

export default ReportExporter;