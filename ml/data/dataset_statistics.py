"""Generate class distributions, missingness, and sparse-target eligibility."""
import json

import pandas as pd

from common import PROCESSED, REPORTS

TARGETS = ("usage", "condition", "type", "category", "material", "pilling", "damage", "stains", "holes", "smell")


def main():
    source = PROCESSED / "metadata_with_splits.parquet"
    if not source.exists():
        raise SystemExit("Run split_dataset.py first")
    frame = pd.read_parquet(source)
    report = {"rows": len(frame), "splits": frame["training_split"].value_counts().to_dict(), "targets": {}}
    for target in TARGETS:
        normalized = f"{target}_normalized"
        values = frame[normalized] if normalized in frame.columns else frame[target]
        present = values.notna() & ~values.astype(str).str.strip().str.lower().isin(["", "none", "null", "nan"])
        counts = values[present].astype(str).str.strip().str.lower().value_counts()
        coverage = float(present.mean())
        report["targets"][target] = {
            "source_column": normalized if normalized in frame.columns else target,
            "coverage": round(coverage, 6),
            "missing": int((~present).sum()),
            "classes": counts.to_dict(),
            "eligible_for_automated_head": bool(coverage >= 0.60 and len(counts) >= 2 and counts.min() >= 25),
        }
    REPORTS.mkdir(parents=True, exist_ok=True)
    path = REPORTS / "dataset_statistics.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
