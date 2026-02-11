# Configuration

Config file: `config/config.yaml`

Important settings:
- `browser.max_tabs`: cap open pages in pool.
- `browser.launch_args`: Chromium flags for low-memory nodes.
- `self_healing.cache_ttl_hours`: selector cache lifetime.
- `performance.block_resource_types`: resource blocking policy.
- `performance.block_ad_domains`: domain-level ad blocking.
- `sessions.directory`: persistent session state files.
- `extraction.stream_chunk_chars`: streaming chunk size.
