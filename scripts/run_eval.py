"""Week 2: grade a predictor against CUAD's lawyer labels.

Usage:
    python scripts/run_eval.py                          # keyword baseline on the dev set
    python scripts/run_eval.py --predictor always_empty
    python scripts/run_eval.py --split test --confirm-test   # the locked final exam: use rarely!

Results are saved to data/results/<predictor>_<split>.json so you can compare runs over time.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fineprint import config  # noqa: E402
from fineprint.baselines import PREDICTORS  # noqa: E402
from fineprint.eval import evaluate, format_report, load_labeled  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictor", choices=sorted(PREDICTORS), default="keyword")
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--confirm-test", action="store_true",
                        help="required to run on the locked test set")
    args = parser.parse_args()

    if args.split == "test" and not args.confirm_test:
        sys.exit("The test set is your final exam. Add --confirm-test if you really mean it.")

    split = json.loads(config.SPLITS_FILE.read_text())
    contracts = load_labeled(config.PROCESSED_DIR, set(split[args.split]))
    report = evaluate(PREDICTORS[args.predictor], contracts, config.MVP_CLAUSES,
                      predictor_name=args.predictor, split=args.split)
    print(format_report(report))

    results_dir = config.ROOT / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    out = results_dir / f"{args.predictor}_{args.split}.json"
    out.write_text(json.dumps(report.to_dict(), indent=2))
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
