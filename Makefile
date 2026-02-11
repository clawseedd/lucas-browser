.PHONY: test validate

test:
	python3 -m unittest discover -s tests -p 'test_*.py' -v

validate:
	python3 scripts/validate_config.py
