from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

FETCH_RE = re.compile(r"fetch\(\s*([`\'\"])(.+?)\1\s*\)", re.DOTALL)
FETCH_WITH_INIT_RE = re.compile(r"fetch\(\s*([`\'\"])(.+?)\1\s*,\s*\{(?P<body>.*?)\}\s*\)", re.DOTALL)
AXIOS_METHOD_RE = re.compile(r"axios\.(get|post|put|patch|delete)\(\s*([`\'\"])(.+?)\2", re.DOTALL)
AXIOS_CONFIG_RE = re.compile(r"axios\(\s*\{(?P<body>.*?)\}\s*\)", re.DOTALL)
REQUEST_CALL_RE = re.compile(r"request(?:<[^>]+>)?\(\s*([`\'\"])(.+?)\1(?:\s*,\s*\{(?P<body>.*?)\})?", re.DOTALL)
URL_FIELD_RE = re.compile(r"url\s*:\s*([`\'\"])(.+?)\1", re.DOTALL)
METHOD_FIELD_RE = re.compile(r"method\s*:\s*([`\'\"])(.+?)\1", re.DOTALL)


def _normalize_path(raw: str) -> str:
    path = raw.strip()
    if not path:
        return path
    if path.startswith("http://") or path.startswith("https://"):
        path = urlparse(path).path
    if "?" in path:
        path = path.split("?", 1)[0]
    if not path.startswith("/"):
        return ""
    path = re.sub(r"\$\{[^}]+\}", "{param}", path)
    path = re.sub(r"\{[^}]+\}", "{param}", path)
    return path


def _scan_frontend_calls(paths: list[Path]) -> set[tuple[str, str]]:
    calls: set[tuple[str, str]] = set()
    for root in paths:
        if root.is_dir():
            files = [p for p in root.rglob("*") if p.is_file() and p.suffix in {".ts", ".tsx", ".js", ".jsx"}]
        elif root.is_file() and root.suffix in {".ts", ".tsx", ".js", ".jsx"}:
            files = [root]
        else:
            files = []

        for file_path in files:
            text = file_path.read_text(encoding="utf-8")
            for match in FETCH_WITH_INIT_RE.finditer(text):
                method_match = METHOD_FIELD_RE.search(match.group("body"))
                method = (method_match.group(2) if method_match else "GET").upper()
                path = _normalize_path(match.group(2))
                if path:
                    calls.add((method, path))
            for _, url in FETCH_RE.findall(text):
                path = _normalize_path(url)
                if path:
                    calls.add(("GET", path))
            for match in REQUEST_CALL_RE.finditer(text):
                method_match = METHOD_FIELD_RE.search(match.group("body") or "")
                method = (method_match.group(2) if method_match else "GET").upper()
                path = _normalize_path(match.group(2))
                if path:
                    calls.add((method, path))
            for method, _, url in AXIOS_METHOD_RE.findall(text):
                path = _normalize_path(url)
                if path:
                    calls.add((method.upper(), path))
            for match in AXIOS_CONFIG_RE.finditer(text):
                body = match.group("body")
                url_match = URL_FIELD_RE.search(body)
                if not url_match:
                    continue
                method_match = METHOD_FIELD_RE.search(body)
                method = (method_match.group(2) if method_match else "GET").upper()
                path = _normalize_path(url_match.group(2))
                if path:
                    calls.add((method, path))
    return calls


def _path_matches(frontend_path: str, openapi_path: str) -> bool:
    openapi_pattern = "^" + re.sub(r"\{[^}]+\}", r"[^/]+", openapi_path) + "$"
    return re.match(openapi_pattern, frontend_path) is not None


def _fetch_openapi(base_url: str) -> dict:
    with urlopen(f"{base_url.rstrip('/')}/openapi.json") as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check frontend API usage against FastAPI OpenAPI spec")
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000", help="Base URL for backend")
    parser.add_argument(
        "--frontend-path",
        action="append",
        default=["apps/web/src"],
        help="Frontend directory or file to scan (can be used multiple times)",
    )
    args = parser.parse_args()

    frontend_calls = _scan_frontend_calls([Path(p) for p in args.frontend_path])
    openapi = _fetch_openapi(args.backend_url)
    openapi_paths = openapi.get("paths", {})

    missing: list[tuple[str, str]] = []
    for method, path in sorted(frontend_calls):
        matched = False
        for openapi_path, operations in openapi_paths.items():
            if not _path_matches(path, openapi_path):
                continue
            if method.lower() in operations:
                matched = True
                break
        if not matched:
            missing.append((method, path))

    if missing:
        print("Frontend calls missing from backend OpenAPI contract:", file=sys.stderr)
        for method, path in missing:
            print(f"- {method} {path}", file=sys.stderr)
        return 1

    print(f"Contract check passed ({len(frontend_calls)} frontend endpoint usage(s) validated).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
