"""Tests for fingerprint manager."""

from __future__ import annotations

import unittest

from src.stealth.fingerprint_manager import FingerprintManager


class FingerprintManagerTests(unittest.TestCase):
    def test_build_init_script_contains_overrides(self) -> None:
        mgr = FingerprintManager(
            device_profile={},
            navigator_overrides={
                "hardware_concurrency": 8,
                "device_memory": 16,
                "platform": "Linux x86_64",
                "language": "de-DE",
            },
        )
        script = mgr.build_init_script()
        self.assertIn("8", script)
        self.assertIn("16", script)
        self.assertIn("Linux x86_64", script)
        self.assertIn("de-DE", script)
        self.assertIn("webdriver", script)

    def test_script_escapes_injection(self) -> None:
        """Verify that malicious platform values are safely JSON-escaped."""
        mgr = FingerprintManager(
            device_profile={},
            navigator_overrides={
                "platform": "'; alert('xss'); '",
                "language": "en-US",
            },
        )
        script = mgr.build_init_script()
        # json.dumps wraps the string in double quotes, so there is no
        # unquoted single-quote breakout.  The getter returns a harmless
        # string literal, never executable code.
        self.assertIn('"', script)  # value is double-quoted by json.dumps
        # The raw single-quote breakout pattern should not appear unescaped
        self.assertNotIn("get: () => '", script)


if __name__ == "__main__":
    unittest.main()
