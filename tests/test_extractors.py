"""Tests for extractor helpers."""

from __future__ import annotations

import unittest

from src.extractors.streaming_extractor import StreamingExtractor
from src.extractors.table_extractor import normalize_cell_value, rows_to_records


class ExtractorHelperTests(unittest.TestCase):
    def test_normalize_cell_value(self) -> None:
        self.assertEqual(normalize_cell_value("$1,299.50"), 1299.5)
        self.assertEqual(normalize_cell_value("Widget"), "Widget")

    def test_rows_to_records(self) -> None:
        records = rows_to_records(["Name", "Price"], [["Item", 10.0]])
        self.assertEqual(records, [{"name": "Item", "price": 10.0}])

    def test_streaming_constructor_bounds(self) -> None:
        extractor = StreamingExtractor(chunk_chars=10, max_chunks=0)
        self.assertEqual(extractor.chunk_chars, 200)
        self.assertEqual(extractor.max_chunks, 1)


if __name__ == "__main__":
    unittest.main()
