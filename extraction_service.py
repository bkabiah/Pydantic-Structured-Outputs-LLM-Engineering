"""Orchestriert den Extraktionsprozess: Prompt bauen, LLM aufrufen, validieren,
bei Bedarf einmal mit Fehlerkontext erneut versuchen ("Self-Healing")."""

from __future__ import annotations

import json
import logging

from pydantic import BaseModel, ValidationError

from app.core.exceptions import ExtractionFailedError, LLMProviderError
from app.models import DocumentType, Invoice, Resume
from app.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

_SCHEMA_MAP: dict[DocumentType, type[BaseModel]] = {
    DocumentType.INVOICE: Invoice,
    DocumentType.RESUME: Resume,
}

_MAX_RETRIES = 1


class ExtractionService:
    """Extrahiert strukturierte, validierte Daten aus Freitext."""

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    async def extract(self, text: str, document_type: DocumentType) -> BaseModel:
        """Extrahiert und validiert Daten für den gegebenen Dokumenttyp.

        Raises:
            ExtractionFailedError: wenn auch nach Retry keine valide Struktur
                erzeugt werden konnte.
        """
        model_cls = _SCHEMA_MAP[document_type]
        schema = model_cls.model_json_schema()
        prompt = self._build_prompt(text, document_type, schema)

        last_error: ValidationError | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                raw = await self._llm_client.complete_json(prompt, schema)
            except LLMProviderError:
                raise

            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                last_error = exc  # type: ignore[assignment]
                logger.warning("Ungültiges JSON vom LLM (Versuch %s): %s", attempt + 1, exc)
                prompt = self._build_retry_prompt(prompt, str(exc))
                continue

            try:
                return model_cls.model_validate(data)
            except ValidationError as exc:
                last_error = exc
                logger.warning(
                    "Validierung fehlgeschlagen (Versuch %s/%s): %s",
                    attempt + 1,
                    _MAX_RETRIES + 1,
                    exc,
                )
                prompt = self._build_retry_prompt(prompt, str(exc))

        raise ExtractionFailedError(
            f"Extraktion nach {_MAX_RETRIES + 1} Versuchen fehlgeschlagen.",
            last_error=str(last_error) if last_error else None,
        )

    @staticmethod
    def _build_prompt(text: str, document_type: DocumentType, schema: dict) -> str:
        return (
            f"Extrahiere strukturierte Daten vom Typ '{document_type.value}' "
            f"aus folgendem Text. Antworte AUSSCHLIESSLICH mit validem JSON, "
            f"das exakt diesem JSON-Schema entspricht:\n\n"
            f"{json.dumps(schema)}\n\n"
            f"Text:\n\"\"\"\n{text}\n\"\"\""
        )

    @staticmethod
    def _build_retry_prompt(previous_prompt: str, error_message: str) -> str:
        return (
            f"{previous_prompt}\n\n"
            f"Dein letzter Versuch war fehlerhaft. Fehler:\n{error_message}\n"
            f"Bitte korrigiere die Daten und antworte erneut AUSSCHLIESSLICH mit validem JSON."
        )
