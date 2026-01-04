from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    # Collect console messages
    console_messages = []
    def handle_console(msg):
        console_messages.append(f"{msg.type}: {msg.text}")
    page.on("console", handle_console)
    
    # Navigate to page
    page.goto("http://localhost:3000", wait_until="networkidle")
    
    # Wait for page to render
    time.sleep(3)
    
    # Take screenshot
    page.screenshot(path="frontend_check.png", full_page=True)
    
    # Get page title and URL
    title = page.title()
    url = page.url
    
    # Check if root element has content
    root_content = page.evaluate("() => document.getElementById('root')?.innerHTML")
    
    browser.close()
    
    # Print results
    print(f"Title: {title}")
    print(f"URL: {url}")
    print(f"\nConsole messages ({len(console_messages)}):")
    for msg in console_messages[:20]:  # First 20 messages
        print(f"  {msg}")
    
    print(f"\nRoot element exists: {bool(root_content)}")
    if root_content:
        print(f"Root HTML length: {len(root_content)} chars")
        print(f"Root preview: {root_content[:500]}...")
