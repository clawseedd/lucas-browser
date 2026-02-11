"""Table extraction and normalization."""

from __future__ import annotations

from typing import Any, Dict, List

from src.utils.helpers import parse_number


def normalize_cell_value(value: str | None) -> str | float | None:
    if value is None:
        return None
    text = " ".join(str(value).split()).strip()
    if not text:
        return ""

    numeric = parse_number(text)
    if numeric is not None:
        stripped = text.replace(",", "")
        if all(ch.isdigit() or ch in ".-$€£¥₹+% " for ch in stripped):
            return numeric

    return text


def rows_to_records(headers: list[str], rows: list[list[Any]]) -> list[dict[str, Any]]:
    if not headers:
        return []

    normalized_headers = []
    for idx, header in enumerate(headers):
        safe = str(header or f"column_{idx + 1}").strip().lower().replace(" ", "_")
        normalized_headers.append(safe)

    records = []
    for row in rows:
        record = {}
        for idx, header in enumerate(normalized_headers):
            record[header] = row[idx] if idx < len(row) else None
        records.append(record)
    return records


class TableExtractor:
    """Extract structured tables from pages."""

    def __init__(self, max_table_rows: int = 1000):
        self.max_table_rows = max(10, int(max_table_rows))

    async def extract_tables(self, page: Any, selector: str = "table") -> list[dict[str, Any]]:
        raw_tables = await page.eval_on_selector_all(
            selector,
            r"""
            (tables, rowLimit) => {
              function clean(value) {
                return String(value || '').replace(/\s+/g, ' ').trim();
              }

              return tables.map((table) => {
                let headers = Array.from(table.querySelectorAll('thead th')).map((el) => clean(el.textContent));
                const bodyRows = Array.from(table.querySelectorAll('tbody tr'));
                const fallbackRows = bodyRows.length ? bodyRows : Array.from(table.querySelectorAll('tr'));

                const rows = fallbackRows.slice(0, rowLimit).map((row) =>
                  Array.from(row.querySelectorAll('th,td')).map((cell) => clean(cell.textContent))
                );

                if (!headers.length && rows.length) {
                  const candidate = rows[0];
                  const headerLike = candidate.every((value) => /[a-zA-Z]/.test(value || ''));
                  if (headerLike) {
                    headers = rows.shift();
                  }
                }

                if (!headers.length && rows.length) {
                  const width = Math.max(...rows.map((row) => row.length));
                  headers = Array.from({ length: width }, (_, idx) => `column_${idx + 1}`);
                }

                return {
                  headers,
                  rows,
                  row_count: rows.length,
                  column_count: headers.length,
                };
              });
            }
            """,
            self.max_table_rows,
        )

        output = []
        for idx, table in enumerate(raw_tables):
            normalized_rows = [
                [normalize_cell_value(cell) for cell in row]
                for row in table.get("rows", [])
            ]
            headers = [str(item) for item in table.get("headers", [])]
            output.append(
                {
                    "index": idx,
                    "headers": headers,
                    "rows": normalized_rows,
                    "records": rows_to_records(headers, normalized_rows),
                    "row_count": len(normalized_rows),
                    "column_count": len(headers),
                }
            )
        return output
