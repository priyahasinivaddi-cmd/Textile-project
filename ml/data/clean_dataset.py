"""Normalize reliable labels and material strings into processed Parquet metadata."""
import json

import pandas as pd

from common import PROCESSED, REPORTS, metadata_frame, normalize_label, parse_material, stable_record_hash


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    summary = {}
    for split in ("train", "test"):
        frame = metadata_frame(split)
        for key in ("usage", "type", "category", "stains", "holes", "smell"):
            frame[f"{key}_normalized"] = frame[key].map(lambda value, name=key: normalize_label(value, name))
        parsed = frame["material"].map(parse_material)
        frame["material_composition_json"] = parsed.map(lambda value: json.dumps(value["composition"]))
        frame["material_total_percentage"] = parsed.map(lambda value: value["total_percentage"])
        frame["material_valid"] = parsed.map(lambda value: value["valid"])
        frame["record_hash"] = frame.apply(lambda row: stable_record_hash(row.to_dict()), axis=1)
        before = len(frame)
        frame = frame.drop_duplicates(subset="record_hash", keep="first")
        frame.to_parquet(PROCESSED / f"{split}_metadata.parquet", index=False)
        summary[split] = {"input_rows": before, "output_rows": len(frame), "duplicates_removed": before - len(frame), "invalid_material_rows": int((~frame["material_valid"]).sum())}
    (REPORTS / "cleaning_report.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
