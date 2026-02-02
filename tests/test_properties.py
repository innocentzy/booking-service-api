import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_properties_empty(client: AsyncClient):
    response = await client.get("/properties")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_properties(client: AsyncClient, test_property):
    response = await client.get("/properties")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_list_properties_pagination(client: AsyncClient, test_property):
    response = await client.get("/properties?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 10
    assert data["offset"] == 0


@pytest.mark.asyncio
async def test_list_properties_filter_by_host(client: AsyncClient, test_property):
    response = await client.get("/properties?host_id=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_list_properties_filter_by_nonexistent_host(client: AsyncClient):
    response = await client.get("/properties?host_id=999")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_get_property_detail(client: AsyncClient, test_property):
    response = await client.get(f"/properties/{test_property.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Property"
    assert data["price"] == 100


@pytest.mark.asyncio
async def test_get_property_detail_not_found(client: AsyncClient):
    response = await client.get("/properties/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_property_as_host(client: AsyncClient, host_token):
    response = await client.post(
        "/properties",
        json={
            "title": "New Property",
            "description": "This is a new property",
            "address": "New Address",
            "price": 100,
            "city": "New City",
            "beds": 2,
        },
        headers={"Authorization": f"Bearer {host_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Property"
    assert data["price"] == 100


@pytest.mark.asyncio
async def test_add_property_as_customer(client: AsyncClient, customer_token):
    response = await client.post(
        "/properties",
        json={
            "title": "New Property",
            "description": "This is a new property",
            "address": "New Address",
            "price": 100,
            "city": "New City",
            "beds": 2,
        },
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_add_property_negative_price(client: AsyncClient, host_token):
    response = await client.post(
        "/properties",
        json={
            "title": "New Property",
            "description": "This is a new property",
            "address": "New Address",
            "price": -100,
            "city": "New City",
            "beds": 2,
        },
        headers={"Authorization": f"Bearer {host_token}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_property(client: AsyncClient, host_token, test_property):
    response = await client.patch(
        f"/properties/{test_property.id}",
        json={"title": "Updated Property"},
        headers={"Authorization": f"Bearer {host_token}"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Property"


@pytest.mark.asyncio
async def test_delete_property(client: AsyncClient, host_token, test_property):
    response = await client.delete(
        f"/properties/{test_property.id}",
        headers={"Authorization": f"Bearer {host_token}"},
    )
    assert response.status_code == 204

    response = await client.get(f"/properties/{test_property.id}")
    assert response.status_code == 404
