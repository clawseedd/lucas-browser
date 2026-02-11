"""Infinite scroll and dynamic loading helpers."""

from __future__ import annotations

import asyncio
from typing import Any, Dict


class ScrollHandler:
    """Handle incremental page scrolling until content stops growing."""

    async def auto_scroll(
        self,
        page: Any,
        max_scrolls: int = 20,
        scroll_delay_sec: float = 0.8,
        stop_if_no_new_content: bool = True,
    ) -> Dict[str, Any]:
        max_scrolls = max(1, int(max_scrolls))
        previous_height = await page.evaluate("() => document.body.scrollHeight")
        no_change_count = 0

        for index in range(max_scrolls):
            await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(max(0.1, float(scroll_delay_sec)))

            current_height = await page.evaluate("() => document.body.scrollHeight")
            if current_height <= previous_height:
                no_change_count += 1
                if stop_if_no_new_content and no_change_count >= 2:
                    return {
                        "success": True,
                        "scroll_count": index + 1,
                        "stopped_reason": "no_new_content",
                        "final_height": current_height,
                    }
            else:
                no_change_count = 0

            previous_height = max(previous_height, current_height)

        return {
            "success": True,
            "scroll_count": max_scrolls,
            "stopped_reason": "max_scrolls_reached",
            "final_height": previous_height,
        }
