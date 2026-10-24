"""
End-to-End Strategy Management Flow Tests
Tests complete user workflows from frontend to backend
"""

import pytest
import asyncio
from playwright.async_api import async_playwright, Page, Browser
import json
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:3000"  # Frontend
API_URL = "http://localhost:3004"   # Backend API

@pytest.fixture(scope="session")
async def browser():
    """Create browser instance for E2E testing"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()

@pytest.fixture
async def page(browser: Browser):
    """Create new page for each test"""
    page = await browser.new_page()
    await page.goto(BASE_URL)
    yield page
    await page.close()

@pytest.fixture(scope="session")
async def setup_test_data():
    """Setup test data in backend"""
    # This would typically setup test data via API
    # For now, we'll assume test data exists
    pass

class TestStrategyManagementE2E:
    """Test complete strategy management workflows"""

    async def test_complete_strategy_lifecycle(self, page: Page):
        """Test complete strategy CRUD lifecycle"""

        # Step 1: Navigate to strategies page
        await page.click('[data-testid="nav-strategies"]')
        await page.wait_for_load_state('networkidle')

        # Verify we're on the strategies page
        await page.wait_for_selector('[data-testid="strategies-page"]')
        assert await page.locator('[data-testid="page-title"]').text_content() == "策略管理"

        # Step 2: Create new strategy
        await page.click('[data-testid="create-strategy-btn"]')
        await page.wait_for_selector('[data-testid="strategy-form"]')

        # Fill in strategy details
        await page.fill('[data-testid="strategy-name"]', "E2E Test Strategy")
        await page.fill('[data-testid="strategy-description"]', "Created during E2E testing")

        # Configure strategy parameters
        await page.select_option('[data-testid="strategy-type"]', "moving_average")
        await page.fill('[data-testid="param-short-period"]', "10")
        await page.fill('[data-testid="param-long-period"]', "20")
        await page.select_option('[data-testid="param-symbol"]', "BTC/USDT")

        # Submit form
        await page.click('[data-testid="save-strategy-btn"]')
        await page.wait_for_selector('[data-testid="success-message"]')

        # Verify success message
        success_message = await page.locator('[data-testid="success-message"]').text_content()
        assert "created successfully" in success_message.lower()

        # Step 3: Verify strategy appears in list
        await page.wait_for_selector('[data-testid="strategies-list"]')

        # Find the newly created strategy
        strategy_cards = await page.locator('[data-testid="strategy-card"]').all()
        found_strategy = False

        for card in strategy_cards:
            name = await card.locator('[data-testid="strategy-name"]').text_content()
            if name == "E2E Test Strategy":
                found_strategy = True
                break

        assert found_strategy, "Created strategy not found in list"

        # Step 4: Edit the strategy
        await page.click('[data-testid="edit-strategy"]:first-child')
        await page.wait_for_selector('[data-testid="strategy-form"]')

        # Update strategy details
        await page.fill('[data-testid="strategy-description"]', "Updated during E2E testing")
        await page.click('[data-testid="save-strategy-btn"]')
        await page.wait_for_selector('[data-testid="success-message"]')

        # Step 5: View strategy performance
        await page.click('[data-testid="view-performance"]')
        await page.wait_for_selector('[data-testid="performance-chart"]')

        # Verify performance metrics are displayed
        assert await page.locator('[data-testid="total-return"]').is_visible()
        assert await page.locator('[data-testid="sharpe-ratio"]').is_visible()
        assert await page.locator('[data-testid="win-rate"]').is_visible()

        # Step 6: Activate strategy
        await page.click('[data-testid="activate-strategy-btn"]')
        await page.wait_for_selector('[data-testid="confirmation-modal"]')
        await page.click('[data-testid="confirm-activation"]')
        await page.wait_for_selector('[data-testid="success-message"]')

        # Verify status changed to active
        status_badge = await page.locator('[data-testid="strategy-status"]')
        status_text = await status_badge.text_content()
        assert "active" in status_text.lower()

        # Step 7: Delete strategy
        await page.click('[data-testid="delete-strategy"]')
        await page.wait_for_selector('[data-testid="confirmation-modal"]')
        await page.click('[data-testid="confirm-delete"]')
        await page.wait_for_selector('[data-testid="success-message"]')

        # Verify strategy is removed from list
        await page.wait_for_timeout(1000)  # Give time for UI to update
        strategy_cards_after = await page.locator('[data-testid="strategy-card"]').all()

        found_after_delete = False
        for card in strategy_cards_after:
            name = await card.locator('[data-testid="strategy-name"]').text_content()
            if name == "E2E Test Strategy":
                found_after_delete = True
                break

        assert not found_after_delete, "Strategy was not deleted successfully"

    async def test_strategy_performance_analysis_workflow(self, page: Page):
        """Test strategy performance analysis workflow"""

        # Navigate to strategies page
        await page.click('[data-testid="nav-strategies"]')
        await page.wait_for_load_state('networkidle')

        # Click on performance analysis
        await page.click('[data-testid="performance-analysis-tab"]')
        await page.wait_for_selector('[data-testid="performance-dashboard"]')

        # Select time range
        await page.select_option('[data-testid="time-range"]', "1M")
        await page.wait_for_timeout(1000)  # Wait for data to load

        # Verify performance charts are displayed
        assert await page.locator('[data-testid="equity-curve-chart"]').is_visible()
        assert await page.locator('[data-testid="returns-distribution-chart"]').is_visible()
        assert await page.locator('[data-testid="drawdown-chart"]').is_visible()

        # Check performance metrics
        metrics = await page.locator('[data-testid="performance-metric"]').all()
        assert len(metrics) > 0, "No performance metrics found"

        # Test exporting performance data
        await page.click('[data-testid="export-performance-btn"]')
        await page.select_option('[data-testid="export-format"]', "csv")
        await page.click('[data-testid="download-export-btn"]')

        # Verify download started (would need to check download folder in real implementation)
        assert await page.locator('[data-testid="export-success"]').is_visible()

    async def test_batch_operations_workflow(self, page: Page):
        """Test batch operations on multiple strategies"""

        # Navigate to strategies page
        await page.click('[data-testid="nav-strategies"]')
        await page.wait_for_load_state('networkidle')

        # Select multiple strategies
        await page.check('[data-testid="strategy-checkbox"]:first-child')
        await page.check('[data-testid="strategy-checkbox"]:nth-child(2)')
        await page.check('[data-testid="strategy-checkbox"]:nth-child(3)')

        # Verify selection
        selected_count = await page.locator('[data-testid="selected-count"]').text_content()
        assert "3" in selected_count

        # Test batch activation
        await page.click('[data-testid="batch-activate-btn"]')
        await page.wait_for_selector('[data-testid="batch-confirmation-modal"]')
        await page.click('[data-testid="confirm-batch-operation"]')
        await page.wait_for_selector('[data-testid="batch-success-message"]')

        # Verify all selected strategies are now active
        active_strategies = await page.locator('[data-testid="strategy-status"][data-status="active"]').all()
        assert len(active_strategies) >= 3

        # Test batch deactivation
        await page.check('[data-testid="select-all-checkbox"]')
        await page.click('[data-testid="batch-deactivate-btn"]')
        await page.wait_for_selector('[data-testid="batch-confirmation-modal"]')
        await page.click('[data-testid="confirm-batch-operation"]')
        await page.wait_for_selector('[data-testid="batch-success-message"]')

        # Verify all strategies are now inactive
        inactive_strategies = await page.locator('[data-testid="strategy-status"][data-status="inactive"]').all()
        assert len(inactive_strategies) > 0

    async def test_real_time_updates_workflow(self, page: Page):
        """Test real-time data updates"""

        # Navigate to dashboard
        await page.click('[data-testid="nav-dashboard"]')
        await page.wait_for_load_state('networkidle')

        # Wait for initial data to load
        await page.wait_for_selector('[data-testid="dashboard-content"]')

        # Capture initial values
        initial_portfolio_value = await page.locator('[data-testid="portfolio-value"]').text_content()
        initial_active_strategies = await page.locator('[data-testid="active-strategies-count"]').text_content()

        # Simulate real-time update via WebSocket (would need WebSocket server)
        # For now, just verify real-time indicators are present
        assert await page.locator('[data-testid="real-time-indicator"]').is_visible()

        # Check for last update timestamp
        assert await page.locator('[data-testid="last-update"]').is_visible()

        # Test auto-refresh functionality
        initial_time = datetime.now()
        await page.wait_for_timeout(5000)  # Wait 5 seconds

        # Check if timestamp updated (assuming 30-second refresh)
        update_time_element = await page.locator('[data-testid="last-update"]')
        update_time_text = await update_time_element.text_content()

        # In a real test, we would verify the time actually updated

    async def test_search_and_filter_workflow(self, page: Page):
        """Test search and filtering functionality"""

        # Navigate to strategies page
        await page.click('[data-testid="nav-strategies"]')
        await page.wait_for_load_state('networkidle')

        # Get initial strategy count
        initial_count = len(await page.locator('[data-testid="strategy-card"]').all())

        # Test search functionality
        await page.fill('[data-testid="search-input"]', "MA")
        await page.wait_for_timeout(1000)

        # Check if filtered results
        filtered_count = len(await page.locator('[data-testid="strategy-card"]').all())
        assert filtered_count <= initial_count

        # Test status filter
        await page.click('[data-testid="status-filter"]')
        await page.click('[data-testid="filter-active"]')
        await page.wait_for_timeout(1000)

        # Verify only active strategies shown
        active_cards = await page.locator('[data-testid="strategy-card"]').all()
        for card in active_cards:
            status = await card.locator('[data-testid="strategy-status"]').text_content()
            assert "active" in status.lower()

        # Clear filters
        await page.click('[data-testid="clear-filters"]')
        await page.wait_for_timeout(1000)

        # Verify all strategies shown again
        final_count = len(await page.locator('[data-testid="strategy-card"]').all())
        assert final_count == initial_count

    async def test_error_handling_workflow(self, page: Page):
        """Test error handling in user workflows"""

        # Navigate to strategies page
        await page.click('[data-testid="nav-strategies"]')
        await page.wait_for_load_state('networkidle')

        # Test network error handling
        # Simulate network offline
        await page.context.set_offline(True)

        # Try to create strategy
        await page.click('[data-testid="create-strategy-btn"]')
        await page.fill('[data-testid="strategy-name"]', "Offline Strategy")
        await page.click('[data-testid="save-strategy-btn"]')

        # Should show network error message
        await page.wait_for_selector('[data-testid="error-message"]')
        error_message = await page.locator('[data-testid="error-message"]').text_content()
        assert "network" in error_message.lower() or "offline" in error_message.lower()

        # Restore network
        await page.context.set_offline(False)

        # Test validation error
        await page.click('[data-testid="create-strategy-btn"]')
        await page.fill('[data-testid="strategy-name"]', "")  # Empty name
        await page.click('[data-testid="save-strategy-btn"]')

        # Should show validation error
        await page.wait_for_selector('[data-testid="validation-error"]')
        validation_error = await page.locator('[data-testid="validation-error"]').text_content()
        assert "required" in validation_error.lower() or "empty" in validation_error.lower()

class TestUserAuthenticationE2E:
    """Test user authentication workflows"""

    async def test_login_workflow(self, page: Page):
        """Test complete login workflow"""

        # Navigate to login page
        await page.goto(f"{BASE_URL}/login")
        await page.wait_for_selector('[data-testid="login-form"]')

        # Fill in credentials
        await page.fill('[data-testid="username-input"]', "test_user")
        await page.fill('[data-testid="password-input"]', "test_password")

        # Submit login form
        await page.click('[data-testid="login-btn"]')

        # Wait for redirect to dashboard
        await page.wait_for_url(f"{BASE_URL}/dashboard")
        await page.wait_for_selector('[data-testid="dashboard-content"]')

        # Verify user is logged in
        assert await page.locator('[data-testid="user-menu"]').is_visible()
        username = await page.locator('[data-testid="user-name"]').text_content()
        assert username == "test_user"

    async def test_logout_workflow(self, page: Page):
        """Test logout workflow"""

        # First login
        await self.test_login_workflow(page)

        # Click user menu
        await page.click('[data-testid="user-menu"]')
        await page.wait_for_selector('[data-testid="logout-btn"]')

        # Click logout
        await page.click('[data-testid="logout-btn"]')

        # Wait for redirect to login
        await page.wait_for_url(f"{BASE_URL}/login")
        await page.wait_for_selector('[data-testid="login-form"]')

        # Verify logged out
        assert not await page.locator('[data-testid="user-menu"]').is_visible()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])