"""Tests for self-healing scoring and cache TTL."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.intelligence.self_healing import SelfHealer


class SelfHealingTests(unittest.TestCase):
    def test_score_candidate(self) -> None:
        score = SelfHealer._score_candidate(
            {
                "id": "product-price",
                "class_name": "price amount",
                "name": "price",
                "role": "button",
                "text": "Buy now for $10",
                "tag": "button",
                "visible": True,
            },
            tokens=["product", "price", "button"],
            text_hint="buy",
        )
        self.assertGreater(score, 7.0)

    def test_cache_ttl(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lucas-cache-") as temp_dir:
            cache_file = Path(temp_dir) / "selectors.json"
            stale = (datetime.now(timezone.utc) - timedelta(hours=999)).isoformat()
            cache_file.write_text(
                json.dumps(
                    {
                        "https://example.com::price": {
                            "selector": ".price",
                            "updated_at": stale,
                        }
                    }
                ),
                encoding="utf-8",
            )

            healer = SelfHealer(
                {
                    "enabled": True,
                    "cache_file": str(cache_file),
                    "cache_ttl_hours": 24,
                }
            )

            self.assertIsNone(healer.recall("https://example.com", "price"))


if __name__ == "__main__":
    unittest.main()
