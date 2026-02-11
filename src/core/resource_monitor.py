"""Lightweight process resource monitoring."""

from __future__ import annotations

import os
from typing import Any, Dict


class ResourceMonitor:
    """Provide memory and CPU snapshots with optional psutil support."""

    def __init__(self):
        try:
            import psutil  # type: ignore

            self._process = psutil.Process(os.getpid())
            self._psutil = psutil
        except Exception:
            self._process = None
            self._psutil = None

    def snapshot(self) -> Dict[str, Any]:
        if self._process is None:
            return {"available": False}

        mem = self._process.memory_info()
        cpu = self._process.cpu_percent(interval=None)
        return {
            "available": True,
            "rss_mb": round(mem.rss / 1024 / 1024, 2),
            "vms_mb": round(mem.vms / 1024 / 1024, 2),
            "cpu_percent": cpu,
        }
