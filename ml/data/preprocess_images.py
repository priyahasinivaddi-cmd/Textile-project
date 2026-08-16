"""Decode, EXIF-normalize, resize, and export reproducible model-ready images."""
import argparse
import json
from pathlib import Path

from PIL import ImageOps

from common import PROCESSED, REPORTS, load


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=224)
    parser.add_argument("--limit", type=int, help="Optional per-split development cap")
    args = parser.parse_args()
    dataset = load(decode_images=True)
    output_root = PROCESSED / f"images_{args.size}"
    report = {"size": args.size, "splits": {}}
    for split, rows in dataset.items():
        destination = output_root / split
        destination.mkdir(parents=True, exist_ok=True)
        total = min(len(rows), args.limit) if args.limit else len(rows)
        failures = []
        for index in range(total):
            try:
                image = ImageOps.exif_transpose(rows[index]["image"]).convert("RGB")
                image.thumbnail((args.size, args.size))
                canvas = image.copy()
                canvas.save(destination / f"{index:06d}.jpg", quality=92, optimize=True)
            except Exception as exc:
                failures.append({"row_index": index, "error": str(exc)})
        report["splits"][split] = {"requested": total, "exported": total - len(failures), "failures": failures}
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "preprocessing_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(output_root)


if __name__ == "__main__":
    main()
