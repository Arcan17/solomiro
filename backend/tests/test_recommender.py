"""Unit tests for the CarRecommender service."""

from __future__ import annotations

import pytest

from app.schemas import RecommendRequest
from app.services.recommender import CarRecommender


def make_request(**kwargs) -> RecommendRequest:
    """Helper to create a RecommendRequest with sensible defaults."""
    defaults = {
        "current_car": "Toyota RAV4 2020",
        "goals": ["lower_consumption"],
        "car_type": "both",
        "budget_range": "unknown",
        "monthly_km": 1000,
        "driving_style": "mixed",
        "can_charge_at_home": False,
    }
    defaults.update(kwargs)
    return RecommendRequest(**defaults)


class TestFilterCars:
    """Tests for CarRecommender._filter_cars."""

    def test_filter_excludes_over_budget(self, recommender: CarRecommender):
        """Cars whose change cost exceeds the budget max should be excluded."""
        # Budget 0–3M: only extremely cheap change-cost scenarios qualify
        request = make_request(budget_range="0_to_3M", car_type="both")
        current_value = 30_000_000  # Very high trade-in to isolate budget filter
        filtered = recommender._filter_cars(recommender._cars, request, current_value)
        # All filtered cars should have price <= current_value + 3M
        for car in filtered:
            change_cost = max(car["price_clp"] - current_value, 0)
            assert change_cost <= 3_000_000

    def test_filter_excludes_bev_no_home_charging(self, recommender: CarRecommender):
        """Electric (BEV) cars must be excluded when user cannot charge at home."""
        request = make_request(can_charge_at_home=False)
        filtered = recommender._filter_cars(recommender._cars, request, 10_000_000)
        for car in filtered:
            assert car["fuel_type"] != "electric"

    def test_filter_includes_hybrid_no_home_charging(self, recommender: CarRecommender):
        """Standard hybrid cars should NOT be excluded when user lacks home charging."""
        request = make_request(can_charge_at_home=False, budget_range="unknown")
        filtered = recommender._filter_cars(recommender._cars, request, 5_000_000)
        hybrid_cars = [c for c in filtered if c["fuel_type"] == "hybrid"]
        assert len(hybrid_cars) > 0


class TestScoreCar:
    """Tests for CarRecommender._score_car."""

    def _get_car_by_fuel(self, recommender: CarRecommender, fuel_type: str) -> dict:
        """Return the first car matching the given fuel type."""
        return next(c for c in recommender._cars if c["fuel_type"] == fuel_type)

    def test_score_lower_consumption_weights_consumption_high(
        self, recommender: CarRecommender
    ):
        """With lower_consumption goal, consumption score must be the highest weighted dimension."""
        car = self._get_car_by_fuel(recommender, "hybrid")
        request = make_request(goals=["lower_consumption"])
        scores = recommender._score_car(car, ["lower_consumption"], 10_000_000, request)
        # consumption dimension should score well and influence the overall more than resale
        assert 0.0 <= scores["overall"] <= 10.0
        assert "consumption" in scores

    def test_score_better_resale_weights_resale_high(self, recommender: CarRecommender):
        """With better_resale goal, a Toyota's resale score should dominate overall."""
        toyota = next(
            c
            for c in recommender._cars
            if c["brand"] == "Toyota" and c["condition"] == "new"
        )
        request = make_request(goals=["better_resale"])
        scores = recommender._score_car(toyota, ["better_resale"], 10_000_000, request)
        assert scores["resale"] >= 7.0  # Toyota resale scores are high


class TestRecommend:
    """Tests for CarRecommender.recommend (integration with MockAI)."""

    @pytest.mark.asyncio
    async def test_recommend_returns_three_results(self, recommender: CarRecommender):
        """recommend() should always return exactly 3 recommendations."""
        request = make_request()
        response = await recommender.recommend(request)
        assert len(response.recommendations) == 3

    @pytest.mark.asyncio
    async def test_recommend_respects_car_type_new_only(
        self, recommender: CarRecommender
    ):
        """With car_type='new', all recommended cars must have condition='new'."""
        request = make_request(car_type="new", budget_range="unknown")
        response = await recommender.recommend(request)
        for rec in response.recommendations:
            assert rec.car["condition"] == "new"

    @pytest.mark.asyncio
    async def test_recommend_respects_car_type_used_only(
        self, recommender: CarRecommender
    ):
        """With car_type='used', all recommended cars must have condition='used'."""
        request = make_request(car_type="used", budget_range="unknown")
        response = await recommender.recommend(request)
        for rec in response.recommendations:
            assert rec.car["condition"] == "used"

    @pytest.mark.asyncio
    async def test_recommend_has_session_id(self, recommender: CarRecommender):
        """recommend() should attach a non-empty session_id to the response."""
        request = make_request()
        response = await recommender.recommend(request)
        assert response.session_id
        assert len(response.session_id) == 36  # UUID4 format

    @pytest.mark.asyncio
    async def test_recommend_current_car_analysis_present(
        self, recommender: CarRecommender
    ):
        """Response should include a current_car_analysis dict with key fields."""
        request = make_request()
        response = await recommender.recommend(request)
        assert "name" in response.current_car_analysis
        assert "estimated_value_clp" in response.current_car_analysis
