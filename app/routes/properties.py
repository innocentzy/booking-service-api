from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    create_property,
    delete_property,
    get_user,
    get_property,
    get_properties,
    update_property,
    get_property_for_update,
    check_property_owner,
)
from app.database import get_db
from app.dependencies import get_admin_user, get_current_user
from app.models import User, UserRole
from app.schemas import (
    PropertyCreate,
    PropertyResponse,
    PropertyUpdate,
    PaginatedProperties,
    PropertyFilter,
)

router = APIRouter(prefix="/properties", tags=["properties"])


@router.get("", response_model=PaginatedProperties)
async def list_properties(
    limit: int = 100,
    offset: int = 0,
    host_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    city: str | None = None,
    beds: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    filters = PropertyFilter(
        min_price=min_price, max_price=max_price, city=city, beds=beds
    )
    properties, total = await get_properties(
        db, skip=offset, limit=limit, host_id=host_id, filters=filters
    )

    return PaginatedProperties(
        items=[
            PropertyResponse.model_validate(property_obj) for property_obj in properties
        ],
        limit=limit,
        offset=offset,
        total=total,
    )


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property_detail(property_id: int, db: AsyncSession = Depends(get_db)):
    property = await get_property(db, property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Property not found"
        )
    return property


@router.post(
    "",
    response_model=PropertyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_property(
    property: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role == UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only host users can add properties",
        )

    return await create_property(db, property, user.id)


@router.patch("/{property_id}", response_model=PropertyResponse)
async def modify_property(
    property_id: int,
    property_update: PropertyUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role == UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    property = await get_property_for_update(db, property_id)

    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Property not found"
        )

    if not await check_property_owner(db, property_id, user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    updated = await update_property(db, property_id, property_update)
    return updated


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_property(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role == UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    property = await get_property_for_update(db, property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Property not found"
        )

    if not await check_property_owner(db, property_id, user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    deleted = await delete_property(db, property_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete"
        )
    return None
