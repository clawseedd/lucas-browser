# Quick Start

1. Install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

2. Validate configuration:
```bash
python3 scripts/validate_config.py
```

3. Run sample task:
```bash
python3 -m src.cli run --task examples/task_basic_extract.json --pretty
```

4. Run tests:
```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```
