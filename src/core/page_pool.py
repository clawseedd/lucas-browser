"""LRU page pool for low-memory browser reuse."""

from __future__ import annotations

from collections import OrderedDict
from typing import Any


class PagePool:
    """Reuse pages and evict least-recently-used tabs when needed."""

    def __init__(self, max_pages: int = 2):
        self.max_pages = max(1, int(max_pages))
        self._pages: OrderedDict[str, Any] = OrderedDict()

    def has(self, tab_id: str) -> bool:
        return tab_id in self._pages

    def get(self, tab_id: str) -> Any | None:
        page = self._pages.get(tab_id)
        if page is None:
            return None
        self._pages.move_to_end(tab_id)
        return page

    async def put(self, tab_id: str, page: Any) -> list[Any]:
        closed: list[Any] = []
        self._pages[tab_id] = page
        self._pages.move_to_end(tab_id)

        while len(self._pages) > self.max_pages:
            evicted_tab, evicted_page = self._pages.popitem(last=False)
            if evicted_tab == tab_id:
                self._pages[evicted_tab] = evicted_page
                break
            closed.append(evicted_page)

        return closed

    def all_items(self) -> list[tuple[str, Any]]:
        return list(self._pages.items())

    async def close_all(self) -> None:
        for _, page in self._pages.items():
            try:
                await page.close()
            except Exception:
                pass
        self._pages.clear()

    async def close_tab(self, tab_id: str) -> None:
        page = self._pages.pop(tab_id, None)
        if page is None:
            return
        try:
            await page.close()
        except Exception:
            pass
