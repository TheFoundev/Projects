"""Normalize raw user queries before retrieval.

Applies lowercase, punctuation stripping, whitespace normalization,
and domain-specific abbreviation expansion so that shorthand or
misspelled queries still match well-formed index text.
"""

from __future__ import annotations

import re
import string

# ---------------------------------------------------------------------------
# Abbreviation / shorthand expansion table
# ---------------------------------------------------------------------------

ABBREVIATIONS: dict[str, str] = {
    # Institution / general
    "inst": "institution",
    "instution": "institution",
    "institue": "institute",
    "instiution": "institution",
    "estd": "established",
    "estb": "established",
    "est": "established",
    "yr": "year",
    "yrs": "years",
    "dept": "department",
    "depts": "departments",
    "col": "college",
    "clg": "college",
    "uni": "university",
    "univ": "university",
    "mgmt": "management",
    "admin": "administration",
    "info": "information",
    "abt": "about",
    # Academics
    "ece": "electronics and communication engineering",
    "eee": "electrical and electronics engineering",
    "mech": "mechanical engineering",
    "aids": "artificial intelligence and data science",
    "aiml": "artificial intelligence and machine learning",
    "ds": "data science",
    # People / roles
    "hod": "head of department",
    "prof": "professor",
    "princi": "principal",
    "princ": "principal",
    # Facilities
    "lib": "library",
    "lab": "laboratory",
    "labs": "laboratories",
    "ac": "air conditioned",
    # Fees / finance
    "tution": "tuition",
    "tutition": "tuition",
    # Misc
    "avail": "available",
    "avble": "available",
    "num": "number",
    "nos": "numbers",
    "cnt": "count",
    "tot": "total",
    "approx": "approximately",
    "addr": "address",
    "loc": "location",
    "tel": "telephone",
}


def _expand_abbreviations(text: str) -> str:
    """Replace known abbreviations with full forms (whole-word match)."""
    words = text.split()
    expanded: list[str] = []
    for word in words:
        clean = word.strip(string.punctuation)
        substitution = ABBREVIATIONS.get(clean.lower())
        expanded.append(substitution if substitution else word)
    return " ".join(expanded)


def normalize_query(query: str) -> str:
    """Return a cleaned, normalized version of *query*.

    Steps:
    1. Lowercase
    2. Remove punctuation (keep word-internal hyphens / apostrophes)
    3. Collapse whitespace
    4. Expand domain abbreviations
    5. Final strip
    """
    if not query or not query.strip():
        return ""

    text = query.lower().strip()
    # Replace punctuation with spaces (keep - and ' inside words)
    text = re.sub(r"[^\w\s\-']", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = _expand_abbreviations(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
