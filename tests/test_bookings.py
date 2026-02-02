import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_booking_success(
    client: AsyncClient, test_property, customer_token
):
    response = await client.post(
        "/bookings",
        json={
            "property_id": test_property.id,
            "guests": 2,
            "check_in": "2025-01-01",
            "check_out": "2025-01-02",
        },
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["guests"] == 2
    assert data["check_in"] == "2025-01-01"


@pytest.mark.asyncio
async def test_create_booking_unauthorized(client: AsyncClient, test_property):
    response = await client.post(
        "/bookings",
        json={
            "property_id": test_property.id,
            "guests": 2,
            "check_in": "2025-01-01",
            "check_out": "2025-01-02",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_booking_property_not_found(client: AsyncClient, customer_token):
    response = await client.post(
        "/bookings",
        json={
            "property_id": 999,
            "guests": 2,
            "check_in": "2025-01-01",
            "check_out": "2025-01-02",
        },
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_list_property(client: AsyncClient, test_booking, host_token):
    response = await client.get(
        "/bookings", headers={"Authorization": f"Bearer {host_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.asyncio
async def test_get_booking_detail(client: AsyncClient, test_booking, host_token):
    response = await client.get(
        f"/bookings/{test_booking.id}",
        headers={"Authorization": f"Bearer {host_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["property_id"] == test_booking.id


@pytest.mark.asyncio
async def test_accept_booking(client: AsyncClient, test_booking, host_token):
    response = await client.post(
        f"/bookings/{test_booking.id}/confirmation",
        headers={"Authorization": f"Bearer {host_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"


@pytest.mark.asyncio
async def test_cancel_booking(client: AsyncClient, test_booking, host_token):
    response = await client.delete(
        f"/bookings/{test_booking.id}",
        headers={"Authorization": f"Bearer {host_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"


@pytest.mark.asyncio
async def test_wrong_user_accept_booking(
    client: AsyncClient, test_booking, customer_token
):
    response = await client.post(
        f"/bookings/{test_booking.id}/confirmation",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_wrong_user_cancel_booking(
    client: AsyncClient, test_booking, customer_token
):
    response = await client.delete(
        f"/bookings/{test_booking.id}",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_cancel_booking(client: AsyncClient, test_booking, admin_token):
    response = await client.delete(
        f"/bookings/{test_booking.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"
