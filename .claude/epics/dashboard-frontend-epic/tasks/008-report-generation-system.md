---
name: task-008-report-generation-system
status: open
created: 2025-12-13T09:33:34Z
updated: 2025-12-13T09:33:34Z
assignee: frontend-team
phase: 3
estimated_hours: 80
priority: medium
---

# Task #8: 報告生成系統

## 📋 任務描述
開發 CBSC Dashboard 的報告生成系統，包括報告模板系統、數據導出功能、PDF 生成集成和郵件推送服務，為用戶提供靈活、專業的報告生成和分享功能。

## 🎯 具體要求

### 8.1 報告模板系統
- [ ] 預定義報告模板（策略績效、風險分析、交易總結）
- [ ] 自定義模板創建器
- [ ] 模板版本管理
- [ ] 動態內容區域
- [ ] 圖表和表格組件
- [ ] 品牌風格配置

### 8.2 數據導出功能
- [ ] CSV 格式導出
- [ ] Excel 格式導出（多工作表）
- [ ] JSON 格式導出
- [ ] 增量數據導出
- [ ] 自定義字段選擇
- [ ] 數據預處理

### 8.3 PDF 生成集成
- [ ] 高質量 PDF 生成
- [ ] 報告分頁控制
- [ ] 頁眉頁尾配置
- [ ] 圖表導出優化
- [ ] 密碼保護
- [ ] 數字簽名支持

### 8.4 郵件推送服務
- [ ] 郵件模板設計
- [ ] 定時發送任務
- [ ] 收件人管理
- [ ] 附件管理
- [ ] 發送狀態追蹤
- [ ] 退訂機制

## ✅ 驗收標準

1. **功能驗收**
   - [ ] 所有模板可以正常生成報告
   - [ ] 各格式導出功能正常
   - [ ] PDF 格式質量符合要求
   - [ ] 郵件可以成功發送

2. **性能標準**
   - [ ] 報告生成時間 < 10 秒
   - [ ] PDF 生成時間 < 15 秒
   - [ ] 大量數據導出 < 30 秒
   - [ ] 支持併發生成

3. **質量標準**
   - [ ] PDF 分辨率 > 300dpi
   - [ ] 圖表清晰度保持
   - [ ] 郵件到達率 > 98%
   - [ ] 無數據遺失

## 🔧 技術要求

