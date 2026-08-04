"""
material_classifier.py
-----------------------
Material Classification Module
--------------------------------
Takes extracted visual features and classifies the textile into a fabric type,
predicts fiber composition, detects blends, and estimates material quality.

Integrates trained ML models (Random Forest) if available, otherwise falls back
to the deterministic rule-based classifier.
"""

import os
import re
import joblib
import pandas as pd
from app.utils.image_utils import get_color_name

# ---------------------------------------------------------------------------
# ML Model Loading
# ---------------------------------------------------------------------------
MODEL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "models", 
    "saved_models"
)

QUALITY_MODEL_PATH = os.path.join(MODEL_DIR, "quality_classifier.joblib")

# Kept as a compatibility marker for older diagnostics. Fabric predictions now
# come exclusively from the image-trained Keras model in model_service.py.
FABRIC_CLASSIFIER = None
QUALITY_CLASSIFIER = None

try:
    if os.path.exists(QUALITY_MODEL_PATH):
        QUALITY_CLASSIFIER = joblib.load(QUALITY_MODEL_PATH)
        print("Loaded quality_classifier ML model successfully.")
except Exception as e:
    print(f"Error loading material classification ML models: {e}. Falling back to rule-based logic.")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

FIBRE_DISPLAY_NAMES = {
    "cotton": "Cotton", "wool": "Wool", "linen": "Linen", "silk": "Silk",
    "viscose": "Rayon", "modal": "Modal", "lyocell": "Lyocell",
    "acetate": "Acetate", "polyester": "Polyester", "polyamide": "Nylon",
    "elastane": "Elastane", "acrylic": "Acrylic", "other": "Other fibres",
}


def _material_from_composition(prediction: dict) -> dict | None:
    """Convert the image composition model output into material details."""
    predicted_fabric = prediction.get("predicted_fabric")
    if predicted_fabric and predicted_fabric != "Uncertain":
        confidence = max(0.0, min(float(prediction.get("confidence", 0.0)) / 100.0, 1.0))
        top_predictions = prediction.get("top_predictions") or []
        return {
            "fabric_type": str(predicted_fabric),
            "confidence": round(confidence, 4),
            "fiber_composition": " / ".join(
                f"{float(item['confidence']):.1f}% {item['fabric']}"
                for item in top_predictions
                if float(item.get("confidence", 0.0)) >= 5.0
            ) or f"{confidence * 100:.1f}% {predicted_fabric}",
            "blend_type": "mixed" if sum(
                float(item.get("confidence", 0.0)) >= 20.0 for item in top_predictions
            ) > 1 else "single",
        }
    if prediction.get("low_confidence"):
        confidence = max(0.0, min(float(prediction.get("confidence", 0.0)) / 100.0, 1.0))
        top_predictions = prediction.get("top_predictions") or []
        return {
            "fabric_type": "Uncertain",
            "confidence": round(confidence, 4),
            "fiber_composition": " / ".join(
                f"{float(item['confidence']):.1f}% {item['fabric']}"
                for item in top_predictions
                if float(item.get("confidence", 0.0)) >= 5.0
            ) or "The new model could not determine the material reliably",
            "blend_type": "unknown",
        }
    composition = prediction.get("predicted_composition")
    if not isinstance(composition, dict) or not composition:
        return None

    usable = []
    for raw_name, raw_percentage in composition.items():
        try:
            percentage = max(0.0, float(raw_percentage))
        except (TypeError, ValueError):
            continue
        name = re.sub(r"_pct$", "", str(raw_name)).lower()
        if percentage >= 1.0:
            usable.append((name, percentage))
    if not usable:
        return None

    usable.sort(key=lambda item: item[1], reverse=True)
    dominant_name, dominant_percentage = usable[0]
    fabric_type = FIBRE_DISPLAY_NAMES.get(dominant_name, dominant_name.replace("_", " ").title())
    if dominant_name == "other":
        fabric_type = "Mixed fabrics"
    meaningful = [(name, value) for name, value in usable if value >= 5.0]

    return {
        "fabric_type": fabric_type,
        "confidence": round(min(dominant_percentage / 100.0, 1.0), 4),
        "fiber_composition": " / ".join(
            f"{value:.1f}% {FIBRE_DISPLAY_NAMES.get(name, name.replace('_', ' ').title())}"
            for name, value in usable
        ),
        "blend_type": "mixed" if len(meaningful) > 1 else "single",
    }


