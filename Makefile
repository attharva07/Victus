PYTHON ?= python

.PHONY: lint test coverage report test-contract test-wire

lint:
	$(PYTHON) -m ruff check .

test:
	$(PYTHON) -m pytest -q --disable-warnings

coverage:
	$(PYTHON) -m pytest --cov=victus --cov-report=term-missing --cov-report=xml

report:
	$(PYTHON) scripts/quality_report.py

test-contract:
	@bash -lc 'python -m uvicorn apps.local.main:app --host 127.0.0.1 --port 8000 >/tmp/victus_contract_backend.log 2>&1 & pid=$$!; trap "kill $$pid" EXIT; sleep 2; $(PYTHON) scripts/contract_check.py --backend-url http://127.0.0.1:8000'

test-wire:
	npm --prefix apps/web run test:wire
