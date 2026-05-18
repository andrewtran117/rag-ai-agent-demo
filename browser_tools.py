"""Playwright browser tools for the QA agent."""

import os
import base64
from datetime import datetime
from playwright.sync_api import sync_playwright, Browser, Page

REPORTS_DIR = "reports"
_browser: Browser | None = None
_page: Page | None = None
_playwright = None


def _ensure_browser():
    global _browser, _page, _playwright
    if _page is None:
        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.launch(headless=False)
        _page = _browser.new_page()
    return _page


def close_browser():
    global _browser, _page, _playwright
    if _browser:
        _browser.close()
    if _playwright:
        _playwright.stop()
    _browser = None
    _page = None
    _playwright = None


def browser_navigate(url: str) -> str:
    page = _ensure_browser()
    page.goto(url, wait_until="domcontentloaded")
    return f"Navigated to {page.url}"


def browser_click(selector: str) -> str:
    page = _ensure_browser()
    page.click(selector)
    page.wait_for_timeout(500)
    return f"Clicked: {selector}"


def browser_type(selector: str, text: str) -> str:
    page = _ensure_browser()
    page.fill(selector, text)
    return f"Typed '{text}' into {selector}"


def browser_screenshot() -> dict:
    page = _ensure_browser()
    os.makedirs(REPORTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(REPORTS_DIR, f"screenshot_{timestamp}.png")
    page.screenshot(path=path)
    return {"path": path, "message": f"Screenshot saved to {path}"}


def browser_assert(condition: str) -> str:
    page = _ensure_browser()
    try:
        locator = page.locator(condition)
        if locator.count() > 0 and locator.first.is_visible():
            return f"PASS — '{condition}' is visible on the page"
        else:
            return f"FAIL — '{condition}' is not visible on the page"
    except Exception as e:
        return f"FAIL — could not evaluate '{condition}': {e}"


def browser_get_text(selector: str) -> str:
    page = _ensure_browser()
    try:
        text = page.locator(selector).first.inner_text()
        return f"Text content: {text}"
    except Exception as e:
        return f"Could not get text from '{selector}': {e}"


def browser_get_html() -> str:
    page = _ensure_browser()
    html = page.content()
    # Truncate to avoid blowing up the context window
    if len(html) > 10000:
        html = html[:10000] + "\n... (truncated)"
    return html
