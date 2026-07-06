"""PII masking used by logging, transcripts, and tool-activity events.

Two layers, applied in this order:

1. Known-value masking (`KnownPII`) - exact values that entered the system
   (e.g. the account number a caller read out). Matches even when the digits
   are spoken/transcribed with spaces or dashes ("10 0234 5678").
2. Regex safety net - digit shapes that look like SA/Botswana identifiers.
   May occasionally mask an innocent 10-digit phone number; for a banking
   POC, over-masking beats leaking.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

# Longest first so a 13-digit ID is never reported as a 10-digit account.
PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("sa_id", re.compile(r"\b\d{13}\b")),  # South African ID number
    ("account", re.compile(r"\b\d{10}\b")),  # POC account numbers are 10 digits
    ("omang", re.compile(r"\b\d{9}\b")),  # Botswana Omang number
]

_MIN_KNOWN_LEN = 6  # never register short values (would mask e.g. "1234" amounts)


def mask_value(value: str) -> str:
    """``"1002345678"`` -> ``"****5678"``."""
    digits = re.sub(r"\D", "", value)
    return f"****{digits[-4:]}" if len(digits) >= 4 else "****"


# Kept as a separate name because call sites read better as mask_account(...).
mask_account = mask_value


class KnownPII:
    """Per-session registry of exact PII values for reliable masking."""

    def __init__(self) -> None:
        self._patterns: dict[str, re.Pattern[str]] = {}

    def add(self, value: str) -> None:
        digits = re.sub(r"\D", "", value)
        if len(digits) < _MIN_KNOWN_LEN or digits in self._patterns:
            return
        # Allow separators between digits so spoken forms still match.
        self._patterns[digits] = re.compile(r"[\s-]?".join(re.escape(d) for d in digits))

    def mask_in(self, text: str) -> str:
        for digits, pattern in self._patterns.items():
            text = pattern.sub(mask_value(digits), text)
        return text


def mask_text(text: str, known: KnownPII | None = None) -> str:
    if known is not None:
        text = known.mask_in(text)
    for _, pattern in PII_PATTERNS:
        text = pattern.sub(lambda m: mask_value(m.group()), text)
    return text


def mask_mapping(obj: Any, known: KnownPII | None = None) -> Any:
    """Recursively mask every string in dicts / lists / tuples."""
    if isinstance(obj, str):
        return mask_text(obj, known)
    if isinstance(obj, Mapping):
        return {k: mask_mapping(v, known) for k, v in obj.items()}
    if isinstance(obj, Sequence) and not isinstance(obj, bytes | bytearray):
        return [mask_mapping(v, known) for v in obj]
    return obj
