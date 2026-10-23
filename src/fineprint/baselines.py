"""Simple non-AI predictors. They set the score the real AI has to beat.

- always_empty: never finds anything. Shows what "doing nothing" scores.
- keyword: grabs sentences containing telltale phrases. A cheap, honest baseline.
"""
from __future__ import annotations

import re

# Split on sentence-ending punctuation or blank lines
_SENTENCE_RE = re.compile(r"(?<=[.;])\s+(?=[A-Z(])|\n\s*\n")

KEYWORDS: dict[str, list[str]] = {
    "Governing Law": [r"governed by", r"laws of the state", r"construed in accordance with"],
    "Renewal Term": [r"automatically renew", r"renew(ed|al)? for (an? )?(additional|successive)"],
    "Notice Period To Terminate Renewal": [
        r"notice of (its )?(intent|intention) not to renew",
        r"(days|months)'? (prior )?(written )?notice .{0,60}(non-?renewal|not to renew)",
    ],
    "Expiration Date": [r"shall (expire|terminate) on", r"initial term of", r"term of this agreement shall"],
    "Termination For Convenience": [r"for convenience", r"terminate this agreement (at any time )?for any reason",
                                    r"without cause"],
    "Cap On Liability": [r"(aggregate|total|maximum) liability", r"shall not exceed",
                         r"in no event shall .{0,40}liab"],
}
_COMPILED = {k: [re.compile(p, re.IGNORECASE) for p in v] for k, v in KEYWORDS.items()}


def sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_RE.split(text) if s and s.strip()]


def always_empty(text: str) -> dict[str, list[str]]:
    return {}


def keyword(text: str, max_per_clause: int = 2) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for sent in sentences(text):
        for clause, patterns in _COMPILED.items():
            if len(out.get(clause, [])) >= max_per_clause:
                continue
            if any(p.search(sent) for p in patterns):
                out.setdefault(clause, []).append(sent)
    return out


PREDICTORS = {"always_empty": always_empty, "keyword": keyword}
