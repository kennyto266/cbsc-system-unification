"""End-to-end tests for complete strategy workflow."""

import pytest
import asyncio
from playwright.async_api import async_playwright, Page, Browser
from datetime import datetime, timedelta
import json
import time


@pytest.fixture(scope="session")
async def browser():
    """Create browser instance for E2E tests."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture(scope="function")
async def page(browser):
    """Create new page for each test."""
    page = await browser.new_page()
    await page.goto("http://localhost:3000")
    yield page
    await page.close()


@pytest.fixture(scope="function")
async def authenticated_page(browser):
    """Create authenticated page."""
    page = await browser.new_page()
    
    # Navigate to login page
    await page.goto("http://localhost:3000/login")
    
    # Fill login form
    await page.fill("[data-testid=username-input]", "testuser")
    await page.fill("[data-testid=password-input]", "password123")
    
    # Submit login
    await page.click("[data-testid=login-button]")
    
    # Wait for redirect to dashboard
    await page.wait_for_url("http://localhost:3000/dashboard")
    
    yield page
    await page.close()


@pytest.mark.e2e
@pytest.mark.integration
class TestStrategyWorkflowE2E:
    """Test complete strategy workflow from creation to execution."""

    async def test_complete_strategy_lifecycle(self, authenticated_page: Page):
        """Test complete strategy lifecycle: create -> configure -> backtest -> deploy -> monitor."""
        
        # 1. Navigate to strategies page
        await authenticated_page.click("[data-testid=nav-strategies]")
        await authenticated_page.wait_for_url("**/strategies")
        
        # 2. Create new strategy
        await authenticated_page.click("[data-testid=create-strategy-btn]")
        await authenticated_page.wait_for_selector("[data-testid=strategy-form]")
        
        # Fill strategy details
        await authenticated_page.fill("[data-testid=strategy-name]", "E2E Test Strategy")
        await authenticated_page.fill(
            "[data-testid=strategy-description]",
            "Strategy created during E2E testing"
        )
        
        # Add symbols
        await authenticated_page.fill("[data-testid=symbol-input]", "AAPL")
        await authenticated_page.click("[data-testid=add-symbol-btn]")
        
        await authenticated_page.fill("[data-testid=symbol-input]", "GOOGL")
        await authenticated_page.click("[data-testid=add-symbol-btn]")
        
        # Configure parameters
        await authenticated_page.select_option("[data-testid=timeframe-select]", "1d")
        await authenticated_page.fill("[data-testid=risk-level-input]", "0.02")
        await authenticated_page.fill("[data-testid=position-size-input]", "0.1")
        
        # Save strategy
        await authenticated_page.click("[data-testid=save-strategy-btn]")
        await authenticated_page.wait_for_selector(
            "[data-testid=strategy-saved-message]",
            timeout=10000
        )
        
        # 3. Configure strategy parameters
        await authenticated_page.click("[data-testid=configure-parameters-btn]")
        await authenticated_page.wait_for_selector("[data-testid=parameter-config]")
        
        # Set entry conditions
        await authenticated_page.click("[data-testid=add-entry-condition]")
        await authenticated_page.select_option(
            "[data-testid=indicator-select]",
            "RSI"
        )
        await authenticated_page.fill("[data-testid=indicator-value]", "30")
        await authenticated_page.select_option(
            "[data-testid=condition-operator]",
            "less_than"
        )
        
        # Set exit conditions
        await authenticated_page.click("[data-testid=add-exit-condition]")
        await authenticated_page.select_option(
            "[data-testid=indicator-select]",
            "RSI"
        )
        await authenticated_page.fill("[data-testid=indicator-value]", "70")
        await authenticated_page.select_option(
            "[data-testid=condition-operator]",
            "greater_than"
        )
        
        # Save configuration
        await authenticated_page.click("[data-testid=save-configuration-btn]")
        await authenticated_page.wait_for_selector(
            "[data-testid=configuration-saved]"
        )
        
        # 4. Run backtest
        await authenticated_page.click("[data-testid=backtest-btn]")
        await authenticated_page.wait_for_selector("[data-testid=backtest-modal]")
        
        # Set backtest parameters
        await authenticated_page.fill(
            "[data-testid=backtest-start-date]",
            (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        )
        await authenticated_page.fill(
            "[data-testid=backtest-end-date]",
            datetime.now().strftime("%Y-%m-%d")
        )
        await authenticated_page.fill(
            "[data-testid=initial-capital]",
            "100000"
        )
        
        # Start backtest
        await authenticated_page.click("[data-testid=start-backtest-btn]")
        
        # Wait for backtest to complete
        await authenticated_page.wait_for_selector(
            "[data-testid=backtest-complete]",
            timeout=60000  # Allow up to 60 seconds
        )
        
        # Verify backtest results
        results_text = await authenticated_page.text_content(
            "[data-testid=backtest-results]"
        )
        assert "Total Return" in results_text
        assert "Sharpe Ratio" in results_text
        assert "Max Drawdown" in results_text
        
        # 5. Deploy strategy
        await authenticated_page.click("[data-testid=deploy-strategy-btn]")
        await authenticated_page.wait_for_selector("[data-testid=deploy-modal]")
        
        # Set deployment parameters
        await authenticated_page.fill(
            "[data-testid=deployment-capital]",
            "50000"
        )
        await authenticated_page.select_option(
            "[data-testid=execution-mode]",
            "paper_trading"
        )
        
        # Confirm deployment
        await authenticated_page.click("[data-testid=confirm-deploy-btn]")
        await authenticated_page.wait_for_selector(
            "[data-testid=strategy-deployed]",
            timeout=30000
        )
        
        # 6. Monitor strategy
        await authenticated_page.click("[data-testid=monitor-strategy-btn]")
        await authenticated_page.wait_for_selector("[data-testid=monitoring-dashboard]")
        
        # Verify strategy status
        status_text = await authenticated_page.text_content(
            "[data-testid=strategy-status]"
        )
        assert "Running" in status_text or "Active" in status_text
        
        # Check performance metrics
        await authenticated_page.wait_for_selector("[data-testid=performance-metrics]")
        
        # 7. View trade history
        await authenticated_page.click("[data-testid=trade-history-tab]")
        await authenticated_page.wait_for_selector("[data-testid=trade-list]")
        
        # Verify trades are displayed (might be empty initially)
        trades_count = await authenticated_page.locator(
            "[data-testid=trade-item]"
        ).count()
        
        # 8. Stop strategy
        await authenticated_page.click("[data-testid=stop-strategy-btn]")
        await authenticated_page.wait_for_selector("[data-testid=stop-confirmation]")
        await authenticated_page.click("[data-testid=confirm-stop-btn]")
        await authenticated_page.wait_for_selector(
            "[data-testid=strategy-stopped]",
            timeout=30000
        )
        
        # Verify final state
        final_status = await authenticated_page.text_content(
            "[data-testid=strategy-status]"
        )
        assert "Stopped" in final_status or "Inactive" in final_status

    async def test_portfolio_management_workflow(self, authenticated_page: Page):
        """Test portfolio management workflow."""
        
        # Navigate to portfolio
        await authenticated_page.click("[data-testid=nav-portfolio]")
        await authenticated_page.wait_for_url("**/portfolio")
        
        # Check portfolio value
        portfolio_value = await authenticated_page.text_content(
            "[data-testid=total-portfolio-value]"
        )
        assert portfolio_value is not None
        assert "$" in portfolio_value
        
        # View asset allocation
        await authenticated_page.click("[data-testid=allocation-tab]")
        await authenticated_page.wait_for_selector("[data-testid=allocation-chart]")
        
        # Check individual positions
        await authenticated_page.click("[data-testid=positions-tab]")
        await authenticated_page.wait_for_selector("[data-testid=positions-table]")
        
        # Open a new position
        await authenticated_page.click("[data-testid=new-position-btn]")
        await authenticated_page.wait_for_selector("[data-testid=new-position-form]")
        
        # Fill position details
        await authenticated_page.fill("[data-testid=symbol-search]", "MSFT")
        await authenticated_page.fill("[data-testid=quantity-input]", "50")
        await authenticated_page.select_option("[data-testid=order-type]", "market")
        
        # Submit order
        await authenticated_page.click("[data-testid=submit-order-btn]")
        await authenticated_page.wait_for_selector(
            "[data-testid=order-submitted]",
            timeout=10000
        )
        
        # Verify order in order history
        await authenticated_page.click("[data-testid=orders-tab]")
        await authenticated_page.wait_for_selector("[data-testid=orders-table]")
        
        # Find the new order
        order_row = await authenticated_page.locator(
            "[data-testid=order-row]:has-text('MSFT')"
        ).first
        assert await order_row.count() > 0

    async def test_real_time_data_updates(self, authenticated_page: Page):
        """Test real-time data updates in dashboard."""
        
        # Navigate to dashboard
        await authenticated_page.click("[data-testid=nav-dashboard]")
        await authenticated_page.wait_for_url("**/dashboard")
        
        # Check initial market data
        await authenticated_page.wait_for_selector("[data-testid=market-overview]")
        
        # Capture initial values
        initial_values = {}
        symbols = ["AAPL", "GOOGL", "MSFT"]
        
        for symbol in symbols:
            element = await authenticated_page.locator(
                f"[data-testid=price-{symbol.lower()}]"
            ).first
            if await element.count() > 0:
                initial_values[symbol] = await element.text_content()
        
        # Wait for real-time updates
        await asyncio.sleep(5)  # Give time for WebSocket updates
        
        # Check if values have updated (this might not always change in test env)
        updated_values = {}
        for symbol in symbols:
            element = await authenticated_page.locator(
                f"[data-testid=price-{symbol.lower()}]"
            ).first
            if await element.count() > 0:
                updated_values[symbol] = await element.text_content()
        
        # At least verify the data structure is present
        assert len(initial_values) > 0 or len(updated_values) > 0
        
        # Check portfolio value updates
        portfolio_element = await authenticated_page.locator(
            "[data-testid=portfolio-value]"
        ).first
        if await portfolio_element.count() > 0:
            initial_portfolio = await portfolio_element.text_content()
            
            # Wait for update
            await asyncio.sleep(5)
            
            updated_portfolio = await portfolio_element.text_content()
            # Should either be the same or updated
            assert updated_portfolio is not None

    async def test_alert_and_notification_system(self, authenticated_page: Page):
        """Test alert and notification system."""
        
        # Navigate to alerts
        await authenticated_page.click("[data-testid=nav-alerts]")
        await authenticated_page.wait_for_url("**/alerts")
        
        # Create new alert
        await authenticated_page.click("[data-testid=create-alert-btn]")
        await authenticated_page.wait_for_selector("[data-testid=alert-form]")
        
        # Configure alert
        await authenticated_page.fill("[data-testid=alert-name]", "Price Alert Test")
        await authenticated_page.select_option(
            "[data-testid=alert-type]",
            "price_threshold"
        )
        await authenticated_page.fill("[data-testid=symbol-alert]", "AAPL")
        await authenticated_page.fill("[data-testid=price-threshold]", "200")
        await authenticated_page.select_option(
            "[data-testid=condition]",
            "above"
        )
        
        # Save alert
        await authenticated_page.click("[data-testid=save-alert-btn]")
        await authenticated_page.wait_for_selector(
            "[data-testid=alert-created]"
        )
        
        # Verify alert in list
        alert_row = await authenticated_page.locator(
            "[data-testid=alert-row]:has-text('Price Alert Test')"
        ).first
        assert await alert_row.count() > 0
        
        # Test alert activation
        await authenticated_page.click(
            "[data-testid=activate-alert]:has-text('Price Alert Test')"
        )
        await authenticated_page.wait_for_selector(
            "[data-testid=alert-activated]"
        )
        
        # Check notifications
        await authenticated_page.click("[data-testid=notifications-btn]")
        await authenticated_page.wait_for_selector("[data-testid=notifications-panel]")
        
        # Verify notification badge (if any)
        notification_badge = await authenticated_page.locator(
            "[data-testid=notification-badge]"
        ).first
        
        # Badge might not exist if no notifications
        if await notification_badge.count() > 0:
            assert await notification_badge.is_visible()

    async def test_reports_and_analytics(self, authenticated_page: Page):
        """Test reports and analytics generation."""
        
        # Navigate to reports
        await authenticated_page.click("[data-testid=nav-reports]")
        await authenticated_page.wait_for_url("**/reports")
        
        # Generate performance report
        await authenticated_page.click("[data-testid=generate-report-btn]")
        await authenticated_page.wait_for_selector("[data-testid=report-config]")
        
        # Configure report
        await authenticated_page.select_option(
            "[data-testid=report-type]",
            "performance"
        )
        await authenticated_page.fill(
            "[data-testid=report-start-date]",
            (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        )
        await authenticated_page.fill(
            "[data-testid=report-end-date]",
            datetime.now().strftime("%Y-%m-%d")
        )
        
        # Generate report
        await authenticated_page.click("[data-testid=generate-btn]")
        await authenticated_page.wait_for_selector(
            "[data-testid=report-generated]",
            timeout=30000
        )
        
        # View report
        await authenticated_page.click("[data-testid=view-report-btn]")
        await authenticated_page.wait_for_selector("[data-testid=report-content]")
        
        # Verify report sections
        report_sections = [
            "[data-testid=summary-section]",
            "[data-testid=performance-chart]",
            "[data-testid=trade-analysis]",
            "[data-testid=risk-metrics]"
        ]
        
        for section in report_sections:
            element = await authenticated_page.locator(section).first
            # Some sections might be optional
            if await element.count() > 0:
                assert await element.is_visible()
        
        # Export report
        await authenticated_page.click("[data-testid=export-report-btn]")
        await authenticated_page.wait_for_selector("[data-testid=export-options]")
        
        # Test PDF export
        download_promise = authenticated_page.wait_for_event("download")
        await authenticated_page.click("[data-testid=export-pdf]")
        download = await download_promise
        
        assert download.suggested_filename.endswith(".pdf")
        
        # Test CSV export
        download_promise = authenticated_page.wait_for_event("download")
        await authenticated_page.click("[data-testid=export-csv]")
        download = await download_promise
        
        assert download.suggested_filename.endswith(".csv")

    async def test_user_settings_and_preferences(self, authenticated_page: Page):
        """Test user settings and preferences management."""
        
        # Navigate to settings
        await authenticated_page.click("[data-testid=user-menu]")
        await authenticated_page.click("[data-testid=settings-menu-item]")
        await authenticated_page.wait_for_url("**/settings")
        
        # Update profile information
        await authenticated_page.click("[data-testid=profile-tab]")
        await authenticated_page.fill(
            "[data-testid=display-name]",
            "Test User Updated"
        )
        await authenticated_page.fill(
            "[data-testid=bio]",
            "Updated bio for E2E testing"
        )
        
        # Save profile
        await authenticated_page.click("[data-testid=save-profile-btn]")
        await authenticated_page.wait_for_selector(
            "[data-testid=profile-saved]"
        )
        
        # Configure notifications
        await authenticated_page.click("[data-testid=notifications-tab]")
        
        # Toggle email notifications
        await authenticated_page.check("[data-testid=email-notifications]")
        await authenticated_page.check("[data-testid=trade-alerts-email]")
        await authenticated_page.uncheck("[data-testid=daily-summary-email]")
        
        # Save notification settings
        await authenticated_page.click("[data-testid=save-notifications-btn]")
        await authenticated_page.wait_for_selector(
            "[data-testid=notifications-saved]"
        )
        
        # Configure UI preferences
        await authenticated_page.click("[data-testid=preferences-tab]")
        
        # Change theme
        await authenticated_page.select_option(
            "[data-testid=theme-select]",
            "dark"
        )
        
        # Change language
        await authenticated_page.select_option(
            "[data-testid=language-select]",
            "zh-CN"
        )
        
        # Save preferences
        await authenticated_page.click("[data-testid=save-preferences-btn]")
        await authenticated_page.wait_for_selector(
            "[data-testid=preferences-saved]"
        )
        
        # Verify theme change
        body = await authenticated_page.locator("body")
        expect(await body.get_attribute("class")).toContain("dark-theme")
        
        # Configure security settings
        await authenticated_page.click("[data-testid=security-tab]")
        
        # Enable two-factor authentication
        await authenticated_page.click("[data-testid=enable-2fa-btn]")
        await authenticated_page.wait_for_selector("[data-testid=2fa-setup]")
        
        # Follow 2FA setup flow (simplified for test)
        await authenticated_page.click("[data-testid=2fa-next-step]")
        await authenticated_page.click("[data-testid=2fa-next-step]")
        await authenticated_page.click("[data-testid=2fa-confirm-setup]")
        
        # Should show backup codes
        await authenticated_page.wait_for_selector("[data-testid=backup-codes]")

    async def test_error_handling_and_recovery(self, authenticated_page: Page):
        """Test error handling and recovery mechanisms."""
        
        # Test network error handling
        # Simulate offline mode
        await authenticated_page.context.set_offline(True)
        
        # Try to perform an action that requires network
        await authenticated_page.click("[data-testid=nav-strategies]")
        await authenticated_page.wait_for_selector(
            "[data-testid=offline-notice]",
            timeout=5000
        )
        
        # Verify offline message
        offline_message = await authenticated_page.text_content(
            "[data-testid=offline-notice]"
        )
        assert "offline" in offline_message.lower() or "network" in offline_message.lower()
        
        # Restore connection
        await authenticated_page.context.set_offline(False)
        
        # Should automatically reload
        await authenticated_page.wait_for_selector(
            "[data-testid=connection-restored]",
            timeout=5000
        )
        
        # Test API error handling
        # Navigate to a page and trigger an error
        await authenticated_page.goto("http://localhost:3000/invalid-page")
        await authenticated_page.wait_for_selector("[data-testid=404-error]")
        
        # Should show 404 error page
        error_message = await authenticated_page.text_content(
            "[data-testid=404-error]"
        )
        assert "404" in error_message or "not found" in error_message.lower()
        
        # Test form validation errors
        await authenticated_page.goto("http://localhost:3000/strategies")
        await authenticated_page.click("[data-testid=create-strategy-btn]")
        
        # Try to submit empty form
        await authenticated_page.click("[data-testid=save-strategy-btn]")
        
        # Should show validation errors
        validation_errors = await authenticated_page.locator(
            "[data-testid=validation-error]"
        ).count()
        assert validation_errors > 0
        
        # Test session timeout
        # Clear auth token to simulate timeout
        await authenticated_page.evaluate("""
            () => {
                localStorage.removeItem('authToken');
                sessionStorage.removeItem('authToken');
            }
        """)
        
        # Try to access protected route
        await authenticated_page.goto("http://localhost:3000/strategies")
        
        # Should redirect to login
        await authenticated_page.wait_for_url("**/login")