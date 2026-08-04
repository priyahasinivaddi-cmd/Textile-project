"""Validate textile images and annotations without deleting or changing data."""

from __future__ import annotations

import argparse
import csv
import hashlib
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, UnidentifiedImageError


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = SCRIPT_DIR / "dataset"
DEFAULT_CSV = DEFAULT_DATASET / "annotations.csv"
DEFAULT_IMAGE_ROOT = DEFAULT_DATASET / "FabricsCompositionDataset" / "FabricsCompositionDataset"
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
MIN_IMAGES_WARNING = 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--image-root", type=Path, default=DEFAULT_IMAGE_ROOT)
    parser.add_argument("--min-images", type=int, default=MIN_IMAGES_WARNING)
    parser.add_argument("--report", type=Path, default=SCRIPT_DIR / "dataset_validation_report.csv")
    return parser.parse_args()


def resolve_annotation_path(image_root: Path, raw_path: str) -> Path:
    normalized = raw_path.strip().replace("\\", "/")
    if normalized.startswith("dataset_root/"):
        normalized = normalized[len("dataset_root/") :]
    return image_root.joinpath(*Path(normalized).parts)


def iter_files(root: Path):
    if root.is_dir():
        yield from sorted(path for path in root.rglob("*") if path.is_file())
    elif root.is_file():
        yield root


def inspect_image(path: Path) -> tuple[str, str]:
    """Verify decoding and hash bytes; exact duplicate files share the digest."""
    try:
        with Image.open(path) as image:
            image.verify()
        return "ok", hashlib.sha256(path.read_bytes()).hexdigest()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        return "corrupt", str(exc)


def read_annotations(csv_path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not csv_path.is_file():
        return [], []
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        return list(reader), list(reader.fieldnames or [])


def main() -> int:
    args = parse_args()
    rows, columns = read_annotations(args.csv)
    target_columns = [column for column in columns if column.endswith("_pct")]
    report_rows: list[dict[str, object]] = []
    counts: Counter[str] = Counter()
    seen_files: set[Path] = set()
    digests: dict[str, Path] = {}

    annotation_paths: list[tuple[str, Path]] = []
    if rows and "relative_path" in columns:
        annotation_paths = [
            (str(row.get("id") or row["relative_path"]), resolve_annotation_path(args.image_root, row["relative_path"]))
            for row in rows
        ]
        print(f"Dataset folder: {args.image_root.resolve()}")
        print("Label mapping: annotations.csv *_pct columns -> composition targets")
        print(f"Targets: {target_columns}")
    else:
        print(f"Dataset folder: {args.dataset.resolve()}")
        print("Label mapping: immediate folder name -> class name")
        annotation_paths = [
            (folder.name, folder)
            for folder in sorted(args.dataset.iterdir())
            if folder.is_dir()
        ] if args.dataset.is_dir() else []

    if not annotation_paths:
        print("WARNING: no annotation paths or class folders were found.")

    for label, source in annotation_paths:
        files = list(iter_files(source))
        if not source.exists():
            report_rows.append({
                "dataset_path": str(source), "label": label, "file_path": "",
                "status": "missing_path", "duplicate_of": "", "details": "Annotated path does not exist",
            })
            continue
        supported_count = 0
        candidates: list[Path] = []
        for path in files:
            resolved = path.resolve()
            if resolved in seen_files:
                continue
            seen_files.add(resolved)
            suffix = path.suffix.lower()
            if suffix not in SUPPORTED_EXTENSIONS:
                report_rows.append({
                    "dataset_path": str(source), "label": label, "file_path": str(path),
                    "status": "unsupported_type", "duplicate_of": "", "details": suffix or "no extension",
                })
                continue
            supported_count += 1
            candidates.append(path)
        with ThreadPoolExecutor(max_workers=12) as executor:
            inspected = zip(candidates, executor.map(inspect_image, candidates))
            for path, (inspection_status, value) in inspected:
                if inspection_status == "ok":
                    digest = value
                    duplicate_of = digests.get(digest)
                    if duplicate_of:
                        status, details = "duplicate", "File content matches another image"
                    else:
                        status, details = "ok", ""
                        digests[digest] = path
                    report_rows.append({
                        "dataset_path": str(source), "label": label, "file_path": str(path),
                        "status": status, "duplicate_of": str(duplicate_of or ""), "details": details,
                    })
                else:
                    report_rows.append({
                        "dataset_path": str(source), "label": label, "file_path": str(path),
                        "status": "corrupt", "duplicate_of": "", "details": value,
                    })
        counts[label] += supported_count
        if supported_count < args.min_images:
            print(f"WARNING: {label} has only {supported_count} readable-candidate images (< {args.min_images}).")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    fields = ["dataset_path", "label", "file_path", "status", "duplicate_of", "details"]
    with args.report.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report_rows)

    statuses = Counter(str(row["status"]) for row in report_rows)
    print("\nImage counts by label/sample:")
    for label, count in sorted(counts.items()):
        print(f"  {label}: {count}")
    print(f"\nStatus totals: {dict(statuses)}")
    print(f"Report saved to: {args.report.resolve()}")
    if not seen_files:
        print("ERROR: no dataset image files were found; training cannot proceed.")
        return 2
    return 1 if statuses["corrupt"] or statuses["missing_path"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
