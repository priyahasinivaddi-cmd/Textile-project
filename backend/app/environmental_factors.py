"""Configurable factors for sustainability estimates.

These planning values are not laboratory-certified measurements. Keeping them
centralized allows verified organization-specific factors to replace them.
"""

DEFAULT_FABRIC = "default"

FABRIC_FACTORS: dict[str, dict[str, float]] = {
    "cotton": {"co2_kg_per_kg": 1.50, "water_l_per_kg": 5000.0, "recovery_rate": 0.82, "recyclability": 85.0, "processing_feasibility": 88.0},
    "polyester": {"co2_kg_per_kg": 2.10, "water_l_per_kg": 120.0, "recovery_rate": 0.88, "recyclability": 90.0, "processing_feasibility": 86.0},
    "wool": {"co2_kg_per_kg": 4.00, "water_l_per_kg": 1700.0, "recovery_rate": 0.72, "recyclability": 76.0, "processing_feasibility": 72.0},
    "silk": {"co2_kg_per_kg": 3.20, "water_l_per_kg": 2300.0, "recovery_rate": 0.68, "recyclability": 68.0, "processing_feasibility": 64.0},
    "linen": {"co2_kg_per_kg": 1.20, "water_l_per_kg": 900.0, "recovery_rate": 0.80, "recyclability": 84.0, "processing_feasibility": 82.0},
    "denim": {"co2_kg_per_kg": 2.40, "water_l_per_kg": 3800.0, "recovery_rate": 0.78, "recyclability": 82.0, "processing_feasibility": 80.0},
    "nylon": {"co2_kg_per_kg": 3.00, "water_l_per_kg": 180.0, "recovery_rate": 0.76, "recyclability": 78.0, "processing_feasibility": 74.0},
    "rayon": {"co2_kg_per_kg": 1.80, "water_l_per_kg": 1100.0, "recovery_rate": 0.70, "recyclability": 72.0, "processing_feasibility": 70.0},
    "viscose": {"co2_kg_per_kg": 1.80, "water_l_per_kg": 1100.0, "recovery_rate": 0.70, "recyclability": 72.0, "processing_feasibility": 70.0},
    "acrylic": {"co2_kg_per_kg": 2.70, "water_l_per_kg": 160.0, "recovery_rate": 0.65, "recyclability": 64.0, "processing_feasibility": 60.0},
    "elastane": {"co2_kg_per_kg": 2.50, "water_l_per_kg": 150.0, "recovery_rate": 0.35, "recyclability": 35.0, "processing_feasibility": 38.0},
    DEFAULT_FABRIC: {"co2_kg_per_kg": 1.50, "water_l_per_kg": 750.0, "recovery_rate": 0.60, "recyclability": 60.0, "processing_feasibility": 58.0},
}

CONDITION_SCORES = {"reusable": 95.0, "excellent": 95.0, "good": 82.0, "recyclable": 75.0, "fair": 65.0, "repairable": 62.0, "damaged": 38.0, "poor": 30.0, "mixed": 45.0, "hazardous": 5.0}
REUSE_SCORES = {"high": 90.0, "medium": 60.0, "low": 25.0}
STATUS_DIVERSION_FACTORS = {"recycled": 1.0, "reused": 1.0, "processing": 0.85, "collected": 0.70, "pickup requested": 0.50, "pending": 0.35, "landfilled": 0.0, "disposed": 0.0}
BENCHMARK_DIVERSION_PERCENT = 75.0
