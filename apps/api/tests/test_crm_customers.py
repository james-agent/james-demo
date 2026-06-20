"""Tests for CRM customer mock API."""

from fastapi.testclient import TestClient

from crm_api.main import app

client = TestClient(app)


def test_list_customers_default_pagination() -> None:
    response = client.get("/api/v1/crm/customers")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["pageSize"] == 10
    assert data["totalItems"] >= 25
    assert len(data["items"]) == 10


def test_list_customers_invalid_page_size() -> None:
    response = client.get("/api/v1/crm/customers?pageSize=15")
    assert response.status_code == 400


def test_list_customers_name_filter() -> None:
    response = client.get(
        "/api/v1/crm/customers", params={"name": "Alice", "pageSize": 25}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["totalItems"] == 1
    assert data["items"][0]["name"] == "Alice Morgan"


def test_list_customers_combined_filters() -> None:
    response = client.get(
        "/api/v1/crm/customers",
        params={"name": "Bruno", "email": "acme", "q": "Brazil", "pageSize": 25},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["totalItems"] == 1
    assert data["items"][0]["email"] == "bruno.ferreira@acme.com.br"


def test_get_customer_detail() -> None:
    response = client.get("/api/v1/crm/customers/cust-001")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "cust-001"
    assert len(data["comments"]) >= 1


def test_get_customer_not_found() -> None:
    response = client.get("/api/v1/crm/customers/missing-id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"
