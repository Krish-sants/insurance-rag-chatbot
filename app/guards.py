"""Guardrails: input screening, citation validation, confidence scoring."""

import re

INJECTION_PATTERNS = [
    r"ignore (all |your |previous |prior )*(instructions|rules)",
    r"disregard (the )?(system|previous) (prompt|instructions)",
    r"reveal (your|the) (system )?prompt",
    r"you are now\b",
    r"list (the )?documents (i|you) can'?t access",
]

OUTCOME_PATTERNS = [
    r"\bwill (this|my|the) claim be (paid|approved|denied)\b",
    r"\bis (this|my|the) claim going to be (paid|approved|denied)\b",
    r"\bshould (i|we|my client) sue\b",
]


def screen_input(question: str) -> str | None:
    """Returns a block reason, or None if the input is allowed."""
    lowered = question.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            return "prompt_injection"
    for pattern in OUTCOME_PATTERNS:
        if re.search(pattern, lowered):
            return "outcome_prediction"
    return None


def _terms(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2}


def validate_citations(answer: str, source_blocks: list[str]) -> dict:
    """Design §9: every [n] must exist, and each cited sentence must be
    supported by (lexically entailed in) its cited source block."""
    cited = [int(n) for n in re.findall(r"\[(\d+)\]", answer)]
    if not cited:
        return {"valid": False, "reason": "no_citations", "coverage": 0.0}
    if any(n < 1 or n > len(source_blocks) for n in cited):
        return {"valid": False, "reason": "citation_out_of_range", "coverage": 0.0}

    # Evaluate per line (bullet or paragraph): sentence-level splitting would
    # detach trailing "[n]" markers from the text they cite.
    sentences = [s.strip() for s in answer.split("\n") if re.search(r"\[\d+\]", s)]
    supported = 0
    for sentence in sentences:
        refs = [int(n) for n in re.findall(r"\[(\d+)\]", sentence)]
        source_terms = set().union(*(_terms(source_blocks[n - 1]) for n in refs))
        content = _terms(re.sub(r"\[\d+\]", "", sentence))
        if content and len(content & source_terms) / len(content) >= 0.5:
            supported += 1
    coverage = supported / len(sentences) if sentences else 0.0
    return {"valid": coverage >= 0.7, "reason": "ok" if coverage >= 0.7 else "low_support",
            "coverage": round(coverage, 3)}


def confidence(top_score: float, coverage: float, n_sources: int) -> str:
    if coverage >= 0.9 and top_score >= 0.03 and n_sources >= 2:
        return "high"
    if coverage >= 0.7:
        return "medium"
    return "low"
