"""Load CUAD (SQuAD-style JSON) and keep only the clause types we care about."""
from __future__ import annotations

import json
import random
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

_QUESTION_RE = re.compile(r'related to "([^"]+)"')


def normalize(name: str) -> str:
    return " ".join(name.lower().split())


def category_of(qa: dict) -> str | None:
    """CUAD question ids look like '<contract title>__<Category>'. Fall back to the question text."""
    qid = qa.get("id", "")
    if "__" in qid:
        return normalize(qid.rsplit("__", 1)[1])
    match = _QUESTION_RE.search(qa.get("question", ""))
    return normalize(match.group(1)) if match else None


@dataclass
class Span:
    text: str
    start: int

    @property
    def end(self) -> int:
        return self.start + len(self.text)


@dataclass
class Contract:
    title: str
    text: str
    labels: dict[str, list[Span]] = field(default_factory=dict)

    def has(self, clause: str) -> bool:
        return bool(self.labels.get(clause))

    def to_record(self) -> dict:
        """JSON-friendly record without the full text (text is saved separately)."""
        return {
            "title": self.title,
            "char_len": len(self.text),
            "labels": {k: [asdict(s) | {"end": s.end} for s in v] for k, v in self.labels.items()},
        }


def load_cuad(path: Path | str, clause_types: list[str]) -> list[Contract]:
    wanted = {normalize(c): c for c in clause_types}
    raw = json.loads(Path(path).read_text(encoding="utf-8"))

    contracts: list[Contract] = []
    seen_categories: set[str] = set()
    for doc in raw["data"]:
        for para in doc["paragraphs"]:
            contract = Contract(doc["title"], para["context"], {c: [] for c in clause_types})
            for qa in para["qas"]:
                cat = category_of(qa)
                if cat:
                    seen_categories.add(cat)
                if cat not in wanted:
                    continue
                unique = {(a["answer_start"], a["text"]) for a in qa.get("answers", [])}
                contract.labels[wanted[cat]] = [Span(t, s) for s, t in sorted(unique)]
            contracts.append(contract)

    missing = [c for c in clause_types if normalize(c) not in seen_categories]
    if missing:
        raise ValueError(
            f"These clause types were not found in CUAD: {missing}. "
            f"Available categories: {sorted(seen_categories)}"
        )
    return contracts


def verify_spans(contracts: list[Contract]) -> list[tuple[str, str, Span]]:
    """Return every label whose text doesn't match the contract at its offset.
    Same idea as the quote check we'll run on model output later."""
    bad = []
    for c in contracts:
        for clause, spans in c.labels.items():
            for s in spans:
                if c.text[s.start : s.end] != s.text:
                    bad.append((c.title, clause, s))
    return bad


def coverage(contracts: list[Contract], clause_types: list[str]) -> Counter:
    return Counter(clause for c in contracts for clause in clause_types if c.has(clause))


def make_split(
    contracts: list[Contract],
    clause_types: list[str],
    test_size: int,
    seed: int,
    min_per_clause: int,
) -> tuple[list[str], list[str]]:
    """Seeded split that guarantees each clause type shows up in the test set.
    Rarest clause types get filled first, then the rest is random."""
    rng = random.Random(seed)
    pool = sorted(c.title for c in contracts)  # sort first so the split is reproducible
    rng.shuffle(pool)
    by_title = {c.title: c for c in contracts}

    test: list[str] = []
    counts = coverage(contracts, clause_types)
    for clause in sorted(clause_types, key=lambda k: counts[k]):
        have = sum(by_title[t].has(clause) for t in test)
        for title in pool:
            if have >= min_per_clause or len(test) >= test_size:
                break
            if title not in test and by_title[title].has(clause):
                test.append(title)
                have += 1

    for title in pool:
        if len(test) >= test_size:
            break
        if title not in test:
            test.append(title)

    test_set = set(test)
    dev = [t for t in pool if t not in test_set]
    return sorted(test), sorted(dev)


def safe_filename(title: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", title)[:150] + ".txt"
