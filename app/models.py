import enum
from datetime import datetime, date

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"
    HOST = "host"


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "canceled"
    COMPLETED = "completed"


class PropertyStatus(str, enum.Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ARCHIVED = "archived"


class TokenType(str, enum.Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password: Mapped[str] = mapped_column(String(100))
    role: Mapped[UserRole] = mapped_column(default=UserRole.CUSTOMER)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="user", lazy="selectin"
    )
    properties: Mapped[list["Property"]] = relationship(
        back_populates="user", lazy="selectin"
    )


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(primary_key=True)
    host_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str] = mapped_column(Text)
    address: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(255))
    beds: Mapped[int] = mapped_column(default=1)
    price: Mapped[float] = mapped_column(default=0.0)
    status: Mapped[PropertyStatus] = mapped_column(default=PropertyStatus.AVAILABLE)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    bookings: Mapped[list["Booking"]] = relationship(back_populates="property")
    user: Mapped["User"] = relationship(back_populates="properties")


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    guest_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    check_in: Mapped[date] = mapped_column(default=datetime.now)
    check_out: Mapped[date] = mapped_column(default=datetime.now)
    guests: Mapped[int] = mapped_column(default=1)
    total_price: Mapped[float] = mapped_column(default=0.0)
    status: Mapped[BookingStatus] = mapped_column(default=BookingStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now)
    cancelled_at: Mapped[datetime] = mapped_column(default=datetime.now)

    property: Mapped["Property"] = relationship(
        back_populates="bookings", lazy="joined"
    )
    user: Mapped["User"] = relationship(back_populates="bookings", lazy="joined")
