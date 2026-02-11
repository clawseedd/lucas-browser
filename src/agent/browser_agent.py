"""High-level BrowserAgent interface for OpenClaw tasks."""

from __future__ import annotations

import asyncio
from typing import Any

from src.actions.form_filler import FormFiller
from src.actions.interaction_handler import InteractionHandler
from src.actions.scroll_handler import ScrollHandler
from src.core.browser_manager import BrowserManager
from src.core.tab_orchestrator import TabOrchestrator
from src.extractors.content_extractor import ContentExtractor
from src.extractors.content_previewer import ContentPreviewer
from src.extractors.file_downloader import FileDownloader
from src.extractors.streaming_extractor import StreamingExtractor
from src.extractors.structure_analyzer import StructureAnalyzer
from src.extractors.table_extractor import TableExtractor
from src.intelligence.relevance_filter import RelevanceFilter
from src.intelligence.self_healing import SelfHealer
from src.utils.config_loader import load_config
from src.utils.logger import get_logger, setup_logging


class BrowserAgent:
    """Coordinate Playwright browsing, extraction, and scraping actions."""

    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = load_config(config_path)
        setup_logging(self.config.get("logging", {}))
        self.logger = get_logger(__name__)

        self.browser_manager = BrowserManager(self.config)

        self_healing_cfg = self.config.get("self_healing", {})
        extraction_cfg = self.config.get("extraction", {})

        self.self_healer = SelfHealer(self_healing_cfg)
        self.content_extractor = ContentExtractor(
            self_healer=self.self_healer,
            max_text_length=extraction_cfg.get("max_text_length", 12000),
            max_table_rows=extraction_cfg.get("max_table_rows", 1000),
        )
        self.table_extractor = TableExtractor(max_table_rows=extraction_cfg.get("max_table_rows", 1000))
        self.structure_analyzer = StructureAnalyzer(self.self_healer)
        self.file_downloader = FileDownloader(download_directory=extraction_cfg.get("download_directory", "./downloads"))
        self.content_previewer = ContentPreviewer()
        self.streaming_extractor = StreamingExtractor(
            chunk_chars=extraction_cfg.get("stream_chunk_chars", 1800),
            max_chunks=extraction_cfg.get("max_stream_chunks", 12),
        )
        self.relevance_filter = RelevanceFilter()
        self.form_filler = FormFiller()
        self.scroll_handler = ScrollHandler()
        delay_cfg = self.config.get("stealth", {}).get("delay_range_ms", {"min": 0, "max": 0})
        self.interactions = InteractionHandler(delay_cfg.get("min", 0), delay_cfg.get("max", 0))
        self.tab_orchestrator = TabOrchestrator(self)

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.stop()

    async def start(self) -> None:
        await self.browser_manager.start()

    async def stop(self) -> None:
        await self.browser_manager.stop()

    async def navigate(self, url: str, tab_id: str = "default", wait_until: str = "domcontentloaded") -> dict[str, Any]:
        return await self.browser_manager.navigate(url, tab_id=tab_id, wait_until=wait_until)

    async def get_page(self, tab_id: str = "default"):
        return await self.browser_manager.get_page(tab_id)

    async def extract_with_nlq(self, query: dict[str, Any], tab_id: str = "default") -> dict[str, Any]:
        page = await self.get_page(tab_id)
        return await self.content_extractor.extract_with_nlq(page, query)

    async def preview_content(self, tab_id: str = "default") -> dict[str, Any]:
        page = await self.get_page(tab_id)
        result = await self.content_previewer.preview(page)
        return {"success": True, **result}

    async def extract_relevant(
        self,
        keywords: list[str] | None = None,
        min_score: float = 0.6,
        max_items: int = 25,
        tab_id: str = "default",
    ) -> dict[str, Any]:
        page = await self.get_page(tab_id)
        items = await self.relevance_filter.filter_page_elements(
            page,
            keywords=keywords,
            min_score=min_score,
            max_items=max_items,
        )
        return {"success": True, "items": items, "count": len(items)}

    async def stream_extract(
        self,
        max_tokens: int = 4000,
        chars_per_token: float = 4.0,
        selector: str = "main, article, body",
        tab_id: str = "default",
    ) -> dict[str, Any]:
        page = await self.get_page(tab_id)
        return await self.streaming_extractor.extract_with_budget(
            page,
            max_tokens=max_tokens,
            chars_per_token=chars_per_token,
            selector=selector,
        )

    async def extract_tables(self, selector: str = "table", tab_id: str = "default") -> dict[str, Any]:
        page = await self.get_page(tab_id)
        tables = await self.table_extractor.extract_tables(page, selector)
        return {"success": True, "selector": selector, "count": len(tables), "tables": tables}

    async def capture_structure(
        self,
        selector: str,
        tab_id: str = "default",
        logical_name: str = "target",
        text_hint: str = "",
        semantic_hint: str = "",
    ) -> dict[str, Any]:
        page = await self.get_page(tab_id)
        return await self.structure_analyzer.capture_structure(
            page,
            selector,
            logical_name=logical_name,
            text_hint=text_hint,
            semantic_hint=semantic_hint,
        )

    async def download_file(
        self,
        tab_id: str = "default",
        url: str | None = None,
        selector: str | None = None,
        filename: str | None = None,
        subdirectory: str | None = None,
    ) -> dict[str, Any]:
        if not url and not selector:
            raise ValueError("download_file requires `url` or `selector`")

        if url:
            return self.file_downloader.download_url(url, filename=filename, subdirectory=subdirectory)

        if selector is None:
            raise ValueError("download_file requires `url` or `selector`")

        page = await self.get_page(tab_id)
        return await self.file_downloader.download_from_selector(
            page,
            selector=selector,
            filename=filename,
            subdirectory=subdirectory,
        )

    async def login(
        self,
        url: str,
        username_selector: str,
        username: str,
        password_selector: str,
        password: str,
        submit_selector: str,
        session_name: str = "default",
        tab_id: str = "default",
    ) -> dict[str, Any]:
        page = await self.get_page(tab_id)
        await page.goto(url, wait_until="domcontentloaded")
        await page.locator(username_selector).first.fill(username)
        await page.locator(password_selector).first.fill(password)
        await page.locator(submit_selector).first.click()

        # Let redirects/cookies settle.
        await asyncio.sleep(1.5)

        session_path = await self.browser_manager.save_session(session_name)
        return {
            "success": True,
            "session_name": session_name,
            "session_path": session_path,
            "current_url": page.url,
        }

    async def load_session(self, session_name: str = "default") -> dict[str, Any]:
        return await self.browser_manager.load_session(session_name)

    async def click(self, selector: str, tab_id: str = "default") -> dict[str, Any]:
        page = await self.get_page(tab_id)
        return await self.interactions.click(page, selector)

    async def type_text(
        self,
        selector: str,
        text: str,
        clear_first: bool = True,
        tab_id: str = "default",
    ) -> dict[str, Any]:
        page = await self.get_page(tab_id)
        return await self.interactions.type_text(page, selector, text, clear_first=clear_first)

    async def screenshot(self, path: str, full_page: bool = False, tab_id: str = "default") -> dict[str, Any]:
        page = await self.get_page(tab_id)
        await page.screenshot(path=path, full_page=full_page)
        return {"success": True, "path": path, "full_page": full_page}

    async def detect_forms(self, tab_id: str = "default") -> dict[str, Any]:
        page = await self.get_page(tab_id)
        forms = await self.form_filler.detect_forms(page)
        return {"success": True, "forms": forms, "count": len(forms)}

    async def fill_form(
        self,
        field_values: dict[str, Any],
        form_selector: str | None = None,
        submit: bool = False,
        tab_id: str = "default",
    ) -> dict[str, Any]:
        page = await self.get_page(tab_id)
        return await self.form_filler.fill_form(page, field_values, form_selector=form_selector, submit=submit)

    async def auto_scroll(
        self,
        max_scrolls: int = 20,
        scroll_delay_sec: float = 0.8,
        stop_if_no_new_content: bool = True,
        tab_id: str = "default",
    ) -> dict[str, Any]:
        page = await self.get_page(tab_id)
        return await self.scroll_handler.auto_scroll(
            page,
            max_scrolls=max_scrolls,
            scroll_delay_sec=scroll_delay_sec,
            stop_if_no_new_content=stop_if_no_new_content,
        )

    async def get_network_calls(self, limit: int = 50) -> dict[str, Any]:
        calls = self.browser_manager.network_monitor.get_recent_calls(limit=limit)
        return {"success": True, "count": len(calls), "calls": calls}

    async def extract_parallel(
        self,
        urls: list[str],
        query: dict[str, Any],
        max_concurrent: int = 2,
    ) -> dict[str, Any]:
        results = await self.tab_orchestrator.extract_from_multiple_pages(
            urls,
            query=query,
            max_concurrent=max_concurrent,
        )
        return {
            "success": True,
            "count": len(results),
            "results": results,
        }

    async def run_task(self, task: dict[str, Any]) -> dict[str, Any]:
        started = self.browser_manager.resource_monitor.snapshot()
        results = []
        tab_id = task.get("tab_id", "default")

        await self.start()

        try:
            if task.get("url"):
                results.append({"step": "navigate", "result": await self.navigate(task["url"], tab_id=tab_id)})

            if task.get("query") or task.get("fields"):
                query = task.get("query") or {"fields": task.get("fields")}
                results.append({"step": "extract", "result": await self.extract_with_nlq(query, tab_id=tab_id)})

            for idx, action in enumerate(task.get("actions", [])):
                action_type = action.get("type")

                if action_type == "navigate":
                    payload = await self.navigate(action["url"], tab_id=action.get("tab_id", tab_id))
                elif action_type == "extract":
                    payload = await self.extract_with_nlq(action.get("query") or action.get("spec") or {}, tab_id=action.get("tab_id", tab_id))
                elif action_type == "extract_tables":
                    payload = await self.extract_tables(action.get("selector", "table"), tab_id=action.get("tab_id", tab_id))
                elif action_type == "capture_structure":
                    payload = await self.capture_structure(
                        action["selector"],
                        tab_id=action.get("tab_id", tab_id),
                        logical_name=action.get("logical_name", "target"),
                        text_hint=action.get("text_hint", ""),
                        semantic_hint=action.get("semantic_hint", ""),
                    )
                elif action_type == "download":
                    payload = await self.download_file(
                        tab_id=action.get("tab_id", tab_id),
                        url=action.get("url"),
                        selector=action.get("selector"),
                        filename=action.get("filename"),
                        subdirectory=action.get("subdirectory"),
                    )
                elif action_type == "preview":
                    payload = await self.preview_content(tab_id=action.get("tab_id", tab_id))
                elif action_type == "relevance_filter":
                    payload = await self.extract_relevant(
                        keywords=action.get("keywords"),
                        min_score=float(action.get("min_score", 0.6)),
                        max_items=int(action.get("max_items", 25)),
                        tab_id=action.get("tab_id", tab_id),
                    )
                elif action_type == "stream_extract":
                    payload = await self.stream_extract(
                        max_tokens=int(action.get("max_tokens", 4000)),
                        chars_per_token=float(action.get("chars_per_token", 4.0)),
                        selector=action.get("selector", "main, article, body"),
                        tab_id=action.get("tab_id", tab_id),
                    )
                elif action_type == "fill_form":
                    payload = await self.fill_form(
                        field_values=action.get("field_values", {}),
                        form_selector=action.get("form_selector"),
                        submit=bool(action.get("submit", False)),
                        tab_id=action.get("tab_id", tab_id),
                    )
                elif action_type == "auto_scroll":
                    payload = await self.auto_scroll(
                        max_scrolls=int(action.get("max_scrolls", 20)),
                        scroll_delay_sec=float(action.get("scroll_delay_sec", 0.8)),
                        stop_if_no_new_content=bool(action.get("stop_if_no_new_content", True)),
                        tab_id=action.get("tab_id", tab_id),
                    )
                elif action_type == "network_calls":
                    payload = await self.get_network_calls(limit=int(action.get("limit", 50)))
                elif action_type == "parallel_extract":
                    payload = await self.extract_parallel(
                        urls=list(action.get("urls", [])),
                        query=action.get("query", {}),
                        max_concurrent=int(action.get("max_concurrent", 2)),
                    )
                else:
                    payload = {
                        "success": False,
                        "error": f"Unsupported action type: {action_type}",
                    }

                results.append({"step": f"action_{idx}", "action": action_type, "result": payload})

            return {
                "success": True,
                "resources_before": started,
                "resources_after": self.browser_manager.resource_monitor.snapshot(),
                "results": results,
            }
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "results": results,
            }
        finally:
            if not task.get("keep_browser_open", False):
                await self.stop()
