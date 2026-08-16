"""
image_analysis.py
-----------------
Image Analysis Orchestrator
-----------------------------
This module is the entry point for the textile analysis pipeline.

Pipeline stages:
    1. Load & decode image with Pillow
    2. Compute pixel statistics (colour, texture, pattern, defects)
    3. Delegate to material_classifier  → fabric type, quality
    4. Delegate to waste_classifier     → waste category, disposal path
    5. Delegate to recommendation_engine → circular economy suggestions

The module purposely keeps only the pixel-level feature extraction here;
all downstream classification lives in dedicated service modules so each
stage can be independently tested or replaced with an ML model.
"""
import math
import os
import logging
from PIL import Image

from app.utils.image_utils import rgb_to_hex, get_color_name, get_dominant_color
from app.services.material_classifier import classify_material
from app.services.waste_classifier import classify_waste
from app.services.recommendation_engine import generate_recommendations
from app.services.model_service import model_service
from app.services.multitask_model_service import multitask_model_service
from app.services.label_composition import parse_label_composition
from app.services.destination_model_service import destination_model_service


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def _extract_features(image_path: str, sensitivity: float) -> dict:
    """
    Load an image and compute visual statistics used by downstream classifiers.

    Returns a flat feature dict consumed by classify_material() /
    classify_waste() / generate_recommendations().
    """
    with Image.open(image_path) as img:
        if img.mode != "RGB":
            img = img.convert("RGB")

        # --- Average colour (background-aware) -----------------------------
        avg_color = get_dominant_color(img)

        # --- 8×8 grid for variance analysis -------------------------------
        grid_img = img.resize((8, 8), Image.Resampling.BILINEAR)
        pixels   = list(grid_img.getdata())

        # Grayscale standard deviation → proxy for weave texture contrast
        gray_pixels = [int(0.299 * r + 0.587 * g + 0.114 * b) for r, g, b in pixels]
        mean_gray   = sum(gray_pixels) / len(gray_pixels)
        variance    = sum((p - mean_gray) ** 2 for p in gray_pixels) / len(gray_pixels)
        std_dev     = math.sqrt(variance)

        # Color variance → proxy for printed vs plain patterns
        color_variance = math.sqrt(
            sum(
                (r - avg_color[0]) ** 2 + (g - avg_color[1]) ** 2 + (b - avg_color[2]) ** 2
                for r, g, b in pixels
            ) / len(pixels)
        )

    # ------------------------------------------------------------------
    # Derived Boolean features
    # ------------------------------------------------------------------
    is_rough    = std_dev > 22.0        # high contrast ↔ rough/denim texture
    is_printed  = color_variance > 25.0 # high colour spread ↔ printed pattern

    # Brightness extremes → damage / contamination proxies
    max_gray       = max(gray_pixels)
    min_gray       = min(gray_pixels)
    contrast_range = max_gray - min_gray

    damage_score        = (contrast_range / 255.0) * sensitivity
    damage_detected     = damage_score > 0.18

    contamination_score    = (color_variance / 150.0) * sensitivity
    contamination_detected = contamination_score > 0.15

    # ------------------------------------------------------------------
    # Human-readable detail strings
    # ------------------------------------------------------------------
    if damage_detected:
        damage_details = (
            "Significant tears and multiple threadbare holes detected."
            if damage_score > 0.35
            else "Minor fraying and small punctures detected on fabric edges."
        )
    else:
        damage_details = "No physical tears or holes detected."

    if contamination_detected:
        contamination_details = (
            "Large grease stains and localised discolouration detected."
            if contamination_score > 0.3
            else "Surface dirt and faint chemical staining observed."
        )
    else:
        contamination_details = "Fabric surface is clean."

    color_name = get_color_name(avg_color)
    color_hex  = rgb_to_hex(avg_color)

    return {
        # Serialisable output fields
        "fabric_texture":          "rough" if is_rough else "smooth",
        "fabric_pattern":          "printed" if is_printed else "plain",
        "color_name":              color_name,
        "color_hex":               color_hex,
        "damage_detected":         damage_detected,
        "damage_details":          damage_details,
        "contamination_detected":  contamination_detected,
        "contamination_details":   contamination_details,
        # Internal fields consumed by downstream classifiers
        "is_rough":                is_rough,
        "is_printed":              is_printed,
        "color_variance":          color_variance,
        "std_dev":                 std_dev,
        "damage_score":            damage_score,
        "contamination_score":     contamination_score,
        "red":                     avg_color[0],
        "green":                   avg_color[1],
        "blue":                    avg_color[2],
    }


