"""Self-healing selector resolution with caching and fallback strategies."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from src.utils.helpers import normalize_space, utc_now_iso
from src.utils.logger import get_logger


@dataclass
class LocatedElement:
    element: Any
    selector: str
    strategy: str
    healed: bool
    score: float = 0.0


class SelfHealer:
    """Find elements with direct selectors, cache hits, and semantic fallbacks."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
        self.enabled = bool(config.get("enabled", True))
        self.timeout_ms = int(config.get("timeout_ms", 1500))
        self.cache_ttl_hours = int(config.get("cache_ttl_hours", 168))
        self.cache_file = Path(str(config.get("cache_file", "./cache/selectors.json"))).resolve()
        self.max_candidates = int(config.get("max_candidates", 1800))
        self.similarity_threshold = float(config.get("similarity_threshold", 3.5))
        self.strategies = list(config.get("strategies", ["direct", "cache", "text", "semantic"]))
        self._cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Dict[str, str]]:
        if not self.cache_file.exists():
            return {}
        try:
            data = json.loads(self.cache_file.read_text(encoding="utf-8"))
        except Exception:
            self.logger.warning("Selector cache is invalid, starting empty")
            return {}
        return data if isinstance(data, dict) else {}

    def _save_cache(self) -> None:
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(json.dumps(self._cache, indent=2), encoding="utf-8")

    def _key(self, url: str, logical_name: str) -> str:
        return f"{url}::{logical_name}"

    def _is_fresh(self, timestamp: str | None) -> bool:
        if not timestamp:
            return False
        try:
            parsed = datetime.fromisoformat(timestamp)
        except Exception:
            return False
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed >= datetime.now(timezone.utc) - timedelta(hours=self.cache_ttl_hours)

    def remember(self, url: str, logical_name: str, selector: str) -> None:
        if not selector:
            return
        key = self._key(url, logical_name)
        self._cache[key] = {"selector": selector, "updated_at": utc_now_iso()}
        self._save_cache()

    def recall(self, url: str, logical_name: str) -> str | None:
        key = self._key(url, logical_name)
        entry = self._cache.get(key)
        if not entry:
            return None
        if not self._is_fresh(entry.get("updated_at")):
            return None
        return entry.get("selector")

    async def _query_selector(self, page: Any, selector: str):
        if selector.startswith("//"):
            return page.locator(f"xpath={selector}").first
        if selector.startswith("xpath="):
            return page.locator(selector).first
        return page.locator(selector).first

    async def _try_selector(self, page: Any, selector: str):
        locator = await self._query_selector(page, selector)
        count = await locator.count()
        if count <= 0:
            return None
        return await locator.element_handle()

    @staticmethod
    def _tokens(selectors: Iterable[str], semantic_hint: str = "") -> list[str]:
        tokens: set[str] = set()
        for selector in selectors:
            for token in re.split(r"[\s\._#\-\[\]>:+~=\(\)\"']+", selector.lower()):
                if len(token) > 1:
                    tokens.add(token)
        for token in semantic_hint.lower().split():
            if len(token) > 1:
                tokens.add(token)
        return sorted(tokens)

    @staticmethod
    def _score_candidate(candidate: Dict[str, Any], tokens: list[str], text_hint: str) -> float:
        text_hint = text_hint.lower().strip()
        score = 0.0
        fields = {
            "id": str(candidate.get("id", "")).lower(),
            "class": str(candidate.get("class_name", "")).lower(),
            "name": str(candidate.get("name", "")).lower(),
            "role": str(candidate.get("role", "")).lower(),
            "text": str(candidate.get("text", "")).lower(),
            "tag": str(candidate.get("tag", "")).lower(),
        }

        for token in tokens:
            if token in fields["id"]:
                score += 3.5
            if token in fields["class"]:
                score += 2.2
            if token in fields["name"]:
                score += 1.5
            if token in fields["role"]:
                score += 1.0
            if token == fields["tag"]:
                score += 1.2

        if text_hint and text_hint in fields["text"]:
            score += 3.0
        if candidate.get("visible"):
            score += 0.8

        return score

    async def _find_by_text(self, page: Any, text_hint: str) -> LocatedElement | None:
        hint = normalize_space(text_hint)
        if not hint:
            return None

        locator = page.locator(f"text={hint}").first
        if await locator.count() <= 0:
            return None

        handle = await locator.element_handle()
        if handle is None:
            return None

        selector = await page.evaluate(
            r"""
            (element) => {
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
                  const classes = Array.from(current.classList).slice(0,2);
                  if (classes.length) {
                    part += classes.map((cls) => '.' + CSS.escape(cls)).join('');
                  }
                  segments.unshift(part);
                  current = current.parentElement;
                }
                return segments.join(' > ');
              }
              return cssPath(element);
            }
            """,
            handle,
        )

        if not selector:
            return None

        return LocatedElement(element=handle, selector=selector, strategy="text", healed=True, score=4.0)

    async def _find_by_semantic(
        self,
        page: Any,
        selectors: list[str],
        semantic_hint: str,
        text_hint: str,
    ) -> LocatedElement | None:
        tokens = self._tokens(selectors, semantic_hint)
        candidates = await page.evaluate(
            r"""
            (maxCandidates) => {
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
                  const classes = Array.from(current.classList).slice(0,2);
                  if (classes.length) {
                    part += classes.map((cls) => '.' + CSS.escape(cls)).join('');
                  } else if (current.parentElement) {
                    const siblings = Array.from(current.parentElement.children).filter((item) => item.tagName === current.tagName);
                    if (siblings.length > 1) {
                      part += ':nth-of-type(' + (siblings.indexOf(current) + 1) + ')';
                    }
                  }
                  segments.unshift(part);
                  current = current.parentElement;
                }
                return segments.join(' > ');
              }

              function visible(el) {
                if (!(el instanceof HTMLElement)) return false;
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
              }

              return Array.from(document.querySelectorAll('body *')).slice(0, maxCandidates).map((el) => ({
                selector: cssPath(el),
                tag: el.tagName.toLowerCase(),
                id: el.id || '',
                class_name: el.className || '',
                name: el.getAttribute('name') || '',
                role: el.getAttribute('role') || '',
                text: (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 140),
                visible: visible(el)
              }));
            }
            """,
            self.max_candidates,
        )

        best: dict[str, Any] | None = None
        best_score = 0.0
        for candidate in candidates:
            score = self._score_candidate(candidate, tokens, text_hint)
            if score > best_score:
                best = candidate
                best_score = score

        if best is None or best_score < self.similarity_threshold:
            return None

        handle = await self._try_selector(page, best["selector"])
        if handle is None:
            return None

        return LocatedElement(
            element=handle,
            selector=best["selector"],
            strategy="semantic",
            healed=True,
            score=best_score,
        )

    async def locate(
        self,
        page: Any,
        selectors: List[str],
        logical_name: str,
        text_hint: str = "",
        semantic_hint: str = "",
    ) -> LocatedElement | None:
        selectors = [item for item in selectors if item]
        current_url = page.url

        if not selectors:
            return None

        if not self.enabled:
            handle = await self._try_selector(page, selectors[0])
            if handle is None:
                return None
            return LocatedElement(handle, selectors[0], "direct", healed=False)

        if "cache" in self.strategies:
            cached = self.recall(current_url, logical_name)
            if cached:
                handle = await self._try_selector(page, cached)
                if handle is not None:
                    return LocatedElement(handle, cached, "cache", healed=False)

        if "direct" in self.strategies:
            for selector in selectors:
                handle = await self._try_selector(page, selector)
                if handle is None:
                    continue
                self.remember(current_url, logical_name, selector)
                return LocatedElement(handle, selector, "direct", healed=False)

        if "text" in self.strategies:
            by_text = await self._find_by_text(page, text_hint)
            if by_text is not None:
                self.remember(current_url, logical_name, by_text.selector)
                return by_text

        if "semantic" in self.strategies:
            semantic = await self._find_by_semantic(page, selectors, semantic_hint or logical_name, text_hint)
            if semantic is not None:
                self.remember(current_url, logical_name, semantic.selector)
                return semantic

        return None
