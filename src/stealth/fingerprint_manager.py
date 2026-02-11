"""Browser fingerprint profile helpers."""

from __future__ import annotations

import json
import random
from typing import Any


# Modern, realistic browser profiles used when no explicit overrides are supplied.
# Each entry mimics a genuine Chrome or Edge installation as of 2025.
MODERN_PROFILES: list[dict[str, Any]] = [
    {
        "platform": "Win32",
        "language": "en-US",
        "hardware_concurrency": 8,
        "device_memory": 8,
        "vendor": "Google Inc.",
        "renderer": "ANGLE (Intel, Intel(R) UHD Graphics 630, OpenGL 4.5)",
        "user_agent_hint": "Chrome/131",
    },
    {
        "platform": "Win32",
        "language": "en-US",
        "hardware_concurrency": 16,
        "device_memory": 16,
        "vendor": "Google Inc.",
        "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060, OpenGL 4.5)",
        "user_agent_hint": "Chrome/130",
    },
    {
        "platform": "Win32",
        "language": "en-US",
        "hardware_concurrency": 12,
        "device_memory": 16,
        "vendor": "Google Inc.",
        "renderer": "ANGLE (AMD, AMD Radeon RX 6700 XT, OpenGL 4.5)",
        "user_agent_hint": "Edge/131",
    },
    {
        "platform": "MacIntel",
        "language": "en-US",
        "hardware_concurrency": 10,
        "device_memory": 8,
        "vendor": "Google Inc.",
        "renderer": "ANGLE (Apple, Apple M1 Pro, OpenGL 4.1)",
        "user_agent_hint": "Chrome/131",
    },
    {
        "platform": "MacIntel",
        "language": "en-US",
        "hardware_concurrency": 12,
        "device_memory": 16,
        "vendor": "Google Inc.",
        "renderer": "ANGLE (Apple, Apple M2 Max, OpenGL 4.1)",
        "user_agent_hint": "Chrome/130",
    },
    {
        "platform": "Linux x86_64",
        "language": "en-US",
        "hardware_concurrency": 8,
        "device_memory": 8,
        "vendor": "Google Inc.",
        "renderer": "ANGLE (Mesa, Intel UHD Graphics 770, OpenGL 4.6)",
        "user_agent_hint": "Chrome/131",
    },
    {
        "platform": "Win32",
        "language": "en-GB",
        "hardware_concurrency": 8,
        "device_memory": 8,
        "vendor": "Google Inc.",
        "renderer": "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics, OpenGL 4.5)",
        "user_agent_hint": "Edge/130",
    },
    {
        "platform": "Win32",
        "language": "en-US",
        "hardware_concurrency": 6,
        "device_memory": 8,
        "vendor": "Google Inc.",
        "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650, OpenGL 4.5)",
        "user_agent_hint": "Chrome/129",
    },
]


class FingerprintManager:
    """Generate stealth script overrides from device profiles."""

    def __init__(self, device_profile: dict[str, Any], navigator_overrides: dict[str, Any]):
        self.device_profile = device_profile
        self.navigator_overrides = navigator_overrides
        # Pick a random modern profile at construction time so it stays
        # consistent for the lifetime of the browser context.
        self._modern_profile: dict[str, Any] = random.choice(MODERN_PROFILES)

    def _get(self, key: str, fallback: Any = None) -> Any:
        """Return an override value, falling back to the random modern profile."""
        value = self.navigator_overrides.get(key)
        if value is not None:
            return value
        return self._modern_profile.get(key, fallback)

    def build_init_script(self) -> str:
        hw_concurrency = int(self._get("hardware_concurrency", 4))
        device_memory = int(self._get("device_memory", 4))
        # Use json.dumps to safely escape string values against JS injection
        platform = json.dumps(str(self._get("platform", "Win32")))
        language = json.dumps(str(self._get("language", "en-US")))
        vendor = json.dumps(str(self._get("vendor", "Google Inc.")))
        renderer = json.dumps(str(self._get("renderer", "")))

        script = f"""
        // --- navigator overrides ---
        Object.defineProperty(navigator, 'webdriver', {{ get: () => false }});
        Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {hw_concurrency} }});
        Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {device_memory} }});
        Object.defineProperty(navigator, 'platform', {{ get: () => {platform} }});
        Object.defineProperty(navigator, 'language', {{ get: () => {language} }});
        Object.defineProperty(navigator, 'languages', {{ get: () => [{language}, 'en'] }});
        Object.defineProperty(navigator, 'vendor', {{ get: () => {vendor} }});
        Object.defineProperty(navigator, 'maxTouchPoints', {{ get: () => 0 }});

        // --- chrome object ---
        window.chrome = window.chrome || {{}};
        window.chrome.runtime = window.chrome.runtime || {{}};
        window.chrome.loadTimes = window.chrome.loadTimes || function() {{}};
        window.chrome.csi = window.chrome.csi || function() {{}};

        // --- permissions ---
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications'
                ? Promise.resolve({{ state: Notification.permission }})
                : originalQuery(parameters)
        );

        // --- plugins ---
        Object.defineProperty(navigator, 'plugins', {{
            get: () => [
                {{ name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }},
                {{ name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' }},
                {{ name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }}
            ]
        }});
        Object.defineProperty(navigator, 'mimeTypes', {{
            get: () => [
                {{ type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format' }},
                {{ type: 'application/x-nacl', suffixes: '', description: 'Native Client Executable' }}
            ]
        }});

        // --- WebGL renderer spoofing ---
        (function() {{
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(param) {{
                if (param === 37445) return {vendor};
                if (param === 37446) return {renderer};
                return getParameter.call(this, param);
            }};
            if (typeof WebGL2RenderingContext !== 'undefined') {{
                const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
                WebGL2RenderingContext.prototype.getParameter = function(param) {{
                    if (param === 37445) return {vendor};
                    if (param === 37446) return {renderer};
                    return getParameter2.call(this, param);
                }};
            }}
        }})();
        """
        return script
