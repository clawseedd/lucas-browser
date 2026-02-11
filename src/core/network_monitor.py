"""Network monitoring and API interception."""

from __future__ import annotations

from collections import deque
from typing import Any, Dict, Deque, List

from src.utils.helpers import utc_now_iso


class NetworkMonitor:
    """Capture request/response metadata for fetch/xhr calls."""

    def __init__(self, max_events: int = 500):
        self.max_events = max(100, int(max_events))
        self.events: Deque[Dict[str, Any]] = deque(maxlen=self.max_events)

    def attach(self, page: Any) -> None:
        page.on("request", self._on_request)
        page.on("response", self._on_response)

    def _on_request(self, request: Any) -> None:
        resource_type = request.resource_type
        if resource_type not in {"xhr", "fetch", "document"}:
            return
        self.events.append(
            {
                "kind": "request",
                "ts": utc_now_iso(),
                "method": request.method,
                "url": request.url,
                "resource_type": resource_type,
            }
        )

    def _on_response(self, response: Any) -> None:
        request = response.request
        resource_type = request.resource_type
        if resource_type not in {"xhr", "fetch", "document"}:
            return

        headers = response.headers
        content_type = headers.get("content-type", "")

        self.events.append(
            {
                "kind": "response",
                "ts": utc_now_iso(),
                "url": response.url,
                "status": response.status,
                "ok": response.ok,
                "resource_type": resource_type,
                "content_type": content_type,
            }
        )

    def get_recent_calls(self, limit: int = 50) -> List[Dict[str, Any]]:
        limit = max(1, int(limit))
        return list(self.events)[-limit:]
