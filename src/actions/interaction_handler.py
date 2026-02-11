"""Basic interaction wrappers with optional human-like delay."""

from __future__ import annotations

from typing import Any

from src.utils.helpers import sleep_random


class InteractionHandler:
    """Provide click/type helpers with jitter."""

    def __init__(self, delay_min_ms: int = 0, delay_max_ms: int = 0):
        self.delay_min_ms = delay_min_ms
        self.delay_max_ms = delay_max_ms

    async def click(self, page: Any, selector: str) -> dict[str, Any]:
        await page.locator(selector).first.click()
        await sleep_random(self.delay_min_ms, self.delay_max_ms)
        return {"success": True, "action": "click", "selector": selector}

    async def type_text(self, page: Any, selector: str, text: str, clear_first: bool = True) -> dict[str, Any]:
        locator = page.locator(selector).first
        if clear_first:
            await locator.fill("")
        await locator.type(text)
        await sleep_random(self.delay_min_ms, self.delay_max_ms)
        return {"success": True, "action": "type_text", "selector": selector, "length": len(text)}
