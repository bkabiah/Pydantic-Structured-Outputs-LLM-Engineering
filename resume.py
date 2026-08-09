"""Datenmodell für die Extraktion von Lebenslauf-Daten."""

from __future__ import annotations

from datetime import date

from pydantic import EmailStr, Field, model_validator

from app.models.base import ExtractableModel


class WorkExperience(ExtractableModel):
    """Eine Station im beruflichen Werdegang."""

    company: str = Field(..., min_length=1, max_length=120)
    role: str = Field(..., min_length=1, max_length=120)
    start_date: date
    end_date: date | None = Field(default=None, description="None = aktuelle Stelle")
    description: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def check_dates(self) -> WorkExperience:
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date darf nicht vor start_date liegen")
        return self


class Skill(ExtractableModel):
    name: str = Field(..., min_length=1, max_length=60)
    years_experience: float | None = Field(default=None, ge=0, le=60)


class Resume(ExtractableModel):
    """Strukturierte Lebenslauf-Daten, wie sie aus Freitext extrahiert werden."""

    full_name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr | None = None
    headline: str | None = Field(default=None, max_length=150)
    work_experience: list[WorkExperience] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    total_years_experience: float = Field(..., ge=0, le=60)
