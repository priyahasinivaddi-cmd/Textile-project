"""Validate schema, metadata duplicates, label support, and optionally image integrity."""
import argparse
import json
from collections import Counter

from common import REPORTS, REQUIRED, load, stable_record_hash


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-images", action="store_true", help="Decode every image; slower but detects corruption.")
    args = parser.parse_args()
    dataset = load(decode_images=args.check_images)
    report = {"valid": True, "splits": {}, "schema": list(dataset["train"].column_names)}
    missing_columns = sorted(REQUIRED - set(report["schema"]))
    if missing_columns:
        report["valid"] = False
        report["missing_columns"] = missing_columns
    for split, rows in dataset.items():
        hashes, corrupted = Counter(), []
        metadata = rows.remove_columns("image").to_pandas()
        for record in metadata.to_dict(orient="records"):
            hashes[stable_record_hash(record)] += 1
        if args.check_images:
            for index in range(len(rows)):
                try:
                    image = rows[index]["image"]
                    image.load()
                    if image.width < 32 or image.height < 32:
                        raise ValueError("image is smaller than 32px")
                except Exception as exc:
                    corrupted.append({"row_index": index, "error": str(exc)})
        duplicates = sum(count - 1 for count in hashes.values() if count > 1)
        report["splits"][split] = {"rows": len(rows), "metadata_duplicates": duplicates, "corrupted_images": corrupted}
        report["valid"] = report["valid"] and not corrupted
    REPORTS.mkdir(parents=True, exist_ok=True)
    path = REPORTS / "validation_report.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(path)
    raise SystemExit(0 if report["valid"] else 1)


if __name__ == "__main__":
    main()
