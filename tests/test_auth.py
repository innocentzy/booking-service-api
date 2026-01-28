import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/auth/register/host",
        json={
            "first_name": "Test",
            "last_name": "Name",
            "email": "newuser@example.com",
            "password": "password",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_customer):
    response = await client.post(
        "/auth/register/customer",
        json={
            "first_name": "Test",
            "last_name": "Name",
            "email": "customer@example.com",
            "password": "password",
        },
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_host):
    response = await client.post(
        "/auth/login",
        json={"email": "host@example.com", "password": "host123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["access_token"]["token_sign"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_host):
    response = await client.post(
        "/auth/login",
        json={"email": "host@example.com", "password": "wrong_password"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    response = await client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "password"},
    )
    assert response.status_code == 404
