import pytest
from fastapi.testclient import TestClient

from main import app
from app.schemas.calculation import CalculationType


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def make_registration_data(username: str, email: str):
    return {
        "first_name": "Test",
        "last_name": "User",
        "email": email,
        "username": username,
        "password": "TestPass123",
    }


def test_user_register_and_login(client):
    register_payload = make_registration_data("testuser1", "test1@example.com")

    response = client.post("/users/register", json=register_payload)
    assert response.status_code == 201
    payload = response.json()
    assert payload["username"] == "testuser1"
    assert payload["email"] == "test1@example.com"
    assert "password_hash" not in payload

    login_payload = {
        "username": "testuser1",
        "password": "TestPass123",
    }
    response = client.post("/users/login", json=login_payload)
    assert response.status_code == 200
    login_data = response.json()
    assert login_data["token_type"] == "bearer"
    assert "access_token" in login_data
    assert login_data["user"]["username"] == "testuser1"


def test_user_registration_duplicate_returns_400(client):
    register_payload = make_registration_data("testuser2", "test2@example.com")
    response = client.post("/users/register", json=register_payload)
    assert response.status_code == 201

    response = client.post("/users/register", json=register_payload)
    assert response.status_code == 400
    assert "error" in response.json()
    assert "already exists" in response.json()["error"].lower()


def test_user_login_invalid_credentials(client):
    login_payload = {
        "username": "missing",
        "password": "DoesNotMatter1",
    }
    response = client.post("/users/login", json=login_payload)
    assert response.status_code == 401
    assert response.json()["error"] == "Invalid username or password"


def test_calculation_bread_lifecycle(client):
    create_payload = {
        "a": 5,
        "b": 3,
        "type": CalculationType.add.value,
    }
    create_response = client.post("/calculations", json=create_payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["a"] == 5.0
    assert created["b"] == 3.0
    assert created["type"] == CalculationType.add.value
    assert created["result"] == 8.0
    calculation_id = created["id"]

    list_response = client.get("/calculations")
    assert list_response.status_code == 200
    calculations = list_response.json()
    assert any(item["id"] == calculation_id for item in calculations)

    read_response = client.get(f"/calculations/{calculation_id}")
    assert read_response.status_code == 200
    read_payload = read_response.json()
    assert read_payload["id"] == calculation_id
    assert read_payload["result"] == 8.0

    update_payload = {
        "a": 10,
        "b": 2,
        "type": CalculationType.divide.value,
    }
    update_response = client.put(f"/calculations/{calculation_id}", json=update_payload)
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["a"] == 10.0
    assert updated["b"] == 2.0
    assert updated["type"] == CalculationType.divide.value
    assert updated["result"] == 5.0

    delete_response = client.delete(f"/calculations/{calculation_id}")
    assert delete_response.status_code == 204

    not_found_response = client.get(f"/calculations/{calculation_id}")
    assert not_found_response.status_code == 404


def test_calculation_invalid_data_returns_400(client):
    invalid_payload = {
        "a": 10,
        "b": 0,
        "type": CalculationType.divide.value,
    }

    response = client.post("/calculations", json=invalid_payload)
    assert response.status_code == 400
    assert "error" in response.json()
    assert "division by zero" in response.json()["error"].lower()

    response = client.put("/calculations/not-a-real-id", json={"a": 1, "b": 2, "type": CalculationType.add.value})
    assert response.status_code == 404
    assert response.json()["error"] == "Calculation not found"
