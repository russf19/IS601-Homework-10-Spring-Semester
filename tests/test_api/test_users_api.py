import pytest
from httpx import AsyncClient
from app.database import get_async_db
from app.main import app
from app.models.user_model import User
from app.utils.security import hash_password  # Import your FastAPI app

@pytest.fixture
async def token(async_client, user):
    response = await async_client.post("/login/", json={"username": user.username, "password": user.clear_password})
    return response.json()["access_token"]

@pytest.fixture
async def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_retrieve_user(async_client, user, auth_headers):
    response = await async_client.get(f"/users/{user.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(user.id)
    assert data["username"] == user.username
    assert data["email"] == user.email

@pytest.mark.asyncio
async def test_create_user_invalid_email(async_client):
    user_data = {
        "username": "uniqueuser",
        "email": "notanemail",
        "password": "ValidPassword123!",
    }
    response = await async_client.post("/register/", json=user_data)
    assert response.status_code == 422
    assert "value is not a valid email" in response.json().get("detail", "")

@pytest.mark.parametrize("username,password,expected_status,expected_detail", [
    ("nonexistentuser", "DoesNotMatter123!", 401, "Incorrect username or password"),
    ("actualUser", "IncorrectPassword123!", 401, "Incorrect username or password"),
])
async def test_login_failure(async_client, username, password, expected_status, expected_detail):
    login_data = {"username": username, "password": password}
    response = await async_client.post("/login/", json=login_data)
    assert response.status_code == expected_status
    assert expected_detail in response.json().get("detail", "")