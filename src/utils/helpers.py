"""Helper utilities for extraction and runtime behavior."""

from __future__ import annotations

import asyncio
import math
import random
import re
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_space(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def parse_number(value: str | None) -> float | None:
    text = normalize_space(value).replace(",", "")
    if not text:
        return None

    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None

    try:
        num = float(match.group(0))
    except ValueError:
        return None

    if math.isfinite(num):
        return num
    return None


def sanitize_filename(name: str, fallback: str = "download") -> str:
    clean = re.sub(r"[<>:\"/\\|?*\x00-\x1F]", "_", name or fallback)
    clean = normalize_space(clean)
    return clean[:180] or fallback


async def sleep_random(min_ms: int, max_ms: int) -> None:
    if max_ms < min_ms:
        min_ms, max_ms = max_ms, min_ms

    if max_ms <= 0:
        return

    delay_ms = random.randint(max(0, min_ms), max(0, max_ms))
    await asyncio.sleep(delay_ms / 1000)


def chunk_text(text: str, chunk_size: int) -> list[str]:
    chunk_size = max(1, int(chunk_size))
    text = normalize_space(text)
    return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]


def ensure_directory(path: str | Path) -> Path:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def unique_ordered(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output
