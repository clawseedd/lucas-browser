"""Playwright browser lifecycle management optimized for constrained environments."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from src.core.network_monitor import NetworkMonitor
from src.core.page_pool import PagePool
from src.core.resource_monitor import ResourceMonitor
from src.core.session_manager import SessionManager
from src.stealth.stealth_engine import StealthEngine
from src.utils.helpers import ensure_directory
from src.utils.logger import get_logger


class BrowserManager:
    """Manage Playwright browser, context, and pooled pages."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)

        self.browser_config = config["browser"]
        self.performance_config = config["performance"]
        self.sessions_config = config["sessions"]
        self.device_profile = config["resolved_device_profile"]

        self.playwright = None
        self.browser = None
        self.context = None

        self.page_pool = PagePool(max_pages=self.browser_config.get("max_tabs", 2))
        self.network_monitor = NetworkMonitor(max_events=600)
        self.resource_monitor = ResourceMonitor()
        self.session_manager = SessionManager(self.sessions_config.get("directory", "./cache/sessions"))
        self.stealth_engine = StealthEngine(config["stealth"], self.device_profile)

        self._route_installed_pages: set[int] = set()

    async def _import_playwright(self):
        try:
            from playwright.async_api import async_playwright
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "playwright is not installed. Run `python3 -m pip install -r requirements.txt` and `python3 -m playwright install chromium`."
            ) from exc
        return async_playwright

    def _launch_options(self) -> dict[str, Any]:
        downloads_dir = ensure_directory(self.config["extraction"]["download_directory"])
        ensure_directory(self.browser_config.get("user_data_dir", "./cache/browser-profile"))

        options: dict[str, Any] = {
            "headless": bool(self.browser_config.get("headless", True)),
            "args": list(self.browser_config.get("launch_args", [])),
            "downloads_path": str(downloads_dir),
        }

        executable_path = self.browser_config.get("executable_path")
        if executable_path and Path(executable_path).exists():
            options["executable_path"] = executable_path

        # Session persistence is handled by storage-state files.
        options["chromium_sandbox"] = False

        return options

    def _context_options(self, storage_state_path: str | None = None) -> dict[str, Any]:
        options: dict[str, Any] = {
            "accept_downloads": True,
            "locale": self.device_profile.get("locale", "en-US"),
            "timezone_id": self.device_profile.get("timezone_id", "UTC"),
            "user_agent": self.device_profile.get("user_agent"),
            "viewport": self.device_profile.get("viewport"),
            "extra_http_headers": self.device_profile.get("extra_http_headers", {}),
            "ignore_https_errors": True,
        }

        if storage_state_path:
            options["storage_state"] = storage_state_path

        return options

    async def start(self, storage_state_path: str | None = None) -> None:
        if self.browser is not None and self.context is not None:
            return

        async_playwright = await self._import_playwright()
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(**self._launch_options())
        await self._create_context(storage_state_path=storage_state_path)

        self.logger.info("Browser started", extra={"max_tabs": self.browser_config.get("max_tabs")})

    async def _create_context(self, storage_state_path: str | None = None) -> None:
        if self.context is not None:
            await self.page_pool.close_all()
            await self.context.close()

        self.context = await self.browser.new_context(**self._context_options(storage_state_path))
        await self.stealth_engine.apply_to_context(self.context)
        self._route_installed_pages.clear()

    async def restart_with_session(self, session_name: str) -> bool:
        state_path = self.session_manager.get(session_name)
        if not state_path:
            return False

        await self.start()
        await self._create_context(storage_state_path=state_path)
        return True

    async def stop(self) -> None:
        await self.page_pool.close_all()

        if self.context is not None:
            await self.context.close()
            self.context = None

        if self.browser is not None:
            await self.browser.close()
            self.browser = None

        if self.playwright is not None:
            await self.playwright.stop()
            self.playwright = None

        self.logger.info("Browser stopped")

    async def _install_routing(self, page: Any) -> None:
        page_id = id(page)
        if page_id in self._route_installed_pages:
            return

        if not self.performance_config.get("enable_request_blocking", True):
            self._route_installed_pages.add(page_id)
            return

        blocked_types = set(self.performance_config.get("block_resource_types", ["image", "media", "font"]))
        blocked_domains = [item.lower() for item in self.performance_config.get("block_ad_domains", [])]

        async def route_handler(route, request):
            resource_type = request.resource_type
            url = request.url.lower()
            if resource_type in blocked_types:
                await route.abort()
                return
            if any(domain in url for domain in blocked_domains):
                await route.abort()
                return
            await route.continue_()

        await page.route("**/*", route_handler)
        self._route_installed_pages.add(page_id)

    async def _configure_page(self, page: Any) -> None:
        page.set_default_navigation_timeout(int(self.browser_config.get("navigation_timeout_ms", 45000)))
        page.set_default_timeout(int(self.browser_config.get("default_timeout_ms", 12000)))

        await self._install_routing(page)
        self.network_monitor.attach(page)

    async def get_page(self, tab_id: str = "default"):
        await self.start()

        page = self.page_pool.get(tab_id)
        if page is not None:
            return page

        page = await self.context.new_page()
        await self._configure_page(page)

        evicted_pages = await self.page_pool.put(tab_id, page)
        for old_page in evicted_pages:
            try:
                await old_page.close()
            except Exception:
                pass

        return page

    async def close_tab(self, tab_id: str) -> None:
        await self.page_pool.close_tab(tab_id)

    async def navigate(self, url: str, tab_id: str = "default", wait_until: str = "load") -> dict[str, Any]:
        page = await self.get_page(tab_id)
        response = await page.goto(url, wait_until=wait_until)

        wait_after_ms = int(self.performance_config.get("wait_after_navigation_ms", 0))
        if wait_after_ms > 0:
            await asyncio.sleep(wait_after_ms / 1000)

        return {
            "success": True,
            "tab_id": tab_id,
            "url": page.url,
            "status": response.status if response else None,
            "ok": response.ok if response else True,
            "resources": self.resource_monitor.snapshot(),
        }

    async def save_session(self, name: str) -> str:
        if self.context is None:
            await self.start()
        return await self.session_manager.save(self.context, name)

    async def load_session(self, name: str) -> dict[str, Any]:
        loaded = await self.restart_with_session(name)
        return {"success": loaded, "session_name": name}
