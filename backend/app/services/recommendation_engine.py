"""
recommendation_engine.py
-------------------------
Recycling Recommendation Module
---------------------------------
Generates a ranked list of actionable circular-economy recommendations based
on the waste category and material blend type.

Recommendation types covered:
    • Fiber recycling
    • Mechanical recycling
    • Chemical recycling
    • Fabric reuse
    • Upcycling ideas
    • Donation
    • Industrial recovery

All logic is rule-based. The recommendations list is ordered from highest
to lowest value-recovery potential.
"""

from typing import List


# ---------------------------------------------------------------------------
# Recommendation templates
# ---------------------------------------------------------------------------

_RECOMMENDATIONS: dict[str, List[str]] = {
    "Reusable": [
        "Fabric reuse: Clean and re-distribute directly to manufacturing off-cut markets.",
        "Donation: Allocate to local clothing charity banks or social enterprise upcycling units.",
        "Industrial recovery: Retain as clean deadstock for direct lining/backing templates.",
    ],
    "Repairable": [
        "Fabric mending: Utilize local tailors/artisans to repair tear lines.",
        "Patchwork restoration: Use matching colour scraps to patch defects.",
        "Direct donation: Gift to vocational sewing schools for training materials.",
    ],
    "Upcyclable": [
        "Upcycling ideas: Convert scraps into small consumer items like bags, coasters, or cushion stuffings.",
        "Patchwork quilting: Compile with other prints for designer circular clothing lines.",
        "Industrial insulation: Supply as sound-proofing panel stuffing for construction.",
    ],
    "Compostable": [
        "Organic composting: Shred into micro-fibres and blend with organic soil matter.",
        "Mechanical fiber recovery: Strip dyes and recover short-staple natural fibres.",
        "Biodegradable agricultural covers: Convert to plant protectors.",
    ],
    "Hazardous": [
        "Industrial containment: Place in dedicated safe hazardous waste bins.",
        "Thermal recovery: Dispose via certified eco-friendly waste-to-energy incineration.",
        "Chemical extraction: Separate and isolate chemical contaminants to salvage base polymers.",
    ],
}

# Recyclable recommendations depend on blend type and fabric family
_NATURAL_FIBERS   = ("Cotton", "Linen", "Denim")
_SYNTHETIC_FIBERS = ("Polyester", "Nylon", "Acrylic", "Rayon")

_RECYCLABLE_NATURAL = [
    "Mechanical recycling: Shred and re-spin into high-grade recycled cotton yarns.",
    "Closed-loop fiber pulping: Process into lyocell-like textile pulp.",
]
_RECYCLABLE_SYNTHETIC = [
    "Chemical recycling: Depolymerize synthetic polymers back into raw monomers.",
    "Pelletizing: Melt down and pelletize for extruded filament spinning.",
]
_RECYCLABLE_MIXED = [
    "Mechanical recycling: Shred mixed fibres to create low-grade insulation felt or carpet underlays.",
    "Chemical separation: Apply solvent extraction to separate cotton and polyester blend constituents.",
]

# Appended to every recommendation set
_CIRCULAR_ECONOMY_TIP = (
    "Industrial recovery: Register batch weight in circular economy ledger "
    "to claim waste offset credits."
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_recommendations(waste: dict, material: dict) -> List[str]:
    """
    Generate recycling and recovery recommendations.

    Parameters
    ----------
    waste : dict
        Output of `classify_waste()`.  
        Expected keys: category
    material : dict
        Output of `classify_material()`.  
        Expected keys: blend_type, fabric_type

    Returns
    -------
    List[str]  Ordered list of actionable recommendation strings.
    """
    category   = waste["category"]
    blend_type = material["blend_type"]
    fabric_type = material["fabric_type"]

    if category in _RECOMMENDATIONS:
        recs = list(_RECOMMENDATIONS[category])
    else:
        # Recyclable — pick set based on blend and fabric family
        if blend_type == "single":
            if fabric_type in _NATURAL_FIBERS:
                recs = list(_RECYCLABLE_NATURAL)
            else:
                recs = list(_RECYCLABLE_SYNTHETIC)
        else:
            recs = list(_RECYCLABLE_MIXED)

    # Always append the circular economy credit tip
    recs.append(_CIRCULAR_ECONOMY_TIP)
    return recs
