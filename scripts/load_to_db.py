"""Load processed CUAD labels and the split into Postgres.

Run after: docker compose up -d  and  python scripts/load_cuad.py
"""
import json
import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fineprint import config  # noqa: E402


def main() -> None:
    load_dotenv(config.ROOT / ".env")
    dsn = os.getenv("DATABASE_URL", "postgresql://fineprint:fineprint@localhost:5432/fineprint")
    split = json.loads(config.SPLITS_FILE.read_text())
    test = set(split["test"])

    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        n_contracts = n_labels = 0
        for line in open(config.PROCESSED_DIR / "labels.jsonl", encoding="utf-8"):
            r = json.loads(line)
            cur.execute(
                """INSERT INTO contracts (title, source, split, char_len, text_file)
                   VALUES (%s, 'cuad', %s, %s, %s)
                   ON CONFLICT (title) DO UPDATE SET split = EXCLUDED.split
                   RETURNING id""",
                (r["title"], "test" if r["title"] in test else "dev", r["char_len"], r["text_file"]),
            )
            contract_id = cur.fetchone()[0]
            cur.execute("DELETE FROM clause_labels WHERE contract_id = %s", (contract_id,))
            for clause, spans in r["labels"].items():
                for s in spans:
                    cur.execute(
                        """INSERT INTO clause_labels (contract_id, clause_type, span_text, span_start, span_end)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (contract_id, clause, s["text"], s["start"], s["end"]),
                    )
                    n_labels += 1
            n_contracts += 1
    print(f"Loaded {n_contracts} contracts and {n_labels} ground-truth labels into Postgres")


if __name__ == "__main__":
    main()
