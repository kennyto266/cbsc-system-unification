import { type Page, Locator, expect } from '@playwright/test';

export interface StrategyFormData {
  name: string;
  type: string;
  initialCapital: number;
  description?: string;
}

export class StrategyPage {
  readonly page: Page;
  readonly pageHeader: Locator;
  readonly strategyList: Locator;
  readonly createStrategyButton: Locator;
  readonly successMessage: Locator;
  readonly validationErrors: Locator;
  readonly loadingIndicator: Locator;

  // Form elements
  readonly strategyNameInput: Locator;
  readonly strategyTypeSelect: Locator;
  readonly initialCapitalInput: Locator;
  readonly descriptionTextarea: Locator;
  readonly saveButton: Locator;
  readonly cancelButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.pageHeader = page.locator('[data-testid=strategy-page-header]');
    this.strategyList = page.locator('[data-testid=strategy-list]');
    this.createStrategyButton = page.locator('[data-testid=create-strategy-btn]');
    this.successMessage = page.locator('[data-testid=success-message]');
    this.validationErrors = page.locator('[data-testid=validation-errors]');
    this.loadingIndicator = page.locator('[data-testid=loading]');

    // Form
    this.strategyNameInput = page.locator('[data-testid=strategy-name-input]');
    this.strategyTypeSelect = page.locator('[data-testid=strategy-type-select]');
    this.initialCapitalInput = page.locator('[data-testid=initial-capital-input]');
    this.descriptionTextarea = page.locator('[data-testid=description-textarea]');
    this.saveButton = page.locator('[data-testid=save-strategy-btn]');
    this.cancelButton = page.locator('[data-testid=cancel-strategy-btn]');
  }

  async clickCreateStrategy() {
    await this.createStrategyButton.click();
    await this.strategyNameInput.waitFor({ state: 'visible' });
  }

  async fillStrategyForm(data: StrategyFormData) {
    await this.strategyNameInput.fill(data.name);
    await this.strategyTypeSelect.selectOption(data.type);
    await this.initialCapitalInput.fill(data.initialCapital.toString());

    if (data.description) {
      await this.descriptionTextarea.fill(data.description);
    }
  }

  async saveStrategy() {
    await this.saveButton.click();
  }

  async cancelStrategy() {
    await this.cancelButton.click();
  }

  async editStrategy(strategyId: string) {
    await this.strategyList.locator(`[data-testid=strategy-${strategyId}] [data-testid=edit-btn]`).click();
  }

  async deleteStrategy(strategyId: string) {
    await this.strategyList.locator(`[data-testid=strategy-${strategyId}] [data-testid=delete-btn]`).click();
    // Confirm deletion
    await this.page.locator('[data-testid=confirm-delete]').click();
  }

  async toggleStrategy(strategyId: string) {
    await this.strategyList.locator(`[data-testid=strategy-${strategyId}] [data-testid=toggle-btn]`).click();
  }

  async viewStrategyPerformance(strategyId: string) {
    await this.strategyList.locator(`[data-testid=strategy-${strategyId}] [data-testid=performance-btn]`).click();
  }

  async backtestStrategy(strategyId: string) {
    await this.strategyList.locator(`[data-testid=strategy-${strategyId}] [data-testid=backtest-btn]`).click();
  }

  async getStrategyCount(): Promise<number> {
    const items = await this.strategyList.locator('[data-testid=strategy-item]').count();
    return items;
  }

  async searchStrategies(query: string) {
    await this.page.fill('[data-testid=strategy-search]', query);
  }

  async filterByType(type: string) {
    await this.page.selectOption('[data-testid=type-filter]', type);
  }

  async sortByField(field: 'name' | 'created' | 'performance' | 'status') {
    await this.page.click(`[data-testid=sort-by-${field}]`);
  }

  async async waitForStrategiesToLoad() {
    await this.loadingIndicator.waitFor({ state: 'hidden' });
    await this.strategyList.waitFor({ state: 'visible' });
  }

  async assertStrategyCreated(strategyName: string) {
    await expect(this.successMessage).toBeVisible();
    await expect(this.strategyList).toContainText(strategyName);
  }

  async assertValidationError(message: string) {
    await expect(this.validationErrors).toBeVisible();
    await expect(this.validationErrors).toContainText(message);
  }

  async assertStrategyVisible(strategyId: string) {
    await expect(this.strategyList.locator(`[data-testid=strategy-${strategyId}]`)).toBeVisible();
  }

  async assertStrategyHidden(strategyId: string) {
    await expect(this.strategyList.locator(`[data-testid=strategy-${strategyId}]`)).not.toBeVisible();
  }

  async getStrategyStatus(strategyId: string): Promise<string> {
    const statusElement = this.strategyList.locator(`[data-testid=strategy-${strategyId}] [data-testid=status]`);
    return await statusElement.textContent() || '';
  }

  async getStrategyPerformance(strategyId: string): Promise<number> {
    const perfElement = this.strategyList.locator(`[data-testid=strategy-${strategyId}] [data-testid=performance]`);
    const text = await perfElement.textContent() || '0%';
    return parseFloat(text.replace('%', ''));
  }

  async loadMoreStrategies() {
    await this.page.click('[data-testid=load-more]');
    await this.loadingIndicator.waitFor({ state: 'hidden' });
  }

  async selectMultipleStrategies(strategyIds: string[]) {
    for (const id of strategyIds) {
      await this.strategyList.locator(`[data-testid=strategy-${id}] [data-testid=checkbox]`).click();
    }
  }

  async batchDeleteStrategies(strategyIds: string[]) {
    await this.selectMultipleStrategies(strategyIds);
    await this.page.click('[data-testid=batch-delete]');
    await this.page.locator('[data-testid=confirm-delete]').click();
  }

  async exportStrategies(format: 'csv' | 'excel') {
    await this.page.click(`[data-testid=export-${format}]`);
  }
}