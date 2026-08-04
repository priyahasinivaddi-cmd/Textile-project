"""Audit TextileNet target classes and reversibly quarantine unsafe images."""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageStat, UnidentifiedImageError


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT = SCRIPT_DIR / "dataset" / "fiber"
TARGET_CLASSES = (
    "cotton", "polyester", "wool", "silk", "flax_linen",
    "nylon", "viscose_rayon", "acrylic",
)
EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


@dataclass
class Record:
    split: str
    label: str
    path: Path
    status: str = "ok"
    reason: str = ""
    exact_hash: str = ""
    perceptual_hash: str = ""
    width: int = 0
    height: int = 0
    brightness_std: float = 0.0
    duplicate_of: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--report", type=Path, default=SCRIPT_DIR / "fibre_cleaning_audit.csv")
    parser.add_argument("--quarantine", type=Path, default=SCRIPT_DIR / "dataset_quarantine")
    parser.add_argument("--apply-quarantine", action="store_true")
    parser.add_argument(
        "--restore-manifest",
        action="store_true",
        help="Restore every file listed in the quarantine manifest.",
    )
    parser.add_argument(
        "--apply-existing-report",
        action="store_true",
        help="Apply quarantine decisions from --report without rescanning images.",
    )
    parser.add_argument("--workers", type=int, default=12)
    return parser.parse_args()


def difference_hash(image: Image.Image) -> str:
    gray = image.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    pixels = np.asarray(gray, dtype=np.int16)
    bits = pixels[:, 1:] > pixels[:, :-1]
    value = 0
    for bit in bits.ravel():
        value = (value << 1) | int(bit)
    return f"{value:016x}"


def inspect(record: Record) -> Record:
    try:
        digest = hashlib.sha256()
        with record.path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        with Image.open(record.path) as image:
            image.load()
            record.width, record.height = image.size
            record.exact_hash = digest.hexdigest()
            record.perceptual_hash = difference_hash(image)
            record.brightness_std = float(ImageStat.Stat(image.convert("L")).stddev[0])
            if min(image.size) < 128:
                record.status, record.reason = "review", "low_resolution"
            elif record.brightness_std < 8:
                record.status, record.reason = "review", "low_visual_information"
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        record.status, record.reason = "quarantine", f"corrupt:{type(exc).__name__}"
    return record


def collect(root: Path) -> list[Record]:
    records: list[Record] = []
    for split in ("train", "test"):
        for label in TARGET_CLASSES:
            folder = root / split / label
            if not folder.is_dir():
                raise FileNotFoundError(f"Missing class folder: {folder}")
            records.extend(
                Record(split, label, path)
                for path in sorted(folder.iterdir())
                if path.is_file() and path.suffix.lower() in EXTENSIONS
            )
    return records


def mark_exact_duplicates(records: list[Record]) -> None:
    groups: dict[str, list[Record]] = defaultdict(list)
    for record in records:
        if record.exact_hash:
            groups[record.exact_hash].append(record)
    for group in groups.values():
        if len(group) < 2:
            continue
        labels = {record.label for record in group}
        if len(labels) > 1:
            for record in group:
                record.status = "quarantine"
                record.reason = "exact_duplicate_conflicting_labels"
            continue
        canonical = sorted(group, key=lambda row: (row.split != "train", str(row.path)))[0]
        for record in group:
            if record is canonical:
                continue
            record.status = "quarantine"
            record.reason = "exact_duplicate"
            record.duplicate_of = str(canonical.path)


def mark_perceptual_matches(records: list[Record]) -> None:
    # Exact dHash matches are conservative near-duplicate candidates. They are
    # review-only because crops and lighting variants may still be useful.
    groups: dict[str, list[Record]] = defaultdict(list)
    for record in records:
        if record.perceptual_hash and record.status != "quarantine":
            groups[record.perceptual_hash].append(record)
    for group in groups.values():
        if len(group) < 2:
            continue
        labels = {record.label for record in group}
        if len(labels) > 1:
            for record in group:
                record.status = "review"
                record.reason = "perceptual_duplicate_conflicting_labels"
            continue
        canonical = sorted(group, key=lambda row: (row.split != "train", str(row.path)))[0]
        for record in group:
            if record is not canonical and record.status == "ok":
                record.status = "review"
                record.reason = "perceptual_duplicate"
                record.duplicate_of = str(canonical.path)


def quarantine(records: list[Record], root: Path, destination: Path) -> None:
    manifest = destination / "quarantine_manifest.csv"
    moved: list[dict[str, str]] = []
    for record in records:
        if record.status != "quarantine" or not record.path.exists():
            continue
        relative = record.path.relative_to(root)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            target = target.with_name(f"{target.stem}_{record.exact_hash[:8]}{target.suffix}")
        shutil.move(str(record.path), str(target))
        moved.append({"original_path": str(record.path), "quarantine_path": str(target), "reason": record.reason})
    destination.mkdir(parents=True, exist_ok=True)
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("original_path", "quarantine_path", "reason"))
        writer.writeheader()
        writer.writerows(moved)
    print(f"Quarantined {len(moved):,} images; recovery manifest: {manifest}")


def restore_manifest(destination: Path) -> None:
    manifest = destination / "quarantine_manifest.csv"
    restored = 0
    with manifest.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        source = Path(row["quarantine_path"])
        target = Path(row["original_path"])
        if not source.exists():
            continue
        if target.exists():
            raise FileExistsError(f"Cannot restore over an existing file: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
        restored += 1
    print(f"Restored {restored:,} images from {manifest}")


def read_report(path: Path) -> list[Record]:
    records: list[Record] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            records.append(
                Record(
                    split=row["split"],
                    label=row["label"],
                    path=Path(row["path"]),
                    status=row["status"],
                    reason=row["reason"],
                    exact_hash=row["exact_hash"],
                    perceptual_hash=row["perceptual_hash"],
                    width=int(row["width"]),
                    height=int(row["height"]),
                    brightness_std=float(row["brightness_std"]),
                    duplicate_of=row["duplicate_of"],
                )
            )
    return records


def main() -> int:
    args = parse_args()
    if args.restore_manifest:
        restore_manifest(args.quarantine)
        return 0
    if args.apply_existing_report:
        if not args.report.is_file():
            raise FileNotFoundError(f"Audit report does not exist: {args.report}")
        records = read_report(args.report)
        quarantine(records, args.root, args.quarantine)
        return 0
    records = collect(args.root)
    print(f"Inspecting {len(records):,} images across {len(TARGET_CLASSES)} target classes...")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        records = list(pool.map(inspect, records))
    mark_exact_duplicates(records)
    mark_perceptual_matches(records)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    fields = tuple(Record.__dataclass_fields__)
    with args.report.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({field: str(getattr(record, field)) for field in fields})

    totals = Counter(record.status for record in records)
    reasons = Counter(record.reason for record in records if record.reason)
    print(f"Status totals: {dict(totals)}")
    print(f"Flag reasons: {dict(reasons)}")
    print(f"Audit report: {args.report}")
    if args.apply_quarantine:
        quarantine(records, args.root, args.quarantine)
    else:
        print("Dry run only; no images moved. Use --apply-quarantine after reviewing the report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
