"""Rule-based relevance scoring for content blocks."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from src.utils.helpers import normalize_space


class RelevanceFilter:
    """Score and filter content blocks without LLM dependencies."""

    DEFAULT_EXCLUDE = ["nav", "footer", "aside", ".advert", ".cookie", ".newsletter", "script", "style"]

    def __init__(self, exclude_selectors: list[str] | None = None):
        self.exclude_selectors = exclude_selectors or list(self.DEFAULT_EXCLUDE)

    @staticmethod
    def _score_text(text: str, keywords: list[str]) -> float:
        text = text.lower()
        if not text:
            return 0.0

        score = min(len(text) / 500.0, 1.2)
        for keyword in keywords:
            if keyword in text:
                score += 0.6

        if text.count(" ") < 4:
            score -= 0.3

        return max(0.0, score)

    async def filter_page_elements(
        self,
        page: Any,
        keywords: Iterable[str] | None = None,
        min_score: float = 0.6,
        max_items: int = 25,
    ) -> list[dict[str, Any]]:
        keyword_list = [normalize_space(item).lower() for item in (keywords or []) if normalize_space(item)]

        elements = await page.evaluate(
            r"""
            (excludeSelectors) => {
              function cssPath(node) {
                if (!(node instanceof Element)) return "";
                const segments = [];
                let current = node;
                while (current && current.nodeType === Node.ELEMENT_NODE && segments.length < 8) {
                  let part = current.tagName.toLowerCase();
                  if (current.id) {
                    part += '#' + CSS.escape(current.id);
                    segments.unshift(part);
                    break;
                  }
                  const classes = Array.from(current.classList).slice(0, 2);
                  if (classes.length) {
                    part += classes.map((cls) => '.' + CSS.escape(cls)).join('');
                  }
                  segments.unshift(part);
                  current = current.parentElement;
                }
                return segments.join(' > ');
              }

              const candidates = Array.from(document.querySelectorAll('main, article, section, div, p, li, h1, h2, h3'));
              return candidates
                .filter((el) => {
                  if (!(el instanceof HTMLElement)) return false;
                  if (!el.innerText || el.innerText.trim().length < 20) return false;
                  return !excludeSelectors.some((selector) => {
                    try {
                      return el.matches(selector) || !!el.closest(selector);
                    } catch {
                      return false;
                    }
                  });
                })
                .slice(0, 800)
                .map((el) => ({
                  selector: cssPath(el),
                  text: (el.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 500),
                  tag: el.tagName.toLowerCase()
                }));
            }
            """,
            self.exclude_selectors,
        )

        scored = []
        for item in elements:
            score = self._score_text(item["text"], keyword_list)
            if score < min_score:
                continue
            scored.append({**item, "relevance_score": round(score, 3)})

        scored.sort(key=lambda obj: obj["relevance_score"], reverse=True)
        return scored[:max_items]
