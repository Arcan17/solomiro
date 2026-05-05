"""Unit tests for the calculator service."""

from __future__ import annotations

from app.services.calculator import (
    calculate_change_cost,
    calculate_monthly_fuel_saving,
    calculate_payback_months,
    estimate_current_car_value,
)


class TestEstimateCurrentCarValue:
    """Tests for estimate_current_car_value."""

    def test_estimate_current_car_value_with_year(self):
        """Should parse year from name and apply depreciation."""
        # Toyota RAV4 2020 → 4 years old at 12% per year
        value = estimate_current_car_value("Toyota RAV4 2020", "suv_medium")
        base = 22_000_000
        expected = int(base * (0.88**4))
        # Allow 5% tolerance
        assert abs(value - expected) < expected * 0.05

    def test_estimate_current_car_value_no_year(self):
        """Should use default age of 3 when no year found in name."""
        value = estimate_current_car_value("Toyota RAV4", "suv_medium")
        base = 22_000_000
        expected = int(base * (0.88**3))
        assert abs(value - expected) < expected * 0.05

    def test_estimate_value_is_non_negative(self):
        """Value should never be negative regardless of car age."""
        value = estimate_current_car_value("Old Car 2005", "sedan")
        assert value >= 0


class TestCalculateChangeCost:
    """Tests for calculate_change_cost."""

    def test_calculate_change_cost_positive(self):
        """Should return new_price minus current_value when positive."""
        result = calculate_change_cost(20_000_000, 12_000_000)
        assert result == 8_000_000

    def test_calculate_change_cost_negative_becomes_zero(self):
        """Should return 0 when current value exceeds new car price."""
        result = calculate_change_cost(10_000_000, 15_000_000)
        assert result == 0


class TestCalculateMonthlyFuelSaving:
    """Tests for calculate_monthly_fuel_saving."""

    def test_calculate_monthly_fuel_saving_gasoline(self):
        """Should calculate positive saving when new car uses more km per liter."""
        prices = {
            "FUEL_PRICE_95": 1100,
            "FUEL_PRICE_DIESEL": 1050,
            "FUEL_PRICE_KWH": 120,
        }
        saving = calculate_monthly_fuel_saving(
            current_consumption=10.0,  # km/L (old car)
            new_consumption=20.0,  # km/L (new car, more efficient)
            monthly_km=1000,
            fuel_type_new="gasoline",
            fuel_prices=prices,
        )
        # Current: 1100/10 * 1000 = 110,000 CLP/month
        # New: 1100/20 * 1000 = 55,000 CLP/month
        # Saving: 55,000 CLP
        assert saving == 55_000

    def test_calculate_monthly_fuel_saving_electric(self):
        """Should compute electric savings against gasoline baseline."""
        prices = {
            "FUEL_PRICE_95": 1100,
            "FUEL_PRICE_DIESEL": 1050,
            "FUEL_PRICE_KWH": 120,
        }
        saving = calculate_monthly_fuel_saving(
            current_consumption=10.0,  # km/L (current gasoline car)
            new_consumption=15.0,  # kWh/100km for electric
            monthly_km=1000,
            fuel_type_new="electric",
            fuel_prices=prices,
        )
        # Current: 1100/10 * 1000 = 110,000 CLP/month
        # New electric: (15 * 120 / 100) * 1000 = 18,000 CLP/month
        # Saving: 92,000 CLP
        assert saving == 92_000

    def test_calculate_monthly_fuel_saving_zero_when_no_improvement(self):
        """Should return 0 when new car has lower km/L (worse consumption)."""
        prices = {
            "FUEL_PRICE_95": 1100,
            "FUEL_PRICE_DIESEL": 1050,
            "FUEL_PRICE_KWH": 120,
        }
        saving = calculate_monthly_fuel_saving(
            current_consumption=15.0,  # km/L (efficient current car)
            new_consumption=10.0,  # km/L (less efficient new car)
            monthly_km=1000,
            fuel_type_new="gasoline",
            fuel_prices=prices,
        )
        assert saving == 0


class TestCalculatePaybackMonths:
    """Tests for calculate_payback_months."""

    def test_calculate_payback_months_basic(self):
        """Should compute correct payback period."""
        result = calculate_payback_months(10_000_000, 100_000)
        assert result == 100

    def test_calculate_payback_months_no_saving_returns_none(self):
        """Should return None when monthly saving is zero or negative."""
        result = calculate_payback_months(10_000_000, 0)
        assert result is None
