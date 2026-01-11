"""Generate regression test templates for failure signatures."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def _sanitize_signature(signature: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", signature.strip())
    return cleaned.strip("_") or "signature"


def generate_template(signature: str, out_path: Path) -> Path:
    safe_signature = _sanitize_signature(signature)
    test_name = f"test_regression_{safe_signature}"
    template = f'''"""Regression test for signature: {signature}.

Event IDs: <event_id_1>, <event_id_2>, <event_id_3>
"""

import pytest


@pytest.mark.skip(reason="TODO implement reproducer")
def {test_name}():
    \"\"\"TODO: implement a reproducer for {signature}.\"\"\"
    # TODO: add steps to reproduce the failure.
    assert False
'''
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(template, encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate regression test template")
    parser.add_argument("--signature", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    out_path = Path(args.out)
    generate_template(args.signature, out_path)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
