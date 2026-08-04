"""Load the production fabric model once and provide safe predictions."""

from __future__ import annotations

import json
import logging
import csv
from io import BytesIO
from pathlib import Path
from threading import Lock
from typing import Any

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError


logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_DIR = PROJECT_ROOT / "waste-classification"
MODEL_PATH = ARTIFACT_DIR / "best_fabric_model.keras"
CLASS_NAMES_PATH = ARTIFACT_DIR / "class_names.json"
EXPECTED_INPUT_SIZE = (160, 160)
CONFIDENCE_THRESHOLD = 70.0


def display_name(name: str) -> str:
    aliases = {"polyamide": "Nylon", "viscose": "Rayon", "other": "Other fibres"}
    return aliases.get(name.lower(), name.replace("_", " ").title())


class ModelService:
    """Own the single model instance used for the lifetime of the API process."""

    def __init__(self) -> None:
        self.model: Any | None = None
        self.class_names: list[str] | None = None
        self.load_error: str | None = None
        self._load_attempted = False
        self._lock = Lock()
        self._prediction_lock = Lock()

    # Compatibility for code that checks the previous attribute name.
    @property
    def target_columns(self) -> list[str] | None:
        return self.class_names

    @target_columns.setter
    def target_columns(self, value: list[str] | None) -> None:
        self.class_names = [item.removesuffix("_pct") for item in value] if value else value

    def load(self) -> None:
        with self._lock:
            if self.model is not None and self.class_names is not None:
                self._load_attempted = True
                return
            if self._load_attempted:
                return
            self._load_attempted = True
            try:
                import tensorflow as tf

                if not MODEL_PATH.is_file():
                    raise FileNotFoundError(f"Production model is missing: {MODEL_PATH}")
                if not CLASS_NAMES_PATH.is_file():
                    raise FileNotFoundError(f"Class mapping is missing: {CLASS_NAMES_PATH}")
                labels = json.loads(CLASS_NAMES_PATH.read_text(encoding="utf-8"))
                if not isinstance(labels, list) or not labels or not all(isinstance(item, str) and item for item in labels):
                    raise ValueError("class_names.json must contain a non-empty list of class names")
                loaded = tf.keras.models.load_model(MODEL_PATH, compile=False)
                output_count = int(loaded.output_shape[-1])
                input_size = tuple(int(value) for value in loaded.input_shape[1:3])
                if output_count != len(labels):
                    raise ValueError(f"Model has {output_count} outputs but class_names.json has {len(labels)} labels")
                if input_size != EXPECTED_INPUT_SIZE:
                    raise ValueError(f"Model input size {input_size} does not match production size {EXPECTED_INPUT_SIZE}")
                self.class_names, self.model = labels, loaded
                logger.info("Loaded production fabric model with %d classes", len(labels))
            except Exception as exc:
                self.model = None
                self.class_names = None
                self.load_error = str(exc)
                logger.exception("Unable to load the production fabric model")

    def preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        try:
            with Image.open(BytesIO(image_bytes)) as image:
                image.verify()
            with Image.open(BytesIO(image_bytes)) as image:
                image = ImageOps.exif_transpose(image).convert("RGB")
                logger.info("Decoded uploaded image dimensions: %dx%d", image.width, image.height)
                image = image.resize(EXPECTED_INPUT_SIZE, Image.Resampling.BILINEAR)
                pixels = np.asarray(image, dtype=np.float32)
        except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
            raise ValueError("The uploaded file is not a valid supported image") from exc
        # The production model embeds MobileNetV2 preprocessing and expects
        # ordinary RGB values in the [0, 255] range.
        return np.expand_dims(pixels, axis=0)

    def predict(self, image_bytes: bytes) -> dict[str, Any]:
        self.load()
        if self.model is None or self.class_names is None:
            raise RuntimeError(self.load_error or "The fabric model is unavailable")
        try:
            with self._prediction_lock:
                raw = self.model.predict(self.preprocess_image(image_bytes), verbose=0)
            probabilities = np.asarray(raw, dtype=np.float64).reshape(-1)
        except ValueError:
            raise
        except Exception as exc:
            logger.exception("Fabric prediction failed")
            raise RuntimeError("The model could not generate a prediction") from exc
        if probabilities.size != len(self.class_names) or not np.all(np.isfinite(probabilities)):
            raise RuntimeError("The model returned an invalid prediction")
        # Compatibility with a mock or a legacy normalized-positive output; the
        # production softmax model already sums to one.
        probabilities = np.maximum(probabilities, 0.0)
        total = float(probabilities.sum())
        if total <= 0:
            raise RuntimeError("The model returned no positive probabilities")
        probabilities /= total
        order = np.argsort(probabilities)[::-1][: min(3, len(probabilities))]
        top = [
            {"fabric": display_name(self.class_names[index]), "confidence": round(float(probabilities[index] * 100), 2)}
            for index in order
        ]
        confidence = top[0]["confidence"]
        low_confidence = confidence < CONFIDENCE_THRESHOLD
        logger.info(
            "Fabric prediction: model_input_shape=%s class_index=%d class_name=%s "
            "confidence=%.2f low_confidence=%s",
            tuple(getattr(self.model, "input_shape", (None, *EXPECTED_INPUT_SIZE, 3))),
            int(order[0]),
            top[0]["fabric"],
            confidence,
            low_confidence,
        )
        result: dict[str, Any] = {
            "predicted_fabric": "Uncertain" if low_confidence else top[0]["fabric"],
            "confidence": confidence,
            "top_predictions": top,
            "low_confidence": low_confidence,
        }
        if low_confidence:
            result["message"] = "The image could not be classified confidently. Upload a clearer fabric image."
        return result

    def status(self) -> dict[str, Any]:
        self.load()
        output_count = int(self.model.output_shape[-1]) if self.model is not None else None
        label_count = len(self.class_names) if self.class_names is not None else None
        training_metrics: dict[str, float | int] = {}
        history_path = ARTIFACT_DIR / "training_history.csv"
        try:
            with history_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            if rows:
                last = rows[-1]
                training_metrics = {
                    "epochs_completed": len(rows),
                    "training_accuracy_percent": round(float(last["accuracy"]) * 100, 2),
                    "validation_accuracy_percent": round(float(last["val_accuracy"]) * 100, 2),
                    "validation_loss": round(float(last["val_loss"]), 4),
                }
        except (OSError, KeyError, TypeError, ValueError):
            logger.warning("Training history metadata could not be read", exc_info=True)
        return {
            "model_loaded": self.model is not None,
            "class_names_loaded": self.class_names is not None,
            "target_labels_loaded": self.class_names is not None,
            "expected_input_size": {"width": EXPECTED_INPUT_SIZE[0], "height": EXPECTED_INPUT_SIZE[1]},
            "model_output_count": output_count,
            "class_name_count": label_count,
            "target_label_count": label_count,
            "outputs_match_class_names": output_count == label_count if output_count is not None and label_count is not None else False,
            "outputs_match_target_labels": output_count == label_count if output_count is not None and label_count is not None else False,
            "confidence_threshold_percent": CONFIDENCE_THRESHOLD,
            "model_artifact": MODEL_PATH.name,
            "model_size_mb": round(MODEL_PATH.stat().st_size / (1024 * 1024), 2) if MODEL_PATH.is_file() else None,
            "model_updated_at": MODEL_PATH.stat().st_mtime if MODEL_PATH.is_file() else None,
            "classes": [display_name(name) for name in self.class_names] if self.class_names else [],
            "training_metrics": training_metrics,
            "error": self.load_error,
        }


model_service = ModelService()
