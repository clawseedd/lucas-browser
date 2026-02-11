"""Tests for LRU page pool."""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from src.core.page_pool import PagePool


class PagePoolTests(unittest.TestCase):
    def test_get_returns_none_for_missing(self) -> None:
        pool = PagePool(max_pages=2)
        self.assertIsNone(pool.get("missing"))

    def test_get_returns_page(self) -> None:
        pool = PagePool(max_pages=2)
        page = MagicMock()
        asyncio.get_event_loop().run_until_complete(pool.put("tab1", page))
        self.assertIs(pool.get("tab1"), page)

    def test_has(self) -> None:
        pool = PagePool(max_pages=2)
        self.assertFalse(pool.has("x"))
        asyncio.get_event_loop().run_until_complete(pool.put("x", MagicMock()))
        self.assertTrue(pool.has("x"))

    def test_eviction(self) -> None:
        pool = PagePool(max_pages=1)
        page1 = MagicMock()
        page2 = MagicMock()
        asyncio.get_event_loop().run_until_complete(pool.put("a", page1))
        evicted = asyncio.get_event_loop().run_until_complete(pool.put("b", page2))
        self.assertEqual(evicted, [page1])
        self.assertFalse(pool.has("a"))
        self.assertTrue(pool.has("b"))

    def test_max_pages_clamped(self) -> None:
        pool = PagePool(max_pages=0)
        self.assertEqual(pool.max_pages, 1)

    def test_close_all(self) -> None:
        pool = PagePool(max_pages=3)
        pages = [AsyncMock() for _ in range(3)]
        for i, p in enumerate(pages):
            asyncio.get_event_loop().run_until_complete(pool.put(f"t{i}", p))
        asyncio.get_event_loop().run_until_complete(pool.close_all())
        self.assertEqual(len(pool.all_items()), 0)
        for p in pages:
            p.close.assert_awaited_once()

    def test_close_tab(self) -> None:
        pool = PagePool(max_pages=3)
        page = AsyncMock()
        asyncio.get_event_loop().run_until_complete(pool.put("tab1", page))
        asyncio.get_event_loop().run_until_complete(pool.close_tab("tab1"))
        self.assertFalse(pool.has("tab1"))
        page.close.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
