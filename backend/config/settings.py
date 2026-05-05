"""Application settings loaded from environment variables via python-decouple."""

from __future__ import annotations

from decouple import config


class Settings:
    """Central configuration object for SoloMiro backend.

    All values are read from environment variables or .env file.
    Defaults are suitable for local SQLite development.
    """

    DATABASE_URL: str = config("DATABASE_URL", default="sqlite:///./data/solomiro.db")
    AI_PROVIDER: str = config("AI_PROVIDER", default="anthropic")
    AI_API_KEY: str = config("AI_API_KEY", default="")
    AI_MODEL: str = config("AI_MODEL", default="claude-sonnet-4-5")
    ALLOWED_ORIGINS: str = config("ALLOWED_ORIGINS", default="http://localhost:3000")
    LOG_LEVEL: str = config("LOG_LEVEL", default="INFO")

    # Fuel prices in CLP per litre / kWh
    FUEL_PRICE_95: int = config("FUEL_PRICE_95", default=1100, cast=int)
    FUEL_PRICE_DIESEL: int = config("FUEL_PRICE_DIESEL", default=1050, cast=int)
    FUEL_PRICE_KWH: int = config("FUEL_PRICE_KWH", default=120, cast=int)

    @property
    def allowed_origins_list(self) -> list[str]:
        """Return ALLOWED_ORIGINS as a list split by comma."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
