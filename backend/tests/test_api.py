"""Integration tests for SoloMiro FastAPI endpoints."""

from __future__ import annotations

RECOMMEND_PAYLOAD = {
    "current_car": "Toyota RAV4 2020",
    "goals": ["lower_consumption", "better_resale"],
    "car_type": "both",
    "budget_range": "unknown",
    "monthly_km": 1000,
    "driving_style": "mixed",
    "can_charge_at_home": False,
}


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_endpoint(self, client):
        """Health endpoint should return 200 with status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestRecommendEndpoint:
    """Tests for POST /recommend."""

    def test_recommend_endpoint_basic(self, client):
        """Recommend endpoint should return 200 with 3 recommendations."""
        response = client.post("/recommend", json=RECOMMEND_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) == 3
        assert "session_id" in data

    def test_recommend_endpoint_saves_to_db(self, client, db_session):
        """Recommend endpoint should persist results to the database."""
        from app.models import Recommendation

        response = client.post("/recommend", json=RECOMMEND_PAYLOAD)
        assert response.status_code == 200
        session_id = response.json()["session_id"]

        rec = db_session.query(Recommendation).filter_by(session_id=session_id).first()
        assert rec is not None
        assert rec.current_car == RECOMMEND_PAYLOAD["current_car"]

    def test_recommend_endpoint_returns_general_verdict(self, client):
        """Response should include a general_verdict string."""
        response = client.post("/recommend", json=RECOMMEND_PAYLOAD)
        assert response.status_code == 200
        assert "general_verdict" in response.json()


class TestCarsEndpoint:
    """Tests for GET /cars and GET /cars/{id}."""

    def test_cars_endpoint_returns_list(self, client):
        """GET /cars should return a non-empty list of cars."""
        response = client.get("/cars")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 55

    def test_cars_by_id_found(self, client):
        """GET /cars/1 should return the first car."""
        response = client.get("/cars/1")
        assert response.status_code == 200
        car = response.json()
        assert car["id"] == 1

    def test_cars_by_id_not_found(self, client):
        """GET /cars/999 should return 404."""
        response = client.get("/cars/999")
        assert response.status_code == 404


class TestLeadsEndpoint:
    """Tests for POST /leads."""

    def test_leads_endpoint_saves_lead(self, client, db_session):
        """POST /leads should persist the lead and return lead_id."""
        from app.models import Lead

        payload = {
            "session_id": "test-session-123",
            "name": "Juan Pérez",
            "whatsapp": "+56912345678",
            "current_car": "Toyota RAV4 2020",
            "budget_clp": 20000000,
            "city": "Santiago",
            "buy_timeframe": "3_months",
        }
        response = client.post("/leads", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "lead_id" in data

        lead = db_session.query(Lead).filter_by(session_id="test-session-123").first()
        assert lead is not None
        assert lead.whatsapp == "+56912345678"
