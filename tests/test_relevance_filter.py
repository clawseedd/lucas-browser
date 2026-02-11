"""Tests for relevance scoring logic."""

from __future__ import annotations

import unittest

from src.intelligence.relevance_filter import RelevanceFilter


class RelevanceFilterTests(unittest.TestCase):
    def test_score_text(self) -> None:
        high = RelevanceFilter._score_text(
            "This section describes product pricing and monthly subscription plan details for enterprise users.",
            ["pricing", "subscription"],
        )
        low = RelevanceFilter._score_text("Tiny", ["pricing"])
        self.assertGreater(high, low)


if __name__ == "__main__":
    unittest.main()
