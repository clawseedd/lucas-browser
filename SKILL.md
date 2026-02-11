---
name: lucas-browser
description: Python Playwright browser automation skill for OpenClaw. Use when Codex must navigate websites, extract structured content (text, numbers, lists, tables), capture CSS/XPath structure, download files, preserve authenticated sessions, and recover from changing page selectors in resource-constrained environments.
---

# LUCAS Browser Skill

## Runtime

- Run tasks with `python3 -m src.cli run --task <task.json|-> --config config/config.yaml --pretty`.
- Keep tasks deterministic JSON in and JSON out.

## Capability Coverage

- Self-healing selectors: direct + cached + text + semantic fallback.
- Natural-language field extraction: rule-based field-name parsing.
- Session management: save and reload storage state.
- Content preview + relevance filtering + streaming extraction.
- Form fill, infinite scroll, network call capture, parallel tab extraction.

## Tuning

- For Raspberry Pi 4, keep `browser.max_tabs` low (1-2).
- Keep resource and ad blocking enabled.
- Keep `self_healing.cache_ttl_hours = 168` for 7-day selector memory.
