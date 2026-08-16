"""Create a factual schema, missingness, and class-distribution report."""
import json
from collections import Counter
from pathlib import Path
from datasets import Image, load_dataset

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "ml" / "data" / "raw" / "fashion-second-hand-front-only-rgb" / "data"
OUT = ROOT / "ml" / "data" / "reports" / "dataset_report.json"
CACHE = ROOT / ".hf-cache" / "datasets"


def main():
    files = {split: sorted(str(p) for p in RAW.glob(f"{split}-*.parquet")) for split in ("train", "test")}
    if not all(files.values()):
        raise SystemExit("Dataset snapshot is incomplete.")
    dataset = load_dataset("parquet", data_files=files, cache_dir=str(CACHE))
    dataset = dataset.cast_column("image", Image(decode=False))
    report = {"splits": {}, "columns": list(dataset["train"].column_names)}
    for split, data in dataset.items():
        missing = {column: 0 for column in data.column_names if column != "image"}
        distributions = {key: Counter() for key in ("usage", "condition", "type", "category", "pilling", "stains", "holes", "smell")}
        for row in data:
            for column in missing:
                if row[column] is None or str(row[column]).strip().lower() in {"", "none", "null", "nan"}:
                    missing[column] += 1
            for key in distributions:
                distributions[key][str(row[key] if row[key] is not None else "missing")] += 1
        report["splits"][split] = {"rows": len(data), "missing": missing, "distributions": {k: dict(v.most_common()) for k, v in distributions.items()}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
