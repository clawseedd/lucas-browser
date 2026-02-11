"""Browser fingerprint profile helpers."""

from __future__ import annotations

from typing import Any, Dict


class FingerprintManager:
    """Generate stealth script overrides from device profiles."""

    def __init__(self, device_profile: Dict[str, Any], navigator_overrides: Dict[str, Any]):
        self.device_profile = device_profile
        self.navigator_overrides = navigator_overrides

    def build_init_script(self) -> str:
        overrides = {
            "hardwareConcurrency": self.navigator_overrides.get("hardware_concurrency", 4),
            "deviceMemory": self.navigator_overrides.get("device_memory", 4),
            "platform": self.navigator_overrides.get("platform", "Linux armv8l"),
            "language": self.navigator_overrides.get("language", "en-US"),
        }

        script = f"""
        Object.defineProperty(navigator, 'webdriver', {{ get: () => false }});
        Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {int(overrides['hardwareConcurrency'])} }});
        Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {int(overrides['deviceMemory'])} }});
        Object.defineProperty(navigator, 'platform', {{ get: () => '{overrides['platform']}' }});
        Object.defineProperty(navigator, 'language', {{ get: () => '{overrides['language']}' }});
        Object.defineProperty(navigator, 'languages', {{ get: () => ['{overrides['language']}', 'en'] }});
        window.chrome = window.chrome || {{ runtime: {{}} }};
        """
        return script
