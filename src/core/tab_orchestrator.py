"""Parallel tab orchestration for multi-page scraping."""

from __future__ import annotations

import asyncio
from typing import Dict, Iterable, List


class TabOrchestrator:
    """Run extraction tasks across multiple URLs with bounded concurrency."""

    def __init__(self, agent):
        self.agent = agent

    async def extract_from_multiple_pages(
        self,
        urls: Iterable[str],
        query: Dict[str, Any],
        max_concurrent: int = 2,
    ) -> List[Dict[str, Any]]:
        semaphore = asyncio.Semaphore(max(1, int(max_concurrent)))

        async def worker(index: int, url: str) -> Dict[str, Any]:
            tab_id = f"parallel_{index}"
            async with semaphore:
                try:
                    nav = await self.agent.navigate(url, tab_id=tab_id)
                    data = await self.agent.extract_with_nlq(query, tab_id=tab_id)
                    return {
                        "success": True,
                        "tab_id": tab_id,
                        "url": url,
                        "navigation": nav,
                        "data": data,
                    }
                except Exception as exc:
                    return {
                        "success": False,
                        "tab_id": tab_id,
                        "url": url,
                        "error": str(exc),
                    }

        tasks = [worker(index, url) for index, url in enumerate(urls)]
        return await asyncio.gather(*tasks)
