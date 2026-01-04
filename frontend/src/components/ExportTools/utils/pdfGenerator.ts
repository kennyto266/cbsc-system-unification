import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { EconomicBacktestReport } from '../ReportExporter';

export interface PDFTemplate {
  name: string;
  id: string;
  includeCharts: boolean;
  includeTrades: boolean;
  colorScheme: 'blue' | 'green' | 'purple' | 'gray';
  fontSize: 'small' | 'medium' | 'large';
  pageOrientation: 'portrait' | 'landscape';
}

export const PDF_TEMPLATES: PDFTemplate[] = [
  {
    name: 'Standard Professional',
    id: 'standard',
    includeCharts: true,
    includeTrades: true,
    colorScheme: 'blue',
    fontSize: 'medium',
    pageOrientation: 'portrait'
  },
  {
    name: 'Executive Summary',
    id: 'executive',
    includeCharts: true,
    includeTrades: false,
    colorScheme: 'gray',
    fontSize: 'large',
    pageOrientation: 'portrait'
  },
  {
    name: 'Technical Analysis',
    id: 'technical',
    includeCharts: true,
    includeTrades: true,
    colorScheme: 'purple',
    fontSize: 'small',
    pageOrientation: 'landscape'
  },
  {
    name: 'Investor Report',
    id: 'investor',
    includeCharts: true,
    includeTrades: false,
    colorScheme: 'green',
    fontSize: 'medium',
    pageOrientation: 'portrait'
  },
  {
    name: 'Research Paper',
    id: 'research',
    includeCharts: true,
    includeTrades: true,
    colorScheme: 'blue',
    fontSize: 'small',
    pageOrientation: 'portrait'
  },
  {
    name: 'Comprehensive Analysis',
    id: 'comprehensive',
    includeCharts: true,
    includeTrades: true,
    colorScheme: 'purple',
    fontSize: 'small',
    pageOrientation: 'landscape'
  },
  {
    name: 'Quick Summary',
    id: 'quick',
    includeCharts: false,
    includeTrades: false,
    colorScheme: 'gray',
    fontSize: 'large',
    pageOrientation: 'portrait'
  },
  {
    name: 'Performance Focus',
    id: 'performance',
    includeCharts: true,
    includeTrades: false,
    colorScheme: 'green',
    fontSize: 'medium',
    pageOrientation: 'portrait'
  },
  {
    name: 'Risk Analysis',
    id: 'risk',
    includeCharts: true,
    includeTrades: true,
    colorScheme: 'red',
    fontSize: 'medium',
    pageOrientation: 'portrait'
  },
  {
    name: 'Compliance Report',
    id: 'compliance',
    includeCharts: false,
    includeTrades: true,
    colorScheme: 'gray',
    fontSize: 'small',
    pageOrientation: 'portrait'
  },
  {
    name: 'Marketing Material',
    id: 'marketing',
    includeCharts: true,
    includeTrades: false,
    colorScheme: 'blue',
    fontSize: 'large',
    pageOrientation: 'portrait'
  },
  {
    name: 'Internal Review',
    id: 'internal',
    includeCharts: true,
    includeTrades: true,
    colorScheme: 'purple',
    fontSize: 'small',
    pageOrientation: 'landscape'
  }
];

const COLOR_SCHEMES = {
  blue: {
    primary: [59, 130, 246],
    secondary: [147, 197, 253],
    text: [30, 58, 138]
  },
  green: {
    primary: [16, 185, 129],
    secondary: [134, 239, 172],
    text: [6, 95, 70]
  },
  purple: {
    primary: [139, 92, 246],
    secondary: [196, 181, 253],
    text: [67, 56, 202]
  },
  gray: {
    primary: [107, 114, 128],
    secondary: [209, 213, 219],
    text: [55, 65, 81]
  },
  red: {
    primary: [239, 68, 68],
    secondary: [252, 165, 165],
    text: [153, 27, 27]
  }
};

