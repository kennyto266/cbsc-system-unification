from playwright.sync_api import sync_playwright
import time

def debug_dashboard():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('http://localhost:3001')
        page.wait_for_load_state('networkidle')

        # Save page source
        with open('dashboard_source.html', 'w', encoding='utf-8') as f:
            f.write(page.content())
        print("[INFO] Page source saved to dashboard_source.html")

        # Check for various selectors
        selectors_to_check = [
            'button',
            'a',
            'div[class*="button"]',
            '[role="button"]',
            'span[class*="quick"]',
            'div[class*="action"]',
            'div[class*="quick-action"]',
            'button:has-text("創建")',
            'button:has-text("策略")',
            '*:has-text("創建新策略")',
            '*:has-text("查看市場數據")',
            '*:has-text("運行回測")',
            '*:has-text("導出報告")',
        ]

        for selector in selectors_to_check:
            elements = page.locator(selector)
            if elements.count() > 0:
                print(f"\n[FOUND] Selector '{selector}' matched {elements.count()} elements:")
                for i in range(min(3, elements.count())):
                    print(f"  Element {i+1}: {elements.nth(i).inner_text()[:50]}")

        # Check the page title
        title = page.title()
        print(f"\nPage Title: {title}")

        # Check current URL
        url = page.url
        print(f"Current URL: {url}")

        # Wait a bit more
        page.wait_for_timeout(3000)

        # Try to find any text that contains the button labels
        text_content = page.content()
        button_labels = ["創建新策略", "查看市場數據", "運行回測", "導出報告"]

        print("\nText content search:")
        for label in button_labels:
            if label in text_content:
                print(f"  [OK] Found text: {label}")
            else:
                print(f"  [MISSING] Text not found: {label}")

        browser.close()

if __name__ == "__main__":
    debug_dashboard()