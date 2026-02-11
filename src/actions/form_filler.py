"""Form discovery and auto-fill helpers."""

from __future__ import annotations

from typing import Any, Dict, List

class FormFiller:
    """Detect and fill forms using field names/labels."""

    async def detect_forms(self, page: Any) -> List[Dict[str, Any]]:
        forms = await page.evaluate(
            """
            () => {
              return Array.from(document.querySelectorAll('form')).map((form, index) => ({
                index,
                id: form.id || null,
                action: form.getAttribute('action') || null,
                method: form.getAttribute('method') || 'get',
                fields: Array.from(form.querySelectorAll('input, textarea, select')).map((field) => ({
                  name: field.getAttribute('name') || null,
                  type: field.getAttribute('type') || field.tagName.toLowerCase(),
                  id: field.id || null,
                  placeholder: field.getAttribute('placeholder') || null,
                }))
              }));
            }
            """
        )
        return forms

    async def fill_form(
        self,
        page: Any,
        field_values: Dict[str, Any],
        form_selector: str | None = None,
        submit: bool = False,
    ) -> Dict[str, Any]:
        prefix = f"{form_selector} " if form_selector else ""
        filled_fields = []

        for key, value in field_values.items():
            candidates = [
                f"{prefix}[name='{key}']",
                f"{prefix}#{key}",
                f"{prefix}input[placeholder*='{key}']",
                f"{prefix}textarea[placeholder*='{key}']",
                f"{prefix}select[name='{key}']",
            ]

            chosen = None
            for selector in candidates:
                locator = page.locator(selector).first
                if await locator.count() > 0:
                    chosen = locator
                    break

            if chosen is None:
                continue

            tag = await chosen.evaluate("el => el.tagName.toLowerCase()")
            input_type = await chosen.get_attribute("type")
            value_text = str(value)

            if tag == "select":
                await chosen.select_option(value=value_text)
            elif input_type in {"checkbox", "radio"}:
                target_checked = value_text.lower() in {"1", "true", "yes", "on"}
                current_checked = await chosen.is_checked()
                if target_checked != current_checked:
                    await chosen.click()
            else:
                await chosen.fill(value_text)

            filled_fields.append(key)

        submitted = False
        if submit:
            submit_candidates = [
                f"{prefix}button[type='submit']",
                f"{prefix}input[type='submit']",
                f"{prefix}button",
            ]
            for selector in submit_candidates:
                locator = page.locator(selector).first
                if await locator.count() > 0:
                    await locator.click()
                    submitted = True
                    break

        return {
            "success": True,
            "filled_fields": filled_fields,
            "submitted": submitted,
        }
