lucas-browser/
├── SKILL.md
├── agents/openai.yaml
├── config/
│   ├── config.yaml
│   └── device_profiles.yaml
├── src/
│   ├── agent/browser_agent.py
│   ├── core/
│   │   ├── browser_manager.py
│   │   ├── network_monitor.py
│   │   ├── page_pool.py
│   │   ├── resource_monitor.py
│   │   ├── session_manager.py
│   │   └── tab_orchestrator.py
│   ├── extractors/
│   │   ├── content_extractor.py
│   │   ├── content_previewer.py
│   │   ├── file_downloader.py
│   │   ├── streaming_extractor.py
│   │   ├── structure_analyzer.py
│   │   └── table_extractor.py
│   ├── intelligence/
│   │   ├── nlq_parser.py
│   │   ├── relevance_filter.py
│   │   └── self_healing.py
│   ├── actions/
│   │   ├── form_filler.py
│   │   ├── interaction_handler.py
│   │   └── scroll_handler.py
│   ├── stealth/
│   │   ├── fingerprint_manager.py
│   │   └── stealth_engine.py
│   └── cli.py
├── scripts/validate_config.py
├── examples/
├── tests/
├── README.md
└── QUICK_START.md
