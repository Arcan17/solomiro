"""Financial calculator functions for car change cost analysis."""

from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Segment depreciation rates per year (as a fraction)
_DEPRECIATION_RATES: dict[str, float] = {
    "suv_compact": 0.12,
    "suv_medium": 0.12,
    "hybrid_phev": 0.10,
    "electric": 0.13,
    "sedan": 0.15,
    "default": 0.12,
}

# Rough segment base prices (CLP) used when no year is parsed
_SEGMENT_BASE_PRICES: dict[str, int] = {
    "suv_compact": 18_000_000,
    "suv_medium": 22_000_000,
    "hybrid_phev": 30_000_000,
    "electric": 25_000_000,
    "sedan": 16_000_000,
    "default": 18_000_000,
}


def estimate_current_car_value(car_name: str, segment: str = "suv_compact") -> int:
    """Estimate the current resale value of the user's car.

    Parses the model year from the car name string (e.g. "Toyota RAV4 2020"),
    then applies an annual depreciation rate appropriate to the segment.
    If no year can be parsed, a single period of depreciation is applied.

    Args:
        car_name: Free-text car name, optionally containing a 4-digit year.
        segment: Vehicle segment key used to select depreciation rate and base price.

    Returns:
        Estimated resale value in CLP.
    """
    current_year = 2024
    base_price = _SEGMENT_BASE_PRICES.get(segment, _SEGMENT_BASE_PRICES["default"])
    rate = _DEPRECIATION_RATES.get(segment, _DEPRECIATION_RATES["default"])

    # Attempt to extract a 4-digit year from the car name
    match = re.search(r"\b(20\d{2})\b", car_name)
    if match:
        car_year = int(match.group(1))
        age = max(current_year - car_year, 0)
    else:
        # No year found: assume 3-year-old car as a conservative default
        age = 3

    value = base_price * ((1 - rate) ** age)
    return max(int(value), 0)


def calculate_change_cost(new_car_price: int, current_car_value: int) -> int:
    """Compute the net out-of-pocket cost to change cars.

    Args:
        new_car_price: Price of the new car in CLP.
        current_car_value: Estimated resale value of the current car in CLP.

    Returns:
        Net change cost (new_price - current_value), minimum 0.
    """
    cost = new_car_price - current_car_value
    return max(cost, 0)


def calculate_monthly_fuel_saving(
    current_consumption: float,
    new_consumption: float,
    monthly_km: int,
    fuel_type_new: str,
    fuel_prices: dict,
) -> int:
    """Compute monthly CLP fuel savings switching from current to new car.

    For electric vehicles, consumption is expressed in kWh/100 km.
    For all others it is km per litre (km/L).

    Args:
        current_consumption: Current car consumption in km/L.
        new_consumption: New car consumption in km/L (or kWh/100 km if electric).
        monthly_km: Average monthly kilometres driven.
        fuel_type_new: Fuel type of the new car: gasoline, diesel, electric, hybrid, phev.
        fuel_prices: Dict with keys FUEL_PRICE_95, FUEL_PRICE_DIESEL, FUEL_PRICE_KWH (CLP).

    Returns:
        Monthly savings in CLP (positive = saving, 0 if new car costs more).
    """
    price_gasoline: int = fuel_prices.get("FUEL_PRICE_95", 1100)
    price_diesel: int = fuel_prices.get("FUEL_PRICE_DIESEL", 1050)
    price_kwh: int = fuel_prices.get("FUEL_PRICE_KWH", 120)

    # Current car cost (assume gasoline unless told otherwise)
    # cost_per_km = price_per_liter / consumption_kpl
    current_cost_per_km = (
        price_gasoline / current_consumption if current_consumption else 0
    )
    current_monthly_cost = current_cost_per_km * monthly_km

    # New car cost
    if fuel_type_new == "electric":
        # new_consumption is kWh/100km for electric
        new_cost_per_km = (new_consumption * price_kwh) / 100
    elif fuel_type_new == "diesel":
        new_cost_per_km = price_diesel / new_consumption if new_consumption else 0
    elif fuel_type_new in ("hybrid", "phev"):
        new_cost_per_km = price_gasoline / new_consumption if new_consumption else 0
    else:
        new_cost_per_km = price_gasoline / new_consumption if new_consumption else 0

    new_monthly_cost = new_cost_per_km * monthly_km

    saving = current_monthly_cost - new_monthly_cost
    return max(int(saving), 0)


def calculate_payback_months(change_cost: int, monthly_saving: int) -> Optional[int]:
    """Calculate the number of months to recover the car change investment.

    Args:
        change_cost: Net cost to change cars in CLP.
        monthly_saving: Monthly fuel savings in CLP.

    Returns:
        Number of months to break even, or None if monthly_saving <= 0.
    """
    if monthly_saving <= 0:
        return None
    return int(change_cost / monthly_saving)


def calculate_annual_depreciation(price: int, resale_score: int) -> int:
    """Estimate the annual monetary depreciation of a vehicle.

    Higher resale scores imply slower depreciation.

    Args:
        price: Current market price of the car in CLP.
        resale_score: Resale score on a 1–10 scale (10 = best retention).

    Returns:
        Estimated annual depreciation in CLP.
    """
    # Map score 1-10 to annual rate: score 10 → 8%, score 1 → 20%
    rate = 0.20 - (resale_score - 1) * (0.12 / 9)
    return int(price * rate)


def estimate_annual_maintenance(maintenance_cost_score: int, price: int) -> int:
    """Estimate annual maintenance expenditure.

    Lower maintenance cost score implies higher annual cost.

    Args:
        maintenance_cost_score: Score on a 1–10 scale (10 = very cheap to maintain).
        price: Car price in CLP used as a reference base.

    Returns:
        Estimated annual maintenance cost in CLP.
    """
    # Score 10 → ~1% of price per year, score 1 → ~4% of price per year
    rate = 0.04 - (maintenance_cost_score - 1) * (0.03 / 9)
    return int(price * rate)
