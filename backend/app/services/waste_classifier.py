"""
waste_classifier.py
--------------------
Waste Classification Module
-----------------------------
Uses material classification output + image condition features to assign a
waste category and recommend an initial disposal path.

Integrates trained ML models (Random Forest) if available, otherwise falls back
to the deterministic rule-based classifier.
"""

import os
import joblib
import pandas as pd

# ---------------------------------------------------------------------------
# Category metadata helpers
# ---------------------------------------------------------------------------

_CATEGORY_META = {
    "Reusable":    {"reuse_potential": "High",   "emoji": "♻️"},
    "Repairable":  {"reuse_potential": "Medium",  "emoji": "🔧"},
    "Upcyclable":  {"reuse_potential": "Medium",  "emoji": "🎨"},
    "Compostable": {"reuse_potential": "Low",     "emoji": "🌱"},
    "Hazardous":   {"reuse_potential": "Low",     "emoji": "⚠️"},
    "Recyclable":  {"reuse_potential": "Medium",  "emoji": "🔄"},
}

# ---------------------------------------------------------------------------
# ML Model Loading
# ---------------------------------------------------------------------------
MODEL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "models", 
    "saved_models"
)

WASTE_MODEL_PATH = os.path.join(MODEL_DIR, "waste_classifier.joblib")

WASTE_CLASSIFIER = None

try:
    if os.path.exists(WASTE_MODEL_PATH):
        WASTE_CLASSIFIER = joblib.load(WASTE_MODEL_PATH)
        print("Loaded waste_classifier ML model successfully.")
except Exception as e:
    print(f"Error loading waste classification ML model: {e}. Falling back to rule-based logic.")


def classify_waste(material: dict, features: dict) -> dict:
    """
    Classify textile waste category from material and feature data.

    Parameters
    ----------
    material : dict
        Output of `classify_material()`.  
        Expected keys: fabric_type, quality
    features : dict
        Output of `extract_features()` in image_analysis.py.  
        Expected keys: damage_detected, contamination_detected, color_name,
                       damage_score, contamination_score

    Returns
    -------
    dict with keys:
        category          – e.g. "Recyclable", "Reusable"
        reuse_potential   – "High" | "Medium" | "Low"
        disposal_method   – human-readable recommendation string
    """
    quality       = material["quality"]
    fabric_type   = material["fabric_type"]
    damage        = features["damage_detected"]
    contamination = features["contamination_detected"]
    color_name    = features["color_name"]

    category = None

    # Check if ML model is available
    if WASTE_CLASSIFIER is not None:
        try:
            X_w = pd.DataFrame([{
                "damage_score": features["damage_score"],
                "contamination_score": features["contamination_score"],
                "damage_detected": int(damage),
                "contamination_detected": int(contamination),
                "color_name": color_name,
                "fabric_type": fabric_type,
                "quality": quality
            }])
            category = WASTE_CLASSIFIER.predict(X_w)[0]
        except Exception as exc:
            print(f"ML waste classification failed: {exc}. Falling back to rule-based logic.")
            category = None

    # Fallback to rule-based logic
    if category is None:
        # ------------------------------------------------------------------
        # Classification decision tree
        # ------------------------------------------------------------------
        if quality == "high":
            category = "Reusable"
        elif quality == "medium":
            if damage and not contamination:
                category = "Repairable"
            else:
                category = "Upcyclable"
        else:  # quality == "low"
            natural_fibers = ("Cotton", "Linen", "Wool")
            if fabric_type in natural_fibers and not contamination:
                category = "Compostable"
            elif contamination and color_name in ("Black", "Grey"):
                category = "Hazardous"
            else:
                category = "Recyclable"

    # Map details based on predicted/fallback category
    disposal_methods = {
        "Reusable":    "Redirect to resale markets, clothing drives, or second-hand retailers.",
        "Repairable":  "Mend physical damage (darning, patching) before returning to stock.",
        "Upcyclable":  "Shred or cut for craft items, accessories, or patchwork designs.",
        "Compostable": "Process in commercial composting facilities to generate soil conditioner.",
        "Hazardous":   "Separate containment for chemical decontamination or incineration.",
        "Recyclable":  "Send to mechanical or chemical shredding and spinning units."
    }
    
    disposal_method = disposal_methods.get(
        category, 
        "Send to mechanical or chemical shredding and spinning units."
    )
    
    reuse_potential = _CATEGORY_META.get(category, {"reuse_potential": "Medium"})["reuse_potential"]

    return {
        "category":         category,
        "reuse_potential":  reuse_potential,
        "disposal_method":  disposal_method,
    }
