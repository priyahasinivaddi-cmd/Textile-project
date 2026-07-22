"""
pipeline.py  (schemas)
-----------------------
Pydantic response models for the Textile Waste Intelligence Pipeline API.

These models:
  1. Provide automatic OpenAPI/Swagger documentation.
  2. Validate the JSON structure returned by /pipeline/analyze.
  3. Make it easy to add new fields without breaking existing consumers.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class ImageFeatures(BaseModel):
    """Visual features extracted from the uploaded textile image."""

    fabric_texture: str = Field(
        ..., description="Surface texture estimate: 'smooth' or 'rough'."
    )
    fabric_pattern: str = Field(
        ..., description="Weave pattern: 'plain' or 'printed'."
    )
    color_name: str = Field(
        ..., description="Closest named colour of the dominant fabric colour."
    )
    color_hex: str = Field(
        ..., description="Hex colour code of the dominant fabric colour, e.g. '#3a7fd5'."
    )
    damage_detected: bool = Field(
        ..., description="True if physical damage (tears/holes) was detected."
    )
    damage_details: str = Field(
        ..., description="Human-readable description of detected damage."
    )
    contamination_detected: bool = Field(
        ..., description="True if contamination (stains/dirt) was detected."
    )
    contamination_details: str = Field(
        ..., description="Human-readable description of detected contamination."
    )


class MaterialResult(BaseModel):
    """Material classification output."""

    fabric_type: str = Field(
        ..., description="Classified fabric type, e.g. 'Cotton', 'Denim', 'Polyester'."
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Classification confidence score between 0 and 1."
    )
    fiber_composition: str = Field(
        ..., description="Predicted fiber blend, e.g. '100% Cotton' or '60% Cotton / 40% Polyester'."
    )
    blend_type: str = Field(
        ..., description="'single' if one fibre type detected, 'mixed' if multiple."
    )
    quality: str = Field(
        ..., description="Overall material quality grade: 'high', 'medium', or 'low'."
    )


class WasteClassification(BaseModel):
    """Waste category and disposal guidance."""

    category: str = Field(
        ...,
        description=(
            "Waste category: Recyclable | Reusable | Repairable | "
            "Upcyclable | Compostable | Hazardous."
        ),
    )
    reuse_potential: str = Field(
        ..., description="Estimated reuse value: 'High', 'Medium', or 'Low'."
    )
    disposal_method: str = Field(
        ..., description="Recommended primary disposal or processing route."
    )


# ---------------------------------------------------------------------------
# Top-level pipeline response
# ---------------------------------------------------------------------------

class PipelineResponse(BaseModel):
    """
    Full structured response from the /pipeline/analyze endpoint.
    Contains every stage of the circular intelligence pipeline.
    """

    image_url: Optional[str] = Field(
        None, description="Relative URL to the uploaded image served via /static."
    )
    features: ImageFeatures = Field(
        ..., description="Visual features extracted from the uploaded image."
    )
    material: MaterialResult = Field(
        ..., description="Material classification result."
    )
    waste_classification: WasteClassification = Field(
        ..., description="Waste category and disposal recommendation."
    )
    recommendations: List[str] = Field(
        ..., description="Ordered list of circular economy recovery recommendations."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "image_url": "/static/uploads/abc123.jpg",
                "features": {
                    "fabric_texture": "rough",
                    "fabric_pattern": "plain",
                    "color_name": "Blue",
                    "color_hex": "#283c7f",
                    "damage_detected": False,
                    "damage_details": "No physical tears or holes detected.",
                    "contamination_detected": False,
                    "contamination_details": "Fabric surface is clean.",
                },
                "material": {
                    "fabric_type": "Denim",
                    "confidence": 0.94,
                    "fiber_composition": "98% Cotton / 2% Elastane",
                    "blend_type": "single",
                    "quality": "high",
                },
                "waste_classification": {
                    "category": "Reusable",
                    "reuse_potential": "High",
                    "disposal_method": "Redirect to resale markets, clothing drives, or second-hand retailers.",
                },
                "recommendations": [
                    "Fabric reuse: Clean and re-distribute directly to manufacturing off-cut markets.",
                    "Donation: Allocate to local clothing charity banks.",
                    "Industrial recovery: Register batch weight in circular economy ledger.",
                ],
            }
        }
