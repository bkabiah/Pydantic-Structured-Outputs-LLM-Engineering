from fastapi.testclient import TestClient


def test_health(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_extract_invoice(client: TestClient):
    payload = {
        "text": "Rechnungsnummer: INV-42. Gesamtbetrag: 119,00 EUR.",
        "document_type": "invoice",
    }
    response = client.post("/api/v1/extract", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["document_type"] == "invoice"
    assert body["data"]["invoice_number"] == "INV-42"
    assert body["data"]["total_amount"] == 119.0


def test_extract_resume(client: TestClient):
    payload = {
        "text": "Name: Anna Beispiel. E-Mail: anna@example.com",
        "document_type": "resume",
    }
    response = client.post("/api/v1/extract", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["full_name"] == "Anna Beispiel"
    assert body["data"]["email"] == "anna@example.com"


def test_extract_invalid_document_type_rejected(client: TestClient):
    payload = {"text": "irrelevant", "document_type": "not_a_type"}
    response = client.post("/api/v1/extract", json=payload)
    assert response.status_code == 422


def test_extract_empty_text_rejected(client: TestClient):
    payload = {"text": "", "document_type": "invoice"}
    response = client.post("/api/v1/extract", json=payload)
    assert response.status_code == 422
