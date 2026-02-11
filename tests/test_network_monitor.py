"""Tests for network monitor."""

from __future__ import annotations

import unittest

from src.core.network_monitor import NetworkMonitor


class NetworkMonitorTests(unittest.TestCase):
    def test_max_events_clamped(self) -> None:
        monitor = NetworkMonitor(max_events=10)
        self.assertEqual(monitor.max_events, 100)

    def test_get_recent_calls_empty(self) -> None:
        monitor = NetworkMonitor()
        self.assertEqual(monitor.get_recent_calls(), [])

    def test_get_recent_calls_limit(self) -> None:
        monitor = NetworkMonitor()
        for i in range(5):
            monitor.events.append({"kind": "request", "index": i})
        result = monitor.get_recent_calls(limit=2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["index"], 3)
        self.assertEqual(result[1]["index"], 4)


if __name__ == "__main__":
    unittest.main()
