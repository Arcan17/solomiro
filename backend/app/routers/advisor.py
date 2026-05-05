"""Advisor router — recommendation and car catalogue endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Recommendation
from app.schemas import RecommendRequest, RecommendResponse
from app.services.ai_service import get_ai_provider
from app.services.recommender import CarRecommender
from config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_recommender() -> CarRecommender:
    """Instantiate a CarRecommender with the configured AI provider.

    Returns:
        Ready-to-use CarRecommender instance.
    """
    ai_provider = get_ai_provider(settings)
    return CarRecommender(ai_provider=ai_provider, settings=settings)


@router.post("/recommend", response_model=RecommendResponse, tags=["advisor"])
async def recommend(
    request: RecommendRequest,
    db: Session = Depends(get_db),
    recommender: CarRecommender = Depends(_get_recommender),
) -> RecommendResponse:
    """Generate car recommendations for the given user request.

    Runs the recommendation pipeline, saves results to the database, and
    returns a structured response.

    Args:
        request: User's car preferences and constraints.
        db: Database session (injected).
        recommender: CarRecommender instance (injected).

    Returns:
        RecommendResponse with ranked car recommendations.
    """
    response = await recommender.recommend(request)

    # Persist to DB
    rec = Recommendation(
        session_id=response.session_id,
        current_car=request.current_car,
        goals=request.goals,
        budget_range=request.budget_range,
        car_type=request.car_type,
        monthly_km=request.monthly_km,
        driving_style=request.driving_style,
        can_charge_at_home=request.can_charge_at_home or False,
        result_json=response.model_dump(),
    )
    db.add(rec)
    db.commit()
    logger.info("Saved recommendation session_id=%s", response.session_id)

    return response


@router.get("/cars", tags=["cars"])
async def get_cars() -> list[dict]:
    """Return the full car catalogue.

    Returns:
        List of all car objects.
    """
    recommender = CarRecommender(
        ai_provider=None,  # type: ignore[arg-type]
        settings=settings,
    )
    return recommender._load_cars()


@router.get("/cars/{car_id}", tags=["cars"])
async def get_car(car_id: int) -> dict:
    """Return a single car by its ID.

    Args:
        car_id: Integer identifier matching the car's ``id`` field.

    Returns:
        Car object dict.

    Raises:
        HTTPException: 404 if not found.
    """
    recommender = CarRecommender(
        ai_provider=None,  # type: ignore[arg-type]
        settings=settings,
    )
    cars = recommender._load_cars()
    for car in cars:
        if car["id"] == car_id:
            return car
    raise HTTPException(status_code=404, detail=f"Car {car_id} not found")


@router.get("/health", tags=["system"])
async def health() -> dict:
    """Health-check endpoint.

    Returns:
        Status and version information.
    """
    return {"status": "ok", "version": "1.0.0"}
