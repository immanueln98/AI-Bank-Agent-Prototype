"""General banking FAQ - the one lookup that needs no identity verification.

Scoring is naive keyword overlap; good enough for ~10 fixture entries. A real
deployment would swap this for the bank's knowledge base / RAG search.
"""

import re

from fastapi import APIRouter, Query

from bankagent_shared.models import FaqResult

from ..fixtures import FAQS

router = APIRouter()

# fmt: off
_STOPWORDS = frozenset([
    "a", "an", "the", "is", "are", "do", "does", "how", "what", "when",
    "where", "my", "i", "to", "of", "for", "in", "on", "with",
])
# fmt: on


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z]+", text.lower()) if t not in _STOPWORDS}


@router.get("/faq/search", response_model=list[FaqResult])
def search_faq(q: str = Query(min_length=2), limit: int = 3) -> list[FaqResult]:
    query_tokens = _tokens(q)
    if not query_tokens:
        return []
    scored: list[FaqResult] = []
    for entry in FAQS:
        entry_tokens = _tokens(entry["question"] + " " + entry["answer"])
        overlap = len(query_tokens & entry_tokens)
        if overlap:
            scored.append(
                FaqResult(
                    question=entry["question"],
                    answer=entry["answer"],
                    score=round(overlap / len(query_tokens), 3),
                )
            )
    scored.sort(key=lambda r: r.score, reverse=True)
    return scored[:limit]
