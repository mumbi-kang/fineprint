"""The eval harness: grades any predictor against CUAD's lawyer labels.

A predictor is any function that takes contract text and returns
{clause_type: [quote, quote, ...]}. An empty list means "not in this contract".

For each contract and clause type, the harness decides one outcome:
  TP  the clause is there and the predictor quoted it correctly
  FP  the predictor claimed a clause that isn't there, or quoted the wrong text
  FN  the clause is there but the predictor missed it
  TN  the clause isn't there and the predictor correctly said nothing
It also counts fabricated quotes: text that doesn't appear in the contract at all.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from fineprint.verify import normalize, quote_exists

Predictor = Callable[[str], dict[str, list[str]]]


@dataclass
class LabeledContract:
    title: str
    text: str
    gold: dict[str, list[str]]  # clause type -> lawyer-highlighted spans


def overlaps(quote: str, gold_span: str) -> bool:
    """A quote counts as correct if it and a lawyer label overlap enough:
    one contains the other (after normalizing spacing, ignoring case)."""
    q, g = normalize(quote).lower(), normalize(gold_span).lower()
    if not q or not g:
        return False
    return q in g or g in q


@dataclass
class ClauseScore:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0

    @property
    def precision(self) -> float | None:
        """Of the times we said 'found it', how often were we right?"""
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else None

    @property
    def recall(self) -> float | None:
        """Of the clauses that really exist, how many did we find?"""
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else None

    @property
    def f1(self) -> float | None:
        p, r = self.precision, self.recall
        if p is None or r is None or p + r == 0:
            return None
        return 2 * p * r / (p + r)


@dataclass
class EvalReport:
    predictor_name: str
    split: str
    n_contracts: int
    scores: dict[str, ClauseScore] = field(default_factory=dict)
    quotes_total: int = 0
    quotes_fabricated: int = 0
    examples: list[dict] = field(default_factory=list)  # a few mistakes to inspect

    @property
    def fabrication_rate(self) -> float:
        return self.quotes_fabricated / self.quotes_total if self.quotes_total else 0.0

    def to_dict(self) -> dict:
        return {
            "predictor": self.predictor_name,
            "split": self.split,
            "n_contracts": self.n_contracts,
            "quotes_total": self.quotes_total,
            "quotes_fabricated": self.quotes_fabricated,
            "fabrication_rate": self.fabrication_rate,
            "clauses": {
                k: {"tp": s.tp, "fp": s.fp, "fn": s.fn, "tn": s.tn,
                    "precision": s.precision, "recall": s.recall, "f1": s.f1}
                for k, s in self.scores.items()
            },
            "examples": self.examples,
        }


def evaluate(
    predictor: Predictor,
    contracts: list[LabeledContract],
    clause_types: list[str],
    predictor_name: str = "predictor",
    split: str = "dev",
    max_examples: int = 20,
) -> EvalReport:
    report = EvalReport(predictor_name, split, len(contracts),
                        {c: ClauseScore() for c in clause_types})

    for contract in contracts:
        predictions = predictor(contract.text)
        for clause in clause_types:
            gold = contract.gold.get(clause, [])
            quotes = [q for q in predictions.get(clause, []) if normalize(q)]

            # Fabrication guard: drop quotes that aren't in the contract at all
            real_quotes = []
            for q in quotes:
                report.quotes_total += 1
                if quote_exists(q, contract.text):
                    real_quotes.append(q)
                else:
                    report.quotes_fabricated += 1

            score = report.scores[clause]
            correct = any(overlaps(q, g) for q in real_quotes for g in gold)
            if gold and correct:
                score.tp += 1
                outcome = "TP"
            elif gold:
                score.fn += 1
                outcome = "FN"
                if real_quotes:  # quoted the wrong text: also a false alarm
                    score.fp += 1
                    outcome = "FN+FP"
            elif real_quotes:
                score.fp += 1
                outcome = "FP"
            else:
                score.tn += 1
                outcome = "TN"

            if outcome not in ("TP", "TN") and len(report.examples) < max_examples:
                report.examples.append({
                    "contract": contract.title, "clause": clause, "outcome": outcome,
                    "predicted": [q[:200] for q in real_quotes],
                    "gold": [g[:200] for g in gold],
                })
    return report


def format_report(report: EvalReport) -> str:
    def pct(x):
        return "  n/a" if x is None else f"{x:5.0%}"

    lines = [
        f"Predictor: {report.predictor_name} | split: {report.split} | contracts: {report.n_contracts}",
        "",
        f"{'Clause type':<38}{'Prec':>6}{'Recall':>8}{'F1':>6}   TP  FP  FN  TN",
    ]
    for clause, s in report.scores.items():
        lines.append(f"{clause:<38}{pct(s.precision):>6}{pct(s.recall):>8}{pct(s.f1):>6}"
                     f" {s.tp:4}{s.fp:4}{s.fn:4}{s.tn:4}")
    lines += ["", f"Fabricated quotes: {report.quotes_fabricated}/{report.quotes_total}"
                  f" ({report.fabrication_rate:.0%})"]
    return "\n".join(lines)


def load_labeled(processed_dir: Path, titles: set[str]) -> list[LabeledContract]:
    """Load contracts + lawyer labels written by scripts/load_cuad.py."""
    out = []
    with open(processed_dir / "labels.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["title"] not in titles:
                continue
            text = (processed_dir / r["text_file"]).read_text(encoding="utf-8")
            gold = {k: [s["text"] for s in v] for k, v in r["labels"].items()}
            out.append(LabeledContract(r["title"], text, gold))
    return out
