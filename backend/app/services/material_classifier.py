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

FABRIC_MODEL_PATH = os.path.join(MODEL_DIR, "fabric_classifier.joblib")
QUALITY_MODEL_PATH = os.path.join(MODEL_DIR, "quality_classifier.joblib")

FABRIC_CLASSIFIER = None
QUALITY_CLASSIFIER = None

try:
    if os.path.exists(FABRIC_MODEL_PATH):
        FABRIC_CLASSIFIER = joblib.load(FABRIC_MODEL_PATH)
        print("Loaded fabric_classifier ML model successfully.")
    if os.path.exists(QUALITY_MODEL_PATH):
        QUALITY_CLASSIFIER = joblib.load(QUALITY_MODEL_PATH)
        print("Loaded quality_classifier ML model successfully.")
except Exception as e:
    print(f"Error loading material classification ML models: {e}. Falling back to rule-based logic.")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_material(features: dict) -> dict:
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

    # Check if ML models are available
    if FABRIC_CLASSIFIER is not None and QUALITY_CLASSIFIER is not None:
        try:
            # 1. Predict Fabric Type
            X_fab = pd.DataFrame([{
                "std_dev": features["std_dev"],
                "color_variance": features["color_variance"],
                "red": features["red"],
                "green": features["green"],
                "blue": features["blue"],
                "color_name": color_name,
                "is_rough": int(is_rough),
                "is_printed": int(is_printed)
            }])
            fabric_type = FABRIC_CLASSIFIER.predict(X_fab)[0]
            confidence = float(max(FABRIC_CLASSIFIER.predict_proba(X_fab)[0]))

            # 2. Predict Quality
            X_q = pd.DataFrame([{
                "damage_score": features["damage_score"],
                "contamination_score": features["contamination_score"],
                "damage_detected": int(damage),
                "contamination_detected": int(contamination)
            }])
            quality = QUALITY_CLASSIFIER.predict(X_q)[0]

        except Exception as exc:
            print(f"ML classification failed: {exc}. Falling back to rule-based logic.")
            fabric_type = None
            quality = None
    else:
        fabric_type = None
        quality = None

    # Fallback to rule-based logic if ML models are missing or failed
    if fabric_type is None or quality is None:
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
    blend_type = "mixed" if is_blend else "single"

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
    fiber_composition = compositions.get(
        fabric_type,
        "50% Polyester / 30% Cotton / 20% Acrylic"
    )
    if fabric_type not in compositions:
        fabric_type = "Mixed fabrics"
        blend_type  = "mixed"

    return {
        "fabric_type":       fabric_type,
        "confidence":        confidence,
        "fiber_composition": fiber_composition,
        "blend_type":        blend_type,
        "quality":           quality,
    }
