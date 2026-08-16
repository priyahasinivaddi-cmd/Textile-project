"""Inference adapter for the promoted EfficientNet multitask checkpoint."""
from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from threading import Lock
from typing import Any

import numpy as np
from PIL import Image, ImageOps

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_DIR = PROJECT_ROOT / "ml" / "artifacts" / "multitask" / "b0"
MODEL_PATH = ARTIFACT_DIR / "best_model.keras"
MAPPING_PATH = ARTIFACT_DIR / "label_mapping.json"
METADATA_PATH = ARTIFACT_DIR / "metadata.json"
CONFIDENCE_THRESHOLD = 0.70
MATERIAL_ALIASES = {
    "acry": "acrylic", "akryl": "acrylic", "bomull": "cotton",
    "cott": "cotton", "nylo": "nylon", "nylone": "nylon",
    "polyamide": "nylon", "visc": "viscose", "viscos": "viscose",
    "viskos": "viscose",
}


class MultitaskModelService:
    def __init__(self) -> None:
        self.model: Any | None = None
        self.mappings: dict[str, dict[str, int]] = {}
        self.metadata: dict[str, Any] = {}
        self.load_error: str | None = None
        self._lock = Lock()

    def load(self) -> None:
        if self.model is not None:
            return
        with self._lock:
            if self.model is not None:
                return
            try:
                import tensorflow as tf
                self.mappings = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
                self.metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
                self.model = tf.keras.models.load_model(MODEL_PATH, compile=False)
                if set(self.model.output_names) != set(self.mappings):
                    raise ValueError("Checkpoint outputs do not match the label mapping")
            except Exception as exc:
                self.model = None
                self.load_error = str(exc)

    @staticmethod
    def preprocess(image_bytes: bytes) -> np.ndarray:
        with Image.open(BytesIO(image_bytes)) as image:
            image = ImageOps.exif_transpose(image).convert("RGB").resize((224, 224), Image.Resampling.BILINEAR)
            return np.expand_dims(np.asarray(image, dtype=np.float32), 0)

    def _head(self, name: str, probabilities: np.ndarray) -> dict[str, Any]:
        reverse = {index: label for label, index in self.mappings[name].items()}
        values = np.asarray(probabilities, dtype=np.float64).reshape(-1)
        values = np.maximum(values, 0)
        values /= values.sum()
        if name == "material":
            merged: dict[str, float] = {}
            for index, probability in enumerate(values):
                label = MATERIAL_ALIASES.get(reverse[index], reverse[index])
                merged[label] = merged.get(label, 0.0) + float(probability)
            ranked = sorted(merged.items(), key=lambda item: item[1], reverse=True)
        else:
            ranked = sorted(((reverse[index], float(value)) for index, value in enumerate(values)), key=lambda item: item[1], reverse=True)
        top = [{"label": label.replace("_", " ").title(), "probability": round(probability, 6)} for label, probability in ranked[:3]]
        confidence = top[0]["probability"]
        return {
            "label": top[0]["label"],
            "confidence": confidence,
            "top_predictions": top,
            "low_confidence": confidence < CONFIDENCE_THRESHOLD,
        }

    def predict(self, image_bytes: bytes) -> dict[str, Any]:
        self.load()
        if self.model is None:
            raise RuntimeError(self.load_error or "Multitask checkpoint unavailable")
        raw = self.model.predict(self.preprocess(image_bytes), verbose=0)
        outputs = raw if isinstance(raw, dict) else dict(zip(self.model.output_names, raw))
        heads = {name: self._head(name, outputs[name][0]) for name in self.mappings}
        return {
            "model": "EfficientNet-B0 multitask",
            "model_version": self.metadata.get("trained_at", "unknown"),
            "development_model": True,
            "manual_review_required": any(head["low_confidence"] for head in heads.values()),
            "warning": "Model quality gates were not met; qualified human review is required.",
            "predictions": heads,
        }

    def status(self) -> dict[str, Any]:
        self.load()
        metrics = self.metadata.get("metrics", {})
        return {
            "loaded": self.model is not None,
            "model": "EfficientNet-B0 multitask",
            "artifact": str(MODEL_PATH),
            "development_model": True,
            "quality_gate_passed": False,
            "test_macro_f1": {name: report.get("macro avg", {}).get("f1-score") for name, report in metrics.items()},
            "error": self.load_error,
        }


multitask_model_service = MultitaskModelService()
