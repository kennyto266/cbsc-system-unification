/**
 * Email Notification Service
 * Handles sending email notifications for alerts and system events
 */

import {
  EmailNotificationPayload,
  EmailAttachment,
  Alert,
  AlertSeverity,
  NotificationChannel
} from '../alerts/types';

export interface EmailConfig {
  smtp: {
    host: string;
    port: number;
    secure: boolean; // true for 465, false for other ports
    auth: {
      user: string;
      pass: string;
    };
  };
  from: {
    name: string;
    email: string;
  };
  replyTo?: string;
  templates: {
    baseUrl: string;
    logoUrl?: string;
    primaryColor?: string;
    footer?: string;
  };
  throttling: {
    enabled: boolean;
    maxEmailsPerMinute: number;
    maxEmailsPerHour: number;
  };
}

export interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  html: string;
  text: string;
  variables: string[];
}

export interface EmailDeliveryStatus {
  messageId: string;
  status: 'pending' | 'sent' | 'delivered' | 'bounced' | 'failed';
  deliveredAt?: Date;
  error?: string;
  attempts: number;
}

export class EmailService {
  private config: EmailConfig;
  private templates: Map<string, EmailTemplate> = new Map();
  private emailQueue: Array<() => Promise<void>> = [];
  private isProcessingQueue = false;
  private emailCounters: {
    minute: number;
    hour: number;
    lastMinuteReset: number;
    lastHourReset: number;
  } = {
    minute: 0,
    hour: 0,
    lastMinuteReset: Date.now(),
    lastHourReset: Date.now()
  };

  constructor(config: EmailConfig) {
    this.config = config;
    this.initializeTemplates();
  }

  /**
   * Initialize email templates
   */
  private initializeTemplates(): void {
    // Alert notification template
    this.templates.set('alert-notification', {
      id: 'alert-notification',
      name: 'Alert Notification',
      subject: '[CBSC] {{severity}}: {{title}}',
      html: this.getAlertNotificationTemplate(),
      text: this.getAlertNotificationTextTemplate(),
      variables: ['severity', 'title', 'message', 'source', 'timestamp', 'actions']
    });

    // Daily summary template
    this.templates.set('daily-summary', {
      id: 'daily-summary',
      name: 'Daily Performance Summary',
      subject: '[CBSC] Daily Strategy Performance Summary',
      html: this.getDailySummaryTemplate(),
      text: this.getDailySummaryTextTemplate(),
      variables: ['date', 'totalReturn', 'activeStrategies', 'topPerformers', 'alerts']
    });

    // Strategy completed template
    this.templates.set('strategy-completed', {
      id: 'strategy-completed',
      name: 'Strategy Execution Completed',
      subject: '[CBSC] Strategy "{{strategyName}}" Execution Completed',
      html: this.getStrategyCompletedTemplate(),
      text: this.getStrategyCompletedTextTemplate(),
      variables: ['strategyName', 'executionTime', 'result', 'metrics', 'nextSteps']
    });
  }

  /**
   * Send alert notification email
   */
  async sendAlertNotification(
    alert: Alert,
    recipients: string[],
    options?: {
      cc?: string[];
      bcc?: string[];
      attachments?: EmailAttachment[];
    }
  ): Promise<EmailDeliveryStatus[]> {
    const template = this.templates.get('alert-notification');
    if (!template) {
      throw new Error('Alert notification template not found');
    }

    const payload: EmailNotificationPayload = {
      to: recipients,
      cc: options?.cc,
      bcc: options?.bcc,
      subject: this.processTemplate(template.subject, {
        severity: alert.severity.toUpperCase(),
        title: alert.title
      }),
      template: template.id,
      data: {
        severity: alert.severity,
        title: alert.title,
        message: alert.message,
        source: alert.source,
        timestamp: alert.createdAt.toLocaleString(),
        actions: [
          {
            text: 'View Alert',
            url: `${this.config.templates.baseUrl}/alerts/${alert.id}`
          },
          {
            text: 'Acknowledge',
            url: `${this.config.templates.baseUrl}/alerts/${alert.id}/acknowledge`
          }
        ]
      },
      attachments: options?.attachments
    };

    return this.sendEmail(payload);
  }

