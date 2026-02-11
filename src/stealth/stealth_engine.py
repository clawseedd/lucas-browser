"""Stealth behavior utilities."""

from __future__ import annotations

from typing import Any

from src.stealth.fingerprint_manager import FingerprintManager
from src.utils.helpers import sleep_random


class StealthEngine:
    """Apply anti-bot evasions and human-like timing jitter."""

    def __init__(self, stealth_config: dict[str, Any], device_profile: dict[str, Any]):
        self.stealth_config = stealth_config
        self.enabled = bool(stealth_config.get("enabled", True))
        self.delay_range = stealth_config.get("delay_range_ms", {"min": 0, "max": 0})
        self.fingerprint = FingerprintManager(
            device_profile=device_profile,
            navigator_overrides=stealth_config.get("navigator_overrides", {}),
        )

    async def apply_to_context(self, context: Any) -> None:
        if not self.enabled:
            return
        await context.add_init_script(self.fingerprint.build_init_script())

    async def human_delay(self) -> None:
        if not self.enabled:
            return
        await sleep_random(int(self.delay_range.get("min", 0)), int(self.delay_range.get("max", 0)))
