from playwright.sync_api import sync_playwright

def test_dashboard_app():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Test home page redirect
        print("Navigating to home page...")
        page.goto('http://localhost:3001')
        page.wait_for_load_state('networkidle')

        # Check if redirected to dashboard
        current_url = page.url
        print(f"Current URL after redirect: {current_url}")

        if '/dashboard' in current_url:
            print("[OK] Successfully redirected to dashboard")
        else:
            print("[FAIL] Redirect to dashboard failed")
            browser.close()
            return

        # Take a screenshot
        page.screenshot(path='dashboard_screenshot.png', full_page=True)
        print("[INFO] Dashboard screenshot saved")

        # Check for dashboard elements
        try:
            # Check for main dashboard heading
            page.wait_for_selector('h1', timeout=5000)
            heading = page.locator('h1').first
            print(f"[OK] Dashboard heading found: {heading.text_content()}")

            # Check for stats cards
            cards = page.locator('[class*="card"]').count()
            print(f"[OK] Found {cards} card elements")

            # Check for navigation
            nav_links = page.locator('nav a').count()
            print(f"[OK] Found {nav_links} navigation links")

            # Test navigation to strategies page
            print("\n[INFO] Testing navigation to strategies page...")
            page.goto('http://localhost:3001/dashboard/strategies')
            page.wait_for_load_state('networkidle')

            if '/dashboard/strategies' in page.url:
                print("[OK] Successfully navigated to strategies page")

                # Check for strategies table
                page.screenshot(path='strategies_screenshot.png', full_page=True)
                print("[INFO] Strategies page screenshot saved")

                table = page.locator('table').count()
                if table > 0:
                    print("[OK] Found strategies table")

                    # Check table rows
                    rows = page.locator('tbody tr').count()
                    print(f"[OK] Found {rows} strategy rows")
                else:
                    print("[WARN] No strategies table found")

            # Test navigation to analytics page
            print("\n[INFO] Testing navigation to analytics page...")
            page.goto('http://localhost:3001/dashboard/analytics')
            page.wait_for_load_state('networkidle')

            if '/dashboard/analytics' in page.url:
                print("[OK] Analytics page loaded")
                page.screenshot(path='analytics_screenshot.png', full_page=True)
            else:
                print("[FAIL] Analytics page failed to load")

            # Test navigation to settings page
            print("\n[INFO] Testing navigation to settings page...")
            page.goto('http://localhost:3001/dashboard/settings')
            page.wait_for_load_state('networkidle')

            if '/dashboard/settings' in page.url:
                print("[OK] Settings page loaded")
                page.screenshot(path='settings_screenshot.png', full_page=True)
            else:
                print("[FAIL] Settings page failed to load")

        except Exception as e:
            print(f"[ERROR] Error testing dashboard: {e}")
            page.screenshot(path='error_screenshot.png', full_page=True)

        browser.close()

if __name__ == "__main__":
    test_dashboard_app()