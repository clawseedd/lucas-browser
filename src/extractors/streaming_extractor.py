"""Streaming extraction utilities for token-budget style usage."""

from __future__ import annotations

from typing import Any, Dict, List

from src.utils.helpers import chunk_text


class StreamingExtractor:
    """Extract content incrementally in bounded chunks."""

    def __init__(self, chunk_chars: int = 1800, max_chunks: int = 12):
        self.chunk_chars = max(200, int(chunk_chars))
        self.max_chunks = max(1, int(max_chunks))

    async def extract_with_budget(
        self,
        page: Any,
        max_tokens: int = 4000,
        chars_per_token: float = 4.0,
        selector: str = "main, article, body",
    ) -> Dict[str, Any]:
        text = await page.eval_on_selector(
            selector,
            "el => (el.innerText || '').replace(/\\s+/g, ' ').trim()",
        )

        limit_chars = max(100, int(max_tokens * max(chars_per_token, 1.0)))
        text = text[:limit_chars]

        chunks = chunk_text(text, self.chunk_chars)[: self.max_chunks]
        estimated_tokens = int(sum(len(chunk) for chunk in chunks) / max(chars_per_token, 1.0))

        return {
            "success": True,
            "sections_extracted": len(chunks),
            "estimated_tokens": estimated_tokens,
            "truncated": len(text) >= limit_chars,
            "chunks": chunks,
        }
