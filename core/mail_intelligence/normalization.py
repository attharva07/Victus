from __future__ import annotations

import re

from core.mail_intelligence.connector import RawEmail
from core.mail_intelligence.models import NormalizedEmail

_QUOTED_MARKERS = (
    r"^On .+ wrote:$",
    r"^From:\s",
    r"^Sent:\s",
    r"^>+",
)
_SIGNATURE_MARKERS = (
    r"^--\s*$",
    r"^Best,\s*$",
    r"^Thanks,\s*$",
    r"^Sent from my",
)


class EmailNormalizer:
    def normalize(self, raw_email: RawEmail) -> NormalizedEmail:
        body = self._compact_whitespace(raw_email.body_text)
        cleaned_text, quoted_removed = self._remove_quoted_history(body)
        cleaned_text, signature_removed = self._remove_signature(cleaned_text)
        return NormalizedEmail(
            metadata=raw_email.metadata,
            body_text=body,
            body_html=raw_email.body_html,
            cleaned_text=cleaned_text,
            quoted_history_removed=quoted_removed,
            signature_removed=signature_removed,
        )

    @staticmethod
    def _compact_whitespace(text: str) -> str:
        lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
        return "\n".join(lines).strip()

    def _remove_quoted_history(self, text: str) -> tuple[str, bool]:
        lines = text.split("\n")
        kept: list[str] = []
        removed = False
        for line in lines:
            if any(re.match(pattern, line.strip(), flags=re.IGNORECASE) for pattern in _QUOTED_MARKERS):
                removed = True
                break
            kept.append(line)
        return "\n".join(kept).strip(), removed

    def _remove_signature(self, text: str) -> tuple[str, bool]:
        lines = text.split("\n")
        for idx, line in enumerate(lines):
            if any(re.match(pattern, line.strip(), flags=re.IGNORECASE) for pattern in _SIGNATURE_MARKERS):
                return "\n".join(lines[:idx]).strip(), True
        return text.strip(), False
