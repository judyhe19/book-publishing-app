"""
Fuzzy author matching utility.

Matches an author name string returned from an external source (e.g. Google Books)
against Author records stored in the database.

Matching strategy (applied in order):
  1. Token normalization — lowercase, strip punctuation, sort tokens.
     Handles "Huxley, Aldous" == "Aldous Huxley" without any scoring.
  2. rapidfuzz token_sort_ratio — fuzzy similarity on the normalized forms.
     Catches abbreviations, middle names, minor typos, etc.

Usage:
    from bookapp.utils.author_matcher import match_author

    candidates = Author.objects.all()
    result = match_author("Huxley, Aldous", candidates)
    # {"author_id": 3, "name": "Aldous Huxley", "confidence": 97, "match_type": "fuzzy"}
"""

import re
import string

from rapidfuzz import fuzz


# Minimum similarity score (0–100) required to consider a match valid.
FUZZY_MATCH_THRESHOLD = 80


def match_author(raw_name: str, candidates) -> dict | None:
    """
    Find the best matching Author record for a raw name string.

    Args:
        raw_name:   Author name as returned by the external source.
        candidates: Iterable of Author model instances to match against.

    Returns:
        A dict with keys author_id, name, confidence (0–100), and match_type
        ("exact" or "fuzzy"), or None if no match meets the threshold.
    """
    normalized_raw = _normalize(raw_name)
    best_score = -1
    best_author = None

    for author in candidates:
        normalized_candidate = _normalize(author.name)

        # Fast path: normalized exact match (handles "Last, First" ↔ "First Last")
        if normalized_raw == normalized_candidate:
            return _result(author, score=100, match_type="exact")

        score = fuzz.token_sort_ratio(normalized_raw, normalized_candidate)
        if score > best_score:
            best_score = score
            best_author = author

    if best_author is not None and best_score >= FUZZY_MATCH_THRESHOLD:
        return _result(best_author, score=best_score, match_type="fuzzy")

    return None


# ──────────────────────────────────────────────────────────────────────────────
# Private helpers
# ──────────────────────────────────────────────────────────────────────────────

def _normalize(name: str) -> str:
    """
    Lowercase, strip punctuation, and sort tokens so that word order and
    common punctuation differences (commas in "Last, First") don't matter.
    """
    name = name.lower()
    name = name.translate(str.maketrans("", "", string.punctuation))
    tokens = sorted(re.split(r"\s+", name.strip()))
    return " ".join(t for t in tokens if t)


def _result(author, score: int, match_type: str) -> dict:
    return {
        "author_id": author.id,
        "name": author.name,
        "confidence": score,
        "match_type": match_type,
    }
