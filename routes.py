"""API-Endpunkte für den Extraction-Service."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.config import LLMProvider, Settings, get_settings
from app.core.exceptions import ExtractionFailedError, LLMProviderError
from app.models import DocumentType
from app.services.extraction_service import ExtractionService
from app.services.llm_client import AnthropicClient, LLMClient, MockLLMClient, OpenAIClient

router = APIRouter(prefix="/api/v1", tags=["extraction"])


class ExtractRequest(BaseModel):
    text: str = Field(
        ..., min_length=1, max_length=20_000, description="Unstrukturierter Quelltext"
    )
    document_type: DocumentType


class ExtractResponse(BaseModel):
    document_type: DocumentType
    data: dict[str, Any]


def get_llm_client(settings: Annotated[Settings, Depends(get_settings)]) -> LLMClient:
    """Baut den passenden LLM-Client anhand der Konfiguration (Dependency Injection)."""
    if settings.llm_provider == LLMProvider.OPENAI and settings.openai_api_key:
        return OpenAIClient(api_key=settings.openai_api_key, model=settings.openai_model)
    if settings.llm_provider == LLMProvider.ANTHROPIC and settings.anthropic_api_key:
        return AnthropicClient(api_key=settings.anthropic_api_key, model=settings.anthropic_model)
    return MockLLMClient()


def get_extraction_service(
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
) -> ExtractionService:
    return ExtractionService(llm_client=llm_client)


@router.post("/extract", response_model=ExtractResponse)
async def extract(
    request: ExtractRequest,
    service: Annotated[ExtractionService, Depends(get_extraction_service)],
) -> ExtractResponse:
    """Extrahiert strukturierte Daten aus unstrukturiertem Text."""
    try:
        result = await service.extract(request.text, request.document_type)
    except ExtractionFailedError as exc:
        raise HTTPException(
            status_code=422,
            detail={"message": str(exc), "last_error": exc.last_error},
        ) from exc
    except LLMProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ExtractResponse(document_type=request.document_type, data=result.model_dump())


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
