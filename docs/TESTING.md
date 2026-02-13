# Testing and Quality Standards

## Local commands
- Run the focused test suite: `python -m pytest -q --disable-warnings`
- Run coverage reporting: `python -m pytest --cov=victus --cov-report=term-missing --cov-report=xml`
- Run lint checks: `ruff check .`
- Regenerate the unified quality report: `python scripts/quality_report.py`

You can also use the provided `Makefile` targets:

- `make test` – run the quiet pytest suite
- `make lint` – run Ruff lint checks
- `make coverage` – generate coverage with XML output
- `make report` – run lint, tests, coverage, and refresh `docs/QUALITY_REPORT.md`

## Policy
- Do not land behavioral changes without matching tests that capture the expected behavior.
- Keep `docs/QUALITY_REPORT.md` generated via `python scripts/quality_report.py`; CI uploads it as an artifact on every push/PR.
- Avoid committing local build artifacts, coverage outputs, or virtual environments; these are ignored via `.gitignore`.

## Manual tests
- Simulate LLM down (open circuit breaker).
- Send: "open calculator" → clarify prompt appears.
- Reply: "calculator" → `local.open_app` executes and pending clears (no loop).
