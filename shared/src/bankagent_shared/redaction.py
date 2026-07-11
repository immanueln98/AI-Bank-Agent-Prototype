"""PII masking used by logging, transcripts, and tool-activity events.

Three layers, applied in this order:

1. Known-value masking (`KnownPII`) - exact values that entered the system
   (e.g. the account number a caller read out). Matches even when the digits
   are spoken/transcribed with spaces or dashes ("10 0234 5678").
2. Regex safety net - digit shapes that look like SA/Botswana identifiers.
3. Spoken-number safety net - voice transcripts carry numbers as WORDS
   ("one double zero two three four five six seven eight", "nine zero eight
   seven") on both sides of the conversation: STT writes the caller's speech
   that way, and the voice prompt tells the agent to say numbers as words.
   Any run of four or more digit-words (including "oh"/"double"/"triple"
   forms) or four or more separated single digits is masked by shape, before
   the value is ever known to the system.

May occasionally mask an innocent number read digit-by-digit; for a banking
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

# --- spoken-number shapes -------------------------------------------------
_DIGIT_WORDS: dict[str, str] = {
    "zero": "0", "oh": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
}  # fmt: skip
_DIGIT_WORD = r"(?:zero|oh|one|two|three|four|five|six|seven|eight|nine)"
_RUN_TOKEN = rf"(?:(?:double|triple)\s+{_DIGIT_WORD}|{_DIGIT_WORD})"
# Four or more tokens ("double zero" is one token, two digits) = an
# identifier being read out, not conversational English ("one or two
# questions" breaks the run at "or"; amounts use scale words like thousand).
_SPOKEN_RUN = re.compile(rf"\b{_RUN_TOKEN}(?:[\s,\-]+{_RUN_TOKEN}){{3,}}\b", re.IGNORECASE)
# STT sometimes emits separated digits instead: "9 0 8 7", "1-0-0-2".
_SEPARATED_DIGITS = re.compile(r"\b\d(?:[\s,\-]+\d){3,}\b")
_TOKEN_SCAN = re.compile(rf"(double|triple)\s+({_DIGIT_WORD})|({_DIGIT_WORD})|(\d)", re.IGNORECASE)


def _mask_number_run(match: re.Match[str]) -> str:
    """Reconstruct the digits from a spoken run, then mask consistently.

    Runs of 8+ digits keep the usual ****last4 form; shorter runs (an ID's
    last four, a step-up code) are fully masked - ****last4 of a 4-digit
    value would reveal the whole thing.
    """
    digits = ""
    for double_triple, multiplied, plain_word, plain_digit in _TOKEN_SCAN.findall(match.group()):
        if multiplied:
            digits += _DIGIT_WORDS[multiplied.lower()] * (
                3 if double_triple.lower() == "triple" else 2
            )
        elif plain_word:
            digits += _DIGIT_WORDS[plain_word.lower()]
        elif plain_digit:
            digits += plain_digit
    return mask_value(digits) if len(digits) >= 8 else "****"


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
    text = _SPOKEN_RUN.sub(_mask_number_run, text)
    text = _SEPARATED_DIGITS.sub(_mask_number_run, text)
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
