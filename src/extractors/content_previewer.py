"""Content preview for cheap structure discovery."""

from __future__ import annotations

from typing import Any, Dict


class ContentPreviewer:
    """Create lightweight page previews to reduce extraction cost."""

    async def preview(self, page: Any, max_sections: int = 20) -> Dict[str, Any]:
        payload = await page.evaluate(
            r"""
            (limit) => {
              const title = document.title || '';
              const h1 = document.querySelector('h1')?.textContent?.trim() || '';
              const h2 = Array.from(document.querySelectorAll('h2')).slice(0, 10).map((el) => el.textContent.trim());
              const paragraphs = Array.from(document.querySelectorAll('p')).slice(0, 8).map((el) => el.textContent.replace(/\s+/g, ' ').trim());

              const sections = Array.from(document.querySelectorAll('main, article, section, div')).slice(0, 600)
                .filter((el) => (el.innerText || '').trim().length > 40)
                .slice(0, limit)
                .map((el, idx) => ({
                  index: idx,
                  tag: el.tagName.toLowerCase(),
                  text_preview: (el.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 180),
                }));

              return {
                preview: {
                  title,
                  h1,
                  h2_headings: h2,
                  paragraph_preview: paragraphs,
                },
                outline: {
                  total_sections: sections.length,
                  sections,
                },
              };
            }
            """,
            max_sections,
        )
        return payload
