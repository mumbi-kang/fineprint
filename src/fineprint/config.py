"""Project-wide settings. Change the MVP clause list here and nowhere else."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
CUAD_JSON = RAW_DIR / "CUAD_v1" / "CUAD_v1.json"
SPLITS_FILE = ROOT / "data" / "splits.json"

# The six MVP clause types. Names match CUAD categories (matching is case-insensitive).
MVP_CLAUSES = [
    "Renewal Term",
    "Notice Period To Terminate Renewal",
    "Expiration Date",
    "Termination For Convenience",
    "Cap On Liability",
    "Governing Law",
]

# Locked test set: never tune prompts on these contracts.
TEST_SET_SIZE = 30
SPLIT_SEED = 42
MIN_TEST_EXAMPLES_PER_CLAUSE = 5
