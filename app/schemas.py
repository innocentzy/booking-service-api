from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import UserRole, BookingStatus, PropertyStatus


class UserCreate(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: UserRole
    created_at: datetime


class PropertyBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=3, max_length=255)
    address: str = Field(..., min_length=3, max_length=255)
    city: str = Field(..., min_length=3, max_length=255)
    beds: int = Field(..., ge=1, le=10)
    host_id: int


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=255)
    description: str | None = Field(None, min_length=3, max_length=255)
    address: str | None = Field(None, min_length=3, max_length=255)
    city: str | None = Field(None, min_length=3, max_length=255)
    beds: int | None = Field(None, ge=1, le=10)


class PropertyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    host_id: int
    title: str
    description: str
    address: str
    city: str
    beds: int
    status: PropertyStatus
    created_at: datetime
    user: UserResponse


class PaginatedProperties(BaseModel):
    items: list[PropertyResponse]
    total: int
    limit: int
    offset: int


class BookingCreate(BaseModel):
    room_id: int
    guests: int


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    guest_id: int
    room_id: int
    guests: int
    check_in: datetime
    check_out: datetime
    total_price: float
    status: BookingStatus
    created_at: datetime
    updated_at: datetime
    cancelled_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
