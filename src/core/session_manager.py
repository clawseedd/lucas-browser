"""Persistent browser session management."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.utils.helpers import ensure_directory


class SessionManager:
    """Save and load Playwright storage states for login reuse."""

    def __init__(self, directory: str):
        self.directory = ensure_directory(directory)

    def session_path(self, name: str) -> Path:
        safe = "".join(ch for ch in name if ch.isalnum() or ch in {"-", "_"}) or "default"
        return self.directory / f"{safe}.json"

    async def save(self, context, name: str) -> str:
        path = self.session_path(name)
        await context.storage_state(path=str(path))
        return str(path)

    def get(self, name: str) -> Optional[str]:
        path = self.session_path(name)
        if path.exists():
            return str(path)
        return None
