from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from .models import MemoryRecord


_SENSITIVE_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"api[_-]?key\s*[:=]\s*\w+", re.IGNORECASE),
    re.compile(r"token\s*[:=]\s*\w+", re.IGNORECASE),
    re.compile(r"password\s*[:=]\s*.+", re.IGNORECASE),
    re.compile(r"bank\s*login", re.IGNORECASE),
    re.compile(r"account\s*number", re.IGNORECASE),
]

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"\b\+?\d?[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


@dataclass
class MemoryCandidate:
    text: str
    scope: str
    kind: str
    tags: List[str]
    source: str
    confidence: float
    pii_risk: str


class MemoryGate:
    def __init__(self) -> None:
        self.explicit_patterns = [
            re.compile(r"\bremember that\b", re.IGNORECASE),
            re.compile(r"\bremember\b", re.IGNORECASE),
            re.compile(r"\bsave this\b", re.IGNORECASE),
            re.compile(r"\bsave that\b", re.IGNORECASE),
        ]

    def extract_candidate(self, text: str, *, source: str = "user") -> Optional[MemoryCandidate]:
        normalized = text.strip()
        if not normalized:
            return None

        explicit = self._is_explicit_request(normalized)
        candidate_text = self._extract_text(normalized) if explicit else normalized
        if not candidate_text:
            return None

        pii_risk = self._pii_risk(candidate_text)
        if self._contains_sensitive(candidate_text):
            return None

        if pii_risk in {"medium", "high"} and not explicit:
            return None

        if not explicit and not self._is_important(candidate_text):
            return None

        scope = "project" if "project" in candidate_text.lower() else "user"
        kind = self._infer_kind(candidate_text)
        tags = self._extract_tags(candidate_text)
        confidence = 0.85 if explicit else 0.6

        return MemoryCandidate(
            text=candidate_text,
            scope=scope,
            kind=kind,
            tags=tags,
            source=source,
            confidence=confidence,
            pii_risk=pii_risk,
        )

    @staticmethod
    def build_record(candidate: MemoryCandidate) -> MemoryRecord:
        return MemoryRecord.create(
            scope=candidate.scope,
            kind=candidate.kind,
            text=candidate.text,
            tags=candidate.tags,
            source=candidate.source,
            confidence=candidate.confidence,
            pii_risk=candidate.pii_risk,
        )

    def _is_explicit_request(self, text: str) -> bool:
        return any(pattern.search(text) for pattern in self.explicit_patterns)

    def _extract_text(self, text: str) -> str:
        lowered = text.lower()
        for phrase in ["remember that", "remember", "save this", "save that", "save"]:
            if phrase in lowered:
                idx = lowered.find(phrase)
                stripped = text[idx + len(phrase) :].strip(" :,-")
                if stripped:
                    return stripped
        return text.strip()

    def _extract_tags(self, text: str) -> List[str]:
        return [tag.lstrip("#") for tag in re.findall(r"#(\w+)", text)]

    def _infer_kind(self, text: str) -> str:
        lowered = text.lower()
        if "todo" in lowered or "to-do" in lowered or "need to" in lowered:
            return "todo"
        if "prefer" in lowered or "preference" in lowered:
            return "preference"
        if "decide" in lowered or "decision" in lowered:
            return "decision"
        if "context" in lowered:
            return "context"
        return "fact"

    def _is_important(self, text: str) -> bool:
        lowered = text.lower()
        signals = ["important", "remember", "preference", "decision", "todo", "deadline", "project"]
        return any(signal in lowered for signal in signals) and len(text) > 10

    def _contains_sensitive(self, text: str) -> bool:
        return any(pattern.search(text) for pattern in _SENSITIVE_PATTERNS)

    def _pii_risk(self, text: str) -> str:
        if _SSN_RE.search(text):
            return "high"
        if "bank" in text.lower() or "account" in text.lower():
            return "high"
        if _EMAIL_RE.search(text) or _PHONE_RE.search(text):
            return "medium"
        return "low"
