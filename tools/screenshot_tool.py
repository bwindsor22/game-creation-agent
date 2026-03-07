"""Playwright-based screenshot and drag-and-drop testing tool."""
from __future__ import annotations

import os
import tempfile
import time


def take_screenshot(
    url: str,
    selector: str | None = None,
    output_path: str | None = None,
    viewport_width: int = 1280,
    viewport_height: int = 800,
    is_mobile: bool = False,
) -> str:
    """Take a screenshot of a URL using headless Chromium.

    Args:
        url: The URL to screenshot.
        selector: Optional CSS selector — screenshots just that element if provided.
        output_path: Where to save the PNG. Defaults to a temp file.

    Returns:
        Path to the saved PNG file.
    """
    from playwright.sync_api import sync_playwright

    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
            is_mobile=is_mobile,
            has_touch=is_mobile,
        )
        page = context.new_page()
        page.goto(url, wait_until="networkidle")

        if selector:
            element = page.locator(selector).first
            element.screenshot(path=output_path)
        else:
            page.screenshot(path=output_path, full_page=True)

        browser.close()

    return output_path


def simulate_drag(
    url: str,
    source_selector: str,
    target_selector: str,
    output_path: str | None = None,
    wait_after_ms: int = 500,
) -> dict:
    """Simulate an HTML5 drag-and-drop action on a web page and return the result.

    Uses JavaScript DragEvent dispatch, which works with react-dnd HTML5Backend.

    Args:
        url: The URL of the page to test.
        source_selector: CSS selector for the element to drag FROM.
        target_selector: CSS selector for the drop target element.
        output_path: Where to save a before+after screenshot PNG. Defaults to a temp file.
        wait_after_ms: Milliseconds to wait after drop before screenshotting.

    Returns:
        Dict with keys:
          - "screenshot_path": path to a side-by-side before/after PNG
          - "before_screenshot": path to before PNG
          - "after_screenshot": path to after PNG
          - "source_found": bool
          - "target_found": bool
          - "console_errors": list of browser console errors
    """
    from playwright.sync_api import sync_playwright

    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix="_drag_result.png")
        os.close(fd)

    before_path = output_path.replace(".png", "_before.png")
    after_path = output_path.replace(".png", "_after.png")

    console_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.on("console", lambda m: console_errors.append(f"{m.type}: {m.text}")
                if m.type in ("error", "warning") else None)

        page.goto(url, wait_until="networkidle")
        page.screenshot(path=before_path)

        # Check elements exist
        source_found = page.locator(source_selector).count() > 0
        target_found = page.locator(target_selector).count() > 0

        if source_found and target_found:
            # Dispatch HTML5 DnD events — works with react-dnd HTML5Backend
            page.evaluate(f"""
                (() => {{
                    const src = document.querySelector({repr(source_selector)});
                    const tgt = document.querySelector({repr(target_selector)});
                    if (!src || !tgt) return;
                    const dt = new DataTransfer();
                    const srcBox = src.getBoundingClientRect();
                    const tgtBox = tgt.getBoundingClientRect();
                    src.dispatchEvent(new DragEvent('dragstart', {{
                        bubbles: true, cancelable: true, dataTransfer: dt,
                        clientX: srcBox.left + srcBox.width / 2,
                        clientY: srcBox.top + srcBox.height / 2,
                    }}));
                    tgt.dispatchEvent(new DragEvent('dragenter', {{
                        bubbles: true, cancelable: true, dataTransfer: dt,
                        clientX: tgtBox.left + tgtBox.width / 2,
                        clientY: tgtBox.top + tgtBox.height / 2,
                    }}));
                    tgt.dispatchEvent(new DragEvent('dragover', {{
                        bubbles: true, cancelable: true, dataTransfer: dt,
                        clientX: tgtBox.left + tgtBox.width / 2,
                        clientY: tgtBox.top + tgtBox.height / 2,
                    }}));
                    tgt.dispatchEvent(new DragEvent('drop', {{
                        bubbles: true, cancelable: true, dataTransfer: dt,
                        clientX: tgtBox.left + tgtBox.width / 2,
                        clientY: tgtBox.top + tgtBox.height / 2,
                    }}));
                    src.dispatchEvent(new DragEvent('dragend', {{
                        bubbles: true, cancelable: true, dataTransfer: dt,
                    }}));
                }})()
            """)
            time.sleep(wait_after_ms / 1000)

        page.screenshot(path=after_path)
        browser.close()

    return {
        "before_screenshot": before_path,
        "after_screenshot": after_path,
        "source_found": source_found,
        "target_found": target_found,
        "console_errors": console_errors,
    }
