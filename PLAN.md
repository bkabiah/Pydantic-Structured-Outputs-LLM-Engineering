# Projektplan: Pydantic AI Extraction Service

## 1. Idee & Motivation

Firmen ertrinken in unstrukturierten Dokumenten (Rechnungen, Lebensläufe, Verträge).
Dieses Projekt zeigt, wie man mit **LLMs + Pydantic** zuverlässig **strukturierte,
validierte Daten** aus freiem Text extrahiert – ein Kernpattern im modernen
AI-Engineering (Structured Outputs / Tool Calling / Function Calling).

Ziel des Projekts (als Portfolio-Stück):
- Zeigen, dass ich Pydantic v2 (Validierung, Custom Validators, Field-Constraints) sicher beherrsche
- Zeigen, dass ich LLM-APIs sauber in eine Service-Architektur einbette (Retry, Fehlerbehandlung, Provider-Abstraktion)
- Zeigen, dass ich eine REST-API mit FastAPI production-ready baue (Dependency Injection, Config-Management, Tests, Docker, CI)

## 2. Anforderungen

### Funktional
- REST-Endpoint, der unstrukturierten Text entgegennimmt und ein strukturiertes
  JSON-Objekt gemäß Pydantic-Schema zurückgibt
- Unterstützung mehrerer Dokumenttypen: `invoice` (Rechnung), `resume` (Lebenslauf)
- Validierungsfehler des LLM-Outputs werden abgefangen und einmal automatisch
  per Retry korrigiert (Self-Healing-Pattern)
- Health-Check-Endpoint

### Nicht-funktional
- Läuft lokal ohne echten API-Key (Mock-LLM-Client für Demo/Tests/CI)
- Austauschbarer LLM-Provider (OpenAI, Anthropic, Mock) über ein Interface
- Vollständig typisiert, mit Unit- und Integrationstests
- Dockerisiert, mit CI-Pipeline (GitHub Actions)

## 3. Architektur

```
Client
  │  POST /api/v1/extract
  ▼
FastAPI Router (app/api/routes.py)
  │  validiert Request (Pydantic)
  ▼
ExtractionService (app/services/extraction_service.py)
  │  wählt Zielschema (Invoice / Resume)
  │  baut Prompt, ruft LLMClient auf
  │  validiert Antwort gegen Pydantic-Modell
  │  bei ValidationError: 1x Retry mit Fehlerkontext im Prompt
  ▼
LLMClient (Interface, app/services/llm_client.py)
  ├── OpenAIClient      (structured outputs via response_format / tool calling)
  ├── AnthropicClient   (structured outputs via tool_use)
  └── MockLLMClient     (regelbasiert, für Tests/Demo ohne API-Key)
  ▼
Pydantic-Modelle (app/models/*.py)
  → Invoice, Resume, ExtractionResult
```

### Design-Entscheidungen (und warum)

| Entscheidung | Begründung |
|---|---|
| Pydantic v2 statt v1 | aktueller Standard, schneller (Rust-Core), bessere Validator-API |
| Provider-Interface (`LLMClient` ABC) | Vendor-Lock-in vermeiden, einfach testbar durch Mock |
| Self-Healing-Retry bei `ValidationError` | typisches Real-World-Problem bei LLM-Outputs – zeigt Verständnis für Zuverlässigkeit |
| Mock-Client als Default | Projekt muss ohne Kosten/Keys lauffähig sein – wichtig für Reviewer/Recruiter |
| FastAPI | Industriestandard für Python-AI-APIs, native Pydantic-Integration |
| Strikte `Field`-Constraints (z. B. `ge=0`, `max_length`) | zeigt Verständnis von Datenqualität, nicht nur "es kompiliert" |

## 4. Roadmap (Umsetzungsschritte)

1. [x] Pydantic-Datenmodelle definieren (Invoice, Resume, gemeinsame Basis)
2. [x] LLM-Client-Interface + Mock-Implementierung
3. [x] Echte Provider-Implementierungen (OpenAI, Anthropic) hinter Feature-Flag
4. [x] ExtractionService mit Retry-Logik
5. [x] FastAPI-Endpoints + Fehlerbehandlung (HTTP 422 bei nicht extrahierbaren Daten)
6. [x] Unit-Tests (Modelle) + Integrationstests (API, mit Mock-Client)
7. [x] Dockerfile + docker-compose
8. [x] GitHub Actions CI (Lint + Tests)
9. [ ] Erweiterung: PDF-Upload statt nur Rohtext (nächster Schritt, siehe README "Ausblick")
10. [ ] Erweiterung: echtes Vektor-Caching für wiederholte Extraktionen

## 5. Was dieses Projekt im Bewerbungsprozess zeigen soll

- Sauberer, idiomatischer Python-Code (Type Hints überall, PEP8, `ruff`)
- Verständnis von LLM-Integrationsmustern (nicht nur "prompt reinschicken")
- Testbarkeit und CI/CD-Bewusstsein
- Dokumentationsfähigkeit (dieses Dokument + README)
