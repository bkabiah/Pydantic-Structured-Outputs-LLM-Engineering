"""Datenmodell für die Extraktion von Rechnungsdaten."""

from __future__ import annotations

from datetime import date

from pydantic import Field, field_validator, model_validator

from app.models.base import ExtractableModel


class LineItem(ExtractableModel):
    """Eine einzelne Position auf der Rechnung."""

    description: str = Field(..., min_length=1, max_length=200)
    quantity: float = Field(..., gt=0, description="Menge, muss positiv sein")
    unit_price: float = Field(..., ge=0, description="Einzelpreis in der Rechnungswährung")
    total: float = Field(..., ge=0, description="quantity * unit_price")

    @model_validator(mode="after")
    def check_total_consistency(self) -> LineItem:
        """Prüft, dass die Summe der Position rechnerisch stimmt (mit Toleranz)."""
        expected = round(self.quantity * self.unit_price, 2)
        if abs(expected - self.total) > 0.05:
            raise ValueError(
                f"Summe der Position stimmt nicht: {self.quantity} * "
                f"{self.unit_price} != {self.total}"
            )
        return self


class Invoice(ExtractableModel):
    """Strukturierte Rechnungsdaten, wie sie aus Freitext extrahiert werden."""

    invoice_number: str = Field(..., min_length=1, max_length=50)
    issue_date: date
    due_date: date | None = None
    vendor_name: str = Field(..., min_length=1, max_length=120)
    customer_name: str = Field(..., min_length=1, max_length=120)
    line_items: list[LineItem] = Field(..., min_length=1)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    total_amount: float = Field(..., ge=0)

    @field_validator("currency")
    @classmethod
    def currency_upper(cls, v: str) -> str:
        return v.upper()

    @model_validator(mode="after")
    def check_due_date_after_issue(self) -> Invoice:
        if self.due_date is not None and self.due_date < self.issue_date:
            raise ValueError("due_date darf nicht vor issue_date liegen")
        return self

    @model_validator(mode="after")
    def check_total_matches_line_items(self) -> Invoice:
        computed = round(sum(item.total for item in self.line_items), 2)
        if abs(computed - self.total_amount) > 0.10:
            raise ValueError(
                f"total_amount ({self.total_amount}) passt nicht zur Summe "
                f"der Positionen ({computed})"
            )
        return self
