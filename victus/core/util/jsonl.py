import json
from pathlib import Path
from typing import Any, List


def ensure_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.touch()


def append_jsonl(path: Path, obj: Any) -> None:
    ensure_file(path)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj) + "\n")


def read_jsonl(path: Path) -> List[Any]:
    ensure_file(path)
    items: List[Any] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    return items
