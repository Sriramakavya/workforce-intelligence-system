"""Regenerate twice with the same seed and compare counts and SHA-256 hashes."""
from pathlib import Path
import argparse, json
from src.data_generator import generate, RAW, TRUTH

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"

def verify(scale="starter", seed=20261022):
    first_manifest = generate(scale, seed)
    first_hashes = json.loads((RAW / "checksums.json").read_text())
    first_truth = (TRUTH / "ground_truth.csv").read_bytes()
    second_manifest = generate(scale, seed)
    second_hashes = json.loads((RAW / "checksums.json").read_text())
    second_truth = (TRUTH / "ground_truth.csv").read_bytes()
    report = {
        "scale": scale, "seed": seed,
        "row_counts_match": first_manifest["generated_tables"] == second_manifest["generated_tables"],
        "csv_checksums_match": first_hashes == second_hashes,
        "ground_truth_checksum_match": first_truth == second_truth,
        "row_counts": second_manifest["generated_tables"],
        "all_reproducibility_checks_pass": (
            first_manifest["generated_tables"] == second_manifest["generated_tables"]
            and first_hashes == second_hashes and first_truth == second_truth
        )
    }
    OUT.mkdir(exist_ok=True)
    (OUT / "reproducibility_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    if not report["all_reproducibility_checks_pass"]:
        raise SystemExit(1)
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", choices=["starter", "full"], default="starter")
    parser.add_argument("--seed", type=int, default=20261022)
    args = parser.parse_args()
    verify(args.scale, args.seed)
