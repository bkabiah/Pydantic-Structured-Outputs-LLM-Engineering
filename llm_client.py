"""Abstraktes LLM-Client-Interface + konkrete Implementierungen.

Design: Jeder Client bekommt einen Prompt + das Ziel-JSON-Schema und muss
rohen JSON-Text zurückgeben. Die Validierung gegen das Pydantic-Modell
passiert bewusst NICHT hier, sondern im ExtractionService – so bleibt der
Client dumm, austauschbar und leicht testbar.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from datetime import date

from app.core.exceptions import LLMProviderError


class LLMClient(ABC):
    """Interface, das jeder LLM-Provider implementieren muss."""

    @abstractmethod
    async def complete_json(self, prompt: str, json_schema: dict) -> str:
        """Gibt einen rohen JSON-String zurück, der dem gegebenen Schema folgen soll."""
        raise NotImplementedError


class OpenAIClient(LLMClient):
    """Nutzt OpenAIs Structured Outputs (response_format=json_schema)."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._api_key = api_key
        self._model = model

    async def complete_json(self, prompt: str, json_schema: dict) -> str:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:  # pragma: no cover
            raise LLMProviderError(
                "Paket 'openai' ist nicht installiert. `pip install openai`."
            ) from exc

        client = AsyncOpenAI(api_key=self._api_key)
        try:
            response = await client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "extraction", "schema": json_schema, "strict": True},
                },
            )
        except Exception as exc:  # pragma: no cover
            raise LLMProviderError(f"OpenAI-Anfrage fehlgeschlagen: {exc}") from exc

        content = response.choices[0].message.content
        if content is None:
            raise LLMProviderError("OpenAI hat keinen Inhalt zurückgegeben.")
        return content


class AnthropicClient(LLMClient):
    """Nutzt Anthropics Tool-Use, um strukturierten JSON-Output zu erzwingen."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-5") -> None:
        self._api_key = api_key
        self._model = model

    async def complete_json(self, prompt: str, json_schema: dict) -> str:
        try:
            from anthropic import AsyncAnthropic
        except ImportError as exc:  # pragma: no cover
            raise LLMProviderError(
                "Paket 'anthropic' ist nicht installiert. `pip install anthropic`."
            ) from exc

        client = AsyncAnthropic(api_key=self._api_key)
        tool_name = "return_extraction"
        try:
            response = await client.messages.create(
                model=self._model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
                tools=[
                    {
                        "name": tool_name,
                        "description": "Gibt die extrahierten, strukturierten Daten zurück.",
                        "input_schema": json_schema,
                    }
                ],
                tool_choice={"type": "tool", "name": tool_name},
            )
        except Exception as exc:  # pragma: no cover
            raise LLMProviderError(f"Anthropic-Anfrage fehlgeschlagen: {exc}") from exc

        for block in response.content:
            if block.type == "tool_use":
                return json.dumps(block.input)
        raise LLMProviderError("Anthropic hat keinen tool_use-Block zurückgegeben.")


class MockLLMClient(LLMClient):
    """Regelbasierter Fake-Client für Demo, lokale Entwicklung und CI.

    Extrahiert Daten mit simplen Heuristiken/Regex statt eines echten LLM.
    So kann das gesamte Projekt (inkl. Tests) ohne API-Key laufen.
    """

    async def complete_json(self, prompt: str, json_schema: dict) -> str:
        schema_title = json_schema.get("title", "")
        source_text = self._extract_source_text(prompt)
        if "Invoice" in schema_title or "invoice_number" in json_schema.get("properties", {}):
            return self._mock_invoice(source_text)
        if "Resume" in schema_title or "full_name" in json_schema.get("properties", {}):
            return self._mock_resume(source_text)
        raise LLMProviderError(f"MockLLMClient kennt Schema '{schema_title}' nicht.")

    @staticmethod
    def _extract_source_text(prompt: str) -> str:
        """Isoliert den eigentlichen Nutzertext aus dem Prompt (zwischen den \"\"\"-Markern),
        damit das eingebettete JSON-Schema nicht versehentlich mit-durchsucht wird."""
        match = re.search(r'"""\n(.*?)\n"""', prompt, re.DOTALL)
        return match.group(1) if match else prompt

    @staticmethod
    def _mock_invoice(prompt: str) -> str:
        number = re.search(r"(?:Rechnungsnummer|Invoice)\s*[:#]?\s*([A-Za-z0-9\-]+)", prompt)
        amount = re.search(r"(\d+(?:[.,]\d{2}))\s*(?:EUR|€)", prompt)
        total = float(amount.group(1).replace(",", ".")) if amount else 119.0
        data = {
            "invoice_number": number.group(1) if number else "MOCK-0001",
            "issue_date": str(date.today()),
            "due_date": None,
            "vendor_name": "Mock Vendor GmbH",
            "customer_name": "Mock Customer AG",
            "line_items": [
                {
                    "description": "Extrahierte Dienstleistung",
                    "quantity": 1,
                    "unit_price": total,
                    "total": total,
                }
            ],
            "currency": "EUR",
            "total_amount": total,
        }
        return json.dumps(data)

    @staticmethod
    def _mock_resume(prompt: str) -> str:
        name_pattern = r"(?:Name|full_name)\s*[:#]?\s*([A-ZÄÖÜ][a-zäöüß]+\s[A-ZÄÖÜ][a-zäöüß]+)"
        name = re.search(name_pattern, prompt)
        email = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", prompt)
        data = {
            "full_name": name.group(1) if name else "Max Mustermann",
            "email": email.group(0) if email else None,
            "headline": "Junior AI Engineer",
            "work_experience": [],
            "skills": [{"name": "Python", "years_experience": 2}],
            "total_years_experience": 2,
        }
        return json.dumps(data)
