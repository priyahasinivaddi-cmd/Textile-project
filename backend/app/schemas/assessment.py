from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: str
    quantity_kg: float
    recyclability_score: float = Field(ge=0, le=100)
    condition_score: float = Field(ge=0, le=100)
    reuse_score: float = Field(ge=0, le=100)
    environmental_benefit_score: float = Field(ge=0, le=100)
    processing_feasibility_score: float = Field(ge=0, le=100)
    material_recovery_score: float = Field(ge=0, le=100)
    sustainability_score: float = Field(ge=0, le=100)
    circularity_score: float = Field(ge=0, le=100)
    circularity_category: str
    co2_saved_kg: float
    water_saved_litres: float
    landfill_reduction_kg: float
    recoverable_material_kg: float
    recommended_action: str
    recommended_processing_method: str
    recommendation_reason: str
    audit_history: list[dict] = []
    created_at: datetime
    updated_at: datetime


class RecommendationOut(BaseModel):
    batch_id: str
    recommended_action: str
    recommended_processing_method: str
    recommendation_reason: str
    estimated_recovery_percentage: float
    estimated_recoverable_quantity_kg: float
    estimated_co2_savings_kg: float
    estimated_water_savings_litres: float
    circularity_score: float
    circularity_category: str


class SustainabilitySummaryOut(BaseModel):
    total_assessments: int
    total_waste_kg: float
    co2_saved_kg: float
    water_saved_litres: float
    landfill_reduction_kg: float
    recoverable_material_kg: float
    waste_diversion_percentage: float
    average_circularity_score: float
    benchmark_diversion_percentage: float
    benchmark_status: str
    category_distribution: dict[str, int]


class MonthlyTrendOut(SustainabilitySummaryOut):
    month: str


class BulkAssessmentOut(BaseModel):
    queued: int
    message: str
