"""SoloMiro FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import advisor, leads
from config.settings import settings

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler — initialise the database on startup."""
    logger.info("Starting SoloMiro API…")
    init_db()
    yield
    logger.info("Shutting down SoloMiro API.")


app = FastAPI(
    title="SoloMiro API",
    version="1.0.0",
    description="AI-powered car advisor for the Chilean market.",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(advisor.router)
app.include_router(leads.router)
