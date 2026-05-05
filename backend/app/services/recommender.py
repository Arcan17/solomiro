"""Car recommendation engine for SoloMiro."""

from __future__ import annotations

import json
import logging
import os

from app.schemas import CarRecommendation, CarScore, RecommendRequest, RecommendResponse
from app.services.ai_service import AIProvider
from app.services.calculator import (
    calculate_change_cost,
    calculate_monthly_fuel_saving,
    calculate_payback_months,
    estimate_current_car_value,
)

logger = logging.getLogger(__name__)

# Goal → dimension weight mapping
GOAL_WEIGHTS: dict[str, dict[str, float]] = {
    "lower_consumption": {
        "consumption": 0.4,
        "resale": 0.2,
        "risk": 0.2,
        "value": 0.2,
    },
    "better_resale": {
        "resale": 0.5,
        "risk": 0.2,
        "consumption": 0.2,
        "value": 0.1,
    },
    "hybrid": {
        "consumption": 0.35,
        "resale": 0.25,
        "risk": 0.2,
        "value": 0.2,
    },
    "more_space": {
        "consumption": 0.1,
        "resale": 0.3,
        "risk": 0.2,
        "value": 0.4,
    },
    "more_equipment": {
        "consumption": 0.1,
        "resale": 0.3,
        "risk": 0.2,
        "value": 0.4,
    },
    "lower_payment": {
        "value": 0.5,
        "consumption": 0.2,
        "risk": 0.2,
        "resale": 0.1,
    },
    "more_power": {
        "consumption": 0.1,
        "resale": 0.3,
        "risk": 0.3,
        "value": 0.3,
    },
    "less_risk": {
        "risk": 0.5,
        "resale": 0.2,
        "consumption": 0.2,
        "value": 0.1,
    },
}

BUDGET_RANGES: dict[str, tuple[int, int]] = {
    "0_to_3M": (0, 3_000_000),
    "3_to_6M": (3_000_000, 6_000_000),
    "6_to_10M": (6_000_000, 10_000_000),
    "10M_plus": (10_000_000, 999_000_000),
    "unknown": (0, 999_000_000),
}

_CARS_JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cars.json")


