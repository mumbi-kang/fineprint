# FinePrint

An AI contract copilot for small businesses. It finds renewal traps, notice deadlines, and risky clauses, cites the exact contract text, and lets a human approve every finding.

> Compliance support, not legal advice.

## Week 1 setup

**1. Environment**
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

**2. Database** (needs Docker Desktop running)
```bash
docker compose up -d
docker compose ps                # wait for "healthy"
```

**3. Get CUAD**
Download `CUAD_v1.zip` from the Atticus Project (atticusprojectai.org/cuad, also mirrored on Zenodo).
Unzip it so this path exists: `data/raw/CUAD_v1/CUAD_v1.json`

**4. Load data and lock the test set**
```bash
python scripts/load_cuad.py      # coverage report, span check, creates data/splits.json
python scripts/load_to_db.py     # loads contracts + labels into Postgres
pytest
```

**5. Commit `data/splits.json`.** That's the locked test set. Never tune prompts on those 30 contracts.

## MVP clause types
Renewal Term · Notice Period To Terminate Renewal · Expiration Date · Termination For Convenience · Cap On Liability · Governing Law

## Layout
```
src/fineprint/   config.py (clause list, split settings), cuad.py (loader, span check, split)
scripts/            load_cuad.py, load_to_db.py
sql/init.sql        schema (runs automatically on first `docker compose up`)
tests/              unit tests on a tiny fake CUAD file
```
