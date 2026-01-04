import * as XLSX from 'xlsx';
import { EconomicBacktestReport } from '../ReportExporter';

export interface ExcelTemplate {
  name: string;
  id: string;
  includeSheets: string[];
  format: 'standard' | 'detailed' | 'summary';
}

export const EXCEL_TEMPLATES: ExcelTemplate[] = [
  {
    name: 'Standard Report',
    id: 'standard',
    includeSheets: ['Summary', 'Metrics', 'Trades', 'Economic Data'],
    format: 'standard'
  },
  {
    name: 'Detailed Analysis',
    id: 'detailed',
    includeSheets: ['Summary', 'Metrics', 'Trades', 'Economic Data', 'Risk Analysis', 'Comparison'],
    format: 'detailed'
  },
  {
    name: 'Quick Summary',
    id: 'summary',
    includeSheets: ['Summary', 'Key Metrics'],
    format: 'summary'
  },
  {
    name: 'Research Data',
    id: 'research',
    includeSheets: ['Summary', 'Metrics', 'Trades', 'Economic Data', 'Correlations', 'Contributions'],
    format: 'detailed'
  },
  {
    name: 'Investor Report',
    id: 'investor',
    includeSheets: ['Executive Summary', 'Performance', 'Risk Metrics'],
    format: 'summary'
  },
  {
    name: 'Compliance Report',
    id: 'compliance',
    includeSheets: ['Summary', 'Trades', 'Risk Analysis', 'Compliance Notes'],
    format: 'standard'
  },
  {
    name: 'Audit Trail',
    id: 'audit',
    includeSheets: ['Trades', 'Positions', 'Cash Flows', 'Adjustments'],
    format: 'detailed'
  },
  {
    name: 'Performance Attribution',
    id: 'attribution',
    includeSheets: ['Summary', 'Contributions', 'Factor Analysis', 'Sector Performance'],
    format: 'detailed'
  },
  {
    name: 'Risk Dashboard',
    id: 'risk',
    includeSheets: ['Risk Summary', 'VaR Analysis', 'Stress Tests', 'Correlations'],
    format: 'standard'
  },
  {
    name: 'Trading Analytics',
    id: 'trading',
    includeSheets: ['Trades', 'Order Analysis', 'Execution Quality', 'Cost Analysis'],
    format: 'detailed'
  }
];

function applyCellStyles(ws: XLSX.WorkSheet, cellRef: string, style: Partial<XLSX.CellStyle>) {
  if (!ws[cellRef]) return;
  ws[cellRef].s = { ...ws[cellRef].s, ...style };
}

function createHeaderStyle(workbook: XLSX.WorkBook) {
  return {
    font: { bold: true, color: { rgb: 'FFFFFF' } },
    fill: { fgColor: { rgb: '4472C4' } },
    alignment: { horizontal: 'center', vertical: 'center' },
    border: {
      top: { style: 'thin', color: { auto: 1 } },
      bottom: { style: 'thin', color: { auto: 1 } },
      left: { style: 'thin', color: { auto: 1 } },
      right: { style: 'thin', color: { auto: 1 } }
    }
  };
}

function createNumberFormat(format: string): Partial<XLSX.CellStyle> {
  return {
    numFmt: format,
    alignment: { horizontal: 'right' }
  };
}

function createCellStyle(isHeader: boolean = false, isAlternate: boolean = false): Partial<XLSX.CellStyle> {
  if (isHeader) {
    return createHeaderStyle({} as XLSX.WorkBook);
  }

  return {
    fill: isAlternate ? { fgColor: { rgb: 'F2F2F2' } } : { fgColor: { rgb: 'FFFFFF' } },
    border: {
      top: { style: 'thin', color: { auto: 1 } },
      bottom: { style: 'thin', color: { auto: 1 } },
      left: { style: 'thin', color: { auto: 1 } },
      right: { style: 'thin', color: { auto: 1 } }
    },
    alignment: { vertical: 'center', wrapText: true }
  };
}

function autoSizeColumns(ws: XLSX.WorkSheet, data: any[][]) {
  const colWidths = data[0].map((_, colIndex) => {
    const maxLength = Math.max(
      ...data.map(row => String(row[colIndex] || '').length)
    );
    return { width: Math.min(Math.max(maxLength + 2, 10), 50) };
  });

  ws['!cols'] = colWidths;
}

