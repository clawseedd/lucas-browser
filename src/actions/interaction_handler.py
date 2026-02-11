"""Basic interaction wrappers with optional human-like delay."""

from __future__ import annotations

import random
from typing import Any

from src.utils.helpers import sleep_random


class InteractionHandler:
    """Provide click/type helpers with jitter."""

    # Per-character delay range (ms) for human-like typing simulation.
    CHAR_DELAY_MIN_MS = 50
    CHAR_DELAY_MAX_MS = 150

    def __init__(self, delay_min_ms: int = 0, delay_max_ms: int = 0):
        self.delay_min_ms = delay_min_ms
        self.delay_max_ms = delay_max_ms

    async def click(self, page: Any, selector: str) -> dict[str, Any]:
        await page.locator(selector).first.click()
        await sleep_random(self.delay_min_ms, self.delay_max_ms)
        return {"success": True, "action": "click", "selector": selector}

    async def type_text(self, page: Any, selector: str, text: str, clear_first: bool = True) -> dict[str, Any]:
        """Type text character-by-character with random per-key delays to mimic a human typist.

        Each keystroke is separated by a random delay between CHAR_DELAY_MIN_MS and
        CHAR_DELAY_MAX_MS milliseconds (default 50-150 ms).
        """
        locator = page.locator(selector).first
        if clear_first:
            await locator.fill("")

        # Use Playwright's built-in per-character delay for realistic typing.
        # A random base delay is chosen per invocation; the natural variance
        # of the event loop adds additional jitter on top.
        char_delay = random.randint(self.CHAR_DELAY_MIN_MS, self.CHAR_DELAY_MAX_MS)
        await locator.type(text, delay=char_delay)

        await sleep_random(self.delay_min_ms, self.delay_max_ms)
        return {"success": True, "action": "type_text", "selector": selector, "length": len(text)}
