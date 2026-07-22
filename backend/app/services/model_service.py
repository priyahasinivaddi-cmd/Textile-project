"""Lifecycle-managed loader for the textile composition Keras model."""

from __future__ import annotations

import json
import logging
from io import BytesIO
from pathlib import Path
from threading import Lock
from typing import Any

import numpy as np
from PIL import Image, UnidentifiedImageError


logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = PROJECT_ROOT / "waste-classification" / "fabric_composition_model.keras"
TARGET_COLUMNS_PATH = PROJECT_ROOT / "waste-classification" / "target_columns.json"
EXPECTED_INPUT_SIZE = (224, 224)


class ModelService:
    """Owns the single model instance used for the lifetime of the API process."""

    def __init__(self) -> None:
        # TensorFlow is imported lazily in load(). This keeps unrelated API
        # routes (including authentication) available if the ML runtime or
        # model artifact cannot be loaded.
        self.model: Any | None = None
        self.target_columns: list[str] | None = None
        self.load_error: str | None = None
        self._load_attempted = False
        self._lock = Lock()
        self._prediction_lock = Lock()

    def load(self) -> None:
        """Load artifacts once; retain a safe error message if loading fails."""
        with self._lock:
            if self._load_attempted:
                return
            self._load_attempted = True

            try:
                import tensorflow as tf

                if not MODEL_PATH.is_file():
                    raise FileNotFoundError(f"Model file is missing: {MODEL_PATH}")
                if not TARGET_COLUMNS_PATH.is_file():
                    raise FileNotFoundError(
                        f"Target columns file is missing: {TARGET_COLUMNS_PATH}"
                    )

                with TARGET_COLUMNS_PATH.open(encoding="utf-8") as target_file:
                    labels = json.load(target_file)
                if not isinstance(labels, list) or not labels or not all(
                    isinstance(label, str) for label in labels
                ):
                    raise ValueError("target_columns.json must contain a non-empty list of strings")

                self.target_columns = labels
                self.model = tf.keras.models.load_model(MODEL_PATH, compile=False)
                logger.info(
                    "Textile composition model loaded with %d target labels",
                    len(labels),
                )
            except Exception as exc:
                self.model = None
                self.load_error = str(exc)
                logger.exception("Unable to load the textile composition model")

    def preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        """Decode an image and apply the same preprocessing used for training."""
        try:
            with Image.open(BytesIO(image_bytes)) as image:
                image = image.convert("RGB")
                image = image.resize(EXPECTED_INPUT_SIZE, Image.Resampling.BILINEAR)
                image_array = np.asarray(image, dtype=np.float32)
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise ValueError("The uploaded file is not a valid PNG or JPEG image") from exc

        # Equivalent to tf.keras.applications.mobilenet_v2.preprocess_input:
        # convert RGB values from [0, 255] to [-1, 1].
        image_array = (image_array / 127.5) - 1.0
        return np.expand_dims(image_array, axis=0)

    def predict(self, image_bytes: bytes) -> dict[str, Any]:
        if self.model is None or self.target_columns is None:
            raise RuntimeError(self.load_error or "The composition model is unavailable")

        batch = self.preprocess_image(image_bytes)
        try:
            with self._prediction_lock:
                raw_prediction = self.model.predict(batch, verbose=0)
            values = np.asarray(raw_prediction, dtype=np.float64).reshape(-1)
        except Exception as exc:
            logger.exception("Textile composition prediction failed")
            raise RuntimeError("The model could not generate a prediction") from exc

        if values.size != len(self.target_columns) or not np.all(np.isfinite(values)):
            raise RuntimeError("The model returned an invalid prediction shape or values")

        values = np.maximum(values, 0.0)
        raw_total = float(values.sum())
        if raw_total <= 0:
            raise RuntimeError("The model did not predict any positive composition values")
        values = values * (100.0 / raw_total)

        composition = {
            label.removesuffix("_pct"): round(float(value), 2)
            for label, value in zip(self.target_columns, values)
        }
        # Correct the small rounding drift so the displayed values total 100.00.
        rounded_total = round(sum(composition.values()), 2)
        dominant_fibre = max(composition, key=composition.get)
        composition[dominant_fibre] = round(
            composition[dominant_fibre] + (100.0 - rounded_total), 2
        )

        return {
            "dominant_fibre": dominant_fibre,
            "predicted_composition": composition,
            "total_percentage": round(sum(composition.values()), 2),
        }

    def status(self) -> dict[str, Any]:
        model_output_count: int | None = None
        if self.model is not None:
            output_shape = self.model.output_shape
            if isinstance(output_shape, tuple) and output_shape:
                model_output_count = int(output_shape[-1])

        target_count = len(self.target_columns) if self.target_columns is not None else None
        return {
            "model_loaded": self.model is not None,
            "target_labels_loaded": self.target_columns is not None,
            "expected_input_size": {
                "width": EXPECTED_INPUT_SIZE[0],
                "height": EXPECTED_INPUT_SIZE[1],
            },
            "model_output_count": model_output_count,
            "target_label_count": target_count,
            "outputs_match_target_labels": (
                model_output_count == target_count
                if model_output_count is not None and target_count is not None
                else False
            ),
            "error": self.load_error,
        }


model_service = ModelService()
