from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    create_booking,
    get_bookings,
    get_booking,
    cancel_booking,
    confirm_booking,
    check_property_owner,
    check_booking_owner,
)
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, UserRole
from app.schemas import BookingCreate, BookingResponse

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("", response_model=list[BookingResponse])
async def list_bookings(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    bookings = await get_bookings(db, user.id)
    return bookings


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking_detail(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not await check_property_owner(
        db, booking_id, user.id
    ) and not await check_booking_owner(db, booking_id, user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    booking = await get_booking(db, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )
    return booking


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def place_booking(
    booking: BookingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role == UserRole.HOST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can place bookings",
        )
    try:
        return await create_booking(db, user.id, booking)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)


@router.get("/{booking_id}/confirmation", response_model=BookingResponse)
async def accept_booking(
    booking_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    booking = await get_booking(db, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )
    if not check_property_owner(db, booking.property_id, user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to confirm this booking",
        )
    confirmed = await confirm_booking(db=db, booking_id=booking_id)
    return confirmed


@router.delete("/{booking_id}", response_model=BookingResponse)
async def delete_booking(
    booking_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    booking = await get_booking(db, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )
    if not check_booking_owner(db, booking_id, user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    canceled = await cancel_booking(db=db, booking_id=booking_id)
    return canceled