export async function generateExcel(
  report: EconomicBacktestReport,
  templateId: string = 'standard',
  branding?: {
    companyName?: string;
    logoUrl?: string;
  }
): Promise<string> {
  const template = EXCEL_TEMPLATES.find(t => t.id === templateId) || EXCEL_TEMPLATES[0];
  const workbook = XLSX.utils.book_new();

  // Common styles
  const headerStyle = createHeaderStyle(workbook);
  const numberFormat = createNumberFormat('#,##0.00');
  const percentFormat = createNumberFormat('0.00%');
  const currencyFormat = createNumberFormat('$#,##0.00');

  // Create Summary Sheet
  if (template.includeSheets.includes('Summary') || template.includeSheets.includes('Executive Summary')) {
    const summaryData = [
      ['Strategy Report Summary', '', '', '', ''],
      ['Generated:', new Date(report.generatedAt).toLocaleString(), '', '', ''],
      [''],
      ['Strategy Information', '', '', '', ''],
      ['Name:', report.strategy.name, '', '', ''],
      ['Category:', report.strategy.category, '', '', ''],
      ['Start Date:', new Date(report.period.start).toLocaleDateString(), '', '', ''],
      ['End Date:', new Date(report.period.end).toLocaleDateString(), '', '', ''],
      ['Duration (days):', report.period.duration, '', '', ''],
      [''],
      ['Performance Summary', '', '', '', ''],
      ['Total Return:', report.metrics.totalReturn, 'Format:Percentage', '', ''],
      ['Annualized Return:', report.metrics.annualizedReturn, 'Format:Percentage', '', ''],
      ['Max Drawdown:', report.metrics.maxDrawdown, 'Format:Percentage', '', ''],
      ['Sharpe Ratio:', report.metrics.sharpeRatio, 'Format:Number', '', ''],
      ['Win Rate:', report.metrics.winRate, 'Format:Percentage', '', ''],
      ['Total Trades:', report.metrics.totalTrades, 'Format:Number', '', '']
    ];

    if (Object.keys(report.strategy.parameters).length > 0) {
      summaryData.push(['']);
      summaryData.push(['Parameters', '', '', '', '']);
      Object.entries(report.strategy.parameters).forEach(([key, value]) => {
        summaryData.push([key, value, '', '', '']);
      });
    }

    if (branding?.companyName) {
      summaryData[0][0] = `${branding.companyName} - Strategy Report Summary`;
    }

    const wsSummary = XLSX.utils.aoa_to_sheet(summaryData);

    // Apply styles
    Object.keys(wsSummary).forEach(cellRef => {
      if (cellRef[0] === '!') return;

      const cell = wsSummary[cellRef];
      const row = parseInt(cellRef.slice(1)) - 1;
      const col = cellRef.charCodeAt(0) - 65;

      if (summaryData[row][0] === 'Strategy Report Summary' ||
          summaryData[row][0].includes('Information') ||
          summaryData[row][0].includes('Performance') ||
          summaryData[row][0] === 'Parameters') {
        cell.s = headerStyle;
      } else if (summaryData[row][1] === 'Format:Percentage') {
        cell.s = { ...createCellStyle(false, row % 2 === 0), ...percentFormat };
        cell.v = summaryData[row][0] === 'Max Drawdown' ? Math.abs(cell.v as number) : cell.v;
        summaryData[row][1] = cell.v;
      } else if (summaryData[row][1] === 'Format:Number') {
        cell.s = { ...createCellStyle(false, row % 2 === 0), ...numberFormat };
      } else {
        cell.s = createCellStyle(false, row % 2 === 0);
      }
    });

    // Merge title cell
    wsSummary['!merges'] = [{ s: { r: 0, c: 0 }, e: { r: 0, c: 4 } }];

    autoSizeColumns(wsSummary, summaryData);
    XLSX.utils.book_append_sheet(workbook, wsSummary, 'Summary');
  }

  // Create Metrics Sheet
  if (template.includeSheets.includes('Metrics') || template.includeSheets.includes('Key Metrics')) {
    const metricsData = [
      ['Performance Metrics', 'Value', 'Description'],
      ['Total Return', report.metrics.totalReturn, 'Total portfolio return over the entire period'],
      ['Annualized Return', report.metrics.annualizedReturn, 'Yearly equivalent return rate'],
      ['Max Drawdown', report.metrics.maxDrawdown, 'Maximum peak-to-trough decline'],
      ['Sharpe Ratio', report.metrics.sharpeRatio, 'Risk-adjusted return measure'],
      ['Sortino Ratio', report.metrics.sortinoRatio, 'Downside risk-adjusted return'],
      ['Calmar Ratio', report.metrics.calmarRatio, 'Return to maximum drawdown ratio'],
      ['Volatility', report.metrics.volatility, 'Annualized standard deviation of returns'],
      ['Win Rate', report.metrics.winRate, 'Percentage of profitable trades'],
      ['Profit Factor', report.metrics.profitFactor, 'Total profit divided by total loss'],
      ['Average Win', report.metrics.averageWin, 'Average profit from winning trades'],
      ['Average Loss', report.metrics.averageLoss, 'Average loss from losing trades'],
      ['Total Trades', report.metrics.totalTrades, 'Total number of trades executed'],
      ['Winning Trades', report.metrics.winningTrades, 'Number of profitable trades'],
      ['Losing Trades', report.metrics.losingTrades, 'Number of losing trades']
    ];

    const wsMetrics = XLSX.utils.aoa_to_sheet(metricsData);

    // Apply styles
    Object.keys(wsMetrics).forEach(cellRef => {
      if (cellRef[0] === '!') return;

      const cell = wsMetrics[cellRef];
      const row = parseInt(cellRef.slice(1)) - 1;
      const col = cellRef.charCodeAt(0) - 65;

      if (row === 0) {
        cell.s = headerStyle;
      } else if (col === 1) {
        // Value column
        const isPercent = metricsData[row][0].includes('Return') ||
                         metricsData[row][0].includes('Drawdown') ||
                         metricsData[row][0].includes('Rate');
        const isCurrency = metricsData[row][0].includes('Win') ||
                          metricsData[row][0].includes('Loss');

        cell.s = {
          ...createCellStyle(false, row % 2 === 0),
          ...(isPercent ? percentFormat : isCurrency ? currencyFormat : numberFormat)
        };

        if (isPercent) {
          metricsData[row][1] = metricsData[row][0] === 'Max Drawdown'
            ? Math.abs(cell.v as number)
            : cell.v;
        }
      } else {
        cell.s = createCellStyle(false, row % 2 === 0);
      }
    });

    autoSizeColumns(wsMetrics, metricsData);
    XLSX.utils.book_append_sheet(workbook, wsMetrics, 'Metrics');
  }

  // Create Trades Sheet
  if (template.includeSheets.includes('Trades') && report.trades) {
    const tradesData = [
      ['Date', 'Type', 'Price', 'Quantity', 'Profit', 'Return %', 'Portfolio Value'],
      ...report.trades.map(trade => [
        new Date(trade.date).toLocaleDateString(),
        trade.type.toUpperCase(),
        trade.price,
        trade.quantity,
        trade.profit || '',
        trade.profitPercent ? (trade.profitPercent * 100).toFixed(2) + '%' : '',
        '' // Will be calculated
      ])
    ];

    // Calculate running portfolio value
    let runningValue = 100000; // Starting value
    tradesData.slice(1).forEach((row, index) => {
      if (row[4]) { // If there's a profit
        runningValue += parseFloat(row[4] as string);
      }
      row[6] = runningValue.toFixed(2);
    });

    const wsTrades = XLSX.utils.aoa_to_sheet(tradesData);

    // Apply styles
    Object.keys(wsTrades).forEach(cellRef => {
      if (cellRef[0] === '!') return;

      const cell = wsTrades[cellRef];
      const row = parseInt(cellRef.slice(1)) - 1;
      const col = cellRef.charCodeAt(0) - 65;

      if (row === 0) {
        cell.s = headerStyle;
      } else if (col >= 2 && col <= 4 || col === 6) {
        // Numeric columns
        cell.s = {
          ...createCellStyle(false, row % 2 === 0),
          ...(col === 4 || col === 6 ? currencyFormat : numberFormat)
        };
      } else if (col === 1) {
        // Trade type column
        cell.s = {
          ...createCellStyle(false, row % 2 === 0),
          font: { bold: true, color: { rgb: tradesData[row][1] === 'BUY' ? '00AA00' : 'FF0000' } }
        };
      } else {
        cell.s = createCellStyle(false, row % 2 === 0);
      }
    });

    autoSizeColumns(wsTrades, tradesData);
    XLSX.utils.book_append_sheet(workbook, wsTrades, 'Trades');
  }

  // Create Economic Data Sheet
  if (template.includeSheets.includes('Economic Data') && report.economicData) {
    const economicData = [
      ['Economic Indicator', 'Current Value', 'Previous Value', 'Correlation with Strategy', 'Impact'],
      ...report.economicData.indicators.map(indicator => {
        const correlation = report.economicData!.correlation[indicator.name] || 0;
        const values = indicator.values;
        return [
          indicator.name,
          values[values.length - 1]?.toFixed(4) || 'N/A',
          values[values.length - 2]?.toFixed(4) || 'N/A',
          correlation.toFixed(4),
          Math.abs(correlation) > 0.5 ? 'High' : Math.abs(correlation) > 0.3 ? 'Medium' : 'Low'
        ];
      })
    ];

    const wsEconomic = XLSX.utils.aoa_to_sheet(economicData);

    // Apply styles
    Object.keys(wsEconomic).forEach(cellRef => {
      if (cellRef[0] === '!') return;

      const cell = wsEconomic[cellRef];
      const row = parseInt(cellRef.slice(1)) - 1;
      const col = cellRef.charCodeAt(0) - 65;

      if (row === 0) {
        cell.s = headerStyle;
      } else if (col <= 3) {
        cell.s = {
          ...createCellStyle(false, row % 2 === 0),
          ...numberFormat
        };
      } else if (col === 4) {
        const impact = economicData[row][col];
        const color = impact === 'High' ? 'FF0000' : impact === 'Medium' ? 'FFA500' : '00AA00';
        cell.s = {
          ...createCellStyle(false, row % 2 === 0),
          font: { color: { rgb: color } }
        };
      } else {
        cell.s = createCellStyle(false, row % 2 === 0);
      }
    });

    autoSizeColumns(wsEconomic, economicData);
    XLSX.utils.book_append_sheet(workbook, wsEconomic, 'Economic Data');
  }

  // Create Strategy Comparison Sheet
  if (template.includeSheets.includes('Comparison') && report.strategyComparison) {
    const comparisonData = [
      ['Strategy', 'Total Return', 'Sharpe Ratio', 'Max Drawdown', 'Volatility', 'Win Rate', 'Correlation'],
      ...report.strategyComparison.map(strategy => [
        strategy.name,
        strategy.totalReturn,
        strategy.sharpeRatio,
        strategy.maxDrawdown,
        strategy.volatility || '',
        strategy.winRate || '',
        strategy.correlation
      ])
    ];

    const wsComparison = XLSX.utils.aoa_to_sheet(comparisonData);

    // Apply styles
    Object.keys(wsComparison).forEach(cellRef => {
      if (cellRef[0] === '!') return;

      const cell = wsComparison[cellRef];
      const row = parseInt(cellRef.slice(1)) - 1;
      const col = cellRef.charCodeAt(0) - 65;

      if (row === 0) {
        cell.s = headerStyle;
      } else if (col >= 1 && col <= 6) {
        const isPercent = col === 1 || col === 3 || col === 4 || col === 5;
        cell.s = {
          ...createCellStyle(false, row % 2 === 0),
          ...(isPercent ? percentFormat : numberFormat)
        };

        // Highlight current strategy
        if (comparisonData[row][0] === report.strategyName) {
          cell.s.fill = { fgColor: { rgb: 'E6F3FF' } };
          cell.s.font = { bold: true };
        }
      } else {
        cell.s = createCellStyle(false, row % 2 === 0);

        // Highlight current strategy name
        if (comparisonData[row][0] === report.strategyName) {
          cell.s.font = { bold: true, color: { rgb: '0066CC' } };
        }
      }
    });

    autoSizeColumns(wsComparison, comparisonData);
    XLSX.utils.book_append_sheet(workbook, wsComparison, 'Strategy Comparison');
  }

  // Create Risk Analysis Sheet
  if (template.includeSheets.includes('Risk Analysis')) {
    const riskData = [
      ['Risk Metric', 'Value', 'Interpretation', 'Risk Level'],
      ['Value at Risk (95%)', report.metrics.maxDrawdown * 0.5, 'Maximum expected loss over 1 month',
       Math.abs(report.metrics.maxDrawdown * 0.5) > 0.05 ? 'High' : 'Medium'],
      ['Conditional VaR (95%)', report.metrics.maxDrawdown * 0.75, 'Expected loss beyond VaR',
       Math.abs(report.metrics.maxDrawdown * 0.75) > 0.08 ? 'High' : 'Medium'],
      ['Maximum Drawdown', report.metrics.maxDrawdown, 'Worst peak-to-trough decline',
       Math.abs(report.metrics.maxDrawdown) > 0.15 ? 'High' : Math.abs(report.metrics.maxDrawdown) > 0.1 ? 'Medium' : 'Low'],
      ['Volatility', report.metrics.volatility, 'Annualized standard deviation',
       report.metrics.volatility > 0.2 ? 'High' : report.metrics.volatility > 0.15 ? 'Medium' : 'Low'],
      ['Sharpe Ratio', report.metrics.sharpeRatio, 'Risk-adjusted return',
       report.metrics.sharpeRatio > 1.5 ? 'Excellent' : report.metrics.sharpeRatio > 1 ? 'Good' : 'Poor'],
      ['Sortino Ratio', report.metrics.sortinoRatio, 'Downside risk-adjusted return',
       report.metrics.sortinoRatio > 2 ? 'Excellent' : report.metrics.sortinoRatio > 1.5 ? 'Good' : 'Poor'],
      ['Calmar Ratio', report.metrics.calmarRatio, 'Return to maximum drawdown ratio',
       report.metrics.calmarRatio > 2 ? 'Excellent' : report.metrics.calmarRatio > 1 ? 'Good' : 'Poor']
    ];

    const wsRisk = XLSX.utils.aoa_to_sheet(riskData);

    // Apply styles
    Object.keys(wsRisk).forEach(cellRef => {
      if (cellRef[0] === '!') return;

      const cell = wsRisk[cellRef];
      const row = parseInt(cellRef.slice(1)) - 1;
      const col = cellRef.charCodeAt(0) - 65;

      if (row === 0) {
        cell.s = headerStyle;
      } else if (col === 1) {
        // Value column
        const isPercent = riskData[row][0].includes('Drawdown') ||
                         riskData[row][0].includes('VaR');
        cell.s = {
          ...createCellStyle(false, row % 2 === 0),
          ...(isPercent ? percentFormat : numberFormat)
        };
      } else if (col === 3) {
        // Risk Level column
        const level = riskData[row][col];
        const color = level === 'High' ? 'FF0000' : level === 'Medium' ? 'FFA500' :
                     level === 'Excellent' ? '00AA00' : level === 'Good' ? '00AA00' : 'FF0000';
        cell.s = {
          ...createCellStyle(false, row % 2 === 0),
          font: { bold: true, color: { rgb: color } }
        };
      } else {
        cell.s = createCellStyle(false, row % 2 === 0);
      }
    });

    autoSizeColumns(wsRisk, riskData);
    XLSX.utils.book_append_sheet(workbook, wsRisk, 'Risk Analysis');
  }

  // Generate Excel file
  const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
  const blob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
  const excelUrl = URL.createObjectURL(blob);

  return excelUrl;
}