class CarRecommender:
    """Scores and ranks cars according to user goals and constraints."""

    def __init__(self, ai_provider: AIProvider, settings) -> None:
        """Initialise the recommender.

        Args:
            ai_provider: AI provider instance used for final text analysis.
            settings: Application settings (fuel prices, etc.).
        """
        self._ai = ai_provider
        self._settings = settings
        self._cars: list[dict] = self._load_cars()

    def _load_cars(self) -> list[dict]:
        """Load the car catalogue from the bundled JSON file.

        Returns:
            List of car dicts.
        """
        path = os.path.abspath(_CARS_JSON_PATH)
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def _detect_segment(self, car_name: str) -> str:
        """Heuristically detect the vehicle segment from the car name.

        Args:
            car_name: Free-text car name.

        Returns:
            Segment key string.
        """
        lower = car_name.lower()
        if any(
            k in lower
            for k in [
                "rav4",
                "cx-5",
                "tucson",
                "sportage",
                "tiguan",
                "cr-v",
                "escape",
                "eclipse cross",
            ]
        ):
            return "suv_medium"
        if any(
            k in lower
            for k in [
                "yaris",
                "corolla",
                "civic",
                "mazda 3",
                "elantra",
                "cerato",
                "vento",
                "swift",
            ]
        ):
            return "sedan"
        if any(k in lower for k in ["phev", "hybrid", "camry"]):
            return "hybrid_phev"
        if any(k in lower for k in ["electric", "ev", "dolphin", "han ev", "mg4"]):
            return "electric"
        return "suv_compact"

    def _get_fuel_prices(self) -> dict:
        """Build a fuel prices dict from settings.

        Returns:
            Dict with FUEL_PRICE_95, FUEL_PRICE_DIESEL, FUEL_PRICE_KWH keys.
        """
        return {
            "FUEL_PRICE_95": self._settings.FUEL_PRICE_95,
            "FUEL_PRICE_DIESEL": self._settings.FUEL_PRICE_DIESEL,
            "FUEL_PRICE_KWH": self._settings.FUEL_PRICE_KWH,
        }

    def _filter_cars(
        self, cars: list[dict], request: RecommendRequest, current_car_value: int
    ) -> list[dict]:
        """Filter the car catalogue to those matching budget and type constraints.

        Args:
            cars: Full car list.
            request: User recommendation request.
            current_car_value: Estimated value of the user's current car in CLP.

        Returns:
            Filtered list of cars.
        """
        budget_min, budget_max = BUDGET_RANGES.get(
            request.budget_range, (0, 999_000_000)
        )
        filtered: list[dict] = []

        for car in cars:
            # Filter by condition (new / used / both)
            if request.car_type == "new" and car["condition"] != "new":
                continue
            if request.car_type == "used" and car["condition"] != "used":
                continue

            # Filter by change cost within budget range
            change_cost = calculate_change_cost(car["price_clp"], current_car_value)
            if not (budget_min <= change_cost <= budget_max):
                continue

            # Exclude pure BEV if no home charging
            if not request.can_charge_at_home and car["fuel_type"] == "electric":
                continue

            filtered.append(car)

        return filtered

    def _score_car(
        self,
        car: dict,
        goals: list[str],
        current_car_value: int,
        request: RecommendRequest,
    ) -> dict:
        """Compute a weighted score for a car given the user's goals.

        Args:
            car: Car dictionary from the catalogue.
            goals: List of goal keys selected by the user.
            current_car_value: Estimated resale value of current car.
            request: Full recommendation request.

        Returns:
            Dict with score dimensions (consumption, resale, risk, value_for_money,
            compatibility, overall).
        """
        # Normalise individual dimension scores (all are 0–10 from JSON)
        consumption_kpl = car.get("consumption_kpl") or 0
        # Convert km/L to a 0-10 score: 6 km/L = score 0, 26+ km/L = score 10
        # Using wider range so hybrids (18-24) and gasolina (10-15) actually differ
        if car["fuel_type"] == "electric":
            kwh = car.get("consumption_kwh100km") or 20
            consumption_score = max(0.0, min(10.0, (25 - kwh) / 1.5))
        else:
            consumption_score = max(0.0, min(10.0, (consumption_kpl - 6) / 2.0))

        resale_score: float = float(car.get("resale_score", 5))
        reliability_score: float = float(car.get("reliability_score", 5))
        parts_score: float = float(car.get("parts_availability_score", 5))
        equipment_score: float = float(car.get("equipment_score", 5))

        # Risk = average of reliability + parts_availability
        risk_score = (reliability_score + parts_score) / 2

        # Value for money: equipment vs price ratio normalised
        price_m = car["price_clp"] / 1_000_000
        value_score = max(0.0, min(10.0, equipment_score - (price_m - 10) * 0.15))

        # Compatibility: penalise PHEV if no home charging
        compatibility: float = 10.0
        if car.get("requires_home_charging") and not request.can_charge_at_home:
            compatibility -= 3.0
        if request.driving_style == "highway" and "city" in car.get("tags", []):
            compatibility -= 2.0

        # Aggregate weights across goals
        if not goals:
            goals = ["lower_consumption"]

        agg_weights: dict[str, float] = {
            "consumption": 0.0,
            "resale": 0.0,
            "risk": 0.0,
            "value": 0.0,
        }
        for goal in goals:
            weights = GOAL_WEIGHTS.get(goal, GOAL_WEIGHTS["lower_consumption"])
            for dim, w in weights.items():
                agg_weights[dim] += w
        # Normalise
        total_w = sum(agg_weights.values()) or 1.0
        for dim in agg_weights:
            agg_weights[dim] /= total_w

        overall = (
            agg_weights["consumption"] * consumption_score
            + agg_weights["resale"] * resale_score
            + agg_weights["risk"] * risk_score
            + agg_weights["value"] * value_score
        )
        # Add small compatibility influence
        overall = overall * 0.9 + compatibility * 0.1

        return {
            "overall": round(overall, 2),
            "consumption": round(consumption_score, 2),
            "resale": round(resale_score, 2),
            "risk": round(risk_score, 2),
            "value_for_money": round(value_score, 2),
            "compatibility": round(compatibility, 2),
        }

    def _build_pros_cons(
        self, car: dict, scores: dict, request: RecommendRequest
    ) -> tuple[list[str], list[str]]:
        """Deterministically build pros and cons lists based on car attributes.

        Args:
            car: Car dictionary from the catalogue.
            scores: Scored dimensions dict.
            request: User recommendation request.

        Returns:
            Tuple of (pros, cons) as lists of strings.
        """
        pros: list[str] = []
        cons: list[str] = []

        # Consumption
        consumption_kpl = car.get("consumption_kpl")
        if consumption_kpl and consumption_kpl > 14:
            pros.append("Muy eficiente: bajo consumo de combustible")
        if car.get("fuel_type") == "electric":
            kwh = car.get("consumption_kwh100km") or 20
            if kwh < 16:
                pros.append("Bajo costo por km eléctrico")

        # Resale
        if car.get("resale_score", 0) >= 8:
            pros.append("Alta reventa en el mercado chileno")

        # Reliability
        if car.get("reliability_score", 0) >= 8:
            pros.append("Alta confiabilidad comprobada")

        # Fuel type bonuses
        if car.get("fuel_type") == "hybrid":
            pros.append("Motor híbrido eficiente")
        if car.get("fuel_type") == "electric":
            pros.append("Cero emisiones locales, bajo costo por km")
        if car.get("fuel_type") == "phev":
            pros.append("Modo eléctrico para ciudad, combustión para viajes largos")

        # Price
        if car["price_clp"] > 25_000_000:
            cons.append("Precio de compra elevado")

        # Parts availability
        if car.get("parts_availability_score", 10) < 7:
            cons.append("Repuestos menos disponibles en Chile")

        # Home charging requirement
        if car.get("requires_home_charging") and not request.can_charge_at_home:
            cons.append("Requiere instalación de cargador en casa")

        # Maintenance
        if car.get("maintenance_cost_score", 10) < 7:
            cons.append("Mantenimiento relativamente costoso")

        return pros or ["Buena relación precio/valor"], cons or [
            "Sin desventajas destacadas"
        ]

    async def recommend(self, request: RecommendRequest) -> RecommendResponse:
        """Run the full recommendation pipeline and return a response.

        Steps:
        1. Estimate current car value.
        2. Filter catalogue.
        3. Score all filtered cars.
        4. Select top 3.
        5. Compute financials and pros/cons per car.
        6. Call AI for text analysis.
        7. Return structured response.

        Args:
            request: User recommendation request payload.

        Returns:
            RecommendResponse with session_id, analysis, and top 3 recommendations.
        """
        import uuid

        session_id = str(uuid.uuid4())
        segment = self._detect_segment(request.current_car)
        current_car_value = estimate_current_car_value(request.current_car, segment)

        # Filter
        filtered = self._filter_cars(self._cars, request, current_car_value)
        if not filtered:
            # Fallback: return the 10 cheapest cars without filter
            filtered = sorted(self._cars, key=lambda c: c["price_clp"])[:10]

        # Score
        scored: list[tuple[dict, dict]] = []
        for car in filtered:
            scores = self._score_car(car, request.goals, current_car_value, request)
            scored.append((car, scores))

        # Sort by overall score descending
        scored.sort(key=lambda x: x[1]["overall"], reverse=True)

        # --- Diversity selection ---
        # Pick 3 cars that differ in price tier so the user sees real options.
        # Tiers (change cost): budget <8M, mid 8-20M, premium >20M
        def change_cost_tier(car: dict) -> str:
            cc = calculate_change_cost(car["price_clp"], current_car_value)
            if cc < 8_000_000:
                return "budget"
            if cc < 20_000_000:
                return "mid"
            return "premium"

        chosen: list[tuple[dict, dict]] = []
        seen_tiers: set[str] = set()
        seen_segments: set[str] = set()

        # Pass 1: pick best car per tier
        for car, scores in scored:
            tier = change_cost_tier(car)
            if tier not in seen_tiers:
                chosen.append((car, scores))
                seen_tiers.add(tier)
                seen_segments.add(car.get("segment", ""))
            if len(chosen) == 3:
                break

        # Pass 2: fill remaining slots with best scores (different segment preferred)
        if len(chosen) < 3:
            chosen_ids = {id(c) for c, _ in chosen}
            for car, scores in scored:
                if id(car) in chosen_ids:
                    continue
                if car.get("segment", "") not in seen_segments:
                    chosen.append((car, scores))
                    seen_segments.add(car.get("segment", ""))
                    chosen_ids.add(id(car))
                if len(chosen) == 3:
                    break

        # Pass 3: fill any remaining with next best
        if len(chosen) < 3:
            chosen_ids = {id(c) for c, _ in chosen}
            for car, scores in scored:
                if id(car) not in chosen_ids:
                    chosen.append((car, scores))
                    if len(chosen) == 3:
                        break

        top_3 = chosen[:3]

        fuel_prices = self._get_fuel_prices()

        # Determine current car consumption estimate (use segment average in km/L)
        current_consumption_map = {
            "suv_compact": 11.0,
            "suv_medium": 9.0,
            "hybrid_phev": 13.0,
            "electric": 0.0,
            "sedan": 12.0,
            "default": 11.0,
        }
        current_consumption = current_consumption_map.get(segment, 11.0)

        recommendations_raw: list[dict] = []
        for rank, (car, scores) in enumerate(top_3, start=1):
            change_cost = calculate_change_cost(car["price_clp"], current_car_value)
            new_consumption = (
                car.get("consumption_kpl") or car.get("consumption_kwh100km") or 10.0
            )
            monthly_saving = calculate_monthly_fuel_saving(
                current_consumption=current_consumption,
                new_consumption=new_consumption,
                monthly_km=request.monthly_km or 1000,
                fuel_type_new=car["fuel_type"],
                fuel_prices=fuel_prices,
            )
            payback = calculate_payback_months(change_cost, monthly_saving)
            pros, cons = self._build_pros_cons(car, scores, request)

            rec_type = "rational"
            if rank == 1 and car["price_clp"] > 25_000_000:
                rec_type = "aspirational"
            elif rank == 3:
                rec_type = "budget"

            recommendations_raw.append(
                {
                    "rank": rank,
                    "type": rec_type,
                    "car": car,
                    "scores": scores,
                    "change_cost_clp": change_cost,
                    "monthly_fuel_saving_clp": monthly_saving,
                    "payback_months": payback,
                    "pros": pros,
                    "cons": cons,
                    "verdict": f"{car['name']} destaca por su puntuación general de {scores['overall']:.1f}/10.",
                    "not_recommended_if": car.get("not_recommended_if", ""),
                    "ai_analysis": "",
                }
            )

        # AI analysis
        prompt = f"""
You are a car advisor for Chile. Based on the following data, write a helpful analysis IN SPANISH.

User's current car: {request.current_car}
User's goals: {request.goals}
Monthly km: {request.monthly_km}
Driving style: {request.driving_style}

Top 3 recommendations (already scored by our algorithm):
{json.dumps([{
    "rank": r["rank"],
    "name": r["car"]["name"],
    "price_clp": r["car"]["price_clp"],
    "fuel_type": r["car"]["fuel_type"],
    "consumption_kpl": r["car"].get("consumption_kpl"),
    "scores": r["scores"],
    "change_cost_clp": r["change_cost_clp"],
    "monthly_fuel_saving_clp": r["monthly_fuel_saving_clp"],
} for r in recommendations_raw], ensure_ascii=False, indent=2)}

For each recommendation, write 2-3 sentences explaining why it fits the user's needs.
Then write a final verdict of 2-3 sentences.
Do NOT invent data. Only explain what the scores already show.
Respond in JSON format:
{{
  "analyses": ["analysis for car 1", "analysis for car 2", "analysis for car 3"],
  "general_verdict": "final verdict text"
}}
"""
        general_verdict = (
            "Revisa las opciones anteriores según tu presupuesto y necesidades."
        )
        try:
            ai_response = await self._ai.generate(prompt)
            # Try to parse the JSON from the AI response
            ai_data = json.loads(ai_response)
            analyses = ai_data.get("analyses", [])
            general_verdict = ai_data.get("general_verdict", general_verdict)
            for i, rec in enumerate(recommendations_raw):
                if i < len(analyses):
                    rec["ai_analysis"] = analyses[i]
                else:
                    rec["ai_analysis"] = "Análisis no disponible."
        except Exception as exc:
            logger.warning("AI analysis failed: %s", exc)
            for rec in recommendations_raw:
                rec["ai_analysis"] = (
                    "Análisis automático no disponible en este momento."
                )

        # Build typed response objects
        recommendations: list[CarRecommendation] = [
            CarRecommendation(
                rank=r["rank"],
                type=r["type"],
                car=r["car"],
                scores=CarScore(**r["scores"]),
                change_cost_clp=r["change_cost_clp"],
                monthly_fuel_saving_clp=r["monthly_fuel_saving_clp"],
                payback_months=r["payback_months"],
                pros=r["pros"],
                cons=r["cons"],
                verdict=r["verdict"],
                not_recommended_if=r["not_recommended_if"],
                ai_analysis=r["ai_analysis"],
            )
            for r in recommendations_raw
        ]

        current_car_analysis = {
            "name": request.current_car,
            "estimated_value_clp": current_car_value,
            "segment": segment,
            "estimated_consumption_kpl": current_consumption,
        }

        return RecommendResponse(
            session_id=session_id,
            current_car_analysis=current_car_analysis,
            recommendations=recommendations,
            general_verdict=general_verdict,
        )