# ---------------------------------------------------------------------------
# Public pipeline entry point
# ---------------------------------------------------------------------------

def analyze_image_file(image_path: str, sensitivity: float = 0.5, label_text: str | None = None) -> dict:
    """
    Run the full textile analysis pipeline on a saved image file.

    Parameters
    ----------
    image_path  : str    Absolute or relative path to the image file.
    sensitivity : float  Defect detection sensitivity (0.0 → lenient, 1.0 → strict).

    Returns
    -------
    dict with keys: features, material, waste_classification, recommendations
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at {image_path}")

    # Stage 1 — Feature extraction
    features = _extract_features(image_path, sensitivity)

    # Stage 2 — Material classification. Prefer the image-trained composition
    # model; retain the older colour/texture classifier as a safe fallback.
    composition_prediction = None
    multitask_prediction = None
    try:
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
            multitask_prediction = multitask_model_service.predict(image_bytes)
            material_head = multitask_prediction["predictions"]["material"]
            composition_prediction = {
                "predicted_fabric": "Uncertain" if material_head["low_confidence"] else material_head["label"],
                "confidence": material_head["confidence"] * 100,
                "top_predictions": [
                    {"fabric": item["label"], "confidence": item["probability"] * 100}
                    for item in material_head["top_predictions"]
                ],
                "low_confidence": material_head["low_confidence"],
            }
    except (OSError, RuntimeError, ValueError):
        logger.exception("Multitask model failed; trying the legacy composition model")
        try:
            with open(image_path, "rb") as image_file:
                composition_prediction = model_service.predict(image_file.read())
        except (OSError, RuntimeError, ValueError):
            logger.exception("Legacy composition model failed; using deterministic fallback")
    material = classify_material(features, composition_prediction)
    material["alternatives"] = (composition_prediction or {}).get("top_predictions", [])
    label_material = parse_label_composition(label_text)
    if label_material is not None:
        label_material["quality"] = material["quality"]
        label_material["alternatives"] = []
        material = label_material
    else:
        material["evidence_source"] = "image_model"

    # Stage 3 — Waste classification
    waste = classify_waste(material, features)

    # Stage 4 — Recycling recommendations
    recommendations = generate_recommendations(waste, material)

    destination_intelligence = None
    try:
        destination_intelligence = destination_model_service.predict(features, material, multitask_prediction)
        waste["category"] = destination_intelligence["destination"]
    except (RuntimeError, ValueError, OSError):
        logger.exception("Structured destination model failed; retaining deterministic decision")

    # Build the public-facing features dict (strip internal helper keys)
    public_features = {
        "fabric_texture":         features["fabric_texture"],
        "fabric_pattern":         features["fabric_pattern"],
        "color_name":             features["color_name"],
        "color_hex":              features["color_hex"],
        "damage_detected":        features["damage_detected"],
        "damage_details":         features["damage_details"],
        "contamination_detected": features["contamination_detected"],
        "contamination_details":  features["contamination_details"],
    }

    return {
        "features":            public_features,
        "material":            material,
        "waste_classification": waste,
        "recommendations":     recommendations,
        "ai_predictions":      multitask_prediction,
        "destination_intelligence": destination_intelligence,
        "ai_disclaimer":       "AI-generated assessment. Predictions are probabilistic and should be reviewed by qualified personnel for operational recycling decisions.",
    }
