"""Pydantic v2 schemas for SoloMiro API request/response validation."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class RecommendRequest(BaseModel):
    """Input payload for the car recommendation endpoint."""

    current_car: str
    goals: list[str]
    car_type: str  # new, used, both
    budget_range: str  # 0_to_3M, 3_to_6M, 6_to_10M, 10M_plus, unknown
    monthly_km: Optional[int] = 1000
    driving_style: Optional[str] = "mixed"  # city, highway, mixed, hills
    can_charge_at_home: Optional[bool] = False


class CarScore(BaseModel):
    """Score breakdown for a single car recommendation."""

    overall: float
    consumption: float
    resale: float
    risk: float
    value_for_money: float
    compatibility: float


class CarRecommendation(BaseModel):
    """A single ranked car recommendation with full details."""

    rank: int
    type: str  # rational, aspirational, budget
    car: dict
    scores: CarScore
    change_cost_clp: int
    monthly_fuel_saving_clp: int
    payback_months: Optional[int]
    pros: list[str]
    cons: list[str]
    verdict: str
    not_recommended_if: str
    ai_analysis: str


class RecommendResponse(BaseModel):
    """Full recommendation response returned to the frontend."""

    session_id: str
    current_car_analysis: dict
    recommendations: list[CarRecommendation]
    general_verdict: str


class LeadRequest(BaseModel):
    """WhatsApp lead capture payload."""

    session_id: str
    name: Optional[str] = None
    whatsapp: str
    current_car: str
    budget_clp: Optional[int] = None
    city: Optional[str] = None
    buy_timeframe: Optional[str] = None
