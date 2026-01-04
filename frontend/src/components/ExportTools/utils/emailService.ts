export interface EmailOptions {
  to: string;
  subject?: string;
  body?: string;
  attachments?: Array<{
    filename: string;
    url: string;
    type: string;
  }>;
  cc?: string[];
  bcc?: string[];
}

export interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  body: string;
  includeSignature: boolean;
  includeDisclaimer: boolean;
}

export const EMAIL_TEMPLATES: EmailTemplate[] = [
  {
    id: 'standard',
    name: 'Standard Report',
    subject: 'Strategy Backtest Report - {strategyName}',
    body: `Dear {recipient},

Please find attached the backtest report for the {strategyName} strategy.

Key Highlights:
• Total Return: {totalReturn}
• Sharpe Ratio: {sharpeRatio}
• Max Drawdown: {maxDrawdown}
• Win Rate: {winRate}

The report covers the period from {startDate} to {endDate}.

Best regards`,
    includeSignature: true,
    includeDisclaimer: true
  },
  {
    id: 'executive',
    name: 'Executive Summary',
    subject: 'Executive Summary: {strategyName} Performance',
    body: `Dear {recipient},

Executive Summary for {strategyName} Strategy

Performance Overview:
The strategy delivered a total return of {totalReturn} over the analysis period, with a Sharpe ratio of {sharpeRatio} indicating strong risk-adjusted returns.

Key Metrics:
• Annualized Return: {annualizedReturn}
• Maximum Drawdown: {maxDrawdown}
• Win Rate: {winRate}
• Profit Factor: {profitFactor}

The detailed analysis is attached for your review.

Sincerely`,
    includeSignature: true,
    includeDisclaimer: false
  },
  {
    id: 'investor',
    name: 'Investor Update',
    subject: 'Investment Update: {strategyName} Strategy Performance',
    body: `Dear Investor,

We are pleased to share the latest performance report for the {strategyName} strategy.

Performance Highlights:
• Total Return: {totalReturn}
• Risk-Adjusted Return (Sharpe): {sharpeRatio}
• Downside Risk (Max DD): {maxDrawdown}

The strategy has demonstrated {performance} performance during the {period} period, outperforming the benchmark by {outperformance}.

Please review the attached detailed report for comprehensive analysis.

Should you have any questions, please don't hesitate to contact us.

Best regards`,
    includeSignature: true,
    includeDisclaimer: true
  },
  {
    id: 'compliance',
    name: 'Compliance Report',
    subject: 'Compliance Report: {strategyName} Backtest Results',
    body: `Dear Compliance Team,

Please find attached the compliance report for the {strategyName} strategy backtest.

Report Details:
• Strategy: {strategyName}
• Period: {startDate} to {endDate}
• Total Trades: {totalTrades}
• Trading Days: {tradingDays}

The report includes all required compliance documentation and risk metrics for your review.

Regards`,
    includeSignature: false,
    includeDisclaimer: true
  },
  {
    id: 'research',
    name: 'Research Analysis',
    subject: 'Research Analysis: {strategyName} Backtest Results',
    body: `Dear {recipient},

Attached is the research analysis report for the {strategyName} strategy.

Analysis Summary:
The strategy was tested over {duration} days with the following key findings:
• Economic Correlation: {economicCorrelation}
• Top Contributing Factor: {topFactor}
• Risk-Adjusted Performance: {riskAdjustedPerformance}

The full research analysis includes:
• Detailed performance metrics
• Economic data correlation analysis
• Factor contribution breakdown
• Strategy comparison matrix

Please let me know if you require any additional analysis.

Best regards`,
    includeSignature: true,
    includeDisclaimer: false
  }
];

export async function sendEmail(options: EmailOptions): Promise<{ success: boolean; message?: string }> {
  try {
    // In a real implementation, this would connect to an email service API
    // For now, we'll simulate the email sending process

    // Validate email address
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(options.to)) {
      throw new Error('Invalid email address');
    }

    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Log the email details (in production, this would be sent to the email service)
    console.log('Sending email:', {
      to: options.to,
      subject: options.subject,
      cc: options.cc,
      bcc: options.bcc,
      attachmentCount: options.attachments?.length || 0
    });

    // Simulate success
    return { success: true };
  } catch (error: any) {
    return { success: false, message: error.message };
  }
}

export async function sendMultipleEmails(
  recipients: string[],
  baseOptions: Omit<EmailOptions, 'to'>
): Promise<{ success: boolean; failed: string[]; message?: string }> {
  const failed: string[] = [];

  for (const recipient of recipients) {
    const result = await sendEmail({
      ...baseOptions,
      to: recipient
    });

    if (!result.success) {
      failed.push(recipient);
    }
  }

  return {
    success: failed.length === 0,
    failed,
    message: failed.length > 0
      ? `Failed to send to ${failed.length} recipients: ${failed.join(', ')}`
      : undefined
  };
}

