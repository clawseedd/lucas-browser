# LUCAS Browser Skill (Python + Playwright)

Headless browser automation skill for OpenClaw, optimized for resource-tight systems such as Raspberry Pi 4.

This project uses Python + Playwright (Chromium) and provides deterministic, rule-based scraping behavior without LLM dependencies.

## Core Capabilities

- Self-Healing Selectors: selector cache + text/semantic fallback when selectors break.
- Natural Language Queries: field-name-driven extraction (`product_price`, `customer_rating`, etc.).
- Session Management: login once and persist storage state for later runs.
- Content Preview: lightweight page summary before full extraction.
- Relevance Filtering: keep only high-signal sections.
- Zero LLM Dependencies: all inference is local and rule-based.

## Performance Optimizations

- Raspberry Pi 4 Optimized: single-process Chromium flags and low-memory defaults.
- Smart Caching: selector cache with 7-day TTL (`cache_ttl_hours: 168`).
- Resource Blocking: block images/media/fonts and ad domains.
- Streaming Extraction: incremental chunked extraction under token budgets.
- Page Pooling: LRU page reuse with max tab limits.

## Advanced Features

- Multi-Tab Orchestration: bounded parallel extraction across URLs.
- Form Auto-Fill: detect/fill inputs, selects, checkboxes.
- Infinite Scroll: auto-scroll until no new content.
- Network Monitoring: capture request/response metadata for API calls.
- Anti-Bot Evasion: navigator fingerprint overrides + humanized delay jitter.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

## Quick Usage

```bash
python3 -m src.cli run --task examples/task_basic_extract.json --pretty
```

Or stdin:

```bash
cat examples/task_basic_extract.json | python3 -m src.cli run --task - --pretty
```

## Config

Main config: `config/config.yaml`

Key parameters:
- `browser.max_tabs`
- `self_healing.cache_ttl_hours`
- `performance.block_resource_types`
- `performance.block_ad_domains`
- `extraction.stream_chunk_chars`
- `sessions.directory`

## API Surface (`BrowserAgent`)

- `navigate(url, tab_id="default")`
- `extract_with_nlq(query, tab_id="default")`
- `preview_content(tab_id="default")`
- `extract_relevant(keywords, min_score, max_items, tab_id)`
- `stream_extract(max_tokens, chars_per_token, selector, tab_id)`
- `extract_tables(selector, tab_id)`
- `capture_structure(selector, tab_id, logical_name, text_hint, semantic_hint)`
- `download_file(url|selector, filename, subdirectory, tab_id)`
- `login(..., session_name)` / `load_session(session_name)`
- `fill_form(field_values, form_selector, submit, tab_id)`
- `auto_scroll(max_scrolls, scroll_delay_sec, stop_if_no_new_content, tab_id)`
- `get_network_calls(limit)`
- `extract_parallel(urls, query, max_concurrent)`

## Testing

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```
