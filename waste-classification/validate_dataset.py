"""Inspect and validate the textile dataset without training a model."""

from __future__ import annotations

import csv
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DATASET_DIR = SCRIPT_DIR / "dataset"
CSV_PATH = DATASET_DIR / "annotations.csv"
IMAGE_ROOT = (
    DATASET_DIR / "FabricsCompositionDataset" / "FabricsCompositionDataset"
)
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def resolve_csv_path(relative_path: str) -> Path:
    """Map a CSV dataset_root path to its real location under IMAGE_ROOT."""
    normalized = relative_path.strip().replace("\\", "/")
    prefix = "dataset_root/"
    if normalized.startswith(prefix):
        normalized = normalized[len(prefix) :]
    return IMAGE_ROOT.joinpath(*Path(normalized).parts)


def main() -> None:
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";")
        rows = list(reader)
        columns = reader.fieldnames or []

    if "relative_path" not in columns:
        raise ValueError("annotations.csv has no 'relative_path' column")

    print("CSV columns:")
    print(columns)

    print("\nFirst five rows:")
    for row_number, row in enumerate(rows[:5], start=1):
        print(f"{row_number}: {row}")

    print("\nrelative_path values:")
    for row in rows:
        print(row["relative_path"])

    pct_columns = [column for column in columns if column.endswith("_pct")]
    print("\nColumns ending with _pct:")
    print(pct_columns)

    png_paths = sorted(
        path for path in IMAGE_ROOT.rglob("*") if path.is_file() and path.suffix.lower() == ".png"
    )
    all_image_paths = sorted(
        path
        for path in IMAGE_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )

    print(f"\nActual PNG images found: {len(png_paths)}")
    print("First five PNG paths:")
    for path in png_paths[:5]:
        print(path)

    print("\nCSV path join rule:")
    print("Remove the 'dataset_root/' prefix, then join the remainder to:")
    print(IMAGE_ROOT)
    if rows:
        example = rows[0]["relative_path"]
        print(f"Example: {example} -> {resolve_csv_path(example)}")

    valid_count = 0
    missing: list[tuple[str, Path, str]] = []
    for row in rows:
        relative_path = row["relative_path"]
        resolved_path = resolve_csv_path(relative_path)
        if resolved_path.is_file():
            has_image = resolved_path.suffix.lower() in IMAGE_EXTENSIONS
        elif resolved_path.is_dir():
            has_image = any(
                path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
                for path in resolved_path.rglob("*")
            )
        else:
            has_image = False

        if has_image:
            valid_count += 1
        else:
            reason = "path missing" if not resolved_path.exists() else "no images found"
            missing.append((relative_path, resolved_path, reason))

    print("\nValidation summary:")
    print(f"Total CSV rows: {len(rows)}")
    print(f"Valid image paths: {valid_count}")
    print(f"Missing image paths: {len(missing)}")
    print(f"Total image files on disk (PNG/JPG/JPEG): {len(all_image_paths)}")

    if missing:
        print("\nMissing image path details:")
        for relative_path, resolved_path, reason in missing:
            print(f"- {relative_path} -> {resolved_path} ({reason})")


if __name__ == "__main__":
    main()
