"""Capture CSS/XPath structure for scraping and data parsing."""

from __future__ import annotations

from typing import Any, Dict

from src.intelligence.self_healing import SelfHealer


class StructureAnalyzer:
    """Inspect DOM structure for a target element."""

    def __init__(self, self_healer: SelfHealer):
        self.self_healer = self_healer

    async def capture_structure(
        self,
        page: Any,
        selector: str,
        logical_name: str = "target",
        text_hint: str = "",
        semantic_hint: str = "",
    ) -> Dict[str, Any]:
        located = await self.self_healer.locate(
            page,
            [selector],
            logical_name=logical_name,
            text_hint=text_hint,
            semantic_hint=semantic_hint or logical_name,
        )

        if located is None:
            return {"success": False, "error": "element_not_found", "selector": selector}

        structure = await page.evaluate(
            r"""
            (element) => {
              function cssPath(node) {
                if (!(node instanceof Element)) return '';
                const parts = [];
                let current = node;
                while (current && current.nodeType === Node.ELEMENT_NODE && parts.length < 10) {
                  let part = current.tagName.toLowerCase();
                  if (current.id) {
                    part += '#' + CSS.escape(current.id);
                    parts.unshift(part);
                    break;
                  }
                  const classes = Array.from(current.classList).slice(0, 3);
                  if (classes.length) {
                    part += classes.map((item) => '.' + CSS.escape(item)).join('');
                  } else if (current.parentElement) {
                    const siblings = Array.from(current.parentElement.children).filter((item) => item.tagName === current.tagName);
                    if (siblings.length > 1) {
                      part += ':nth-of-type(' + (siblings.indexOf(current) + 1) + ')';
                    }
                  }
                  parts.unshift(part);
                  current = current.parentElement;
                }
                return parts.join(' > ');
              }

              function xpath(node) {
                if (!(node instanceof Element)) return '';
                if (node.id) return '//*[@id="' + node.id + '"]';
                const parts = [];
                let current = node;
                while (current && current.nodeType === Node.ELEMENT_NODE) {
                  let index = 1;
                  let prev = current.previousElementSibling;
                  while (prev) {
                    if (prev.tagName === current.tagName) index += 1;
                    prev = prev.previousElementSibling;
                  }
                  parts.unshift(current.tagName.toLowerCase() + '[' + index + ']');
                  current = current.parentElement;
                }
                return '/' + parts.join('/');
              }

              const attrs = Array.from(element.attributes || []).slice(0, 16).map((attr) => ({
                name: attr.name,
                value: attr.value,
              }));

              const suggested = [];
              if (element.id) suggested.push('#' + CSS.escape(element.id));
              if (element.classList.length) {
                suggested.push(
                  element.tagName.toLowerCase() + '.' + Array.from(element.classList).slice(0, 3).map((v) => CSS.escape(v)).join('.')
                );
              }
              ['name', 'data-testid', 'data-qa', 'aria-label'].forEach((attr) => {
                const value = element.getAttribute(attr);
                if (value) {
                  suggested.push(`${element.tagName.toLowerCase()}[${attr}="${value}"]`);
                }
              });

              return {
                tag: element.tagName.toLowerCase(),
                id: element.id || null,
                classes: Array.from(element.classList),
                attributes: attrs,
                text_preview: (element.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 200),
                html_preview: (element.outerHTML || '').slice(0, 500),
                css_path: cssPath(element),
                xpath: xpath(element),
                parent: element.parentElement ? {
                  tag: element.parentElement.tagName.toLowerCase(),
                  id: element.parentElement.id || null,
                  classes: Array.from(element.parentElement.classList),
                } : null,
                children_count: element.children.length,
                suggested_selectors: Array.from(new Set(suggested)),
              };
            }
            """,
            located.element,
        )

        return {
            "success": True,
            "resolved_by": located.strategy,
            "healed": located.healed,
            "structure": structure,
        }