### 報告模板系統
```typescript
// types/reports.ts
export interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  type: ReportType;
  sections: ReportSection[];
  styles: ReportStyles;
  metadata: {
    version: string;
    author: string;
    createdAt: Date;
    updatedAt: Date;
  };
}

export interface ReportSection {
  id: string;
  type: 'header' | 'text' | 'chart' | 'table' | 'image' | 'spacer';
  content: SectionContent;
  layout: SectionLayout;
  conditions?: SectionCondition[];
}

export interface ReportData {
  period: {
    start: Date;
    end: Date;
  };
  strategies: Strategy[];
  performance: PerformanceMetrics;
  risk: RiskMetrics;
  trades: Trade[];
  charts: ChartData[];
  customFields?: Record<string, any>;
}

// services/report/ReportService.ts
export class ReportService {
  private templates: Map<string, ReportTemplate> = new Map();
  private pdfGenerator: PDFGenerator;
  private emailService: EmailService;

  constructor() {
    this.pdfGenerator = new PDFGenerator();
    this.emailService = new EmailService();
    this.loadDefaultTemplates();
  }

  // 生成報告
  async generateReport(
    templateId: string,
    data: ReportData,
    format: 'pdf' | 'html' | 'json' = 'pdf'
  ): Promise<ReportResult> {
    const template = this.getTemplate(templateId);
    if (!template) {
      throw new Error(`Template ${templateId} not found`);
    }

    const reportData = await this.processData(template, data);

    switch (format) {
      case 'pdf':
        return this.generatePDF(template, reportData);
      case 'html':
        return this.generateHTML(template, reportData);
      case 'json':
        return this.generateJSON(template, reportData);
      default:
        throw new Error(`Unsupported format: ${format}`);
    }
  }

  // 生成 PDF
  private async generatePDF(
    template: ReportTemplate,
    data: ProcessedReportData
  ): Promise<ReportResult> {
    const document = await this.pdfGenerator.createDocument({
      format: 'A4',
      margin: {
        top: '20mm',
        right: '20mm',
        bottom: '20mm',
        left: '20mm'
      },
      header: this.createHeader(template),
      footer: this.createFooter(template),
      watermark: template.styles.watermark
    });

    // 渲染各個部分
    for (const section of template.sections) {
      if (this.shouldRenderSection(section, data)) {
        await this.renderSection(document, section, data);
      }
    }

    const pdfBuffer = await document.generate();

    return {
      format: 'pdf',
      data: pdfBuffer,
      filename: this.generateFilename(template, data),
      size: pdfBuffer.length,
      createdAt: new Date()
    };
  }

  // 渲染部分
  private async renderSection(
    document: PDFDocument,
    section: ReportSection,
    data: ProcessedReportData
  ): Promise<void> {
    switch (section.type) {
      case 'header':
        await this.renderHeader(document, section, data);
        break;
      case 'text':
        await this.renderText(document, section, data);
        break;
      case 'chart':
        await this.renderChart(document, section, data);
        break;
      case 'table':
        await this.renderTable(document, section, data);
        break;
      case 'image':
        await this.renderImage(document, section, data);
        break;
      case 'spacer':
        document.addSpacing(section.layout.height || 20);
        break;
    }
  }

  // 渲染圖表
  private async renderChart(
    document: PDFDocument,
    section: ReportSection,
    data: ProcessedReportData
  ): Promise<void> {
    const chartConfig = section.content as ChartSectionContent;
    const chartData = data.charts[chartConfig.chartId];

    if (!chartData) {
      console.warn(`Chart data not found: ${chartConfig.chartId}`);
      return;
    }

    // 生成圖表圖片
    const chartImage = await this.generateChartImage({
      type: chartData.type,
      data: chartData.data,
      options: {
        ...chartConfig.options,
        width: section.layout.width || 600,
        height: section.layout.height || 400,
        backgroundColor: '#ffffff'
      }
    });

    // 添加到文檔
    document.addImage({
      image: chartImage,
      width: section.layout.width || 600,
      height: section.layout.height || 400,
      alignment: section.layout.alignment || 'center'
    });

    // 添加標題和說明
    if (chartConfig.title) {
      document.addText(chartConfig.title, {
        fontSize: 16,
        fontWeight: 'bold',
        alignment: 'center',
        marginTop: 10
      });
    }

    if (chartConfig.description) {
      document.addText(chartConfig.description, {
        fontSize: 12,
        alignment: 'center',
        marginTop: 5,
        color: '#666666'
      });
    }
  }

  // 創建自定義模板
  async createTemplate(templateData: CreateTemplateRequest): Promise<ReportTemplate> {
    const template: ReportTemplate = {
      id: generateId(),
      name: templateData.name,
      description: templateData.description,
      type: templateData.type,
      sections: templateData.sections,
      styles: {
        ...DEFAULT_STYLES,
        ...templateData.styles
      },
      metadata: {
        version: '1.0.0',
        author: templateData.author,
        createdAt: new Date(),
        updatedAt: new Date()
      }
    };

    // 驗證模板
    this.validateTemplate(template);

    // 保存模板
    this.templates.set(template.id, template);

    return template;
  }

  // 導出數據
  async exportData(
    data: ReportData,
    format: 'csv' | 'excel' | 'json',
    options: ExportOptions = {}
  ): Promise<ExportResult> {
    switch (format) {
      case 'csv':
        return this.exportToCSV(data, options);
      case 'excel':
        return this.exportToExcel(data, options);
      case 'json':
        return this.exportToJSON(data, options);
      default:
        throw new Error(`Unsupported export format: ${format}`);
    }
  }

  // 導出到 Excel
  private async exportToExcel(
    data: ReportData,
    options: ExportOptions
  ): Promise<ExportResult> {
    const workbook = new ExcelJS.Workbook();

    // 創建概要工作表
    const summarySheet = workbook.addWorksheet('概要');
    summarySheet.addRow(['報告期間', formatDate(data.period.start), '至', formatDate(data.period.end)]);
    summarySheet.addRow(['策略數量', data.strategies.length]);
    summarySheet.addRow(['總交易次數', data.trades.length]);
    summarySheet.addRow(['總收益率', formatPercent(data.performance.totalReturn)]);

    // 創建策略詳情工作表
    if (options.includeStrategies) {
      const strategiesSheet = workbook.addWorksheet('策略詳情');
      strategiesSheet.columns = [
        { header: '策略名稱', key: 'name', width: 20 },
        { header: '類型', key: 'type', width: 15 },
        { header: '狀態', key: 'status', width: 10 },
        { header: '總收益', key: 'totalReturn', width: 15 },
        { header: '夏普比率', key: 'sharpeRatio', width: 15 },
        { header: '最大回撤', key: 'maxDrawdown', width: 15 },
        { header: '勝率', key: 'winRate', width: 10 }
      ];

      data.strategies.forEach(strategy => {
        strategiesSheet.addRow({
          name: strategy.name,
          type: strategy.type,
          status: strategy.status,
          totalReturn: formatPercent(strategy.performance.totalReturn),
          sharpeRatio: strategy.performance.sharpeRatio?.toFixed(2) || 'N/A',
          maxDrawdown: formatPercent(strategy.performance.maxDrawdown),
          winRate: formatPercent(strategy.performance.winRate)
        });
      });
    }

    // 創建交易記錄工作表
    if (options.includeTrades) {
      const tradesSheet = workbook.addWorksheet('交易記錄');
      tradesSheet.columns = [
        { header: '時間', key: 'timestamp', width: 20 },
        { header: '策略', key: 'strategy', width: 20 },
        { header: '標的', key: 'symbol', width: 15 },
        { header: '類型', key: 'type', width: 10 },
        { header: '價格', key: 'price', width: 15 },
        { header: '數量', key: 'quantity', width: 15 },
        { header: '手續費', key: 'fee', width: 15 },
        { header: '盈虧', key: 'pnl', width: 15 }
      ];

      data.trades.forEach(trade => {
        tradesSheet.addRow({
          timestamp: formatDateTime(trade.timestamp),
          strategy: trade.strategyName,
          symbol: trade.symbol,
          type: trade.type,
          price: trade.price.toFixed(4),
          quantity: trade.quantity,
          fee: trade.fee.toFixed(2),
          pnl: trade.pnl?.toFixed(2) || 'N/A'
        });
      });
    }

    // 設置樣式
    this.applyExcelStyles(workbook);

    // 生成緩衝區
    const buffer = await workbook.xlsx.writeBuffer();

    return {
      format: 'excel',
      data: buffer,
      filename: `strategy_report_${formatDate(new Date())}.xlsx`,
      size: buffer.length,
      createdAt: new Date()
    };
  }
}

// React 組件
export const ReportGenerator: React.FC<ReportGeneratorProps> = ({
  strategyIds,
  period,
  onGenerate
}) => {
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [format, setFormat] = useState<'pdf' | 'html'>('pdf');
  const [isGenerating, setIsGenerating] = useState(false);

  const reportService = useMemo(() => new ReportService(), []);

  useEffect(() => {
    const loadTemplates = async () => {
      const templates = await reportService.getTemplates();
      setTemplates(templates);
      if (templates.length > 0) {
        setSelectedTemplate(templates[0].id);
      }
    };

    loadTemplates();
  }, [reportService]);

  const handleGenerate = async () => {
    if (!selectedTemplate || !period) return;

    setIsGenerating(true);
    try {
      // 獲取報告數據
      const data = await fetchReportData(strategyIds, period);

      // 生成報告
      const result = await reportService.generateReport(
        selectedTemplate,
        data,
        format
      );

      // 下載文件
      downloadFile(result.data, result.filename);

      onGenerate?.(result);
    } catch (error) {
      console.error('Failed to generate report:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>生成報告</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 模板選擇 */}
          <div>
            <label className="block text-sm font-medium mb-2">選擇模板</label>
            <Select
              value={selectedTemplate}
              onValueChange={setSelectedTemplate}
            >
              {templates.map(template => (
                <SelectItem key={template.id} value={template.id}>
                  {template.name}
                </SelectItem>
              ))}
            </Select>
          </div>

          {/* 格式選擇 */}
          <div>
            <label className="block text-sm font-medium mb-2">輸出格式</label>
            <RadioGroup
              value={format}
              onValueChange={(value: 'pdf' | 'html') => setFormat(value)}
            >
              <RadioGroupItem value="pdf" id="pdf">
                <Label htmlFor="pdf">PDF</Label>
              </RadioGroupItem>
              <RadioGroupItem value="html" id="html">
                <Label htmlFor="html">HTML</Label>
              </RadioGroupItem>
            </RadioGroup>
          </div>

          {/* 生成按鈕 */}
          <Button
            onClick={handleGenerate}
            disabled={!selectedTemplate || isGenerating}
            className="w-full"
          >
            {isGenerating ? (
              <>
                <LoadingSpinner className="mr-2 h-4 w-4" />
                生成中...
              </>
            ) : (
              <>
                <DocumentArrowDownIcon className="mr-2 h-4 w-4" />
                生成報告
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* 快速導出 */}
      <Card>
        <CardHeader>
          <CardTitle>快速導出數據</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <Button
              variant="outline"
              onClick={() => handleExport('csv')}
            >
              <DocumentArrowDownIcon className="mr-2 h-4 w-4" />
              CSV
            </Button>
            <Button
              variant="outline"
              onClick={() => handleExport('excel')}
            >
              <DocumentArrowDownIcon className="mr-2 h-4 w-4" />
              Excel
            </Button>
            <Button
              variant="outline"
              onClick={() => handleExport('json')}
            >
              <DocumentArrowDownIcon className="mr-2 h-4 w-4" />
              JSON
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
```

