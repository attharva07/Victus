# victus_local (compatibility module)

This package is kept for compatibility and unit-test coverage of local assistant flows.

## Important
- It is **not** the primary runtime entrypoint for this repository.
- The supported backend run path is documented in the root `README.md` and uses:
  - `uvicorn apps.local.main:app --host 127.0.0.1 --port 8000`

Historical docs and demo assets have been moved to `docs/legacy/`.
