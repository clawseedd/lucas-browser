"""Tests for session manager."""

from __future__ import annotations

import tempfile
import unittest

from src.core.session_manager import SessionManager


class SessionManagerTests(unittest.TestCase):
    def test_session_path_sanitizes_name(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            mgr = SessionManager(td)
            path = mgr.session_path("../etc/passwd")
            self.assertEqual(path.name, "etcpasswd.json")

    def test_session_path_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            mgr = SessionManager(td)
            path = mgr.session_path("!!!!")
            self.assertEqual(path.name, "default.json")

    def test_get_missing_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            mgr = SessionManager(td)
            self.assertIsNone(mgr.get("nonexistent"))

    def test_get_existing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            mgr = SessionManager(td)
            path = mgr.session_path("test")
            path.write_text("{}", encoding="utf-8")
            self.assertEqual(mgr.get("test"), str(path))


if __name__ == "__main__":
    unittest.main()
