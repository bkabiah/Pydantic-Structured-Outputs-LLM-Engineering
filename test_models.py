
import pytest
from pydantic import ValidationError

from app.models import Invoice, LineItem, Resume


def make_line_item(**overrides) -> dict:
    base = {"description": "Beratung", "quantity": 2, "unit_price": 50.0, "total": 100.0}
    base.update(overrides)
    return base


def make_invoice(**overrides) -> dict:
    base = {
        "invoice_number": "INV-001",
        "issue_date": "2026-01-01",
        "due_date": "2026-01-15",
        "vendor_name": "Acme GmbH",
        "customer_name": "Kunde AG",
        "line_items": [make_line_item()],
        "currency": "eur",
        "total_amount": 100.0,
    }
    base.update(overrides)
    return base


class TestLineItem:
    def test_valid_line_item(self):
        item = LineItem.model_validate(make_line_item())
        assert item.total == 100.0

    def test_negative_quantity_rejected(self):
        with pytest.raises(ValidationError):
            LineItem.model_validate(make_line_item(quantity=-1))

    def test_inconsistent_total_rejected(self):
        with pytest.raises(ValidationError):
            LineItem.model_validate(make_line_item(total=999.0))


class TestInvoice:
    def test_valid_invoice(self):
        invoice = Invoice.model_validate(make_invoice())
        assert invoice.invoice_number == "INV-001"
        # currency wird normalisiert (ConfigDict + Validator)
        assert invoice.currency == "EUR"

    def test_due_date_before_issue_date_rejected(self):
        with pytest.raises(ValidationError):
            Invoice.model_validate(
                make_invoice(issue_date="2026-01-15", due_date="2026-01-01")
            )

    def test_total_amount_mismatch_rejected(self):
        with pytest.raises(ValidationError):
            Invoice.model_validate(make_invoice(total_amount=500.0))

    def test_empty_line_items_rejected(self):
        with pytest.raises(ValidationError):
            Invoice.model_validate(make_invoice(line_items=[]))

    def test_unknown_field_rejected(self):
        data = make_invoice()
        data["not_a_real_field"] = "sollte ablehnen"
        with pytest.raises(ValidationError):
            Invoice.model_validate(data)


class TestResume:
    def test_valid_resume(self):
        resume = Resume.model_validate(
            {
                "full_name": "Maria Musterfrau",
                "email": "maria@example.com",
                "total_years_experience": 3,
            }
        )
        assert resume.full_name == "Maria Musterfrau"

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            Resume.model_validate(
                {
                    "full_name": "Maria Musterfrau",
                    "email": "keine-email",
                    "total_years_experience": 3,
                }
            )

    def test_negative_experience_rejected(self):
        with pytest.raises(ValidationError):
            Resume.model_validate(
                {"full_name": "Maria Musterfrau", "total_years_experience": -1}
            )
