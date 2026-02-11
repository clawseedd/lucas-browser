.PHONY: test validate lint format check

test:
	python3 -m unittest discover -s tests -p 'test_*.py' -v

validate:
	python3 scripts/validate_config.py

lint:
	python3 -m ruff check src/ tests/ scripts/

format:
	python3 -m ruff format src/ tests/ scripts/

check: lint test
