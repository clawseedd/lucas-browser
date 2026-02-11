# Raspberry Pi 4 Optimization

Recommended defaults:
- `browser.max_tabs = 2`
- `browser.headless = true`
- Keep `--single-process` and `--disable-dev-shm-usage` in launch args.
- Enable request blocking and ad-domain blocking.
- Keep streaming extraction enabled for large pages.

If memory pressure remains high:
- Set `max_tabs = 1`
- Reduce `extraction.max_text_length`
- Reduce `extraction.max_stream_chunks`
