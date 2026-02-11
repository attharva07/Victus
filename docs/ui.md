# UI Status

The in-repository UI paths were removed during repository cleanup to keep a single unambiguous run path.

## Current status
- No maintained frontend is bundled in this repository.
- The supported runtime target is the backend API in `apps/local/main.py`.

## Why
Multiple UI implementations existed with different API expectations and startup commands, which created a misleading and non-deterministic developer experience.

## If you need a UI
Build a client against the backend OpenAPI contract served by:
- `GET /openapi.json`
- `GET /docs`