  /**
   * Send daily performance summary
   */
  async sendDailySummary(
    recipients: string[],
    data: {
      date: string;
      totalReturn: number;
      activeStrategies: number;
      topPerformers: Array<{ name: string; return: number }>;
      alerts: Array<{ severity: string; count: number }>;
    }
  ): Promise<EmailDeliveryStatus[]> {
    const template = this.templates.get('daily-summary');
    if (!template) {
      throw new Error('Daily summary template not found');
    }

    const payload: EmailNotificationPayload = {
      to: recipients,
      subject: this.processTemplate(template.subject, {}),
      template: template.id,
      data
    };

    return this.sendEmail(payload);
  }

  /**
   * Send strategy execution completed notification
   */
  async sendStrategyCompletedNotification(
    recipients: string[],
    data: {
      strategyName: string;
      executionTime: string;
      result: string;
      metrics: Record<string, any>;
      nextSteps: string[];
    }
  ): Promise<EmailDeliveryStatus[]> {
    const template = this.templates.get('strategy-completed');
    if (!template) {
      throw new Error('Strategy completed template not found');
    }

    const payload: EmailNotificationPayload = {
      to: recipients,
      subject: this.processTemplate(template.subject, data),
      template: template.id,
      data
    };

    return this.sendEmail(payload);
  }

  /**
   * Send custom email
   */
  async sendCustomEmail(
    payload: EmailNotificationPayload
  ): Promise<EmailDeliveryStatus[]> {
    return this.sendEmail(payload);
  }

  /**
   * Send email with throttling
   */
  private async sendEmail(
    payload: EmailNotificationPayload
  ): Promise<EmailDeliveryStatus[]> {
    // Check throttling
    if (this.config.throttling.enabled && !this.checkThrottling(payload.to.length)) {
      throw new Error('Email rate limit exceeded');
    }

    const statuses: EmailDeliveryStatus[] = [];

    for (const recipient of payload.to) {
      const status = await this.sendSingleEmail(recipient, payload);
      statuses.push(status);
    }

    return statuses;
  }

  /**
   * Send email to a single recipient
   */
  private async sendSingleEmail(
    recipient: string,
    payload: EmailNotificationPayload
  ): Promise<EmailDeliveryStatus> {
    const messageId = this.generateMessageId();

    try {
      // Get or generate email content
      let html: string;
      let text: string;

      if (payload.template) {
        const template = this.templates.get(payload.template);
        if (!template) {
          throw new Error(`Template ${payload.template} not found`);
        }
        html = this.processTemplate(template.html, payload.data);
        text = this.processTemplate(template.text, payload.data);
      } else {
        // Direct content
        html = payload.html || '';
        text = payload.text || '';
      }

      // Prepare email options
      const mailOptions = {
        from: `"${this.config.from.name}" <${this.config.from.email}>`,
        to: recipient,
        cc: payload.cc,
        bcc: payload.bcc,
        subject: payload.subject,
        html,
        text,
        attachments: payload.attachments?.map(attachment => ({
          filename: attachment.filename,
          content: attachment.content,
          contentType: attachment.contentType
        })),
        headers: {
          'X-Mailer': 'CBSC Alert System',
          'X-Priority': this.getPriorityHeader(payload.data),
          'Message-ID': messageId
        }
      };

      // Send email (in production, use your email service API)
      await this.transportEmail(mailOptions);

      return {
        messageId,
        status: 'sent',
        attempts: 1
      };

    } catch (error) {
      console.error(`Failed to send email to ${recipient}:`, error);

      return {
        messageId,
        status: 'failed',
        error: error instanceof Error ? error.message : String(error),
        attempts: 1
      };
    }
  }

  /**
   * Transport email (implementation depends on your email service)
   * This is a mock implementation
   */
  private async transportEmail(mailOptions: any): Promise<void> {
    // In production, integrate with your email service:
    // - SendGrid
    // - AWS SES
    // - Nodemailer
    // - Mailgun
    // - etc.

    console.log('Sending email:', mailOptions);

    // Simulate email sending delay
    await new Promise(resolve => setTimeout(resolve, 100));

    // For development, just log the email
    if (process.env.NODE_ENV === 'development') {
      console.log('=== EMAIL SENT ===');
      console.log('To:', mailOptions.to);
      console.log('Subject:', mailOptions.subject);
      console.log('Body:', mailOptions.text);
      console.log('=================');
    }
  }

