"""Browser fingerprint profile helpers."""

from __future__ import annotations

import json
from typing import Any


class FingerprintManager:
    """Generate stealth script overrides from device profiles."""

    def __init__(self, device_profile: dict[str, Any], navigator_overrides: dict[str, Any]):
        self.device_profile = device_profile
        self.navigator_overrides = navigator_overrides

    def build_init_script(self) -> str:
        hw_concurrency = int(self.navigator_overrides.get("hardware_concurrency", 4))
        device_memory = int(self.navigator_overrides.get("device_memory", 4))
        # Use json.dumps to safely escape string values against JS injection
        platform = json.dumps(str(self.navigator_overrides.get("platform", "Linux armv8l")))
        language = json.dumps(str(self.navigator_overrides.get("language", "en-US")))

        script = f"""
        Object.defineProperty(navigator, 'webdriver', {{ get: () => false }});
        Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {hw_concurrency} }});
        Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {device_memory} }});
        Object.defineProperty(navigator, 'platform', {{ get: () => {platform} }});
        Object.defineProperty(navigator, 'language', {{ get: () => {language} }});
        Object.defineProperty(navigator, 'languages', {{ get: () => [{language}, 'en'] }});
        window.chrome = window.chrome || {{ runtime: {{}} }};
        """
        return script
