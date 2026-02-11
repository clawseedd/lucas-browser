"""Rule-based natural language query parser for field inference."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.utils.helpers import unique_ordered


@dataclass
class ParsedField:
    name: str
    field_type: str
    selectors: list[str]
    attribute: str | None = None
    text_hint: str | None = None


class NLQParser:
    """Generate selector candidates from plain field names without LLM usage."""

    NUMBER_HINTS = ("price", "cost", "amount", "total", "score", "rating", "count", "number")
    LINK_HINTS = ("link", "url", "href")
    BUTTON_HINTS = ("button", "cta", "submit", "buy", "add_to_cart")
    TABLE_HINTS = ("table", "rows", "columns")
    LIST_HINTS = ("list", "items", "results")
    BOOLEAN_HINTS = ("enabled", "available", "active", "checked")

    def infer_type(self, field_name: str) -> str:
        name = field_name.lower()

        if any(token in name for token in self.TABLE_HINTS):
            return "table"
        if any(token in name for token in self.LIST_HINTS):
            return "list"
        if any(token in name for token in self.NUMBER_HINTS):
            return "number"
        if any(token in name for token in self.BOOLEAN_HINTS):
            return "boolean"
        if any(token in name for token in self.LINK_HINTS):
            return "link"
        if any(token in name for token in self.BUTTON_HINTS):
            return "button"
        return "text"

    def build_selectors(self, field_name: str, field_type: str) -> list[str]:
        normalized = field_name.strip().lower().replace(" ", "_")
        selector_parts: list[str] = [
            f"[data-field='{normalized}']",
            f"[data-testid*='{normalized}']",
            f"[name*='{normalized}']",
            f"#{normalized}",
            f".{normalized}",
        ]

        if field_type == "number":
            selector_parts.extend(["[data-price]", ".price", "[itemprop='price']", ".amount"])
        elif field_type == "button":
            selector_parts.extend(["button", "[role='button']", "input[type='submit']"])
        elif field_type == "link":
            selector_parts.extend(["a[href]"])
        elif field_type == "table":
            selector_parts.extend(["table", "[role='table']"])
        elif field_type == "list":
            selector_parts.extend(["ul li", "ol li", "[role='listitem']"])
        else:
            selector_parts.extend(["h1", "h2", "h3", ".title", ".name", ".label", "p"])

        return unique_ordered(selector_parts)

    def parse_field(self, field_name: str, spec: dict[str, Any] | None = None) -> ParsedField:
        spec = spec or {}
        field_type = str(spec.get("type") or self.infer_type(field_name)).lower()

        explicit_selectors = spec.get("selectors")
        selector_list: list[str] = []
        if isinstance(explicit_selectors, list):
            selector_list.extend(str(item) for item in explicit_selectors if item)
        elif isinstance(spec.get("selector"), str):
            selector_list.append(spec["selector"])

        selector_list.extend(self.build_selectors(field_name, field_type))

        attribute = spec.get("attribute")
        if field_type == "link" and not attribute:
            attribute = "href"

        return ParsedField(
            name=field_name,
            field_type=field_type,
            selectors=unique_ordered(selector_list),
            attribute=attribute,
            text_hint=str(spec.get("text_hint") or field_name.replace("_", " ")),
        )

    def parse_query(self, query: dict[str, Any]) -> dict[str, ParsedField]:
        raw_fields = query.get("fields")
        if isinstance(raw_fields, dict):
            fields = raw_fields
        else:
            fields = query
        parsed: dict[str, ParsedField] = {}
        for name, spec in fields.items():
            parsed[name] = self.parse_field(name, spec if isinstance(spec, dict) else {})
        return parsed
