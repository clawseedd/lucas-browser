"""Validate runtime config and print summary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.config_loader import load_config


def main() -> int:
    try:
        config = load_config(sys.argv[1] if len(sys.argv) > 1 else "config/config.yaml")
    except Exception as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, indent=2))
        return 1

    summary = {
        "max_tabs": config["browser"]["max_tabs"],
        "headless": config["browser"]["headless"],
        "device_profile": config["resolved_device_profile"]["name"],
        "download_directory": config["extraction"]["download_directory"],
        "resource_blocking": config["performance"]["enable_request_blocking"],
    }
    print(json.dumps({"valid": True, "summary": summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