const FONT_SIZES = {
  small: { title: 20, heading: 14, text: 10, caption: 8 },
  medium: { title: 24, heading: 16, text: 11, caption: 9 },
  large: { title: 28, heading: 18, text: 12, caption: 10 }
};

export async function generatePDF(
  report: EconomicBacktestReport,
  templateId: string = 'standard',
  branding?: {
    companyName?: string;
    logoUrl?: string;
    customColors?: string[];
  }
): Promise<string> {
  const template = PDF_TEMPLATES.find(t => t.id === templateId) || PDF_TEMPLATES[0];
  const colorScheme = COLOR_SCHEMES[template.colorScheme];
  const fontSize = FONT_SIZES[template.fontSize];

  // Initialize PDF
  const pdf = new jsPDF({
    orientation: template.pageOrientation,
    unit: 'mm',
    format: 'a4'
  });

  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const margin = 20;
  let currentY = margin;

  // Helper functions
  const addHeader = () => {
    // Add header background
    pdf.setFillColor(...colorScheme.primary, 0.1);
    pdf.rect(0, 0, pageWidth, 40, 'F');

    // Add title
    pdf.setFontSize(fontSize.title);
    pdf.setTextColor(...colorScheme.text);
    pdf.text('Economic Strategy Backtest Report', margin, 25);

    // Add subtitle
    pdf.setFontSize(fontSize.heading);
    pdf.setTextColor(100, 100, 100);
    pdf.text(report.strategyName, margin, 35);

    // Add date
    pdf.setFontSize(fontSize.text);
    pdf.text(`Generated: ${new Date(report.generatedAt).toLocaleDateString()}`, pageWidth - margin - 40, 25);

    // Add logo if provided
    if (branding?.logoUrl) {
      try {
        pdf.addImage(branding.logoUrl, 'PNG', pageWidth - 60, 10, 40, 20);
      } catch (error) {
        console.warn('Failed to load logo:', error);
      }
    }

    currentY = 50;
  };

  const addSection = (title: string, content: () => void) => {
    if (currentY > pageHeight - 60) {
      pdf.addPage();
      addHeader();
    }

    // Section title
    pdf.setFontSize(fontSize.heading);
    pdf.setTextColor(...colorScheme.primary);
    pdf.text(title, margin, currentY);
    currentY += 10;

    // Draw underline
    pdf.setDrawColor(...colorScheme.secondary);
    pdf.setLineWidth(0.5);
    pdf.line(margin, currentY, pageWidth - margin, currentY);
    currentY += 10;

    content();
    currentY += 15;
  };

  const addMetricCard = (label: string, value: string | number, unit: string = '', description?: string) => {
    // Card background
    pdf.setFillColor(250, 250, 250);
    pdf.roundedRect(margin, currentY, 60, 30, 2, 2, 'F');
    pdf.setDrawColor(230, 230, 230);
    pdf.roundedRect(margin, currentY, 60, 30, 2, 2, 'S');

    // Label
    pdf.setFontSize(fontSize.caption);
    pdf.setTextColor(100, 100, 100);
    pdf.text(label, margin + 5, currentY + 8);

    // Value
    pdf.setFontSize(fontSize.text);
    pdf.setTextColor(50, 50, 50);
    const displayValue = typeof value === 'number' && unit === '%'
      ? `${(value * 100).toFixed(2)}%`
      : typeof value === 'number' && unit === '$'
      ? `$${value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
      : value.toString();
    pdf.text(displayValue, margin + 5, currentY + 18);

    // Description
    if (description) {
      pdf.setFontSize(fontSize.caption);
      pdf.setTextColor(150, 150, 150);
      const lines = pdf.splitTextToSize(description, 50);
      pdf.text(lines, margin + 5, currentY + 24);
    }

    currentY += 35;
  };

  const addTable = (headers: string[], rows: string[][]) => {
    const tableWidth = pageWidth - 2 * margin;
    const columnWidth = tableWidth / headers.length;

    // Draw headers
    pdf.setFillColor(...colorScheme.primary, 0.1);
    pdf.rect(margin, currentY, tableWidth, 8, 'F');

    pdf.setFontSize(fontSize.text);
    pdf.setTextColor(...colorScheme.text);
    headers.forEach((header, i) => {
      pdf.text(header, margin + i * columnWidth + 2, currentY + 5);
    });

    currentY += 8;

    // Draw rows
    pdf.setTextColor(50, 50, 50);
    rows.forEach((row, i) => {
      if (currentY > pageHeight - 20) {
        pdf.addPage();
        addHeader();
        currentY = margin;

        // Redraw headers on new page
        pdf.setFillColor(...colorScheme.primary, 0.1);
        pdf.rect(margin, currentY, tableWidth, 8, 'F');
        pdf.setTextColor(...colorScheme.text);
        headers.forEach((header, j) => {
          pdf.text(header, margin + j * columnWidth + 2, currentY + 5);
        });
        currentY += 8;
        pdf.setTextColor(50, 50, 50);
      }

      // Alternate row colors
      if (i % 2 === 0) {
        pdf.setFillColor(250, 250, 250);
        pdf.rect(margin, currentY, tableWidth, 6, 'F');
      }

      row.forEach((cell, j) => {
        pdf.text(cell, margin + j * columnWidth + 2, currentY + 4);
      });

      currentY += 6;
    });

    currentY += 5;
  };

  // Generate PDF content
  addHeader();

  // Strategy Information
  addSection('Strategy Overview', () => {
    pdf.setFontSize(fontSize.text);
    pdf.setTextColor(80, 80, 80);

    const info = [
      ['Strategy Name:', report.strategy.name],
      ['Category:', report.strategy.category],
      ['Period:', `${new Date(report.period.start).toLocaleDateString()} - ${new Date(report.period.end).toLocaleDateString()}`],
      ['Duration:', `${report.period.duration} days`]
    ];

    info.forEach(([label, value]) => {
      pdf.setFont(undefined, 'bold');
      pdf.text(label, margin, currentY);
      pdf.setFont(undefined, 'normal');
      pdf.text(value, margin + 60, currentY);
      currentY += 7;
    });

    // Parameters
    if (Object.keys(report.strategy.parameters).length > 0) {
      currentY += 5;
      pdf.setFont(undefined, 'bold');
      pdf.text('Parameters:', margin, currentY);
      currentY += 7;

      Object.entries(report.strategy.parameters).forEach(([key, val]) => {
        pdf.setFont(undefined, 'normal');
        pdf.text(`  • ${key}: ${val}`, margin, currentY);
        currentY += 5;
      });
    }
  });

  // Performance Metrics
  addSection('Performance Metrics', () => {
    const metrics = [
      ['Total Return', report.metrics.totalReturn],
      ['Annualized Return', report.metrics.annualizedReturn],
      ['Max Drawdown', report.metrics.maxDrawdown],
      ['Sharpe Ratio', report.metrics.sharpeRatio]
    ];

    metrics.forEach(([label, value]) => {
      addMetricCard(label, value);
    });

    currentY = Math.max(currentY, margin + 150);
    currentY += 20;

    // Additional metrics
    const additionalMetrics = [
      ['Sortino Ratio', report.metrics.sortinoRatio],
      ['Calmar Ratio', report.metrics.calmarRatio],
      ['Volatility', report.metrics.volatility],
      ['Win Rate', report.metrics.winRate],
      ['Profit Factor', report.metrics.profitFactor],
      ['Total Trades', report.metrics.totalTrades]
    ];

    additionalMetrics.forEach(([label, value], i) => {
      const x = margin + (i % 3) * 65;
      const y = currentY - ((i % 3) === 0 && i > 0 ? 70 : 0);

      pdf.setFillColor(250, 250, 250);
      pdf.roundedRect(x, y, 55, 25, 2, 2, 'F');

      pdf.setFontSize(fontSize.caption);
      pdf.setTextColor(100, 100, 100);
      pdf.text(label, x + 3, y + 7);

      pdf.setFontSize(fontSize.text);
      pdf.setTextColor(50, 50, 50);
      const displayValue = label.includes('Rate') || label.includes('Return') || label.includes('Drawdown')
        ? `${(value as number * 100).toFixed(2)}%`
        : value.toString();
      pdf.text(displayValue, x + 3, y + 16);

      if ((i + 1) % 3 === 0) currentY += 30;
    });
  });

  // Economic Data
  if (report.economicData && template.includeCharts) {
    addSection('Economic Indicators', () => {
      report.economicData!.indicators.forEach((indicator, i) => {
        const correlation = report.economicData!.correlation[indicator.name] || 0;

        pdf.setFontSize(fontSize.text);
        pdf.setTextColor(80, 80, 80);
        pdf.text(`${indicator.name}:`, margin, currentY);

        const corrColor = correlation >= 0.3 ? [16, 185, 129] : correlation <= -0.3 ? [239, 68, 68] : [156, 163, 175];
        pdf.setTextColor(...corrColor);
        pdf.text(`Correlation: ${correlation.toFixed(3)}`, margin + 80, currentY);

        currentY += 7;
      });
    });
  }

  // Trades Table
  if (template.includeTrades && report.trades && report.trades.length > 0) {
    addSection('Trading History', () => {
      const headers = ['Date', 'Type', 'Price', 'Quantity', 'Profit', 'Return'];
      const rows = report.trades!.slice(0, 20).map(trade => [
        new Date(trade.date).toLocaleDateString(),
        trade.type,
        `$${trade.price.toFixed(2)}`,
        trade.quantity.toString(),
        trade.profit ? `$${trade.profit.toFixed(2)}` : '-',
        trade.profitPercent ? `${(trade.profitPercent * 100).toFixed(2)}%` : '-'
      ]);

      addTable(headers, rows);

      if (report.trades!.length > 20) {
        pdf.setFontSize(fontSize.caption);
        pdf.setTextColor(150, 150, 150);
        pdf.text(`Showing first 20 of ${report.trades!.length} trades`, margin, currentY);
      }
    });
  }

  // Footer
  const addFooter = () => {
    const pageCount = pdf.internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      pdf.setPage(i);
      pdf.setFontSize(fontSize.caption);
      pdf.setTextColor(150, 150, 150);
      pdf.text(
        `Page ${i} of ${pageCount}`,
        pageWidth / 2,
        pageHeight - 10,
        { align: 'center' }
      );

      if (branding?.companyName) {
        pdf.text(branding.companyName, margin, pageHeight - 10);
      }

      pdf.text(`© ${new Date().getFullYear()} All Rights Reserved`, pageWidth - margin - 40, pageHeight - 10);
    }
  };

  addFooter();

  // Generate PDF blob
  const pdfBlob = pdf.output('blob');
  const pdfUrl = URL.createObjectURL(pdfBlob);

  return pdfUrl;
}

export async function generatePDFWithCharts(
  report: EconomicBacktestReport,
  elementIds: string[],
  templateId: string = 'standard'
): Promise<string> {
  const template = PDF_TEMPLATES.find(t => t.id === templateId) || PDF_TEMPLATES[0];
  const pdf = new jsPDF({
    orientation: template.pageOrientation,
    unit: 'mm',
    format: 'a4'
  });

  // Add title page
  await generatePDF(report, templateId);

  // Add chart pages
  for (const elementId of elementIds) {
    const element = document.getElementById(elementId);
    if (element) {
      const canvas = await html2canvas(element, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#ffffff'
      });

      const imgData = canvas.toDataURL('image/png');
      const imgWidth = 180;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;

      pdf.addPage();
      pdf.addImage(imgData, 'PNG', 15, 20, imgWidth, imgHeight);
    }
  }

  const pdfBlob = pdf.output('blob');
  return URL.createObjectURL(pdfBlob);
}