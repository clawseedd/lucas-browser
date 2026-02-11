"""File downloading helpers for URL and page-selector workflows."""

from __future__ import annotations

import hashlib
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any, Dict, Optional

from src.utils.helpers import ensure_directory, sanitize_filename


class FileDownloader:
    """Download files in a deterministic way for scraping pipelines."""

    def __init__(self, download_directory: str):
        self.download_directory = ensure_directory(download_directory)

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file_obj:
            while True:
                chunk = file_obj.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()

    def _target_path(self, filename: str | None, url: str, subdirectory: str | None = None) -> Path:
        if not filename:
            parsed = urllib.parse.urlparse(url)
            filename = Path(parsed.path).name or f"download-{hash(url) & 0xFFFFF}.bin"

        safe_name = sanitize_filename(filename)
        directory = self.download_directory / sanitize_filename(subdirectory, "") if subdirectory else self.download_directory
        ensure_directory(directory)
        return directory / safe_name

    def download_url(
        self,
        url: str,
        filename: str | None = None,
        headers: dict[str, str] | None = None,
        subdirectory: str | None = None,
        timeout_sec: int = 120,
    ) -> Dict[str, Any]:
        target = self._target_path(filename, url, subdirectory=subdirectory)
        request = urllib.request.Request(url, headers=headers or {})

        with urllib.request.urlopen(request, timeout=timeout_sec) as response:
            target.write_bytes(response.read())
            content_type = response.headers.get("Content-Type")

        stat = target.stat()
        return {
            "success": True,
            "url": url,
            "path": str(target),
            "filename": target.name,
            "size_bytes": stat.st_size,
            "sha256": self._sha256(target),
            "content_type": content_type,
        }

    async def download_from_selector(
        self,
        page: Any,
        selector: str,
        filename: str | None = None,
        subdirectory: str | None = None,
    ) -> Dict[str, Any]:
        href = await page.get_attribute(selector, "href")
        if not href:
            href = await page.get_attribute(selector, "src")
        if not href:
            raise ValueError(f"No href/src attribute found for selector: {selector}")

        absolute_url = urllib.parse.urljoin(page.url, href)

        cookies = await page.context.cookies()
        cookie_header = "; ".join(f"{item['name']}={item['value']}" for item in cookies)
        headers = {
            "Referer": page.url,
        }
        if cookie_header:
            headers["Cookie"] = cookie_header

        return self.download_url(
            absolute_url,
            filename=filename,
            headers=headers,
            subdirectory=subdirectory,
        )
