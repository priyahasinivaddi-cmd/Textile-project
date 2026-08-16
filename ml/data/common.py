import hashlib
import json
import re
from pathlib import Path

import pandas as pd
from datasets import Image, load_dataset

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "ml" / "data" / "raw" / "fashion-second-hand-front-only-rgb" / "data"
CACHE = ROOT / ".hf-cache" / "datasets"
PROCESSED = ROOT / "ml" / "data" / "processed"
REPORTS = ROOT / "ml" / "data" / "reports"
SEED = 42
REQUIRED = {"image", "usage", "condition", "type", "category", "material", "pilling", "damage", "stains", "holes", "smell"}
ALIASES = {
    "rcycle": "recycle", "poly": "polyester", "elastan": "elastane",
    "acryl": "acrylic", "akryl": "acrylic", "ull": "wool",
    "bomull": "cotton", "viskos": "viscose", "polyamide": "nylon",
}


def files():
    result = {split: sorted(str(path) for path in RAW.glob(f"{split}-*.parquet")) for split in ("train", "test")}
    if not all(result.values()):
        raise FileNotFoundError("Pinned dataset snapshot is incomplete; run download_dataset.py")
    return result


def load(decode_images=False):
    dataset = load_dataset("parquet", data_files=files(), cache_dir=str(CACHE))
    return dataset if decode_images else dataset.cast_column("image", Image(decode=False))


def text(value):
    return str(value or "unknown").strip().lower()


def normalize_label(value, key):
    value = text(value)
    if key == "usage":
        value = ALIASES.get(value, value)
    if key == "category":
        value = {"ladys": "ladies", "women": "ladies"}.get(value, value)
    if key == "type":
        value = {"jacker": "jacket", "nightgown": "night gown"}.get(value, value)
    return value


def parse_material(value):
    raw = text(value)
    parts = []
    for percentage, material in re.findall(r"(\d+(?:\.\d+)?)\s*%\s*([a-zA-Z]+)", raw):
        name = ALIASES.get(material.lower(), material.lower())
        parts.append({"material": name, "percentage": float(percentage)})
    total = sum(item["percentage"] for item in parts)
    valid = bool(parts) and 95 <= total <= 105
    return {"raw": raw, "composition": parts, "total_percentage": round(total, 2), "valid": valid}


def metadata_frame(split):
    dataset = load(False)[split]
    frame = dataset.remove_columns("image").to_pandas()
    frame.insert(0, "row_index", range(len(frame)))
    frame.insert(1, "split", split)
    return frame


def stable_record_hash(row):
    payload = json.dumps({key: str(value) for key, value in sorted(row.items()) if key not in {"row_index", "split"}}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
