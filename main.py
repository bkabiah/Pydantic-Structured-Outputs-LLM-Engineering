"""Entry point der FastAPI-Anwendung."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api.routes import router
from app.config import get_settings

settings = get_settings()

logging.basicConfig(level=settings.log_level)

app = FastAPI(
    title=settings.app_name,
    description=(
        "Extrahiert strukturierte, validierte Daten (Rechnungen, Lebensläufe) "
        "aus unstrukturiertem Text mittels LLM + Pydantic."
    ),
    version="0.1.0",
)

app.include_router(router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"{settings.app_name} läuft. Siehe /docs für die API-Dokumentation."}
