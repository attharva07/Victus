from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .app_aliases import is_learnable_alias, is_safe_alias, list_known_apps, normalize_app_name


DEFAULT_PATH = Path(__file__).parent / "app_dict.json"
PROMOTE_THRESHOLD = 3


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _seed_dictionary() -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "canonical": {},
        "aliases": {},
        "candidates": {},
        "updated_at": _now_iso(),
    }
    for app in list_known_apps():
        data["canonical"][app.target] = {
            "label": app.label,
            "usage": 0,
            "last_seen": None,
        }
        for alias in app.aliases:
            normalized = normalize_app_name(alias)
            if not normalized:
                continue
            data["aliases"][normalized] = {
                "canonical": app.target,
                "usage": 0,
                "last_seen": None,
            }
    return data


def _atomic_write(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(path.parent), encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.flush()
        temp_path = Path(handle.name)
    temp_path.replace(path)


def _is_safe_to_learn(alias: str) -> bool:
    return is_safe_alias(alias) and is_learnable_alias(alias)


@dataclass
class AppDictionary:
    data: Dict[str, Any]
    path: Path = DEFAULT_PATH
    promote_threshold: int = PROMOTE_THRESHOLD

    @classmethod
    def load(cls, path: Optional[Path] = None) -> AppDictionary:
        target = path or DEFAULT_PATH
        if not target.exists():
            seed = _seed_dictionary()
            _atomic_write(target, seed)
            return cls(data=seed, path=target)

        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = _seed_dictionary()
            _atomic_write(target, data)
            return cls(data=data, path=target)

        if not isinstance(data, dict):
            data = _seed_dictionary()
            _atomic_write(target, data)
            return cls(data=data, path=target)

        data.setdefault("canonical", {})
        data.setdefault("aliases", {})
        data.setdefault("candidates", {})
        data["updated_at"] = data.get("updated_at") or _now_iso()

        normalized_aliases: Dict[str, Any] = {}
        for raw_alias, raw_entry in (data.get("aliases") or {}).items():
            if not isinstance(raw_alias, str) or not isinstance(raw_entry, dict):
                continue
            normalized = normalize_app_name(raw_alias)
            canonical = raw_entry.get("canonical")
            if not normalized or not isinstance(canonical, str):
                continue
            normalized_aliases[normalized] = {
                "canonical": canonical,
                "usage": int(raw_entry.get("usage") or 0),
                "last_seen": raw_entry.get("last_seen"),
            }
        data["aliases"] = normalized_aliases
        data["candidates"] = data.get("candidates") or {}
        return cls(data=data, path=target)

    @property
    def aliases(self) -> Dict[str, Dict[str, Any]]:
        return self.data.setdefault("aliases", {})

    @property
    def candidates(self) -> Dict[str, Dict[str, Any]]:
        return self.data.setdefault("candidates", {})

    @property
    def canonical(self) -> Dict[str, Dict[str, Any]]:
        return self.data.setdefault("canonical", {})

    def alias_map(self) -> Dict[str, str]:
        return {
            alias: entry.get("canonical", "")
            for alias, entry in self.aliases.items()
            if isinstance(entry, dict) and isinstance(entry.get("canonical"), str)
        }

    def record_success(self, requested_alias: str, target: str, label: Optional[str] = None) -> Optional[Dict[str, str]]:
        normalized = normalize_app_name(requested_alias)
        now = _now_iso()
        canonical_entry = self.canonical.get(target)
        if not isinstance(canonical_entry, dict):
            canonical_entry = {"label": label or target, "usage": 0, "last_seen": None}
        canonical_entry["usage"] = int(canonical_entry.get("usage") or 0) + 1
        canonical_entry["last_seen"] = now
        if label and not canonical_entry.get("label"):
            canonical_entry["label"] = label
        self.canonical[target] = canonical_entry

        if not normalized or not _is_safe_to_learn(requested_alias):
            self._save()
            return None

        alias_entry = self.aliases.get(normalized)
        if isinstance(alias_entry, dict) and alias_entry.get("canonical") == target:
            alias_entry["usage"] = int(alias_entry.get("usage") or 0) + 1
            alias_entry["last_seen"] = now
            self.aliases[normalized] = alias_entry
            self._save()
            return None

        candidate_entry = self.candidates.get(normalized)
        if not isinstance(candidate_entry, dict) or candidate_entry.get("canonical") != target:
            candidate_entry = {"canonical": target, "count": 0, "last_seen": None}
        candidate_entry["count"] = int(candidate_entry.get("count") or 0) + 1
        candidate_entry["last_seen"] = now
        if candidate_entry["count"] >= self.promote_threshold:
            self.aliases[normalized] = {
                "canonical": target,
                "usage": candidate_entry["count"],
                "last_seen": now,
            }
            self.candidates.pop(normalized, None)
            self._save()
            return {"alias": normalized, "target": target}

        self.candidates[normalized] = candidate_entry
        self._save()
        return None

    def _save(self) -> None:
        self.data["updated_at"] = _now_iso()
        _atomic_write(self.path, self.data)


def load_app_dictionary(path: Optional[Path] = None) -> AppDictionary:
    return AppDictionary.load(path)
