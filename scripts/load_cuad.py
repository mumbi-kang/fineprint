"""Week 1: load CUAD, report label coverage, verify spans, and lock the test split.

Usage:
    python scripts/load_cuad.py              # first run creates data/splits.json
    python scripts/load_cuad.py --force      # rebuild the split (don't do this casually)
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fineprint import config  # noqa: E402
from fineprint.cuad import coverage, load_cuad, make_split, safe_filename, verify_spans  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cuad", type=Path, default=config.CUAD_JSON)
    parser.add_argument("--force", action="store_true", help="overwrite an existing locked split")
    args = parser.parse_args()

    if not args.cuad.exists():
        sys.exit(f"Can't find {args.cuad}. Unzip CUAD_v1.zip into data/raw/ first (see README).")

    contracts = load_cuad(args.cuad, config.MVP_CLAUSES)
    print(f"Loaded {len(contracts)} contracts\n")

    counts = coverage(contracts, config.MVP_CLAUSES)
    print(f"{'Clause type':<38}{'Contracts':>10}{'Share':>8}")
    for clause in config.MVP_CLAUSES:
        print(f"{clause:<38}{counts[clause]:>10}{counts[clause] / len(contracts):>8.0%}")

    bad = verify_spans(contracts)
    total = sum(len(s) for c in contracts for s in c.labels.values())
    print(f"\nSpan check: {total - len(bad)}/{total} labels match the contract text exactly")
    for title, clause, span in bad[:5]:
        print(f"  mismatch: {title} | {clause} | {span.text[:60]!r}")

    # Save per-contract labels + raw text
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    text_dir = config.PROCESSED_DIR / "text"
    text_dir.mkdir(exist_ok=True)
    with open(config.PROCESSED_DIR / "labels.jsonl", "w", encoding="utf-8") as f:
        for c in contracts:
            record = c.to_record() | {"text_file": f"text/{safe_filename(c.title)}"}
            f.write(json.dumps(record) + "\n")
            (text_dir / safe_filename(c.title)).write_text(c.text, encoding="utf-8")
    print(f"Wrote {config.PROCESSED_DIR / 'labels.jsonl'}")

    # Lock the test split
    if config.SPLITS_FILE.exists() and not args.force:
        split = json.loads(config.SPLITS_FILE.read_text())
        print(f"\nTest split already locked ({len(split['test'])} contracts). Use --force to rebuild.")
    else:
        test, dev = make_split(
            contracts, config.MVP_CLAUSES, config.TEST_SET_SIZE,
            config.SPLIT_SEED, config.MIN_TEST_EXAMPLES_PER_CLAUSE,
        )
        split = {"seed": config.SPLIT_SEED, "test": test, "dev": dev}
        config.SPLITS_FILE.write_text(json.dumps(split, indent=2))
        print(f"\nLocked split: {len(test)} test / {len(dev)} dev -> {config.SPLITS_FILE}")

    test_contracts = [c for c in contracts if c.title in set(split["test"])]
    test_counts = coverage(test_contracts, config.MVP_CLAUSES)
    print("Test-set coverage:", {k: test_counts[k] for k in config.MVP_CLAUSES})


if __name__ == "__main__":
    main()
