"""Tests for rule-based NLQ parsing."""

from __future__ import annotations

import unittest

from src.intelligence.nlq_parser import NLQParser


class NLQParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = NLQParser()

    def test_infer_type(self) -> None:
        self.assertEqual(self.parser.infer_type("product_price"), "number")
        self.assertEqual(self.parser.infer_type("results_table"), "table")
        self.assertEqual(self.parser.infer_type("cta_button"), "button")

    def test_parse_field_builds_selectors(self) -> None:
        parsed = self.parser.parse_field("product_price", {})
        self.assertIn(".price", parsed.selectors)
        self.assertIn("[data-price]", parsed.selectors)
        self.assertEqual(parsed.field_type, "number")


if __name__ == "__main__":
    unittest.main()