  /**
   * Process template with variables
   */
  private processTemplate(template: string, data: Record<string, any>): string {
    let processed = template;

    // Simple template processing ({{variable}})
    for (const [key, value] of Object.entries(data)) {
      const regex = new RegExp(`{{${key}}}`, 'g');
      processed = processed.replace(regex, String(value));
    }

    return processed;
  }

  /**
   * Get priority header based on alert severity
   */
  private getPriorityHeader(data: any): string {
    if (!data.severity) {
      return '3'; // Normal
    }

    switch (data.severity) {
      case AlertSeverity.CRITICAL:
        return '1'; // High
      case AlertSeverity.WARNING:
        return '2'; // Medium
      default:
        return '3'; // Normal
    }
  }

  /**
   * Check throttling limits
   */
  private checkThrottling(emailCount: number): boolean {
    const now = Date.now();

    // Reset minute counter
    if (now - this.emailCounters.lastMinuteReset > 60000) {
      this.emailCounters.minute = 0;
      this.emailCounters.lastMinuteReset = now;
    }

    // Reset hour counter
    if (now - this.emailCounters.lastHourReset > 3600000) {
      this.emailCounters.hour = 0;
      this.emailCounters.lastHourReset = now;
    }

    // Check limits
    if (this.emailCounters.minute + emailCount > this.config.throttling.maxEmailsPerMinute) {
      return false;
    }

    if (this.emailCounters.hour + emailCount > this.config.throttling.maxEmailsPerHour) {
      return false;
    }

    // Update counters
    this.emailCounters.minute += emailCount;
    this.emailCounters.hour += emailCount;

    return true;
  }

  /**
   * Generate unique message ID
   */
  private generateMessageId(): string {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substr(2, 9);
    return `<${timestamp}.${random}@cbsc.com>`;
  }

  /**
   * Email Templates
   */