export function generateEmailBody(
  template: EmailTemplate,
  data: Record<string, any>,
  recipient: string
): string {
  let body = template.body
    .replace(/{recipient}/g, recipient.split('@')[0])
    .replace(/{strategyName}/g, data.strategyName || 'N/A')
    .replace(/{totalReturn}/g, data.totalReturn ? `${(data.totalReturn * 100).toFixed(2)}%` : 'N/A')
    .replace(/{annualizedReturn}/g, data.annualizedReturn ? `${(data.annualizedReturn * 100).toFixed(2)}%` : 'N/A')
    .replace(/{maxDrawdown}/g, data.maxDrawdown ? `${(Math.abs(data.maxDrawdown) * 100).toFixed(2)}%` : 'N/A')
    .replace(/{sharpeRatio}/g, data.sharpeRatio?.toFixed(2) || 'N/A')
    .replace(/{winRate}/g, data.winRate ? `${(data.winRate * 100).toFixed(2)}%` : 'N/A')
    .replace(/{profitFactor}/g, data.profitFactor?.toFixed(2) || 'N/A')
    .replace(/{totalTrades}/g, data.totalTrades || 'N/A')
    .replace(/{startDate}/g, data.startDate ? new Date(data.startDate).toLocaleDateString() : 'N/A')
    .replace(/{endDate}/g, data.endDate ? new Date(data.endDate).toLocaleDateString() : 'N/A')
    .replace(/{duration}/g, data.duration || 'N/A')
    .replace(/{tradingDays}/g, data.tradingDays || 'N/A')
    .replace(/{economicCorrelation}/g, data.economicCorrelation || 'N/A')
    .replace(/{topFactor}/g, data.topFactor || 'N/A')
    .replace(/{riskAdjustedPerformance}/g, data.riskAdjustedPerformance || 'N/A')
    .replace(/{performance}/g, data.performance || 'strong')
    .replace(/{outperformance}/g, data.outperformance || 'N/A')
    .replace(/{period}/g, data.period || 'analysis');

  // Add signature
  if (template.includeSignature) {
    body += `

---
${data.senderName || 'Strategy Team'}
${data.senderTitle || 'Investment Analyst'}
${data.senderCompany || 'Investment Firm'}
${data.senderPhone || ''}
${data.senderEmail || ''}`;
  }

  // Add disclaimer
  if (template.includeDisclaimer) {
    body += `


Disclaimer:
This report is for informational purposes only and does not constitute investment advice.
Past performance is not indicative of future results. The information contained in this
report is based on data we believe to be reliable but no representation is made that it
is accurate or complete. Investing involves risk including possible loss of principal.

© ${new Date().getFullYear()} ${data.companyName || 'Investment Firm'}. All rights reserved.`;
  }

  return body;
}

export function generateSubject(
  template: EmailTemplate,
  data: Record<string, any>
): string {
  return template.subject
    .replace(/{strategyName}/g, data.strategyName || 'Strategy')
    .replace(/{date}/g, new Date().toLocaleDateString());
}

export async function sendReportEmail(
  reportData: any,
  recipient: string,
  templateId: string = 'standard',
  reportUrl: string,
  reportFormat: 'PDF' | 'Excel' = 'PDF'
): Promise<{ success: boolean; message?: string }> {
  const template = EMAIL_TEMPLATES.find(t => t.id === templateId) || EMAIL_TEMPLATES[0];

  const subject = generateSubject(template, {
    strategyName: reportData.strategyName
  });

  const body = generateEmailBody(template, {
    ...reportData,
    senderName: reportData.senderName,
    senderTitle: reportData.senderTitle,
    senderCompany: reportData.senderCompany,
    companyName: reportData.senderCompany
  }, recipient);

  return sendEmail({
    to: recipient,
    subject,
    body,
    attachments: [{
      filename: `${reportData.strategyName}_Report.${reportFormat.toLowerCase()}`,
      url: reportUrl,
      type: reportFormat === 'PDF' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }]
  });
}

export async function scheduleEmail(
  options: EmailOptions,
  scheduledDate: Date
): Promise<{ success: boolean; scheduledId?: string; message?: string }> {
  try {
    // In a real implementation, this would use a scheduling service like
    // AWS SES, SendGrid Scheduled Sends, or a custom cron job

    const scheduledId = `email_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    console.log('Scheduling email:', {
      id: scheduledId,
      scheduledFor: scheduledDate.toISOString(),
      to: options.to
    });

    // Simulate scheduling
    return {
      success: true,
      scheduledId,
      message: `Email scheduled for ${scheduledDate.toLocaleString()}`
    };
  } catch (error: any) {
    return { success: false, message: error.message };
  }
}

export async function cancelScheduledEmail(scheduledId: string): Promise<{ success: boolean; message?: string }> {
  try {
    // In a real implementation, this would cancel the scheduled email
    console.log('Cancelling scheduled email:', scheduledId);

    return { success: true, message: 'Scheduled email cancelled' };
  } catch (error: any) {
    return { success: false, message: error.message };
  }
}

// Email validation utilities
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

export function extractDomain(email: string): string {
  return email.split('@')[1] || '';
}

export function isCorporateEmail(email: string): boolean {
  const domain = extractDomain(email);
  const personalDomains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com'];
  return !personalDomains.includes(domain.toLowerCase());
}