# tests/e2e/test_e2e.py
# HTTP-based E2E tests for FastAPI Calculator - More efficient than browser automation

import pytest
import requests
from uuid import uuid4


@pytest.fixture
def base_url(fastapi_server: str) -> str:
    """Returns the FastAPI server base URL."""
    return fastapi_server.rstrip("/")


def register_and_login(base_url: str, user_data: dict) -> dict:
    """Helper to register a user and return login response with token."""
    # Register
    reg_response = requests.post(f"{base_url}/users/register", json=user_data)
    assert reg_response.status_code == 201, f"Registration failed: {reg_response.text}"
    
    # Login
    login_payload = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    login_response = requests.post(f"{base_url}/users/login", json=login_payload)
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    return login_response.json()


# ---------------------------------------------------------------------------
# Health and Basic Tests
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_hello_world(base_url):
    """Test that the homepage is accessible."""
    response = requests.get(f"{base_url}/")
    assert response.status_code == 200
    assert "Hello World" in response.text or response.text


@pytest.mark.e2e
def test_calculator_add(base_url):
    """Test addition operation via API."""
    response = requests.post(f"{base_url}/add", json={"a": 10, "b": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["result"] == 15


@pytest.mark.e2e
def test_calculator_divide_by_zero(base_url):
    """Test division by zero error handling."""
    response = requests.post(f"{base_url}/divide", json={"a": 10, "b": 0})
    # Accept either 400 (Bad Request) or 422 (Validation Error)
    assert response.status_code in [400, 422]
    # Just verify we got an error response (don't check exact message format)
    assert response.status_code >= 400


# ---------------------------------------------------------------------------
# Authentication Tests
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_user_registration(base_url):
    """Test user registration."""
    user_data = {
        "username": f"testuser_{uuid4()}",
        "email": f"test_{uuid4()}@example.com",
        "password": "TestPass123"
    }
    response = requests.post(f"{base_url}/users/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]


@pytest.mark.e2e
def test_user_login(base_url):
    """Test user login and token generation."""
    user_data = {
        "username": f"loginuser_{uuid4()}",
        "email": f"login_{uuid4()}@example.com",
        "password": "TestPass123"
    }
    login_data = register_and_login(base_url, user_data)
    
    assert "access_token" in login_data
    assert login_data["token_type"].lower() == "bearer"


# ---------------------------------------------------------------------------
# BREAD Operations Tests
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_bread_create_calculation(base_url):
    """Test creating a calculation (CREATE)."""
    user_data = {
        "username": f"create_{uuid4()}",
        "email": f"create_{uuid4()}@example.com",
        "password": "TestPass123"
    }
    token_data = register_and_login(base_url, user_data)
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {"a": 10, "b": 5, "type": "add"}
    response = requests.post(f"{base_url}/calculations", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["result"] == 15
    assert "id" in data


@pytest.mark.e2e
def test_bread_browse_calculations(base_url):
    """Test browsing calculations (READ/BROWSE)."""
    user_data = {
        "username": f"browse_{uuid4()}",
        "email": f"browse_{uuid4()}@example.com",
        "password": "TestPass123"
    }
    token_data = register_and_login(base_url, user_data)
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a calculation
    payload = {"a": 20, "b": 3, "type": "subtract"}
    create_response = requests.post(f"{base_url}/calculations", json=payload, headers=headers)
    assert create_response.status_code == 201
    
    # Browse/list calculations
    list_response = requests.get(f"{base_url}/calculations", headers=headers)
    assert list_response.status_code == 200
    calcs = list_response.json()
    assert len(calcs) > 0
    assert any(c["result"] == 17 for c in calcs)


@pytest.mark.e2e
def test_bread_read_single_calculation(base_url):
    """Test reading a single calculation."""
    user_data = {
        "username": f"read_{uuid4()}",
        "email": f"read_{uuid4()}@example.com",
        "password": "TestPass123"
    }
    token_data = register_and_login(base_url, user_data)
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a calculation
    payload = {"a": 15, "b": 7, "type": "multiply"}
    create_response = requests.post(f"{base_url}/calculations", json=payload, headers=headers)
    assert create_response.status_code == 201
    calc_id = create_response.json()["id"]
    
    # Read single calculation
    read_response = requests.get(f"{base_url}/calculations/{calc_id}", headers=headers)
    assert read_response.status_code == 200
    data = read_response.json()
    assert data["id"] == calc_id
    assert data["result"] == 105


@pytest.mark.e2e
def test_bread_update_calculation(base_url):
    """Test updating a calculation (UPDATE/EDIT)."""
    user_data = {
        "username": f"update_{uuid4()}",
        "email": f"update_{uuid4()}@example.com",
        "password": "TestPass123"
    }
    token_data = register_and_login(base_url, user_data)
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a calculation
    payload = {"a": 12, "b": 3, "type": "divide"}
    create_response = requests.post(f"{base_url}/calculations", json=payload, headers=headers)
    assert create_response.status_code == 201
    calc_id = create_response.json()["id"]
    
    # Update calculation
    update_payload = {"a": 20, "b": 4, "type": "divide"}
    update_response = requests.put(f"{base_url}/calculations/{calc_id}", json=update_payload, headers=headers)
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["result"] == 5


@pytest.mark.e2e
def test_bread_delete_calculation(base_url):
    """Test deleting a calculation (DELETE)."""
    user_data = {
        "username": f"delete_{uuid4()}",
        "email": f"delete_{uuid4()}@example.com",
        "password": "TestPass123"
    }
    token_data = register_and_login(base_url, user_data)
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a calculation
    payload = {"a": 8, "b": 2, "type": "add"}
    create_response = requests.post(f"{base_url}/calculations", json=payload, headers=headers)
    assert create_response.status_code == 201
    calc_id = create_response.json()["id"]
    
    # Delete calculation
    delete_response = requests.delete(f"{base_url}/calculations/{calc_id}", headers=headers)
    assert delete_response.status_code in [200, 204]
    
    # Verify deletion
    get_response = requests.get(f"{base_url}/calculations/{calc_id}", headers=headers)
    assert get_response.status_code == 404


# ---------------------------------------------------------------------------
# Authorization Tests
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_unauthorized_access_calculations(base_url):
    """Test that unauthenticated requests are rejected."""
    response = requests.get(f"{base_url}/calculations")
    assert response.status_code == 401


@pytest.mark.e2e
def test_invalid_token_access(base_url):
    """Test that invalid tokens are rejected."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(f"{base_url}/calculations", headers=headers)
    assert response.status_code == 401


@pytest.mark.e2e
def test_user_isolation(base_url):
    """Test that users only see their own calculations."""
    # Create user 1 and their calculation
    user1_data = {
        "username": f"user1_{uuid4()}",
        "email": f"user1_{uuid4()}@example.com",
        "password": "TestPass123"
    }
    user1_token = register_and_login(base_url, user1_data)["access_token"]
    user1_headers = {"Authorization": f"Bearer {user1_token}"}
    
    payload1 = {"a": 5, "b": 3, "operation": "add"}
    user1_calc = requests.post(f"{base_url}/calculations", json=payload1, headers=user1_headers).json()
    
    # Create user 2 and their calculation
    user2_data = {
        "username": f"user2_{uuid4()}",
        "email": f"user2_{uuid4()}@example.com",
        "password": "TestPass123"
    }
    user2_token = register_and_login(base_url, user2_data)["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}
    
    payload2 = {"a": 10, "b": 2, "operation": "multiply"}
    user2_calc = requests.post(f"{base_url}/calculations", json=payload2, headers=user2_headers).json()
    
    # User 1 should only see their own calculation
    user1_calcs = requests.get(f"{base_url}/calculations", headers=user1_headers).json()
    assert len(user1_calcs) == 1
    assert user1_calcs[0]["id"] == user1_calc["id"]
    
    # User 2 should only see their own calculation
    user2_calcs = requests.get(f"{base_url}/calculations", headers=user2_headers).json()
    assert len(user2_calcs) == 1
    assert user2_calcs[0]["id"] == user2_calc["id"]


# ---------------------------------------------------------------------------
# Error Handling Tests
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_invalid_calculation_operation(base_url):
    """Test handling of invalid calculation operations."""
    user_data = {
        "username": f"invalid_{uuid4()}",
        "email": f"invalid_{uuid4()}@example.com",
        "password": "TestPass123"
    }
    token_data = register_and_login(base_url, user_data)
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {"a": 5, "b": 3, "operation": "invalid_op"}
    response = requests.post(f"{base_url}/calculations", json=payload, headers=headers)
    assert response.status_code in [400, 422]


@pytest.mark.e2e
def test_missing_calculation_fields(base_url):
    """Test handling of missing required fields."""
    user_data = {
        "username": f"missing_{uuid4()}",
        "email": f"missing_{uuid4()}@example.com",
        "password": "TestPass123"
    }
    token_data = register_and_login(base_url, user_data)
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {"a": 5}  # Missing 'b' and 'operation'
    response = requests.post(f"{base_url}/calculations", json=payload, headers=headers)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# New Feature: Modulus and Power Operations
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_calculator_modulus(base_url):
    """Test modulus operation via quick calculator endpoint."""
    response = requests.post(f"{base_url}/modulus", json={"a": 10, "b": 3})
    assert response.status_code == 200
    assert response.json()["result"] == pytest.approx(1)


@pytest.mark.e2e
def test_calculator_modulus_by_zero(base_url):
    """Test modulus by zero returns an error."""
    response = requests.post(f"{base_url}/modulus", json={"a": 10, "b": 0})
    assert response.status_code == 400


@pytest.mark.e2e
def test_calculator_power(base_url):
    """Test exponentiation via quick calculator endpoint."""
    response = requests.post(f"{base_url}/power", json={"a": 2, "b": 10})
    assert response.status_code == 200
    assert response.json()["result"] == pytest.approx(1024)


@pytest.mark.e2e
def test_bread_modulus_calculation(base_url):
    """Test saving a modulus calculation via BREAD endpoint."""
    user_data = {
        "username": f"mod_{uuid4()}",
        "email": f"mod_{uuid4()}@example.com",
        "password": "TestPass123"
    }
    token = register_and_login(base_url, user_data)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"a": 17, "b": 5, "type": "modulus"}
    response = requests.post(f"{base_url}/calculations", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["result"] == pytest.approx(2)
    assert data["type"] == "modulus"


@pytest.mark.e2e
def test_bread_power_calculation(base_url):
    """Test saving a power calculation via BREAD endpoint."""
    user_data = {
        "username": f"pow_{uuid4()}",
        "email": f"pow_{uuid4()}@example.com",
        "password": "TestPass123"
    }
    token = register_and_login(base_url, user_data)["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"a": 3, "b": 4, "type": "power"}
    response = requests.post(f"{base_url}/calculations", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["result"] == pytest.approx(81)
    assert data["type"] == "power"

