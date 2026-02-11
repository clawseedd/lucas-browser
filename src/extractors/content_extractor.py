"""Structured extraction with NLQ parsing and self-healing selectors."""

from __future__ import annotations

from typing import Any, Dict

from src.extractors.table_extractor import TableExtractor
from src.intelligence.nlq_parser import NLQParser
from src.intelligence.self_healing import SelfHealer
from src.utils.helpers import normalize_space, parse_number, utc_now_iso


class ContentExtractor:
    """Extract text, numbers, tables and lists from pages."""

    def __init__(
        self,
        self_healer: SelfHealer,
        max_text_length: int = 12000,
        max_table_rows: int = 1000,
    ):
        self.nlq_parser = NLQParser()
        self.self_healer = self_healer
        self.max_text_length = max(500, int(max_text_length))
        self.table_extractor = TableExtractor(max_table_rows=max_table_rows)

    async def _extract_text_or_attr(self, element: Any, attribute: str | None) -> str | None:
        if attribute:
            return await element.get_attribute(attribute)
        text = await element.text_content()
        return text

    def _cast_value(self, raw: str | None, field_type: str):
        text = normalize_space(raw)
        if raw is None:
            return None

        if field_type == "number":
            return parse_number(text)

        if field_type == "boolean":
            lowered = text.lower()
            if lowered in {"true", "yes", "1", "on", "enabled", "checked"}:
                return True
            if lowered in {"false", "no", "0", "off", "disabled", "unchecked"}:
                return False
            return bool(text)

        return text[: self.max_text_length]

    async def extract_with_nlq(self, page: Any, query: Dict[str, Any]) -> Dict[str, Any]:
        parsed = self.nlq_parser.parse_query(query)

        data: dict[str, Any] = {}
        meta: dict[str, Any] = {
            "url": page.url,
            "extracted_at": utc_now_iso(),
            "fields": {},
        }

        for field_name, field in parsed.items():
            if field.field_type == "table":
                tables = await self.table_extractor.extract_tables(page, selector=field.selectors[0])
                data[field_name] = tables
                meta["fields"][field_name] = {
                    "type": "table",
                    "item_count": len(tables),
                    "strategy": "table",
                }
                continue

            if field.field_type == "list":
                values = await page.eval_on_selector_all(
                    field.selectors[0],
                    "elements => elements.slice(0, 80).map((el) => (el.textContent || '').replace(/\\s+/g, ' ').trim())",
                )
                data[field_name] = [normalize_space(item) for item in values if normalize_space(item)]
                meta["fields"][field_name] = {
                    "type": "list",
                    "item_count": len(data[field_name]),
                    "strategy": "list",
                }
                continue

            located = await self.self_healer.locate(
                page,
                field.selectors,
                logical_name=field.name,
                text_hint=field.text_hint or "",
                semantic_hint=field.name,
            )

            if located is None:
                data[field_name] = None
                meta["fields"][field_name] = {
                    "type": field.field_type,
                    "strategy": "not_found",
                }
                continue

            raw = await self._extract_text_or_attr(located.element, field.attribute)
            data[field_name] = self._cast_value(raw, field.field_type)
            meta["fields"][field_name] = {
                "type": field.field_type,
                "strategy": located.strategy,
                "selector": located.selector,
                "healed": located.healed,
            }

        return {"success": True, "data": data, "meta": meta}
