"""Tests for configuration loading and normalization."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.utils.config_loader import load_config


class ConfigLoaderTests(unittest.TestCase):
    def test_load_config_normalizes_values(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lucas-config-") as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            profiles_path = Path(temp_dir) / "device_profiles.yaml"

            config_path.write_text(
                json.dumps(
                    {
                        "browser": {"max_tabs": 0, "navigation_timeout_ms": 1000},
                        "self_healing": {"cache_ttl_hours": 0, "similarity_threshold": 999},
                        "device_profile": {"name": "desktop_chrome"},
                    }
                ),
                encoding="utf-8",
            )
            profiles_path.write_text(
                json.dumps(
                    {
                        "default_profile": "desktop_chrome",
                        "profiles": {
                            "desktop_chrome": {
                                "user_agent": "UA",
                                "viewport": {"width": 1000, "height": 700},
                                "locale": "en-US",
                                "timezone_id": "UTC",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            cfg = load_config(str(config_path))

            self.assertEqual(cfg["browser"]["max_tabs"], 1)
            self.assertEqual(cfg["browser"]["navigation_timeout_ms"], 5000)
            self.assertEqual(cfg["self_healing"]["cache_ttl_hours"], 1)
            self.assertEqual(cfg["self_healing"]["similarity_threshold"], 20.0)
            self.assertEqual(cfg["resolved_device_profile"]["name"], "desktop_chrome")
            self.assertEqual(cfg["resolved_device_profile"]["user_agent"], "UA")


if __name__ == "__main__":
    unittest.main()
