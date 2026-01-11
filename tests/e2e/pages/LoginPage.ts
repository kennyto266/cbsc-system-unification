import { type Page, Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;
  readonly errorMessage: Locator;
  readonly rememberMeCheckbox: Locator;
  readonly forgotPasswordLink: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usernameInput = page.locator('[data-testid=username-input]');
    this.passwordInput = page.locator('[data-testid=password-input]');
    this.loginButton = page.locator('[data-testid=login-button]');
    this.errorMessage = page.locator('[data-testid=error-message]');
    this.rememberMeCheckbox = page.locator('[data-testid=remember-me]');
    this.forgotPasswordLink = page.locator('[data-testid=forgot-password]');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(username: string, password: string) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
  }

  async loginWithRememberMe(username: string, password: string) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.rememberMeCheckbox.check();
    await this.loginButton.click();
  }

  async getErrorMessage() {
    return await this.errorMessage.textContent();
  }

  async clickForgotPassword() {
    await this.forgotPasswordLink.click();
  }

  async assertPageLoaded() {
    await expect(this.usernameInput).toBeVisible();
    await expect(this.passwordInput).toBeVisible();
    await expect(this.loginButton).toBeVisible();
  }

  async assertLoginSuccess() {
    // Wait for redirect to dashboard
    await expect(this.page).toHaveURL(/dashboard/);
  }

  async assertLoginError() {
    await expect(this.errorMessage).toBeVisible();
  }
}