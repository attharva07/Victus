from __future__ import annotations

import re

from core.signals.models import SignalBundle


_FINANCE_INTENT = re.compile(r"\b(spent|paid|bought|transaction|charged|add\s+transaction)\b", re.IGNORECASE)
_MEMORY_INTENT = re.compile(r"\b(remember|save\s+to\s+memory|add\s+to\s+memory)\b", re.IGNORECASE)
_REMINDER_INTENT = re.compile(r"\b(remind\s+me|reminder)\b", re.IGNORECASE)

_AMOUNT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("dollar_prefix", re.compile(r"\$(\d+(?:\.\d{1,2})?)", re.IGNORECASE)),
    ("dollar_suffix", re.compile(r"(\d+(?:\.\d{1,2})?)\$", re.IGNORECASE)),
    ("usd_suffix", re.compile(r"\b(\d+(?:\.\d{1,2})?)\s*usd\b", re.IGNORECASE)),
    ("dollars_suffix", re.compile(r"\b(\d+(?:\.\d{1,2})?)\s*dollars?\b", re.IGNORECASE)),
)


def _extract_amount(text: str) -> tuple[float | None, str | None, dict[str, object]]:
    for key, pattern in _AMOUNT_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        return float(match.group(1)), "USD", {"amount_pattern": key, "amount_match": match.group(0)}

    spent_match = re.search(r"\b(?:spent|paid|bought|charged)\b\s+(\d+(?:\.\d{1,2})?)\b", text, re.IGNORECASE)
    if spent_match:
        return float(spent_match.group(1)), "USD", {"amount_pattern": "spend_verb_plain", "amount_match": spent_match.group(0)}

    transaction_match = re.search(r"\badd\s+transaction\s+(\d+(?:\.\d{1,2})?)\b", text, re.IGNORECASE)
    if transaction_match:
        return float(transaction_match.group(1)), "USD", {"amount_pattern": "add_transaction_plain", "amount_match": transaction_match.group(0)}
    return None, None, {}


def _extract_merchant(text: str) -> tuple[str | None, dict[str, object]]:
    for pattern_name, pattern in (
        ("at_or_for_phrase", re.compile(r"\b(?:at|for)\s+([A-Za-z][\w&\-'. ]{1,40})", re.IGNORECASE)),
        ("trailing_token", re.compile(r"\b(?:transaction|spent|paid|bought|charged)\b.*?(?:\$?\d+(?:\.\d{1,2})?)\s+([A-Za-z][\w&\-'.]*)\s*$", re.IGNORECASE)),
    ):
        match = pattern.search(text.strip())
        if match:
            merchant = match.group(1).strip(" .,!?")
            if merchant:
                return merchant, {"merchant_pattern": pattern_name, "merchant_match": match.group(0)}
    return None, {}


def extract_signals(text: str) -> SignalBundle:
    normalized = text.strip()
    evidence: dict[str, object] = {}

    amount, currency, amount_evidence = _extract_amount(normalized)
    evidence.update(amount_evidence)

    merchant, merchant_evidence = _extract_merchant(normalized)
    evidence.update(merchant_evidence)

    lowered = normalized.lower()
    intent_hint: str | None = None
    if _FINANCE_INTENT.search(lowered):
        intent_hint = "finance.add_transaction"
        evidence["intent_match"] = _FINANCE_INTENT.search(normalized).group(0)
    elif _MEMORY_INTENT.search(lowered):
        intent_hint = "memory.add"
        evidence["intent_match"] = _MEMORY_INTENT.search(normalized).group(0)
        content = re.sub(r"^(?:remember|save to memory|add to memory)\s*(?:that\s+)?", "", normalized, flags=re.IGNORECASE).strip(" .")
        if content:
            evidence["memory_content"] = content
    elif _REMINDER_INTENT.search(lowered):
        intent_hint = "reminder.add"
        evidence["intent_match"] = _REMINDER_INTENT.search(normalized).group(0)

    signal_count = sum(value is not None for value in (amount, merchant, intent_hint))
    confidence = min(1.0, 0.2 + signal_count * 0.25 + (0.1 if evidence else 0.0))

    return SignalBundle(
        raw_text=normalized,
        amount=amount,
        currency=currency,
        merchant=merchant,
        category_hint=merchant,
        datetime_hint=None,
        intent_hint=intent_hint,
        confidence=round(confidence, 4),
        evidence=evidence,
    )
