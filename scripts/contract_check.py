#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse
from urllib.error import URLError
from urllib.request import urlopen

FETCH_RE = re.compile(
    r"fetch\(\s*(['\"])(?P<url>[^'\"]+)\1\s*(?:,\s*(?P<options>\{[\s\S]*?\}))?\)",
    re.MULTILINE,
)
METHOD_RE = re.compile(r"method\s*:\s*(['\"])(?P<method>[A-Za-z]+)\1")
AXIOS_METHOD_RE = re.compile(
    r"axios\.(?P<method>get|post|put|delete|patch|options|head)\s*\(\s*(['\"])(?P<url>[^'\"]+)\2",
    re.IGNORECASE,
)
AXIOS_CONFIG_RE = re.compile(r"axios\s*\(\s*\{(?P<config>[\s\S]*?)\}\s*\)", re.MULTILINE)
URL_IN_CONFIG_RE = re.compile(r"url\s*:\s*(['\"])(?P<url>[^'\"]+)\1")

SOURCE_EXTENSIONS = {'.js', '.jsx', '.ts', '.tsx'}


def normalize_path(raw_url: str) -> str | None:
    if not raw_url:
        return None
    parsed = urlparse(raw_url)
    path = parsed.path if parsed.scheme or parsed.netloc else raw_url
    if not path.startswith('/'):
        return None
    return path


def extract_used_endpoints(text: str) -> set[tuple[str, str]]:
    endpoints: set[tuple[str, str]] = set()

    for match in FETCH_RE.finditer(text):
        path = normalize_path(match.group('url'))
        if not path:
            continue
        method = 'GET'
        options = match.group('options') or ''
        method_match = METHOD_RE.search(options)
        if method_match:
            method = method_match.group('method').upper()
        endpoints.add((method, path))

    for match in AXIOS_METHOD_RE.finditer(text):
        path = normalize_path(match.group('url'))
        if not path:
            continue
        endpoints.add((match.group('method').upper(), path))

    for match in AXIOS_CONFIG_RE.finditer(text):
        config = match.group('config')
        url_match = URL_IN_CONFIG_RE.search(config)
        if not url_match:
            continue
        path = normalize_path(url_match.group('url'))
        if not path:
            continue
        method = 'GET'
        method_match = METHOD_RE.search(config)
        if method_match:
            method = method_match.group('method').upper()
        endpoints.add((method, path))

    return endpoints


def load_openapi_endpoints(openapi_url: str) -> set[tuple[str, str]]:
    with urlopen(openapi_url) as response:  # noqa: S310 - URL is user-provided for CI contract check
        payload = json.loads(response.read().decode('utf-8'))

    endpoints: set[tuple[str, str]] = set()
    for path, methods in payload.get('paths', {}).items():
        for method in methods.keys():
            endpoints.add((method.upper(), path))
    return endpoints


def iter_source_files(frontend_root: Path) -> Iterable[Path]:
    for path in frontend_root.rglob('*'):
        if path.suffix in SOURCE_EXTENSIONS and 'node_modules' not in path.parts:
            yield path


def main() -> int:
    parser = argparse.ArgumentParser(description='Compare frontend API calls against backend OpenAPI spec.')
    parser.add_argument('--backend-url', default='http://127.0.0.1:8000', help='FastAPI base URL')
    parser.add_argument('--frontend-dir', default='apps/web', help='Frontend source directory to scan')
    args = parser.parse_args()

    frontend_root = Path(args.frontend_dir)
    if not frontend_root.exists():
        print(f'Frontend directory not found: {frontend_root}', file=sys.stderr)
        return 2

    used: set[tuple[str, str]] = set()
    for file_path in iter_source_files(frontend_root):
        used.update(extract_used_endpoints(file_path.read_text(encoding='utf-8')))

    openapi_url = f"{args.backend_url.rstrip('/')}/openapi.json"
    try:
        available = load_openapi_endpoints(openapi_url)
    except URLError as exc:
        print(f"Unable to load OpenAPI spec from {openapi_url}: {exc}", file=sys.stderr)
        return 2

    missing = sorted(endpoint for endpoint in used if endpoint not in available)
    if missing:
        print('Missing backend endpoints referenced by frontend:')
        for method, path in missing:
            print(f'- {method} {path}')
        return 1

    print(f'Contract check passed. {len(used)} frontend endpoints found in OpenAPI.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
