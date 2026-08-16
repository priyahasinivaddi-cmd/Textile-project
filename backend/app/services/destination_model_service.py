"""Calibrated structured model and visual/structured fusion for waste destinations."""
from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
ARTIFACT = ROOT / "ml" / "artifacts" / "destination" / "destination_model.joblib"
METADATA = ARTIFACT.with_name("metadata.json")


class DestinationModelService:
    def __init__(self) -> None:
        self.bundle: dict[str, Any] | None = None
        self.metadata: dict[str, Any] = {}
        self.error: str | None = None
        self._lock = Lock()

    def load(self) -> None:
        if self.bundle is not None:
            return
        with self._lock:
            try:
                self.bundle = joblib.load(ARTIFACT)
                self.metadata = json.loads(METADATA.read_text(encoding="utf-8"))
            except Exception as exc:
                self.error = str(exc)

    @staticmethod
    def _inputs(features: dict, material: dict, ai: dict) -> dict[str, Any]:
        predictions = (ai or {}).get("predictions", {})
        return {
            "condition": str(predictions.get("condition", {}).get("label", "unknown")).lower(),
            "type_normalized": str(predictions.get("type", {}).get("label", "unknown")).lower(),
            "category_normalized": "unknown",
            "pilling": "unknown",
            "damage": "damage" if features.get("damage_detected") else "none",
            "stains_normalized": "major" if features.get("contamination_detected") else "none",
            "holes_normalized": "yes" if features.get("damage_detected") else "none",
            "smell_normalized": "unknown",
            "pattern": features.get("fabric_pattern", "unknown"),
            "season": "unknown",
            "price": np.nan,
            "material_total_percentage": 100.0 if material.get("blend_type") == "single" else np.nan,
        }

    def predict(self, features: dict, material: dict, ai: dict | None) -> dict[str, Any]:
        self.load()
        if not self.bundle:
            raise RuntimeError(self.error or "Destination model unavailable")
        values = self._inputs(features, material, ai or {})
        model = self.bundle["model"]
        labels = self.bundle["label_encoder"].classes_
        structured = model.predict_proba(pd.DataFrame([values]))[0]
        visual_head = ((ai or {}).get("predictions") or {}).get("usage", {})
        visual = {item["label"].lower(): float(item["probability"]) for item in visual_head.get("top_predictions", [])}
        fused = np.asarray([0.65 * float(structured[i]) + 0.35 * visual.get(label.lower(), 0.0) for i, label in enumerate(labels)])
        fused /= fused.sum()
        order = np.argsort(fused)[::-1]
        ranked = [{"label": str(labels[i]).title(), "probability": round(float(fused[i]), 6)} for i in order]
        confidence = ranked[0]["probability"]
        reasons = [
            f"Condition signal: {values['condition']}",
            f"Garment signal: {values['type_normalized']}",
            f"Damage detected: {'yes' if features.get('damage_detected') else 'no'}",
            f"Staining/contamination detected: {'yes' if features.get('contamination_detected') else 'no'}",
            f"Material evidence: {material.get('fabric_type', 'unknown')}",
        ]
        return {
            "destination": ranked[0]["label"], "confidence": confidence,
            "probabilities": ranked, "calibrated": True,
            "fusion": {"structured_weight": 0.65, "visual_weight": 0.35},
            "manual_review_required": confidence < 0.70 or not self.metadata.get("quality_gate_passed", False),
            "reasoning": reasons,
            "global_drivers": self.metadata.get("global_feature_importance", [])[:8],
            "model_version": self.metadata.get("trained_at", "unknown"),
            "quality_gate_passed": self.metadata.get("quality_gate_passed", False),
            "warning": "Development model: macro-F1 quality gate was not met; a qualified reviewer must confirm this decision.",
        }

    def status(self) -> dict[str, Any]:
        self.load()
        return {"loaded": self.bundle is not None, "artifact": str(ARTIFACT), "error": self.error, **self.metadata}


destination_model_service = DestinationModelService()
