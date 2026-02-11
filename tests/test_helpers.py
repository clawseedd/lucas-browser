"""Tests for helper utilities."""

from __future__ import annotations

import unittest

from src.utils.helpers import (
    chunk_text,
    ensure_directory,
    normalize_space,
    parse_number,
    sanitize_filename,
    unique_ordered,
    utc_now_iso,
)


class HelpersTests(unittest.TestCase):
    def test_utc_now_iso_format(self) -> None:
        ts = utc_now_iso()
        self.assertIn("T", ts)
        self.assertIn("+00:00", ts)

    def test_normalize_space(self) -> None:
        self.assertEqual(normalize_space("  hello   world  "), "hello world")
        self.assertEqual(normalize_space(None), "")
        self.assertEqual(normalize_space(""), "")

    def test_parse_number(self) -> None:
        self.assertEqual(parse_number("$1,299.50"), 1299.5)
        self.assertEqual(parse_number("-42"), -42.0)
        self.assertIsNone(parse_number("abc"))
        self.assertIsNone(parse_number(None))
        self.assertIsNone(parse_number(""))

    def test_sanitize_filename(self) -> None:
        self.assertEqual(sanitize_filename("hello<world>.txt"), "hello_world_.txt")
        self.assertEqual(sanitize_filename("", "fallback"), "fallback")
        self.assertEqual(sanitize_filename(None, "default"), "default")

    def test_chunk_text(self) -> None:
        chunks = chunk_text("abcdefghij", 3)
        self.assertEqual(chunks, ["abc", "def", "ghi", "j"])
        self.assertEqual(chunk_text("", 5), [])

    def test_ensure_directory(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            new_dir = Path(td) / "sub" / "dir"
            result = ensure_directory(new_dir)
            self.assertTrue(result.exists())
            self.assertTrue(result.is_dir())

    def test_unique_ordered(self) -> None:
        result = unique_ordered(["a", "b", "a", "c", "b"])
        self.assertEqual(result, ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
