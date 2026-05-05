"""Database engine and session management for SoloMiro."""

from __future__ import annotations

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config.settings import settings

logger = logging.getLogger(__name__)


def _get_engine():
    """Create SQLAlchemy engine with appropriate configuration."""
    connect_args = {}
    if settings.DATABASE_URL.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_engine(settings.DATABASE_URL, connect_args=connect_args)


engine = _get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""

    pass


def get_db():
    """Yield a database session and close it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables defined in the ORM models."""
    from app import models  # noqa: F401 – ensure models are imported before create_all

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized.")