## 📊 預估工作量
| 子任務 | 預估時間 | 負責人 |
|--------|----------|--------|
| 報告模板系統 | 32小時 | 前端工程師 A |
| 數據導出功能 | 16小時 | 前端工程師 B |
| PDF 生成集成 | 24小時 | 前端工程師 A |
| 郵件推送服務 | 8小時 | 後端工程師 + 前端工程師 B |
| **總計** | **80小時** | |

## 🔗 依賴關係
- 前置任務：Task #5 (實時數據可視化), Task #6 (策略管理界面)
- 後續任務：Task #9 (移動端適配)

## 📝 注意事項
1. 實現報告生成任務隊列
2. 考慮大數據量的分批處理
3. 實現報告緩存機制
4. 處理特殊字符和多語言支持
5. 確保敏感數據的脫敏處理

## 🧪 測試要求
```typescript
// services/report/__tests__/ReportService.test.ts
describe('ReportService', () => {
  let reportService: ReportService;
  let mockData: ReportData;

  beforeEach(() => {
    reportService = new ReportService();
    mockData = createMockReportData();
  });

  test('generates PDF report successfully', async () => {
    const template = await reportService.createTemplate({
      name: 'Test Template',
      type: 'performance',
      sections: [
        {
          type: 'header',
          content: { title: 'Test Report' },
          layout: { height: 100 }
        },
        {
          type: 'chart',
          content: { chartId: 'performance-chart' },
          layout: { width: 600, height: 400 }
        }
      ],
      styles: DEFAULT_STYLES,
      author: 'test'
    });

    const result = await reportService.generateReport(
      template.id,
      mockData,
      'pdf'
    );

    expect(result.format).toBe('pdf');
    expect(result.filename).toMatch(/\.pdf$/);
    expect(result.size).toBeGreaterThan(0);
  });

  test('exports data to Excel correctly', async () => {
    const result = await reportService.exportData(mockData, 'excel', {
      includeStrategies: true,
      includeTrades: true
    });

    expect(result.format).toBe('excel');
    expect(result.filename).toMatch(/\.xlsx$/);

    // 驗證 Excel 內容
    const workbook = new ExcelJS.Workbook();
    await workbook.xlsx.load(result.data);

    expect(workbook.worksheets).toHaveLength(3); // 概要、策略、交易
    expect(workbook.getWorksheet('策略詳情')?.rowCount).toBeGreaterThan(1);
  });

  test('handles large data sets', async () => {
    const largeData = createLargeReportData(10000); // 10k trades

    const startTime = Date.now();
    const result = await reportService.exportData(largeData, 'csv');
    const duration = Date.now() - startTime;

    expect(duration).toBeLessThan(30000); // 30 seconds max
    expect(result.size).toBeGreaterThan(0);
  });
});
```

## 📚 相關文檔
- [jsPDF 文檔](https://github.com/parallax/jsPDF)
- [PDFKit 文檔](http://pdfkit.org/)
- [ExcelJS 文檔](https://github.com/exceljs/exceljs)
- [Nodemailer 文檔](https://nodemailer.com/)
- [Handlebars 模板引擎](https://handlebarsjs.com/)