"""Train, calibrate, evaluate, and explain the structured destination classifier."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.frozen import FrozenEstimator
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "ml" / "data" / "processed" / "metadata_with_splits.parquet"
OUT = ROOT / "ml" / "artifacts" / "destination"
TARGET = "usage_normalized"
CATEGORICAL = [
    "condition", "type_normalized", "category_normalized", "pilling", "damage",
    "stains_normalized", "holes_normalized", "smell_normalized", "pattern", "season",
]
NUMERIC = ["price", "material_total_percentage"]


def calibration_error(y_true: np.ndarray, probabilities: np.ndarray, bins: int = 10) -> float:
    confidence = probabilities.max(axis=1)
    correct = probabilities.argmax(axis=1) == y_true
    edges = np.linspace(0, 1, bins + 1)
    total = len(y_true)
    return float(sum(
        abs(correct[(confidence > edges[i]) & (confidence <= edges[i + 1])].mean() -
            confidence[(confidence > edges[i]) & (confidence <= edges[i + 1])].mean()) *
        ((confidence > edges[i]) & (confidence <= edges[i + 1])).sum() / total
        for i in range(bins)
        if ((confidence > edges[i]) & (confidence <= edges[i + 1])).any()
    ))


def prepare(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame[CATEGORICAL + NUMERIC].copy()
    for column in CATEGORICAL:
        result[column] = result[column].fillna("unknown").astype(str).str.lower().str.strip()
    for column in NUMERIC:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--estimators", type=int, default=350)
    parser.add_argument("--max-depth", type=int, default=7)
    args = parser.parse_args()
    frame = pd.read_parquet(DATA)
    frame = frame[frame[TARGET].notna() & frame["training_split"].isin(["train", "validation", "test"])].copy()
    encoder = LabelEncoder().fit(frame[TARGET].astype(str))
    split = {name: frame[frame.training_split == name] for name in ("train", "validation", "test")}
    x = {name: prepare(value) for name, value in split.items()}
    y = {name: encoder.transform(value[TARGET].astype(str)) for name, value in split.items()}

    preprocessing = ColumnTransformer([
        ("category", Pipeline([
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore", min_frequency=3)),
        ]), CATEGORICAL),
        ("number", SimpleImputer(strategy="median", add_indicator=True), NUMERIC),
    ])
    classifier = XGBClassifier(
        n_estimators=args.estimators, max_depth=args.max_depth, learning_rate=0.06,
        subsample=0.85, colsample_bytree=0.85, objective="multi:softprob",
        eval_metric="mlogloss", n_jobs=-1, random_state=42,
    )
    pipeline = Pipeline([("features", preprocessing), ("classifier", classifier)])
    pipeline.fit(x["train"], y["train"], classifier__sample_weight=compute_sample_weight("balanced", y["train"]))
    calibrated = CalibratedClassifierCV(FrozenEstimator(pipeline), method="sigmoid")
    calibrated.fit(x["validation"], y["validation"])

    probabilities = calibrated.predict_proba(x["test"])
    predictions = probabilities.argmax(axis=1)
    report = classification_report(y["test"], predictions, target_names=encoder.classes_, output_dict=True, zero_division=0)
    metrics = {
        "accuracy": accuracy_score(y["test"], predictions),
        "macro_f1": report["macro avg"]["f1-score"],
        "weighted_f1": report["weighted avg"]["f1-score"],
        "log_loss": log_loss(y["test"], probabilities),
        "expected_calibration_error": calibration_error(y["test"], probabilities),
        "classification_report": report,
        "confusion_matrix": confusion_matrix(y["test"], predictions).tolist(),
    }

    transformed = pipeline.named_steps["features"].transform(x["test"].iloc[: min(500, len(x["test"]))])
    feature_names = pipeline.named_steps["features"].get_feature_names_out().tolist()
    explainer = shap.TreeExplainer(pipeline.named_steps["classifier"])
    shap_values = np.asarray(explainer.shap_values(transformed))
    axes = tuple(range(shap_values.ndim - 1)) if shap_values.ndim > 1 else (0,)
    importance = np.abs(shap_values).mean(axis=axes)
    if importance.shape[0] != len(feature_names):
        importance = np.abs(shap_values).mean(axis=tuple(i for i in range(shap_values.ndim) if i != 1))
    ranked = sorted(zip(feature_names, importance.tolist()), key=lambda item: item[1], reverse=True)[:30]

    OUT.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": calibrated, "label_encoder": encoder, "input_columns": CATEGORICAL + NUMERIC}, OUT / "destination_model.joblib")
    metadata = {
        "trained_at": datetime.now(timezone.utc).isoformat(), "classes": encoder.classes_.tolist(),
        "features": CATEGORICAL + NUMERIC, "split_rows": {name: len(value) for name, value in split.items()},
        "metrics": metrics, "quality_gate_passed": metrics["macro_f1"] >= 0.70,
        "global_feature_importance": [{"feature": name, "mean_abs_shap": score} for name, score in ranked],
        "limitations": [
            "Sparse stains, holes, and smell fields are treated as optional metadata.",
            "The current artifact uses structured metadata; visual outputs remain available from the EfficientNet service and are fused by the backend decision layer.",
            "Predictions below the configured confidence threshold require human review.",
        ],
    }
    (OUT / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps({"artifact": str(OUT), "metrics": {k: v for k, v in metrics.items() if k not in {"classification_report", "confusion_matrix"}}}, indent=2))


if __name__ == "__main__":
    main()
