"""Preserve the official test set and create a seeded stratified validation set."""
import json

import pandas as pd
from sklearn.model_selection import train_test_split

from common import PROCESSED, REPORTS, SEED


def main():
    source = PROCESSED / "metadata.parquet"
    if not source.exists():
        raise SystemExit("Run build_metadata.py first")
    frame = pd.read_parquet(source)
    official_train = frame[frame["split"] == "train"].copy()
    official_test = frame[frame["split"] == "test"].copy()
    test_hashes = set(official_test["record_hash"])
    cross_split_duplicates = int(official_train["record_hash"].isin(test_hashes).sum())
    official_train = official_train[~official_train["record_hash"].isin(test_hashes)].reset_index(drop=True)
    official_test = official_test.reset_index(drop=True)
    frame = pd.concat([official_train, official_test], ignore_index=True)
    train_indices, validation_indices = train_test_split(
        official_train.index,
        test_size=0.15,
        random_state=SEED,
        stratify=official_train["usage_normalized"],
    )
    frame["training_split"] = "test"
    frame.loc[train_indices, "training_split"] = "train"
    frame.loc[validation_indices, "training_split"] = "validation"
    frame.to_parquet(PROCESSED / "metadata_with_splits.parquet", index=False)
    frame[["split", "row_index", "record_hash", "training_split"]].to_csv(PROCESSED / "splits.csv", index=False)
    hash_sets = {name: set(group["record_hash"]) for name, group in frame.groupby("training_split")}
    overlaps = {f"{left}_{right}": len(hash_sets[left] & hash_sets[right]) for left, right in (("train", "validation"), ("train", "test"), ("validation", "test"))}
    report = {
        "seed": SEED,
        "strategy": "official test split; seeded usage-stratified validation from official train",
        "item_identifier_available": False,
        "limitation": "The source dataset has no item identifier; item-level leakage cannot be proven.",
        "counts": frame["training_split"].value_counts().to_dict(),
        "cross_split_training_rows_removed": cross_split_duplicates,
        "record_hash_overlaps": overlaps,
        "no_exact_metadata_leakage": all(value == 0 for value in overlaps.values()),
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "leakage_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
