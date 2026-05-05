"""SQLAlchemy ORM models for SoloMiro."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.database import Base


class Recommendation(Base):
    """Stores each recommendation session result."""

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(
        String(36), unique=True, index=True, nullable=False
    )
    current_car: Mapped[str] = mapped_column(String(200), nullable=False)
    goals: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    budget_range: Mapped[str] = mapped_column(String(20), nullable=False)
    car_type: Mapped[str] = mapped_column(String(10), nullable=False)
    monthly_km: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    driving_style: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    can_charge_at_home: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    result_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )


class Lead(Base):
    """Stores WhatsApp lead capture data."""

    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    whatsapp: Mapped[str] = mapped_column(String(20), nullable=False)
    current_car: Mapped[str] = mapped_column(String(200), nullable=False)
    budget_clp: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    buy_timeframe: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
