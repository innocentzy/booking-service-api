from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from datetime import date

from app.models import Booking, Property, User, PropertyStatus, BookingStatus
from app.schemas import (
    BookingCreate,
    BookingResponse,
    PaginatedProperties,
    PropertyCreate,
    PropertyResponse,
    PropertyUpdate,
    UserCreate,
    UserResponse,
)
from app.security import get_password_hash


async def get_user(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: User) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        password=hashed_password,
        role=user.role,
    )
    db.add(db_user)
    await db.flush()
    await db.refresh(db_user)
    return db_user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_property(db: AsyncSession, property: PropertyCreate) -> Property:
    db_property = Property(**property.model_dump())
    db.add(db_property)
    await db.flush()
    await db.refresh(db_property)
    return db_property


async def get_properties(
    db: AsyncSession, skip: int = 0, limit: int = 100, host_id: int | None = None
) -> tuple[list[Property], int]:
    query = select(Property)
    count_query = select(func.count(Property.id))

    if host_id:
        query = query.where(Property.host_id == host_id)
        count_query = count_query.where(Property.host_id == host_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all()), total


async def get_property(db: AsyncSession, property_id: int) -> Property | None:
    result = await db.execute(select(Property).where(Property.id == property_id))
    return result.scalar_one_or_none()


async def update_property(
    db: AsyncSession, property_id: int, property_update: PropertyUpdate
) -> Property | None:
    db_property = await get_property(db, property_id)
    if not db_property:
        return None

    update_data = property_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_property, field, value)

    await db.flush()
    await db.refresh(db_property)
    return db_property


async def delete_property(db: AsyncSession, property_id: int) -> bool:
    db_property = await get_property(db, property_id)
    if not db_property:
        return False
    await db.delete(db_property)
    await db.flush()
    return True


async def get_property_for_update(
    db: AsyncSession, property_id: int
) -> Property | None:

    result = await db.execute(
        select(Property).where(Property.id == property_id).with_for_update()
    )
    return result.scalar_one_or_none()


async def check_availability(db: AsyncSession, booking_data: BookingCreate) -> bool:
    query = select(Booking).where(
        and_(
            Booking.property_id == booking_data.property_id,
            Booking.status.in_(
                [
                    BookingStatus.CONFIRMED,
                    BookingStatus.PENDING,
                ]
            ),
            or_(
                and_(
                    Booking.check_in < booking_data.check_out,
                    Booking.check_out > booking_data.check_in,
                )
            ),
        )
    )

    result = await db.execute(query)
    conflicting_bookings = result.scalars().all()

    return len(conflicting_bookings) == 0


async def create_booking(
    db: AsyncSession, guest_id: int, booking_data: BookingCreate
) -> Booking:
    property = await get_property_for_update(db, booking_data.property_id)
    if not property:
        raise ValueError("Property not found")

    if property.status != PropertyStatus.AVAILABLE:
        raise ValueError("Property is not available")

    if not await check_availability(db, booking_data):
        raise ValueError("Property is not available for the selected dates")

    booking = Booking(
        property_id=booking_data.property_id,
        guest_id=guest_id,
        guests=booking_data.guests,
        check_in=booking_data.check_in,
        check_out=booking_data.check_out,
        total_price=property.price
        * booking_data.guests
        * (booking_data.check_out - booking_data.check_in).days,
    )
    db.add(booking)
    await db.flush()
    await db.refresh(booking)
    return booking