export async function generateBatchExcel(
  reports: EconomicBacktestReport[],
  templateId: string = 'standard'
): Promise<string> {
  const workbook = XLSX.utils.book_new();

  // Create summary sheet with all reports
  const summaryData = [
    ['Report ID', 'Strategy Name', 'Total Return', 'Sharpe Ratio', 'Max Drawdown', 'Win Rate', 'Generated Date'],
    ...reports.map(report => [
      report.id,
      report.strategy.name,
      report.metrics.totalReturn,
      report.metrics.sharpeRatio,
      report.metrics.maxDrawdown,
      report.metrics.winRate,
      new Date(report.generatedAt).toLocaleDateString()
    ])
  ];

  const wsSummary = XLSX.utils.aoa_to_sheet(summaryData);
  XLSX.utils.book_append_sheet(workbook, wsSummary, 'Summary');

  // Create individual sheets for each report
  reports.forEach((report, index) => {
    const reportData = [
      ['Strategy Report', report.strategy.name],
      ['Period', `${new Date(report.period.start).toLocaleDateString()} - ${new Date(report.period.end).toLocaleDateString()}`],
      [''],
      ['Metric', 'Value'],
      ['Total Return', report.metrics.totalReturn],
      ['Annualized Return', report.metrics.annualizedReturn],
      ['Max Drawdown', report.metrics.maxDrawdown],
      ['Sharpe Ratio', report.metrics.sharpeRatio],
      ['Win Rate', report.metrics.winRate],
      ['Total Trades', report.metrics.totalTrades]
    ];

    const wsReport = XLSX.utils.aoa_to_sheet(reportData);
    const sheetName = `Report ${index + 1}`;
    XLSX.utils.book_append_sheet(workbook, wsReport, sheetName.slice(0, 31)); // Excel sheet name limit
  });

  // Generate Excel file
  const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
  const blob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
  const excelUrl = URL.createObjectURL(blob);

  return excelUrl;
}