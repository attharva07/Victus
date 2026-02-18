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


BACKEND_URL ?= http://127.0.0.1:8000

test-contract:
	$(PYTHON) scripts/contract_check.py --backend-url $(BACKEND_URL)

test-wire:
	cd apps/web && npm run test:wire