  private getAlertNotificationTemplate(): string {
    const primaryColor = this.config.templates.primaryColor || '#3b82f6';
    const logoUrl = this.config.templates.logoUrl || '/static/logo.png';

    return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CBSC Alert</title>
  <style>
    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background-color: ${primaryColor}; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }
    .content { background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }
    .severity { display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: bold; margin-bottom: 15px; }
    .severity.info { background-color: #3b82f6; color: white; }
    .severity.warning { background-color: #f59e0b; color: white; }
    .severity.critical { background-color: #ef4444; color: white; }
    .alert-details { margin: 20px 0; padding: 15px; background-color: white; border-radius: 6px; border-left: 4px solid ${primaryColor}; }
    .actions { margin-top: 30px; text-align: center; }
    .btn { display: inline-block; padding: 12px 24px; background-color: ${primaryColor}; color: white; text-decoration: none; border-radius: 6px; margin: 0 10px; }
    .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; text-align: center; font-size: 12px; color: #6c757d; }
    .logo { max-height: 40px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <img src="${logoUrl}" alt="CBSC" class="logo">
      <h1>Strategy Alert</h1>
    </div>

    <div class="content">
      <span class="severity {{severity}}">{{severity}}</span>

      <h2>{{title}}</h2>

      <div class="alert-details">
        <p><strong>Source:</strong> {{source.type}} - {{source.name}}</p>
        <p><strong>Time:</strong> {{timestamp}}</p>
        <hr style="margin: 15px 0;">
        <p>{{message}}</p>
      </div>

      <div class="actions">
        {{#each actions}}
        <a href="{{this.url}}" class="btn">{{this.text}}</a>
        {{/each}}
      </div>
    </div>

    <div class="footer">
      <p>${this.config.templates.footer || '© 2024 CBSC Quantitative Trading. All rights reserved.'}</p>
      <p>This is an automated message. Please do not reply to this email.</p>
    </div>
  </div>
</body>
</html>
    `;
  }

  private getAlertNotificationTextTemplate(): string {
    return `
CBSC Strategy Alert

Severity: {{severity}}
Title: {{title}}
Source: {{source.type}} - {{source.name}}
Time: {{timestamp}}

{{message}}

{{#each actions}}
{{this.text}}: {{this.url}}
{{/each}}

---
${this.config.templates.footer || '© 2024 CBSC Quantitative Trading'}
This is an automated message. Please do not reply to this email.
    `;
  }

  private getDailySummaryTemplate(): string {
    return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>CBSC Daily Summary</title>
  <style>
    /* Styles for daily summary */
  </style>
</head>
<body>
  <h1>Daily Performance Summary - {{date}}</h1>

  <h2>Total Return: {{totalReturn}}%</h2>
  <p>Active Strategies: {{activeStrategies}}</p>

  <h3>Top Performers</h3>
  {{#each topPerformers}}
  <p>{{name}}: {{return}}%</p>
  {{/each}}

  <h3>Alert Summary</h3>
  {{#each alerts}}
  <p>{{severity}}: {{count}} alerts</p>
  {{/each}}
</body>
</html>
    `;
  }

  private getDailySummaryTextTemplate(): string {
    return `
CBSC Daily Performance Summary - {{date}}

Total Return: {{totalReturn}}%
Active Strategies: {{activeStrategies}}

Top Performers:
{{#each topPerformers}}
- {{name}}: {{return}}%
{{/each}}

Alert Summary:
{{#each alerts}}
- {{severity}}: {{count}} alerts
{{/each}}
    `;
  }

  private getStrategyCompletedTemplate(): string {
    return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Strategy Execution Completed</title>
</head>
<body>
  <h1>Strategy Execution Completed</h1>

  <h2>{{strategyName}}</h2>
  <p>Execution Time: {{executionTime}}</p>
  <p>Result: {{result}}</p>

  <h3>Metrics</h3>
  {{#each metrics}}
  <p>{{@key}}: {{this}}</p>
  {{/each}}

  <h3>Next Steps</h3>
  <ul>
    {{#each nextSteps}}
    <li>{{this}}</li>
    {{/each}}
  </ul>
</body>
</html>
    `;
  }

  private getStrategyCompletedTextTemplate(): string {
    return `
Strategy Execution Completed

Strategy: {{strategyName}}
Execution Time: {{executionTime}}
Result: {{result}}

Metrics:
{{#each metrics}}
- {{@key}}: {{this}}
{{/each}}

Next Steps:
{{#each nextSteps}}
- {{this}}
{{/each}}
    `;
  }

  /**
   * Public methods for template management
   */

  /**
   * Add custom email template
   */
  addTemplate(template: EmailTemplate): void {
    this.templates.set(template.id, template);
  }

  /**
   * Get email template
   */
  getTemplate(templateId: string): EmailTemplate | undefined {
    return this.templates.get(templateId);
  }

  /**
   * List all templates
   */
  listTemplates(): EmailTemplate[] {
    return Array.from(this.templates.values());
  }

  /**
   * Get email statistics
   */
  getEmailStats(): {
    minute: number;
    hour: number;
    limitPerMinute: number;
    limitPerHour: number;
  } {
    return {
      minute: this.emailCounters.minute,
      hour: this.emailCounters.hour,
      limitPerMinute: this.config.throttling.maxEmailsPerMinute,
      limitPerHour: this.config.throttling.maxEmailsPerHour
    };
  }

  /**
   * Test email configuration
   */
  async testEmail(recipient: string): Promise<boolean> {
    try {
      const testPayload: EmailNotificationPayload = {
        to: [recipient],
        subject: 'CBSC Email Test',
        template: 'alert-notification',
        data: {
          severity: 'info',
          title: 'Email Configuration Test',
          message: 'This is a test email to verify your email configuration is working correctly.',
          source: {
            type: 'system',
            name: 'Email Service',
            id: 'test'
          },
          timestamp: new Date().toLocaleString(),
          actions: []
        }
      };

      const result = await this.sendEmail(testPayload);
      return result[0].status === 'sent';
    } catch (error) {
      console.error('Email test failed:', error);
      return false;
    }
  }
}