"""Configuration loading and validation."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency in tests
    yaml = None


DEFAULT_CONFIG: dict[str, Any] = {
    "browser": {
        "headless": True,
        "executable_path": "",
        "max_tabs": 2,
        "navigation_timeout_ms": 45000,
        "default_timeout_ms": 12000,
        "user_data_dir": "./cache/browser-profile",
        "launch_args": [
            "--single-process",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-background-networking",
            "--disable-extensions",
            "--disable-blink-features=AutomationControlled",
        ],
    },
    "performance": {
        "enable_request_blocking": True,
        "block_resource_types": ["image", "media", "font"],
        "block_ad_domains": [],
        "wait_after_navigation_ms": 250,
        "low_memory_mode": True,
    },
    "stealth": {
        "enabled": True,
        "delay_range_ms": {"min": 35, "max": 150},
        "navigator_overrides": {
            "hardware_concurrency": 4,
            "device_memory": 4,
            "platform": "Linux armv8l",
            "language": "en-US",
        },
    },
    "self_healing": {
        "enabled": True,
        "timeout_ms": 1500,
        "cache_file": "./cache/selectors.json",
        "cache_ttl_hours": 168,
        "max_candidates": 1800,
        "similarity_threshold": 3.5,
        "strategies": ["direct", "cache", "text", "semantic"],
    },
    "sessions": {
        "enabled": True,
        "directory": "./cache/sessions",
        "default_name": "default",
        "auto_save_after_login": True,
    },
    "extraction": {
        "download_directory": "./downloads",
        "max_table_rows": 1000,
        "max_text_length": 12000,
        "stream_chunk_chars": 1800,
        "max_stream_chunks": 12,
    },
    "device_profile": {"name": "raspberry_pi_4"},
    "logging": {"level": "INFO", "file": "./logs/agent.log"},
}

DEFAULT_DEVICE_PROFILES: dict[str, Any] = {
    "default_profile": "raspberry_pi_4",
    "profiles": {
        "raspberry_pi_4": {
            "user_agent": "Mozilla/5.0 (X11; Linux armv8l) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "viewport": {"width": 1366, "height": 768},
            "locale": "en-US",
            "timezone_id": "UTC",
            "extra_http_headers": {"Accept-Language": "en-US,en;q=0.9"},
        }
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _parse_text(raw: str, file_path: Path) -> dict[str, Any]:
    raw = raw.strip()
    if not raw:
        return {}

    if yaml is not None:
        loaded = yaml.safe_load(raw)
        return loaded or {}

    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError as exc:  # pragma: no cover
        raise RuntimeError(
            f"PyYAML not installed and {file_path} is not JSON-compatible YAML. Install PyYAML or convert to JSON-style YAML."
        ) from exc

    return loaded or {}


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _parse_text(path.read_text(encoding="utf-8"), path)


def _bounded_int(value: Any, default: int, min_value: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(min_value, parsed)


def _bounded_float(value: Any, default: float, min_value: float, max_value: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return max(min_value, min(max_value, parsed))


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    merged = _deep_merge(DEFAULT_CONFIG, config)

    merged["browser"]["max_tabs"] = _bounded_int(merged["browser"].get("max_tabs"), 2, 1)
    merged["browser"]["navigation_timeout_ms"] = _bounded_int(
        merged["browser"].get("navigation_timeout_ms"), 45000, 5000
    )
    merged["browser"]["default_timeout_ms"] = _bounded_int(
        merged["browser"].get("default_timeout_ms"), 12000, 1000
    )

    merged["self_healing"]["timeout_ms"] = _bounded_int(
        merged["self_healing"].get("timeout_ms"), 1500, 250
    )
    merged["self_healing"]["cache_ttl_hours"] = _bounded_int(
        merged["self_healing"].get("cache_ttl_hours"), 168, 1
    )
    merged["self_healing"]["similarity_threshold"] = _bounded_float(
        merged["self_healing"].get("similarity_threshold"), 3.5, 0.5, 20.0
    )

    merged["extraction"]["max_table_rows"] = _bounded_int(
        merged["extraction"].get("max_table_rows"), 1000, 10
    )
    merged["extraction"]["max_text_length"] = _bounded_int(
        merged["extraction"].get("max_text_length"), 12000, 500
    )
    merged["extraction"]["stream_chunk_chars"] = _bounded_int(
        merged["extraction"].get("stream_chunk_chars"), 1800, 200
    )
    merged["extraction"]["max_stream_chunks"] = _bounded_int(
        merged["extraction"].get("max_stream_chunks"), 12, 1
    )

    delay = merged["stealth"].get("delay_range_ms", {})
    min_delay = _bounded_int(delay.get("min"), 35, 0)
    max_delay = _bounded_int(delay.get("max"), 150, 0)
    if max_delay < min_delay:
        min_delay, max_delay = max_delay, min_delay
    merged["stealth"]["delay_range_ms"] = {"min": min_delay, "max": max_delay}

    return merged


def load_config(config_path: str = "config/config.yaml") -> dict[str, Any]:
    config_file = Path(config_path).resolve()
    config_dir = config_file.parent

    loaded_config = _read_yaml(config_file)
    config = validate_config(loaded_config)

    profiles_file = (config_dir / "device_profiles.yaml").resolve()
    profiles_data = _deep_merge(DEFAULT_DEVICE_PROFILES, _read_yaml(profiles_file))

    selected_name = config.get("device_profile", {}).get("name") or profiles_data.get("default_profile")
    selected_profile = profiles_data.get("profiles", {}).get(selected_name)
    if selected_profile is None:
        default_name = profiles_data.get("default_profile")
        selected_profile = profiles_data.get("profiles", {}).get(default_name, {})
        selected_name = default_name

    config["paths"] = {
        "config": str(config_file),
        "config_dir": str(config_dir),
        "device_profiles": str(profiles_file),
    }
    config["resolved_device_profile"] = {"name": selected_name, **(selected_profile or {})}

    return config