def classify_material(features: dict, composition_prediction: dict | None = None) -> dict:
    """
    Classify textile material from extracted image features.

    Parameters
    ----------
    features : dict
        Output dict from `extract_features()` in image_analysis.py.
        Expected keys: color_name, is_rough, is_printed,
                       damage_detected, contamination_detected, color_variance,
                       std_dev, damage_score, contamination_score, red, green, blue

    Returns
    -------
    dict with keys:
        fabric_type        – e.g. "Cotton", "Denim", "Polyester"
        confidence         – float 0–1
        fiber_composition  – human-readable composition string
        blend_type         – "single" | "mixed"
        quality            – "high" | "medium" | "low"
    """
    color_name      = features["color_name"]
    is_rough        = features["is_rough"]
    is_printed      = features["is_printed"]
    color_variance  = features["color_variance"]
    damage          = features["damage_detected"]
    contamination   = features["contamination_detected"]

    composition_material = _material_from_composition(composition_prediction or {})

    # Fabric classification comes exclusively from the image-trained model.
    # Low-confidence predictions remain explicitly uncertain so an older model
    # cannot silently replace the new model's result.
    if composition_material is not None:
        fabric_type = composition_material["fabric_type"]
        confidence = composition_material["confidence"]
    else:
        fabric_type = None

    if QUALITY_CLASSIFIER is not None:
        try:
            X_q = pd.DataFrame([{
                "damage_score": features["damage_score"],
                "contamination_score": features["contamination_score"],
                "damage_detected": int(damage),
                "contamination_detected": int(contamination)
            }])
            quality = QUALITY_CLASSIFIER.predict(X_q)[0]
        except Exception as exc:
            print(f"ML quality classification failed: {exc}. Falling back to rule-based logic.")
            quality = None
    else:
        quality = None

    # Fallback to rule-based logic if ML models are missing or failed
    if fabric_type is None:
        # ------------------------------------------------------------------
        # Step 1 — Fabric type from visual features
        # ------------------------------------------------------------------
        if color_name == "Blue" and is_rough:
            fabric_type = "Denim"
            confidence  = 0.94
        elif color_name in ("Beige", "White") and is_rough and not is_printed:
            fabric_type = "Linen"
            confidence  = 0.88
        elif is_rough and color_name in ("Grey", "Brown", "Black"):
            fabric_type = "Wool"
            confidence  = 0.82
        elif not is_rough and not is_printed and color_name in ("White", "Pink", "Yellow"):
            fabric_type = "Silk"
            confidence  = 0.90
        elif is_printed:
            fabric_type = "Polyester"
            confidence  = 0.80
        elif not is_rough and color_name in ("Grey", "Blue"):
            fabric_type = "Nylon"
            confidence  = 0.78
        else:
            fabric_type = "Cotton"
            confidence  = 0.85

        # ------------------------------------------------------------------
        # Step 4 — Quality estimation
        # ------------------------------------------------------------------
    if quality is None:
        if damage and contamination:
            quality = "low"
        elif damage or contamination:
            quality = "medium"
        else:
            quality = "high"

    # ------------------------------------------------------------------
    # Step 2 — Blend detection (high color variance signals multi-fiber)
    # ------------------------------------------------------------------
    is_blend  = color_variance > 35.0
    blend_type = (
        composition_material["blend_type"]
        if composition_material is not None
        else ("mixed" if is_blend else "single")
    )

    # ------------------------------------------------------------------
    # Step 3 — Fiber composition
    # ------------------------------------------------------------------
    compositions = {
        "Cotton":    "60% Cotton / 40% Polyester" if is_blend else "100% Cotton",
        "Polyester": "70% Polyester / 30% Viscose" if is_blend else "100% Polyester",
        "Wool":      "80% Wool / 20% Nylon" if is_blend else "100% Wool",
        "Silk":      "100% Mulberry Silk",
        "Linen":     "100% Linen",
        "Denim":     "98% Cotton / 2% Elastane",
        "Nylon":     "100% Polyamide (Nylon)",
        "Rayon":     "100% Rayon / Viscose",
        "Acrylic":   "100% Acrylic",
    }
    fiber_composition = (
        composition_material["fiber_composition"]
        if composition_material is not None
        else compositions.get(fabric_type, "Composition could not be determined reliably")
    )
    if composition_material is None and fabric_type not in compositions:
        fabric_type = "Mixed fabrics"
        blend_type  = "mixed"

    return {
        "fabric_type":       fabric_type,
        "confidence":        confidence,
        "fiber_composition": fiber_composition,
        "blend_type":        blend_type,
        "quality":           quality,
    }
